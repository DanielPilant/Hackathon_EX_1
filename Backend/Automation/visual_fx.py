"""
Visual Effects Module for TestFlow AI

Contains the RED_HALO_SCRIPT - a JavaScript function that creates a pulsing
red glow effect around elements before actions are performed, allowing users
to follow along with the AI's actions in "Passive View" mode.
"""

RED_HALO_SCRIPT = """(element) => {
    // Unique ID to prevent duplicate style injection
    const STYLE_ID = 'testflow-halo-style';
    const HALO_CLASS = 'testflow-red-halo';
    
    // 1. Check if style already exists before injecting (prevents DOM clogging)
    if (!document.getElementById(STYLE_ID)) {
        const style = document.createElement('style');
        style.id = STYLE_ID;
        style.textContent = `
            @keyframes testflow-pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7);
                }
                50% {
                    box-shadow: 0 0 20px 10px rgba(255, 0, 0, 0.4);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7);
                }
            }
            
            .${HALO_CLASS} {
                animation: testflow-pulse 1s ease-in-out infinite !important;
                outline: 3px solid red !important;
                outline-offset: 2px !important;
                position: relative;
                z-index: 9999;
            }
        `;
        document.head.appendChild(style);
    }
    
    // 2. Remove halo from any previously highlighted element
    const previousElement = document.querySelector('.' + HALO_CLASS);
    if (previousElement) {
        previousElement.classList.remove(HALO_CLASS);
    }
    
    // 3. Add animation class to target element
    element.classList.add(HALO_CLASS);
    
    // 4. Scroll element into view (centered)
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'center'
    });
}"""


def remove_halo_script() -> str:
    """Returns JS to remove the red halo from all elements."""
    return """() => {
        const HALO_CLASS = 'testflow-red-halo';
        const elements = document.querySelectorAll('.' + HALO_CLASS);
        elements.forEach(el => el.classList.remove(HALO_CLASS));
    }"""

