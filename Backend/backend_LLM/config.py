"""
Configuration file for LLM backend settings.
This module centralizes all model-related constants to maintain consistency
across the application and facilitate future updates.
"""

# Default Gemini model to be used across the application.
# This is now a fallback; the actual model is selected dynamically at runtime.
DEFAULT_MODEL_NAME = "gemini-2.5-flash"

# Additional configuration constants can be added here in the future
# For example:
# DEFAULT_TEMPERATURE = 0.7
# DEFAULT_MAX_TOKENS = 2048
