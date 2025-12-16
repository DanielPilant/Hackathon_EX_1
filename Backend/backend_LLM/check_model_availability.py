import os
import sys
import logging
import time
import random
import string
from typing import List, Dict, Any, Optional

# Ensure we can import from the local package if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def load_api_key():
    load_dotenv()
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        # Try loading from parent directory .env if not found
        parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(parent_env):
            load_dotenv(parent_env)
            key = os.getenv("GOOGLE_API_KEY")
            
    if not key:
        logger.error("GOOGLE_API_KEY not found in environment.")
        sys.exit(1)
    return key

def generate_dummy_prompt(approx_tokens: int) -> str:
    # Approx 4 chars per token
    num_chars = approx_tokens * 4
    # Generate random text to avoid caching or compression artifacts affecting token count too much
    return ''.join(random.choices(string.ascii_letters + string.digits + " ", k=num_chars))

def get_usable_models(client: genai.Client) -> List[Dict[str, Any]]:
    logger.info("Listing available models...")
    candidates = []
    try:
        for model in client.models.list():
            methods = getattr(model, "supported_generation_methods", [])
            
            # Debug log
            # logger.info(f"Model: {model.name}, Methods: {methods}")

            # Relaxed filtering:
            # If methods include generateContent OR if methods is empty but name looks like a text model
            if "generateContent" in methods or (not methods and "gemini" in model.name.lower() and "vision" not in model.name.lower() and "embedding" not in model.name.lower()):
                candidates.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "input_token_limit": getattr(model, "input_token_limit", None),
                    "methods": methods
                })
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return []
    
    logger.info(f"Found {len(candidates)} potential models.")
    return candidates

def probe_model(client: genai.Client, model_name: str, token_count: int = 2000) -> Dict[str, Any]:
    """
    Probes a model with a specific token count.
    Returns dict with status, error_code, error_message, latency.
    """
    prompt_text = generate_dummy_prompt(token_count)
    instruction = "Return a JSON object with a single key called 'status' set to 'ok'. Do not output markdown."
    
    full_prompt = f"{instruction}\n\n[CONTEXT START]\n{prompt_text}\n[CONTEXT END]"
    
    start_time = time.time()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        latency = time.time() - start_time
        return {
            "success": True,
            "latency": latency,
            "error": None
        }
    except errors.ClientError as e:
        latency = time.time() - start_time
        # Parse error
        status_code = e.code
        message = e.message
        
        # Check for quota issues
        is_quota = False
        if status_code == 429:
            is_quota = True
        
        return {
            "success": False,
            "latency": latency,
            "error": message,
            "status_code": status_code,
            "is_quota": is_quota
        }
    except Exception as e:
        latency = time.time() - start_time
        return {
            "success": False,
            "latency": latency,
            "error": str(e),
            "status_code": 500,
            "is_quota": False
        }

def evaluate_models():
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    
    candidates = get_usable_models(client)
    
    # Prioritize testing order to fail fast on preferred models
    # We want to test newer models first
    def sort_key(m):
        name = m['name'].lower()
        score = 0
        if 'gemini' in name: score += 100
        if 'pro' in name: score += 50
        if 'flash' in name: score += 40
        if '2.5' in name: score += 30
        if '2.0' in name: score += 20
        if '1.5' in name: score += 10
        return score

    candidates.sort(key=sort_key, reverse=True)
    
    results = []
    
    logger.info("Starting probe tests (approx 2k tokens)...")
    
    for model in candidates:
        name = model['name']
        logger.info(f"Probing {name}...")
        
        # Initial probe (2k tokens)
        probe_result = probe_model(client, name, token_count=2000)
        
        if probe_result['success']:
            logger.info(f"✅ {name} passed basic probe ({probe_result['latency']:.2f}s)")
            
            # Capacity check
            # Try 8k
            logger.info(f"   Checking 8k capacity for {name}...")
            cap_result = probe_model(client, name, token_count=8000)
            
            max_capacity = "2k+"
            if cap_result['success']:
                max_capacity = "8k+"
                logger.info(f"   ✅ {name} passed 8k probe")
            else:
                logger.warning(f"   ⚠️ {name} failed 8k probe: {cap_result['error']}")
            
            results.append({
                "name": name,
                "status": "USABLE",
                "max_capacity": max_capacity,
                "latency": probe_result['latency'],
                "score": sort_key(model) # Keep preference score
            })
            
        else:
            error_msg = probe_result['error']
            if probe_result.get('is_quota'):
                logger.warning(f"⛔ {name} hit QUOTA LIMIT (429).")
                status = "QUOTA_LIMITED"
            else:
                logger.error(f"❌ {name} failed: {error_msg}")
                status = "ERROR"
                
            results.append({
                "name": name,
                "status": status,
                "error": error_msg,
                "score": 0
            })
        
        # Sleep briefly to avoid self-imposed rate limits between models
        time.sleep(1)

    # Ranking Logic
    # Filter usable
    usable = [r for r in results if r['status'] == "USABLE"]
    
    # Sort by capacity (desc), then preference score (desc), then latency (asc)
    # We map capacity to int for sorting
    def capacity_val(s):
        if s == "8k+": return 8000
        if s == "2k+": return 2000
        return 0
        
    usable.sort(key=lambda x: (capacity_val(x['max_capacity']), x['score'], -x['latency']), reverse=True)
    
    print("\n" + "="*60)
    print("MODEL AVAILABILITY REPORT")
    print("="*60)
    
    if not usable:
        print("NO USABLE MODELS FOUND.")
        print("Check your API key, billing status, or region availability.")
    else:
        print(f"{'MODEL ID':<40} | {'CAPACITY':<10} | {'LATENCY':<10}")
        print("-" * 60)
        for m in usable:
            print(f"{m['name']:<40} | {m['max_capacity']:<10} | {m['latency']:.2f}s")
            
        best_model = usable[0]['name']
        print("-" * 60)
        print(f"RECOMMENDED MODEL: {best_model}")
        print("="*60)
        
    # Print blocked
    blocked = [r for r in results if r['status'] == "QUOTA_LIMITED"]
    if blocked:
        print("\nBLOCKED BY QUOTA (429):")
        for m in blocked:
            print(f"- {m['name']}")

if __name__ == "__main__":
    evaluate_models()
