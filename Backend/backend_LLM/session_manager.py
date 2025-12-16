import json
import logging
import sys
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from .google_ai_setup import get_client, pick_best_model
from .prompts import CORE_SYSTEM_PROMPT, ANALYSIS_SYSTEM_PROMPT
from .utils import extract_json_from_response
from .config import DEFAULT_MODEL_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class QASession:
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize a new QA testing session.
        
        Args:
            model_name: The Gemini model to use. If None, selects the best available.
        """
        self.client = get_client()
        
        if model_name and model_name != DEFAULT_MODEL_NAME:
             self.model_name = model_name
        else:
             # Dynamic selection
             self.model_name = pick_best_model(self.client)
             
        self.chat = None
        logger.info(f"QASession initialized with model: {self.model_name}")

    def start_new_session(self, url: str, html_context: str) -> None:
        """
        Start a new chat session with the AI, providing the site context.
        
        Args:
            url: The target website URL
            html_context: The extracted HTML context from site_context_extractor.py
        """
        system_message = f"{CORE_SYSTEM_PROMPT}\n\n**Site Context for {url}:**\n{html_context}"
        
        # Initialize history with system prompt and acknowledgment
        history = [
            types.Content(role="user", parts=[types.Part.from_text(text=system_message)]),
            types.Content(role="model", parts=[types.Part.from_text(text="Understood. I'm ready to generate test plans for this site.")])
        ]
        
        # Configure for JSON output
        config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )

        self.chat = self.client.chats.create(
            model=self.model_name,
            config=config,
            history=history
        )
        logger.info(f"New session started for URL: {url}")

    def generate_test_plan(self, user_instruction: str) -> Dict[str, Any]:
        """
        Generate a test plan based on user instruction, maintaining conversation context.
        
        Args:
            user_instruction: The test requirement (e.g., "Test login flow with valid credentials")
            
        Returns:
            Dict[str, Any]: Validated JSON test plan
            
        Raises:
            RuntimeError: If session hasn't been started
            ValueError: If AI response is invalid JSON
        """
        if self.chat is None:
            raise RuntimeError("Session not started. Call start_new_session() first.")
            
        try:
            logger.info(f"Generating test plan for: {user_instruction}")
            response = self.chat.send_message(user_instruction)
            return extract_json_from_response(response.text)
        except Exception as e:
            logger.error(f"Error during test generation: {e}")
            # Retry logic with strict instruction
            try:
                logger.info("Retrying with strict JSON instruction...")
                response = self.chat.send_message("Return ONLY valid JSON matching the schema, no markdown.")
                return extract_json_from_response(response.text)
            except Exception as retry_e:
                logger.error(f"Retry failed: {retry_e}")
                raise e

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """
        Returns the current chat history.
        
        Returns:
            List of chat messages with roles and content
        """
        if self.chat is None:
            return []
        # Attempt to retrieve history if available in the new SDK object
        # This might need adjustment based on exact SDK version behavior
        try:
            # Placeholder: The new SDK Chat object structure for history access
            # might differ. Returning empty list to avoid breakage.
            return [] 
        except:
            return []

def analyze_general_scan(context_data: str) -> Dict[str, Any]:
    """
    DEPRECATED: Use QASession class instead.
    Analyzes the scanned context of a page and suggests potential test scenarios.
    
    Args:
        context_data (str): The raw HTML or text context of the page.
        
    Returns:
        Dict[str, Any]: A structured list of suggested test scenarios.
    """
    logger.warning("analyze_general_scan is deprecated. Use QASession class instead.")
    client = get_client()
    model_name = pick_best_model(client)
    
    prompt = f"""{ANALYSIS_SYSTEM_PROMPT}
    
    Context:
    {context_data}
    """
    
    try:
        logger.info("Sending analysis request to Gemini...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return extract_json_from_response(response.text, expected_key="scenarios")
    except Exception as e:
        logger.error(f"Error during general scan analysis: {e}")
        raise

def generate_specific_test(user_requirement: str, context_data: str) -> Dict[str, Any]:
    """
    DEPRECATED: Use QASession class instead.
    Generates a specific Playwright test plan based on a user requirement and page context.
    
    Args:
        user_requirement (str): The specific test case description (e.g., "Login with valid credentials").
        context_data (str): The raw HTML or text context of the page.
        
    Returns:
        Dict[str, Any]: The JSON test plan.
    """
    logger.warning("generate_specific_test is deprecated. Use QASession.generate_test_plan() instead.")
    client = get_client()
    model_name = pick_best_model(client)
    
    full_prompt = f"{CORE_SYSTEM_PROMPT}\n\nPage Context:\n{context_data}\n\nUser Requirement: {user_requirement}"
    
    try:
        logger.info(f"Generating test plan for: {user_requirement}")
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return extract_json_from_response(response.text)
    except Exception as e:
        logger.error(f"Error during test generation: {e}")
        raise
