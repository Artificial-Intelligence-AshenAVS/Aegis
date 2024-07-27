import requests
import os

class SafeguardAPI:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.getenv("SAFEGUARD_API_URL")

    def moderate(self, text):
        try:
            response = requests.post(self.api_url, json={'input_text': text})
            response.raise_for_status()  # Raises an error for bad status codes
            data = response.json()
            if 'result' in data:
                return data['result']
            else:
                return f"Unexpected response format: {data}"
        except requests.RequestException as e:
            return f"Error: Unable to reach safeguard API. Details: {e}"
        except ValueError:
            return "Error: Invalid response received from safeguard API."

            # curl -X POST http://127.0.0.1:5001/toggle_safeguard
