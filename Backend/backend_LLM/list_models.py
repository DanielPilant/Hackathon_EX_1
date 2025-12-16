import os
import logging
from dotenv import load_dotenv
from google import genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_available_models():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not found.")
        return

    client = genai.Client(api_key=api_key)
    
    try:
        logger.info("Listing available models...")
        # The new SDK uses client.models.list()
        # We need to iterate over the pager
        for model in client.models.list():
            # Debug: print model info
            # logger.info(f"Found model: {model.name}")
            
            # Check if it supports generateContent
            methods = getattr(model, "supported_generation_methods", [])
            if "generateContent" in methods:
                logger.info(f"Model: {model.name} | Methods: {methods}")
            else:
                # Print what we found anyway to debug
                logger.info(f"Skipped: {model.name} | Methods: {methods}")
    except Exception as e:
        logger.error(f"Error listing models: {e}")

if __name__ == "__main__":
    list_available_models()
