import json
import re

class JsonExtractor:
    @staticmethod
    def extract_json_from_reading(reading):
        regex = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(regex, reading)
        if match and match.group(1):
            try:
                json_data = json.loads(match.group(1))
                return json_data
            except json.JSONDecodeError as e:
                print("Error parsing JSON:", e)
        return None
