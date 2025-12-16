"""
Logic Controller - Main Orchestration Layer

This module coordinates the complete workflow:
1. Fetch and parse website HTML
2. Initialize AI session with site context
3. Generate test plans based on user requirements
4. Return validated JSON output

Author: GitHub Copilot
Date: 2025-12-16
"""
import logging
import json
import argparse
import sys
import copy
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


# Internal imports
from Backend.backend_LLM.config import DEFAULT_MODEL_NAME
from Backend.backend_LLM.session_manager import QASession
from Backend.backend_LLM.site_context_extractor import extract_site_context, fetch_html

# Configure logging to write to stderr instead of stdout
# This ensures JSON output to stdout remains clean and parseable
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # ← CRITICAL: Logs go to stderr, not stdout
)
logger = logging.getLogger(__name__)

# Log this configuration change for developers
logger.debug("Logging configured to stderr - stdout reserved for JSON output")


def truncate_site_context(site_context: Dict[str, Any], max_elements: int = 50, max_forms: int = 5, max_links: int = 20) -> Dict[str, Any]:
    """
    Intelligently truncate site context data structures before JSON serialization.

    This function limits the size of lists within the context dictionary to prevent
    token limit issues while maintaining valid JSON structure.

    Args:
        site_context: The full site context dictionary from extract_site_context()
        max_elements: Maximum number of interactive elements to keep (default: 50)
        max_forms: Maximum number of forms to keep (default: 5)
        max_links: Maximum number of internal links to keep (default: 20)

    Returns:
        A truncated but structurally valid copy of the site context

    Notes:
        - Creates a shallow copy to avoid mutating the original
        - Logs warnings when truncation occurs
        - Preserves all non-list fields unchanged
    """
    # Create a shallow copy to avoid mutating the original context
    truncated = copy.copy(site_context)

    # Truncate interactive elements if present
    if 'interactive_elements' in truncated and isinstance(truncated['interactive_elements'], list):
        original_count = len(truncated['interactive_elements'])
        truncated['interactive_elements'] = truncated['interactive_elements'][:max_elements]
        if original_count > max_elements:
            logger.warning(
                f"Truncated interactive_elements from {original_count} to {max_elements} items"
            )

    # Truncate forms if present
    if 'forms' in truncated and isinstance(truncated['forms'], list):
        original_count = len(truncated['forms'])
        truncated['forms'] = truncated['forms'][:max_forms]
        if original_count > max_forms:
            logger.warning(
                f"Truncated forms from {original_count} to {max_forms} items"
            )

    # Truncate internal links if present
    if 'internal_links' in truncated and isinstance(truncated['internal_links'], list):
        original_count = len(truncated['internal_links'])
        truncated['internal_links'] = truncated['internal_links'][:max_links]
        if original_count > max_links:
            logger.warning(
                f"Truncated internal_links from {original_count} to {max_links} items"
            )

    # Truncate text snippet if present (keep first 1000 characters)
    if 'text_snippet' in truncated and truncated['text_snippet']:
        if len(truncated['text_snippet']) > 1000:
            truncated['text_snippet'] = truncated['text_snippet'][:1000]
            logger.warning("Truncated text_snippet to 1000 characters")

    # Truncate headings if present
    if 'headings' in truncated and isinstance(truncated['headings'], list):
        original_count = len(truncated['headings'])
        truncated['headings'] = truncated['headings'][:15]
        if original_count > 15:
            logger.warning(
                f"Truncated headings from {original_count} to 15 items"
            )

    return truncated

