from google import genai
from google.genai import types
import os

class Agent:
    def __init__(self, GEN_API_KEY):
        self.api_key = GEN_API_KEY
        self.client = genai.Client(api_key=GEN_API_KEY)

    def execute(self, task, data=None):
        contents = [task]
        if data:
            if isinstance(data, dict) and 'data' in data:
                # Wrap the bytes into a Part object
                part = types.Part.from_bytes(
                    data=data['data'],
                    mime_type=data.get('mime_type', 'image/jpeg')
                )
                contents.append(part)
            else:
                contents.append(data)
            
        # The contents list now has [str, Part]
        response = self.client.models.generate_content(
            model="gemini-flash-latest", 
            contents=contents
        )
        return response.text