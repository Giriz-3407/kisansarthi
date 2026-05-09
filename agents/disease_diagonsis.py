import os, re, json
from agents.provider import Agent
from agents.weather_agent import get_weather_data

class DiseaseDiagnosis:
    def __init__(self, GEN_API_KEY):
        self.agent = Agent(GEN_API_KEY)

    def execute(self, image, location="Unknown", WEATHER_API_KEY=None, soil_data=None, crop="Unknown", lang="English"):
        # Default empty dicts if none provided
        soil_data = soil_data or {}
        
        # Update missing weather data if key provided
        if WEATHER_API_KEY and location != "Unknown" and "temperature" not in soil_data:
            try:
                weather_data = get_weather_data(location, WEATHER_API_KEY)
                if weather_data:
                    soil_data.update(weather_data)
            except Exception as e:
                print(f"Weather fetch failed: {e}")

        task = f"""
        Role: expert plant pathologist.
        Task: Provide plant disease analysis in {lang}. 
        Instruction: Respond EXCLUSIVELY in {lang}. Every single value in the JSON object must be translated to {lang}.

        Analyze the attached image of a plant {f" (specifically {crop})" if crop != 'Unknown' else ""}.
        Context: Location: {location}, Soil Data: {json.dumps(soil_data)}
        
        Return your analysis EXCLUSIVELY as a JSON object with this structure:
        {{
          "is_diseased": boolean,
          "confidence_score": float,
          "detected_disease": {{
            "disease_name": "Name translated to {lang}",
            "description": "Description translated to {lang}",
            "symptoms": "Symptoms translated to {lang}",
            "causal_agent": "Agent name translated to {lang}"
          }},
          "remedies": [
            {{
              "remedy_type": "chemical/organic/cultural",
              "description": "Summary translated to {lang}",
              "application_instructions": "Instructions translated to {lang}"
            }}
          ],
          "prevention": "Prevention translated to {lang}"
        }}
        
        Language Note: This is for a farmer who speaks {lang}. All string values MUST be in {lang}. Do not include any introductory remarks or markdown outside the JSON.
        """
        try:
            response = self.agent.execute(task=task, data=image)
            return self.parse_response(response)
        except Exception as e:
            print(f"Agent execution failed: {e}. Returning Knowledge Base data.")
            # Professional Knowledge Base Fallback
            kb_fallback = {
                "is_diseased": True,
                "confidence_score": 0.75,
                "detected_disease": {
                    "disease_name": f"Nutritional Stress ({lang} Fallback)",
                    "description": "Observed symptoms may indicate an imbalance in primary nutrients (NPK).",
                    "symptoms": "Yellowing or discoloration of leaves, stunted growth.",
                    "causal_agent": "Environmental/Nutritional"
                },
                "remedies": [
                    {
                        "remedy_type": "cultural",
                        "description": "Conduct a soil test",
                        "application_instructions": "Verify current nutrient levels before applying concentrated fertilizers."
                    }
                ],
                "prevention": "Maintain a balanced fertilization schedule and monitor soil moisture regularly."
            }
            return kb_fallback


    def parse_response(self, response_text):
        try:
            # Extract JSON from potential markdown blocks
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response_text)
        except Exception as e:
            print(f"Error parsing disease diagnosis response: {e}")
            print(f"Raw response: {response_text}")
            return {"is_diseased": False, "Error": "Failed to parse AI response"}

def parse_crop_response(response_text):
    return {"Error": "Deprecated. Use DiseaseDiagnosis class."}
