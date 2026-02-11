
from google import genai
import os

CREDENTIALS_PATH = "/Users/rci/lekhaslides/celtic-origin-480214-d5-e0c80e18c8c5.json"
PROJECT_ID = "celtic-origin-480214-d5"

def test_genai():
    print("--- Testing google-genai SDK ---")
    try:
        # Load service account credentials for google-genai
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
        
        client = genai.Client(vertexai=True, project=PROJECT_ID, location='us-central1')
        
        print("Model check...")
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents='Hello, are you there?'
        )
        print(f"✅ Success! Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed with google-genai: {e}")

test_genai()
