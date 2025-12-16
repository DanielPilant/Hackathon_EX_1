import google.generativeai as genai
import json
import os

def get_playwright_actions(instruction: str, api_key: str) -> list[dict]:
    """
    Generates Playwright actions from a natural language instruction using Google's Gemini API.
    
    Args:
        instruction (str): The user's natural language instruction.
        api_key (str): The Google Gemini API key.
        
    Returns:
        list[dict]: A list of structured Playwright actions.
    """
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    # Define the JSON Schema for the output
    # This matches the user's requested structure
    response_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The type of Playwright action required.",
                    "enum": ["navigate", "click", "type", "assert_text"]
                },
                "selector": {
                    "type": "string",
                    "description": "The CSS selector (e.g., '#id', '.class', 'button') for the target element. Empty for 'navigate'."
                },
                "value": {
                    "type": "string",
                    "description": "The value to use (URL for 'navigate', text for 'type', text to look for for 'assert_text'). Null for 'click'.",
                    "nullable": True # Explicitly allowing nulls for better compatibility
                }
            },
            "required": ["action", "selector"]
        }
    }

    # Initialize the model
    # Using gemini-2.5-flash as confirmed available by list_models()
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
            "temperature": 0.1 # Low temperature for deterministic output
        }
    )

    prompt = f"""
    You are an expert QA Automation Engineer. 
    Your task is to convert the following natural language test instruction into a sequence of structured Playwright actions.
    
    Instruction: "{instruction}"
    
    Generate a JSON array of actions following the provided schema strictly.
    """

    try:
        response = model.generate_content(prompt)
        # The response.text should be a valid JSON string due to response_mime_type="application/json"
        return json.loads(response.text)
    except Exception as e:
        # In a real app, you might want to log this or raise a specific error
        raise RuntimeError(f"Failed to generate actions: {str(e)}")
