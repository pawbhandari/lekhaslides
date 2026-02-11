
import os
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

CREDENTIALS_PATH = "/Users/rci/lekhaslides/celtic-origin-480214-d5-e0c80e18c8c5.json"
VERTEX_PROJECT_ID = "celtic-origin-480214-d5"

def check_models(region):
    print(f"\n--- Checking Region: {region} ---")
    try:
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        vertexai.init(project=VERTEX_PROJECT_ID, location=region, credentials=creds)
        model = GenerativeModel("gemini-1.0-pro")
        # Try a very small generation to see if it works
        response = model.generate_content("Hi")
        print(f"✅ Success in {region} with gemini-1.5-flash")
        return True
    except Exception as e:
        print(f"❌ Failed in {region}: {e}")
        return False

regions = ["us-central1", "us-east1", "us-east4", "europe-west1", "asia-southeast1"]
for r in regions:
    if check_models(r):
        print(f"\n🚀 RECOMMENDED REGION: {r}")
        break