def process_url_request(
    url: str,
    user_instruction: Optional[str] = None,
    fetch_mode: str = "requests",
    max_elements: int = 250
) -> Dict[str, Any]:
    """
    Complete workflow orchestrator: URL → Test Plan JSON

    This function coordinates the entire process:
    1. Fetches HTML from the target URL
    2. Extracts structured site context (forms, buttons, links, etc.)
    3. Initializes an AI session with the site context
    4. Generates test plans based on user instruction (or general analysis)
    5. Returns validated JSON test plan

    Args:
        url (str): Target website URL (e.g., "https://example.com")
        user_instruction (Optional[str]): Specific test requirement.
            Examples:
            - "Test login with valid credentials"
            - "Test search functionality"
            - None = perform general site analysis
        fetch_mode (str): HTML fetch method - "requests" or "playwright"
        max_elements (int): Maximum interactive elements to extract

    Returns:
        Dict[str, Any]: Complete test plan in JSON format:
        {
            "url": "https://example.com",
            "instruction": "Test login flow",
            "site_context_summary": {...},
            "test_plan": {
                "plan": [
                    {
                        "step_id": 1,
                        "description": "Navigate to login page",
                        "action": "navigate",
                        "target": {...},
                        "data": "https://example.com/login"
                    },
                    ...
                ]
            },
            "metadata": {
                "generated_at": "2025-12-16T10:30:00Z",
                "elements_analyzed": 42,
                "model_used": "gemini-1.5-pro"
            }
        }

    Raises:
        ValueError: If URL is invalid or empty
        requests.RequestException: If HTML fetch fails
        RuntimeError: If AI session fails to initialize
        Exception: For any other processing errors
    """
    # ========================================
    # STEP 1: Input Validation
    # ========================================
    logger.info(f"Starting workflow for URL: {url}")
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    # ========================================
    # STEP 2: Fetch HTML Content
    # ========================================
    try:
        logger.info(f"Fetching HTML using mode: {fetch_mode}")
        html_content = fetch_html(url, mode=fetch_mode, timeout=15)
        logger.info(f"Successfully fetched HTML ({len(html_content)} bytes)")
    except Exception as e:
        logger.error(f"Failed to fetch HTML from {url}: {e}")
        raise RuntimeError(f"HTML fetch failed: {e}") from e

    # ========================================
    # STEP 3: Extract Structured Site Context
    # ========================================
    try:
        logger.info("Extracting site context (forms, buttons, links...)")
        site_context = extract_site_context(
            url=url,
            html=html_content,
            max_elements=max_elements,
            max_links=80
        )
        
        # Log summary
        num_elements = len(site_context.get("interactive_elements", []))
        num_forms = len(site_context.get("forms", []))
        logger.info(f"Extracted context: {num_elements} elements, {num_forms} forms")
    except Exception as e:
        logger.error(f"Failed to extract site context: {e}")
        raise RuntimeError(f"Site context extraction failed: {e}") from e

    # ========================================
    # STEP 4: Initialize AI Session
    # ========================================
    try:
        logger.info("Initializing QA Session with AI model")
        session = QASession(model_name=DEFAULT_MODEL_NAME)
        
        # CRITICAL FIX: Truncate data structures BEFORE serialization
        logger.info("Truncating site context to fit within token limits...")
        truncated_context = truncate_site_context(
            site_context,
            max_elements=50,
            max_forms=5,
            max_links=20
        )

        # Now serialize - guaranteed to be valid JSON
        context_str = json.dumps(truncated_context, indent=2, ensure_ascii=False)
        logger.info(f"Serialized context size: {len(context_str)} characters")
        
        # Start session with valid, truncated context
        logger.info("Starting new AI session with site context")
        session.start_new_session(url=url, html_context=context_str)
    except Exception as e:
        logger.error(f"Failed to initialize AI session: {e}")
        raise RuntimeError(f"AI session initialization failed: {e}") from e

    # ========================================
    # STEP 5: Generate Test Plan
    # ========================================
    try:
        if user_instruction:
            logger.info(f"Generating test plan for: '{user_instruction}'")
            test_plan = session.generate_test_plan(user_instruction)
        else:
            logger.info("No specific instruction - performing general analysis")
            # Use a default instruction for general site analysis
            default_instruction = (
                "Analyze this website and generate a comprehensive test plan "
                "covering the most critical user flows and interactions. "
                "Focus on: navigation, forms, buttons, and key user journeys."
            )
            test_plan = session.generate_test_plan(default_instruction)
        
        logger.info(f"Test plan generated with {len(test_plan.get('plan', []))} steps")
    except Exception as e:
        logger.error(f"Failed to generate test plan: {e}")
        raise RuntimeError(f"Test plan generation failed: {e}") from e

    # ========================================
    # STEP 6: Compile Final Output
    # ========================================
    final_output = {
        "url": url,
        "instruction": user_instruction or "General site analysis",
        "site_context_summary": {
            "title": site_context.get("page", {}).get("title"),
            "total_elements": len(site_context.get("interactive_elements", [])),
            "total_forms": len(site_context.get("forms", [])),
            "total_links": len(site_context.get("internal_links", [])),
            "tech_hints": site_context.get("tech_hints", {})
        },
        "test_plan": test_plan,
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "elements_analyzed": len(site_context.get("interactive_elements", [])),
            "model_used": DEFAULT_MODEL_NAME,
            "fetch_mode": fetch_mode
        }
    }

    logger.info("Workflow completed successfully")
    return final_output

