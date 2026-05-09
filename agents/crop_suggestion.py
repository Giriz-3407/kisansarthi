from agents.provider import Agent
from agents.weather_agent import get_weather_data
from agents.knowledge_base import DEFAULT_CROP, get_crop_details
import joblib
import pandas as pd
import re
import time

model = joblib.load('./agents/model/crop_model.pkl')

class CropSuggestionInputError(ValueError):
    pass

def require_detail(data, key):
    value = data.get(key)
    if value is None:
        raise ValueError(f"Crop knowledge base is missing '{key}'.")
    return value

def build_basic_crop_response(prediction, lang="English"):
    return {
        "Crop": prediction,
        "Match": DEFAULT_CROP["Match"],
        "Description": DEFAULT_CROP["Description"],
        "Explanation": "Basic recommendation (AI unavailable)",
        "growing_season": DEFAULT_CROP["growing_season"],
        "best_season": "Local Kharif or Rabi cycles",
        "growth_duration": "--",
        "water_requirement": DEFAULT_CROP["water_requirement"],
        "total_water_liters": "--",
        "spacing": "--",
        "expected_yield": DEFAULT_CROP["expected_yield"],
        "Recommendations": DEFAULT_CROP["Recommendations"],
    }

def attach_prediction_metadata(response, top_crops):
    response["top_crops"] = [
        {"crop": crop, "confidence": confidence}
        for crop, confidence in top_crops
    ]
    response["primary_crop"] = response["top_crops"][0] if response["top_crops"] else None
    if response["primary_crop"]:
        response["Match"] = response["primary_crop"]["confidence"]
    return response

def parse_or_basic(response_text, prediction, lang="English"):
    parsed_response = parse_crop_response(response_text, lang)
    if parsed_response.get("Error"):
        print(f"Crop response parsing failed: {parsed_response['Error']}. Returning basic ML recommendation.")
        return build_basic_crop_response(prediction, lang)
    return parsed_response

def diagnose_agent_failure(error):
    message = str(error).lower()
    if "503" in message or "unavailable" in message or "overload" in message:
        return "Model overload or temporary service unavailable (503 UNAVAILABLE)."
    if "429" in message or "quota" in message or "rate" in message:
        return "API quota exhaustion or rate limiting."
    if "api key" in message or "permission" in message or "unauthorized" in message or "401" in message or "403" in message:
        return "Invalid API key or permission problem."
    if "timeout" in message or "timed out" in message or "connection" in message or "network" in message:
        return "Network timeout or connectivity issue."
    return "Unknown agent failure."

