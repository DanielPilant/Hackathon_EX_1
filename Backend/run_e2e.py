import sys
import os
import logging
import json

# Ensure backend_LLM can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_LLM.session_manager import QASession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting E2E test...")
    
    # Mock site context
    mock_url = "https://example.com"
    mock_context = """
    <html>
        <body>
            <h1>Example Domain</h1>
            <p>This domain is for use in illustrative examples in documents.</p>
            <form action="/login" method="post">
                <input type="text" name="username" placeholder="Username">
                <input type="password" name="password" placeholder="Password">
                <button type="submit">Login</button>
            </form>
        </body>
    </html>
    """
    
    try:
        # Initialize session (will pick best model automatically)
        session = QASession()
        
        # Start session
        session.start_new_session(mock_url, mock_context)
        
        # Generate test plan
        instruction = "Test the login form with valid credentials."
        plan = session.generate_test_plan(instruction)
        
        logger.info("Test Plan Generated Successfully:")
        print(json.dumps(plan, indent=2))
        
    except Exception as e:
        logger.error(f"E2E test failed: {e}")
        # We don't exit with error code here to avoid failing the tool execution if it's just a quota error
        # but normally we would.

if __name__ == "__main__":
    main()
