
import vertexai
from google.oauth2 import service_account
from google.cloud import aiplatform

CREDENTIALS_PATH = "/Users/rci/lekhaslides/celtic-origin-480214-d5-cc10414afe29.json"
PROJECT_ID = "celtic-origin-480214-d5"

def list_models(region):
    print(f"\n--- Listing Models in {region} ---")
    try:
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        aiplatform.init(project=PROJECT_ID, location=region, credentials=creds)
        # This requires aiplatform.Model.list()
        models = aiplatform.Model.list()
        print(f"Found {len(models)} models")
        for m in models:
            print(f" - {m.display_name} ({m.resource_name})")
    except Exception as e:
        print(f"❌ Error in {region}: {e}")

list_models("us-central1")
list_models("us-east1")