class Crop_Suggestion:
    def __init__(self, GEN_API_KEY):
        self.agent = Agent(GEN_API_KEY)

    def execute(self, location, WEATHER_API_KEY, soil_data=None, crop='Tur', lang="English", lat=None, lon=None):
        soil_data = soil_data or {}

        required_fields = ['pH', 'temperature', 'humidity', 'Nitrogen', 'Phosphorus', 'Potassium', 'rainfall']
        missing_fields = [field for field in required_fields if soil_data.get(field) is None]
        if missing_fields:
            raise CropSuggestionInputError(f"Missing required crop suggestion ML inputs: {', '.join(missing_fields)}")

        try:
            ph = float(soil_data['pH'])
            t = float(soil_data['temperature'])
            h = float(soil_data['humidity'])
            n = float(soil_data['Nitrogen'])
            p = float(soil_data['Phosphorus'])
            k = float(soil_data['Potassium'])
            rainfall = float(soil_data['rainfall'])
        except (TypeError, ValueError) as e:
            raise CropSuggestionInputError("Invalid crop suggestion ML input values.") from e

        input_df = pd.DataFrame([{
            "N": n,
            "P": p,
            "K": k,
            "temperature": t,
            "humidity": h,
            "ph": ph,
            "rainfall": rainfall,
        }], columns=["N", "P", "K", "temperature", "humidity", "ph", "rainfall"])
        print("MODEL INPUT:", input_df)
        prediction = model.predict(input_df)[0]
        probabilities = model.predict_proba(input_df)[0]
        classes = model.classes_
        top_indices = probabilities.argsort()[-3:][::-1]
        top_crops = [(classes[idx], float(probabilities[idx])) for idx in top_indices]
        print("TOP PREDICTIONS:", top_crops)
        if not top_crops:
            raise RuntimeError("Crop suggestion model did not return any supported crop probabilities.")

        print(f"ML Model Result: {prediction}")

        basic_response = attach_prediction_metadata(build_basic_crop_response(prediction, lang), top_crops)

        # 3. Get rich data from Knowledge Base (falling back cleanly if missing)
        try:
            kb_data = get_crop_details(prediction)
            kb_response = f"""
Crop: {prediction}
Match: {require_detail(kb_data, 'Match')}
Description: {require_detail(kb_data, 'Description')}
Explanation: {require_detail(kb_data, 'Explanation')}
Growing Season: {require_detail(kb_data, 'growing_season')}
Best Sowing Season: Local Kharif or Rabi cycles
Growth Duration: 90-120 Days
Water Requirement: {require_detail(kb_data, 'water_requirement')}
Total Water (Liters): --
Spacing: --
Expected Yield: {require_detail(kb_data, 'expected_yield')}
Recommendations: {require_detail(kb_data, 'Recommendations')}
"""
        except Exception as e:
            print(f"Crop knowledge base failed: {e}. Returning basic ML recommendation.")
            return basic_response

        task = f"""
Role: expert agricultural specialist.
Task: Provide detailed crop recommendations exclusively in the {lang} language. 
Instruction: You MUST TRANSLATE ALL VALUES (the text on the right side of the colon) into {lang}. This is an absolute requirement. This includes descriptions, reasoning, and every single recommendation. Do NOT output English for the values. However, you MUST keep all KEYS (the text on the left side of the colon) EXACTLY as they are written in English below. Keep descriptions and explanations very short and direct.

Format: Your response MUST strictly follow this exact structure, keeping the English labels:

English_Crop_Name: <Original English name of the crop>
Crop: <name of the crop translated to {lang}>
Match: <Matching Score between 0 to 1>
Description: <a brief 1-sentence description in {lang}>
Explanation: <1-sentence explanation for the farmer in {lang}>
Growing Season: <season details in {lang}>
Best Sowing Season: <Ideal month/season to plant in {lang}>
Growth Duration: <Total days from planting to harvest in {lang}>
Water Requirement: <Brief water status in {lang}>
Total Water (Liters): <Estimate total liters needed per acre/plant in {lang}>
Spacing: <Row x Column spacing in {lang}>
Expected Yield: <yield details in {lang}>
Recommendations: <List of 3 tips in {lang} separated by '\\n'>

Context:
Suggested Crop: {prediction}
Soil Data: {soil_data}
Knowledge Base Context: {require_detail(kb_data, 'Description')}

Language Note: This is for a farmer who speaks {lang}. Respond ONLY with the requested data format. Do not translate the left-hand labels.
"""
        retry_count = 2
        for attempt in range(retry_count):
            print("[AGENT REQUEST] crop:", prediction)
            try:
                response = self.agent.execute(task=task)
                print("[AGENT SUCCESS] crop:", prediction)
                parsed_response = parse_crop_response(response, lang)
                if parsed_response.get("Error"):
                    print(f"Agent response parsing failed: {parsed_response['Error']}. Returning Knowledge Base data.")
                    return attach_prediction_metadata(parse_or_basic(kb_response, prediction, lang), top_crops)
                return attach_prediction_metadata(parsed_response, top_crops)
            except Exception as e:
                print("[AGENT FAILURE]")
                print("Crop:", prediction)
                print("Error:", str(e))
                print("Error Type:", type(e))
                print("Likely Cause:", diagnose_agent_failure(e))
                print(f"[AGENT ERROR] crop={prediction}, error={str(e)}")
                if attempt < retry_count - 1 and ("503" in str(e) or "UNAVAILABLE" in str(e).upper()):
                    time.sleep(1)
                    continue
                return attach_prediction_metadata(parse_or_basic(kb_response, prediction, lang), top_crops)

def parse_crop_response(response_text, lang="English"):
    pattern = re.compile(
        r"Crop:\s*(.*?)\s*"
        r"Match:\s*(.*?)\s*"
        r"Description:\s*(.*?)\s*"
        r"Explanation:\s*(.*?)\s*"
        r"Growing Season:\s*(.*?)\s*"
        r"(?:Best Sowing Season:\s*(.*?)\s*)?"
        r"(?:Growth Duration:\s*(.*?)\s*)?"
        r"Water Requirement:\s*(.*?)\s*"
        r"(?:Total Water \(Liters\):\s*(.*?)\s*)?"
        r"(?:Spacing:\s*(.*?)\s*)?"
        r"Expected Yield:\s*(.*?)\s*"
        r"Recommendations:\s*(.*)",
        re.DOTALL | re.IGNORECASE
    )

    match = pattern.search(response_text)
    if not match:
        return {"Error": "Invalid or improperly formatted response"}

    fields = [
        "Crop", "Match", "Description", "Explanation",
        "growing_season", "best_season", "growth_duration",
        "water_requirement", "total_water_liters", "spacing",
        "expected_yield", "Recommendations"
    ]
    data = {field: match.group(i+1).strip() if match.group(i+1) else "--" for i, field in enumerate(fields)}
    return data
