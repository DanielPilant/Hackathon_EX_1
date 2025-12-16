import streamlit as st
import json
from ai_agent import get_playwright_actions
from test_executor import execute_test_plan

# Page Configuration
st.set_page_config(
    page_title="Autonomous QA Agent POC",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state for actions if not present
if 'actions' not in st.session_state:
    st.session_state.actions = None

# Title and Description
st.title("🤖 Autonomous QA Agent POC")
st.markdown("""
This tool converts natural language test instructions into structured **Playwright** actions using **Google Gemini**.
""")

# Sidebar for Configuration
with st.sidebar:
    st.header("Configuration")
    
    # Check for API key in secrets
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("API Key loaded from secrets.")
    else:
        api_key = st.text_input(
            "Gemini API Key", 
            type="password", 
            help="Enter your Google Gemini API Key. You can get one from Google AI Studio."
        )
    st.markdown("---")
    st.markdown("### About")
    st.info(
        "This POC uses the `gemini-2.5-flash` model to generate structured JSON outputs compatible with Playwright automation."
    )

# Main Content Area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Input Instruction")
    instruction = st.text_area(
        "Describe the test case:",
        height=150,
        placeholder="Example: Go to https://www.google.com, type 'Streamlit' into the search bar, and click the search button.",
        value="Navigate to https://example.com, click on the 'More information' link, and verify the text 'Example Domain' is present."
    )
    
    generate_btn = st.button("Generate Plan", type="primary", use_container_width=True)

    if generate_btn:
        if not api_key:
            st.error("⚠️ Please enter your Gemini API Key in the sidebar to proceed.")
        elif not instruction.strip():
            st.warning("⚠️ Please enter an instruction.")
        else:
            with st.spinner("Analyzing instruction and generating Playwright actions..."):
                try:
                    # Call the AI agent
                    actions = get_playwright_actions(instruction, api_key)
                    # Store in session state
                    st.session_state.actions = actions
                except Exception as e:
                    st.error(f"An error occurred during generation: {str(e)}")

with col2:
    st.subheader("Generated Action Plan")
    
    if st.session_state.actions:
        # Display the raw JSON
        st.json(st.session_state.actions, expanded=True)
        
        # Optional: Display a more readable summary
        with st.expander("View Action Summary"):
            for i, action in enumerate(st.session_state.actions, 1):
                act_type = action.get('action', 'UNKNOWN').upper()
                selector = action.get('selector', 'N/A')
                value = action.get('value')
                
                desc = f"**{i}. {act_type}**"
                if selector:
                    desc += f" on `{selector}`"
                if value:
                    desc += f" with value `{value}`"
                st.markdown(desc)
        
        st.markdown("---")
        st.subheader("Execute Test")
        if st.button("▶️ Run Test Live", type="secondary", use_container_width=True):
            with st.spinner("Running Playwright Test... Check the opened browser window!"):
                try:
                    execute_test_plan(st.session_state.actions)
                    st.success("Test execution completed successfully!")
                except Exception as e:
                    st.error(f"Test execution failed: {str(e)}")

    elif not generate_btn:
        st.info("Enter an instruction and click 'Generate Plan' to see the results.")

# Footer
st.markdown("---")
st.caption("Powered by Streamlit & Google Gemini")
