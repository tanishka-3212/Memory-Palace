import requests
import json

class OpenAIImageGenerator:
    API_KEY = "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"
    API_URL = "https://api.openai.com/v1/images/generations"

    @classmethod
    def generate_image(cls, prompt):
        # Create the request body
        request_body = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }

        # Set up the headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.API_KEY}"
        }

        # Send the request
        response = requests.post(
            cls.API_URL,
            headers=headers,
            json=request_body
        )

        # Check for successful response
        response.raise_for_status()
        
        # Return the JSON response
        return response.json()

if __name__ == "__main__":
    try:
        response = OpenAIImageGenerator.generate_image("a futuristic city at night")
        print(json.dumps(response, indent=2))
        
        # Extract the image URL
        image_url = response['data'][0]['url']
        print(f"\nGenerated image URL: {image_url}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")