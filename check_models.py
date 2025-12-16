import google.generativeai as genai
import os

# The user provided this key in the chat
api_key = "AIzaSyD0YbKLETAvD9n8q8ZBnJzOoqmfc6Uskyo"

genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model: {m.name}")
            print(f"  Display Name: {m.display_name}")
            print(f"  Description: {m.description}")
            print("-" * 20)
except Exception as e:
    print(f"Error listing models: {e}")
