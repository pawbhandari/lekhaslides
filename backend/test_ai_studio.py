
import google.generativeai as genai
from google.oauth2 import service_account
import google.auth
import os

CREDENTIALS_PATH = "/Users/rci/lekhaslides/celtic-origin-480214-d5-e0c80e18c8c5.json"

def test_ai_studio():
    print("--- Testing AI Studio SDK with Service Account ---")
    try:
        # Load credentials
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, 
            scopes=['https://www.googleapis.com/auth/generative-language'])
        
        # Configure genai with these credentials
        # Note: google-generativeai doesn't natively take creds object like Vertex does
        # It usually prefers an API Key. 
        # But we can try setting the environment variable for auth
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
        
        # If it doesn't work, we'll try to get an API Key from the project?
        # Actually, let's try to initialize Vertex with a different project ID if this one is wrong?
        # But the JSON project ID is celtic-origin-480214-d5.
        
        print("This SDK usually requires an API_KEY. Trying with credentials anyway...")
        # genai.configure(api_key="YOUR_KEY") # This is standard
        
        # Let's see if it can list models
        models = genai.list_models()
        print("Successfully listed models!")
        # Try to use the first available model that supports generateContent
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"Testing model: {m.name}")
                model = genai.GenerativeModel(m.name)
                response = model.generate_content("Hello")
                print(f"✅ Success! Response: {response.text}")
                break
            
    except Exception as e:
        print(f"❌ Failed AI Studio check: {e}")

test_ai_studio()
