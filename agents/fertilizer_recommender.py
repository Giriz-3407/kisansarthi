import os, re, warnings
# Suppress the unpickling warnings
warnings.filterwarnings("ignore", category=UserWarning)
import pickle
import pandas as pd
from agents.provider import Agent
import aiohttp
import json
import asyncio
from bs4 import BeautifulSoup
from agents.weather_agent import get_weather_data


async def fetch_content(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            html_content = await response.text()
            soup = BeautifulSoup(html_content, 'html.parser')
            text_data = soup.get_text(separator='\n', strip=True)
            return {url: text_data}
    except Exception as e:
        return {url: f"Error: {str(e)}"}


async def scrape_websites_parallel(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_content(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results


def extract_text_from_websites(urls):
    return asyncio.run(scrape_websites_parallel(urls))


from agents.knowledge_base import get_fert_details, FERT_LABEL_MAP

class FertilizerRecommender:
    def __init__(self, GEN_API_KEY):
        self.agent = Agent(GEN_API_KEY)
        self.model_path = './agents/model/fertilizer.pkl'
        self.crop_mapping = {
            'sugarcane': 1, 'jowar': 2, 'sorghum': 2, 'cotton': 3,
            'rice': 4, 'wheat': 5, 'groundnut': 6, 'maize': 7,
            'corn': 7, 'tur': 8, 'redgram': 8, 'urad': 9,
            'blackgram': 9, 'moong': 10, 'greengram': 10, 'gram': 11,
            'bengalgram': 11, 'masoor': 12, 'soybean': 13,
            'soyabean': 13, 'ginger': 14, 'turmeric': 15, 'grapes': 16,
        }

    def load_model_and_predict(self, soil_data, crop):
        if not os.path.exists(self.model_path):
            print(f"❌ Error: Model file not found at {self.model_path}")
            raise FileNotFoundError(f"Model file not found at {self.model_path}")

        with open(self.model_path, 'rb') as model_file:
            model = pickle.load(model_file)

        # Crop Mapping
        crop_encoded = self.crop_mapping.get(str(crop).strip().lower())
        soil_color_encoded = soil_data.get('Soil_color')

        if crop_encoded is None:
            raise ValueError(f"Crop '{crop}' is not supported by the fertilizer model mapping.")
        if soil_color_encoded not in [0, 1, 2, 3, 4]:
            raise ValueError(f"Soil color '{soil_color_encoded}' is not supported by the fertilizer model mapping.")

        required_fields = ['Nitrogen', 'Phosphorus', 'Potassium', 'pH', 'rainfall', 'temperature']
        missing_fields = [field for field in required_fields if soil_data.get(field) is None]
        if missing_fields:
            raise ValueError(f"Missing required fertilizer ML inputs: {', '.join(missing_fields)}")

        # Input Data - Must match training structure exactly
        input_data = pd.DataFrame([{
            'Soil_color': soil_color_encoded,
            'Nitrogen': int(soil_data['Nitrogen']),
            'Phosphorus': int(soil_data['Phosphorus']),
            'Potassium': int(soil_data['Potassium']),
            'pH': float(soil_data['pH']),
            'Rainfall': float(soil_data['rainfall']),
            'Temperature': float(soil_data['temperature']),
            'Crop': crop_encoded
        }])

        # Prediction
        prediction = model.predict(input_data)[0]
        return prediction

    def execute(self, location, WEATHER_API_KEY, soil_data, crop, lang="English"):
        # 1. Fill weather-only inputs from live weather. Soil readings remain mandatory.
        if "rainfall" not in soil_data:
            d = get_weather_data(location, WEATHER_API_KEY)
            if not d or d.get('rainfall') is None:
                raise ValueError("Rainfall is required for fertilizer ML input.")
            soil_data['rainfall'] = d['rainfall']
            if soil_data.get('humidity') is None and d.get('humidity') is not None:
                soil_data['humidity'] = d['humidity']

        # 2. Model Prediction
        prediction_val = self.load_model_and_predict(soil_data, crop)
        prediction_key = str(prediction_val)
        if prediction_key not in FERT_LABEL_MAP:
            raise ValueError(f"Fertilizer prediction '{prediction_val}' is not supported by FERT_LABEL_MAP.")
        prediction_name = FERT_LABEL_MAP[prediction_key]

        if prediction_name is None or prediction_name == "None":
            raise ValueError("Fertilizer model returned an invalid prediction.")

        print(f"ML Model Result: {prediction_name}")

        # 3. Get rich data from Knowledge Base
        kb_data = get_fert_details(prediction_name)

        # 4. Knowledge base response used when translation generation is unavailable.
        kb_response = f"""
Crop: {crop} ({lang})
Fertilizer: {prediction_name}
Product: {kb_data['Product']}
Buy at: {kb_data['Buy at']}
Amount: {kb_data['Amount']}
Price: {kb_data['Price']}
Description: {kb_data['Description']}
Explanation: {kb_data['Explanation']}
"""

        task = f"""
Role: expert agricultural specialist.
Task: Provide fertilizer recommendations EXCLUSIVELY in the {lang} language.
Instruction: You MUST TRANSLATE ALL VALUES (the text on the right side of the colon) into {lang}. This is an absolute requirement. This includes descriptions, reasoning, dosages, and every single recommendation. Do NOT output English for the values. However, you MUST keep the KEYS on the left side of the colon EXACTLY as they are written in English below. Do not translate the formatting keys.

Format: Your response MUST strictly follow this structure:

Crop: <crop name in {lang}>
Fertilizer: <fertilizer name in {lang}>
Product: <product name in {lang}>
Buy at: <availability info in {lang}>
Amount: <dosage details in {lang}>
Price: <pricing in {lang}>
Description: <brief description in {lang}>
Explanation: <Layman's explanation in {lang}>

Context:
Soil Data: {soil_data}
Target Crop: {crop}
Model Recommendation: {prediction_name}
Knowledge Base Context: {kb_data['Description']}

Language Note: The values MUST be mapped to the English labels above but written in {lang}. Respond ONLY with the data format. Do not include introductory remarks.
"""

        try:
            response = self.agent.execute(task=task)
            return parse_crop_response(response)
        except Exception as e:
            print(f"Agent execution failed: {e}. Returning Knowledge Base data.")
            return parse_crop_response(kb_response)


def parse_crop_response(response_text):
    """
    Parses the crop recommendation response and converts it into a dictionary.

    Args:
        response_text (str): The input text in the specified response format.

    Returns:
        dict: A dictionary containing parsed information.
    """
    pattern = re.compile(
        r"Crop:\s*(.*?)\s*"
        r"Fertilizer:\s*(.*?)\s*"
        r"Product:\s*(.*?)\s*"
        r"Buy at:\s*(.*?)\s*"
        r"Amount:\s*(.*?)\s*"
        r"Price:\s*(.*?)\s*"
        r"Description:\s*(.*?)\s*"
        r"Explanation:\s*(.*)",
        re.DOTALL
    )

    match = pattern.search(response_text)
    if not match:
        return {"Error": "Invalid or improperly formatted response"}

    fields = ["Crop", "Fertilizer", "Fertilizer_Product", "Buy at", "Amount", "Price", "Description", "Explanation"]
    data = {field: match.group(i + 1).strip() for i, field in enumerate(fields)}
    print(data)
    return data
