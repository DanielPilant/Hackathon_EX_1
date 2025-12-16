"""
Pydantic Schemas for TestFlow AI Automation Engine

Provides strict validation for execution plans with:
- Target locator configuration
- Step definitions with action-specific constraints
- Full plan validation with uniqueness checks
"""

from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


# Allowed values for strict validation
ALLOWED_ACTIONS = Literal["navigate", "click", "fill", "press", "read", "wait"]
ALLOWED_STRATEGIES = Literal["role", "text", "placeholder", "label", "css", "xpath"]


class Target(BaseModel):
    """
    Target locator configuration for element selection.
    
    Attributes:
        strategy: Locator strategy (role, text, placeholder, label, css, xpath)
        selector: The selector value or accessible name
        role_type: ARIA role type (required when strategy is "role")
    """
    strategy: ALLOWED_STRATEGIES
    selector: str = Field(..., min_length=1)
    role_type: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_role_strategy(self) -> 'Target':
        """If strategy is 'role', role_type is mandatory."""
        if self.strategy == "role":
            if not self.role_type or not self.role_type.strip():
                raise ValueError("role_type is required when strategy is 'role'")
        elif self.role_type is not None:
            raise ValueError("role_type must be null unless strategy is 'role'")
        return self


class Step(BaseModel):
    """
    A single execution step in the test plan.
    
    Attributes:
        step_id: Unique identifier for this step
        description: Human-readable description of the action
        action: The action type to perform
        target: Element locator (null for navigate/wait)
        data: Action data (URL for navigate, text for fill/press, ms for wait)
    """
    step_id: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    action: ALLOWED_ACTIONS
    target: Optional[Target] = None
    data: Optional[Union[str, int, float]] = None
    
    @model_validator(mode='after')
    def validate_action_constraints(self) -> 'Step':
        """Validate action-specific constraints."""
        action = self.action
        target = self.target
        data = self.data
        
        if action == "navigate":
            if target is not None:
                raise ValueError(f"Step {self.step_id}: 'target' must be null for navigate")
            if not isinstance(data, str) or not data.strip():
                raise ValueError(f"Step {self.step_id}: 'data' must be a URL string for navigate")
        
        elif action == "wait":
            if target is not None:
                raise ValueError(f"Step {self.step_id}: 'target' must be null for wait")
            if data is None:
                raise ValueError(f"Step {self.step_id}: 'data' must be milliseconds for wait")
            # Validate it's a valid number
            try:
                ms = int(data) if isinstance(data, (int, float)) else int(str(data).strip())
                if ms < 0:
                    raise ValueError(f"Step {self.step_id}: wait milliseconds must be non-negative")
            except (ValueError, TypeError):
                raise ValueError(f"Step {self.step_id}: 'data' must be milliseconds (int or numeric string)")
        
        elif action in {"click", "read"}:
            if target is None:
                raise ValueError(f"Step {self.step_id}: 'target' is required for {action}")
            if data is not None:
                raise ValueError(f"Step {self.step_id}: 'data' must be null for {action}")
        
        elif action in {"fill", "press"}:
            if target is None:
                raise ValueError(f"Step {self.step_id}: 'target' is required for {action}")
            if not isinstance(data, str):
                raise ValueError(f"Step {self.step_id}: 'data' must be a string for {action}")
        
        return self


class Plan(BaseModel):
    """
    Complete execution plan containing a list of steps.
    
    Attributes:
        plan: List of steps to execute in order
    """
    plan: List[Step] = Field(..., min_length=1)
    
    @field_validator('plan')
    @classmethod
    def validate_unique_step_ids(cls, steps: List[Step]) -> List[Step]:
        """Ensure all step_ids are unique."""
        seen_ids = set()
        for step in steps:
            if step.step_id in seen_ids:
                raise ValueError(f"Duplicate step_id: {step.step_id}")
            seen_ids.add(step.step_id)
        return steps


class ExecutionResult(BaseModel):
    """
    Result of plan execution.
    
    Attributes:
        ok: Whether execution completed successfully
        results: Dict of step results (e.g., read text)
        log: List of execution log messages
        error: Error details if execution failed
    """
    ok: bool
    results: dict = Field(default_factory=dict)
    log: List[str] = Field(default_factory=list)
    error: Optional[dict] = None

