"""
TestFlow AI Automation Layer

Production-grade automation engine with:
- Pydantic schema validation
- Async Playwright execution
- Visual feedback (Red Halo)
- Screenshot/Tracing on failure
"""

from .schemas import Target, Step, Plan, ExecutionResult
from .visual_fx import RED_HALO_SCRIPT
from .executor import run_execution_plan, run_plan_sync

__all__ = [
    "Target",
    "Step", 
    "Plan",
    "ExecutionResult",
    "RED_HALO_SCRIPT",
    "run_execution_plan",
    "run_plan_sync",
]