def quick_test_generation(url: str, test_description: str) -> Dict[str, Any]:
    """
    Quick wrapper for generating a single test plan.

    Args:
        url: Target website URL
        test_description: What to test (e.g., "login flow")

    Returns:
        Just the test plan portion of the output

    Example:
        >>> plan = quick_test_generation(
        ...     "https://example.com",
        ...     "Test user registration"
        ... )
    """
    result = process_url_request(url, user_instruction=test_description)
    return result["test_plan"]

def analyze_site(url: str, fetch_mode: str = "requests") -> Dict[str, Any]:
    """
    Perform general site analysis without specific test instruction.

    Args:
        url: Target website URL
        fetch_mode: "requests" or "playwright"

    Returns:
        Complete analysis including suggested test scenarios
    """
    return process_url_request(url, user_instruction=None, fetch_mode=fetch_mode)

def batch_process_urls(
    urls: List[str],
    instruction: str,
    output_file: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Process multiple URLs with the same instruction.

    Args:
        urls: List of target URLs
        instruction: Test requirement to apply to all URLs
        output_file: Optional JSON file to save results

    Returns:
        List of test plans for each URL
    """
    results = []
    for i, url in enumerate(urls, 1):
        logger.info(f"Processing URL {i}/{len(urls)}: {url}")
        try:
            result = process_url_request(url, user_instruction=instruction)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            results.append({
                "url": url,
                "error": str(e),
                "test_plan": None
            })
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Batch results saved to {output_file}")
    
    return results

def _test_basic_workflow():
    """
    Basic test to verify the workflow works end-to-end.
    Run with: python logic_controller.py (when no args provided, runs this test)
    """
    print("Running basic workflow test...")
    test_url = "https://www.google.com"
    test_instruction = "Test the search functionality"
    
    try:
        result = process_url_request(test_url, test_instruction)
        print(f"✓ Successfully generated test plan with {len(result['test_plan']['plan'])} steps")
        print(f"✓ Analyzed {result['site_context_summary']['total_elements']} elements")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def interactive_mode(url: str, fetch_mode: str = "requests") -> int:
    """
    Interactive mode for multi-turn test generation conversations.
    
    This mode allows users to refine test plans iteratively without losing context.
    The AI session persists across multiple instructions, enabling conversational
    test generation.
    
    Args:
        url: Target website URL
        fetch_mode: HTML fetch method ("requests" or "playwright")
    
    Returns:
        Exit code (0 for success, 1 for failure)
    
    Usage:
        python logic_controller.py --url "https://example.com" --interactive
        
        Then provide instructions like:
        > Test login with valid credentials
        > Now test with invalid password
        > Add validation for empty username field
        > help
        > exit
    
    Commands:
        <instruction>  - Generate/refine test plan based on instruction
        history / h    - Show all instructions from this session
        save <file>    - Save current test plan to file
        help / ?       - Show available commands
        exit / quit    - Exit interactive mode
    """
    print(f"\n{'='*70}")
    print(f"  Interactive Test Generation Mode")
    print(f"  URL: {url}")
    print(f"{'='*70}\n")
    
    # ========================================
    # STEP 1: Initialize Session (One-time)
    # ========================================
    try:
        logger.info(f"Fetching site context for {url}...")
        print("⏳ Fetching and analyzing website...", file=sys.stderr)
        
        html_content = fetch_html(url, mode=fetch_mode, timeout=15)
        site_context = extract_site_context(url, html_content, max_elements=250)
        
        # Truncate intelligently
        truncated_context = truncate_site_context(
            site_context,
            max_elements=50,
            max_forms=5,
            max_links=20
        )
        context_str = json.dumps(truncated_context, indent=2, ensure_ascii=False)
        
        # Start persistent session
        session = QASession(model_name=DEFAULT_MODEL_NAME)
        session.start_new_session(url=url, html_context=context_str)
        
        print(f"✓ Session initialized successfully", file=sys.stderr)
        print(f"✓ Analyzed {len(site_context.get('interactive_elements', []))} elements", file=sys.stderr)
        print(f"✓ Found {len(site_context.get('forms', []))} forms\n", file=sys.stderr)
        
        print("Type your test instructions (or 'help' for commands):\n")
        
    except Exception as e:
        print(f"✗ Failed to initialize session: {e}", file=sys.stderr)
        logger.error(f"Session initialization failed: {e}")
        return 1
    
    # ========================================
    # STEP 2: Interactive Loop
    # ========================================
    conversation_history = []
    current_test_plan = None
    
    while True:
        try:
            # Get user input
            user_input = input("\n> ").strip()
            
            # Handle empty input
            if not user_input:
                continue
            
            # Handle exit commands
            if user_input.lower() in ("exit", "quit", "q"):
                print("\n👋 Exiting interactive mode. Goodbye!", file=sys.stderr)
                break
            
            # Handle history command
            if user_input.lower() in ("history", "h"):
                if not conversation_history:
                    print("No instructions yet in this session.", file=sys.stderr)
                else:
                    print(f"\n{'='*50}", file=sys.stderr)
                    print("Conversation History:", file=sys.stderr)
                    print(f"{'='*50}", file=sys.stderr)
                    for i, item in enumerate(conversation_history, 1):
                        print(f"\n{i}. {item['instruction']}", file=sys.stderr)
                        print(f"   → Generated {len(item['plan'])} steps", file=sys.stderr)
                    print(f"\n{'='*50}\n", file=sys.stderr)
                continue
            
            # Handle save command
            if user_input.lower().startswith("save "):
                if not current_test_plan:
                    print("✗ No test plan to save. Generate one first.", file=sys.stderr)
                    continue
                
                filename = user_input[5:].strip()
                if not filename:
                    filename = f"test_plan_{len(conversation_history)}.json"
                
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(current_test_plan, f, indent=2, ensure_ascii=False)
                    print(f"✓ Test plan saved to {filename}", file=sys.stderr)
                except Exception as e:
                    print(f"✗ Failed to save: {e}", file=sys.stderr)
                continue
            
            # Handle help command
            if user_input.lower() in ("help", "?"):
                print(f"\n{'='*50}", file=sys.stderr)
                print("Available Commands:", file=sys.stderr)
                print(f"{'='*50}", file=sys.stderr)
                print("  <instruction>     - Generate/refine test plan", file=sys.stderr)
                print("  history / h       - Show conversation history", file=sys.stderr)
                print("  save <filename>   - Save current test plan to file", file=sys.stderr)
                print("  help / ?          - Show this help message", file=sys.stderr)
                print("  exit / quit / q   - Exit interactive mode", file=sys.stderr)
                print(f"{'='*50}\n", file=sys.stderr)
                continue
            
            # ========================================
            # STEP 3: Generate Test Plan
            # ========================================
            print("⏳ Generating test plan...", file=sys.stderr)
            logger.info(f"Processing instruction: {user_input}")
            
            test_plan = session.generate_test_plan(user_input)
            current_test_plan = test_plan
            
            # Store in history
            conversation_history.append({
                "instruction": user_input,
                "plan": test_plan.get("plan", [])
            })
            
            # ========================================
            # STEP 4: Display Results
            # ========================================
            steps = test_plan.get("plan", [])
            print(f"\n✓ Generated {len(steps)} steps:\n", file=sys.stderr)
            
            for step in steps:
                step_num = step.get("step_id", "?")
                description = step.get("description", "No description")
                action = step.get("action", "unknown")
                print(f"  {step_num}. [{action}] {description}", file=sys.stderr)
            
            # Offer to print full JSON
            show_json = input("\nShow full JSON? (y/N): ").strip().lower()
            if show_json == 'y':
                print("\n" + "="*50)
                print(json.dumps(test_plan, indent=2, ensure_ascii=False))
                print("="*50)
            
            # Prompt for next action
            print(f"\nContinue refining, type 'save <file>' to save, or 'exit' to quit.", file=sys.stderr)
        
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted. Type 'exit' to quit or continue with a new instruction.", file=sys.stderr)
            continue
        
        except Exception as e:
            print(f"\n✗ Error: {e}", file=sys.stderr)
            logger.error(f"Error in interactive mode: {e}")
            print("You can continue with a new instruction or type 'exit'", file=sys.stderr)
            continue
    
    # Session summary
    if conversation_history:
        print(f"\n📊 Session Summary:", file=sys.stderr)
        print(f"   Total instructions: {len(conversation_history)}", file=sys.stderr)
        print(f"   Total steps generated: {sum(len(h['plan']) for h in conversation_history)}", file=sys.stderr)
    
    return 0

def main():
    """
    Command-line interface for the logic controller.

    Usage:
        python logic_controller.py --url "https://example.com" --instruction "Test login"
        python logic_controller.py --url "https://example.com" --analyze
        python logic_controller.py --batch urls.txt --instruction "Test checkout" --output results.json
    """
    parser = argparse.ArgumentParser(
        description="AI-Powered Test Plan Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate specific test:
    python logic_controller.py --url "https://example.com" --instruction "Test login flow"
  
  General analysis:
    python logic_controller.py --url "https://example.com" --analyze
  
  Batch processing:
    python logic_controller.py --batch urls.txt --instruction "Test checkout" --output results.json

  Interactive mode:
    python logic_controller.py --url "https://example.com" --interactive
"""
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive mode for multi-turn test generation conversations"
    )
    
    parser.add_argument("--url", help="Target website URL")
    parser.add_argument("--instruction", help="Specific test requirement")
    parser.add_argument("--analyze", action="store_true", help="Perform general site analysis")
    parser.add_argument("--batch", help="File containing list of URLs (one per line)")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--mode", choices=["requests", "playwright"], default="requests",
                       help="HTML fetch mode")
    
    args = parser.parse_args()
    
    try:
        # Check for interactive mode FIRST
        if args.interactive:
            if not args.url:
                parser.error("--url is required for interactive mode")
            return interactive_mode(args.url, fetch_mode=args.mode)

        elif args.batch:
            # Batch processing
            with open(args.batch, "r") as f:
                urls = [line.strip() for line in f if line.strip()]
            
            if not args.instruction:
                parser.error("--instruction required for batch processing")
            
            results = batch_process_urls(urls, args.instruction, args.output)
            print(f"\nProcessed {len(results)} URLs")
            
        elif args.url:
            # Single URL processing
            if args.analyze:
                result = analyze_site(args.url, fetch_mode=args.mode)
            else:
                if not args.instruction:
                    parser.error("--instruction required (or use --analyze)")
                result = process_url_request(args.url, args.instruction, fetch_mode=args.mode)
            
            # Output
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"Result saved to {args.output}", file=sys.stderr)
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        
        else:
            # If no arguments provided, run the basic test
            if len(sys.argv) == 1:
                _test_basic_workflow()
            else:
                parser.error("Either --url or --batch is required")
                
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
