import os
import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    from google import genai
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    logger.error("Please ensure 'python-dotenv' and 'google-genai' are installed.")

def get_client(env_path: Optional[str] = None) -> "genai.Client":
    """
    Configures and returns the Google GenAI Client with the API key from environment variables.

    Args:
        env_path (Optional[str]): Path to the .env file. If None, searches in current directory.

    Returns:
        genai.Client: The configured client.

    Raises:
        ValueError: If GOOGLE_API_KEY is missing or empty.
        ImportError: If required libraries are not installed.
    """
    # Check imports again inside the function
    if 'load_dotenv' not in globals() or 'genai' not in globals():
         raise ImportError("Required libraries 'python-dotenv' or 'google-genai' are not installed.")

    # Load environment variables
    logger.info("Loading environment variables...")
    if env_path:
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    # Retrieve API key
    api_key = os.getenv("GOOGLE_API_KEY")

    # Validate API key
    if not api_key or not api_key.strip():
        error_msg = "GOOGLE_API_KEY environment variable is missing or empty."
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Create Client
        logger.info("Creating Google GenAI Client...")
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        logger.error(f"Failed to create Google GenAI Client: {e}")
        raise

def pick_best_model(client: "genai.Client") -> str:
    """
    Selects the best available Gemini model for text generation.
    
    Prioritizes:
    1. gemini-2.5-pro
    2. gemini-2.5-flash
    3. gemini-2.0-*
    4. gemini-1.5-pro
    
    Args:
        client: The GenAI client.
        
    Returns:
        str: The model ID to use.
    """
    try:
        logger.info("Listing available models to pick the best one...")
        models = list(client.models.list())
        model_names = [m.name for m in models]
        
        # Helper to find model
        def find_model(substring):
            for name in model_names:
                if substring in name and "vision" not in name and "embedding" not in name:
                     return name
            return None

        # 1. Prefer gemini-2.5-flash (Prioritized over Pro due to quota limits)
        for name in model_names:
            if "gemini-2.5-flash" in name and "preview" not in name:
                logger.info(f"Selected model: {name}")
                return name

        # 2. Prefer gemini-2.5-pro
        # The listing showed 'models/gemini-2.5-pro'
        for name in model_names:
            if "gemini-2.5-pro" in name and "preview" not in name:
                logger.info(f"Selected model: {name}")
                return name

        # 3. Fallback to any gemini-2.5
        for name in model_names:
            if "gemini-2.5" in name:
                logger.info(f"Selected model: {name}")
                return name

        # 4. Fallback to gemini-2.0
        for name in model_names:
            if "gemini-2.0" in name:
                logger.info(f"Selected model: {name}")
                return name

        # 5. Fallback to gemini-1.5-pro
        for name in model_names:
            if "gemini-1.5-pro" in name:
                logger.info(f"Selected model: {name}")
                return name
                
        # Ultimate fallback
        fallback = "gemini-1.5-pro"
        logger.warning(f"No preferred model found. Fallback to {fallback}")
        return fallback

    except Exception as e:
        logger.error(f"Error picking best model: {e}")
        return "gemini-1.5-pro"

# Deprecated function for backward compatibility if needed, but updated to use new client
def configure_google_ai(env_path: Optional[str] = None) -> None:
    logger.warning("configure_google_ai is deprecated. Use get_client() instead.")
    get_client(env_path)

if __name__ == "__main__":
    try:
        client = get_client()
        model = pick_best_model(client)
        print(f"Best model selected: {model}")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
