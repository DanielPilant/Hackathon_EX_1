from typing import TypedDict, List, Optional, Any, Dict

class InteractiveElement(TypedDict):
    uid: str
    tag_name: str
    text: str
    href: Optional[str]
    aria_label: Optional[str]
    is_visible: bool
    location: Dict[str, int]

class FormElement(TypedDict):
    action: Optional[str]
    method: Optional[str]
    inputs: List[Dict[str, Any]]

class SiteContext(TypedDict):
    page: Dict[str, str]
    interactive_elements: List[InteractiveElement]
    forms: List[FormElement]
    internal_links: List[str]
    headings: List[str]
    text_snippet: str
    tech_hints: Dict[str, Any]

class TestStep(TypedDict):
    step_id: int
    description: str
    action: str
    target: Dict[str, Any]
    data: Optional[str]

class TestPlan(TypedDict):
    plan: List[TestStep]
