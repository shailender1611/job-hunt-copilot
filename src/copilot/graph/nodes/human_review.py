"""Pause the graph so a person approves or requests changes to the draft."""

from typing import Any, Literal

from langgraph.types import interrupt

from copilot.schemas import ReviewDecision
from copilot.schemas.state import CopilotState

MAX_REVISIONS = 3


def human_review(state: CopilotState) -> dict[str, Any]:
    # On resume, LangGraph re-runs this node from the top and interrupt() returns
    # the reviewer's payload, so nothing before it may have side effects.
    payload = interrupt(
        {
            "tailored": state.tailored.model_dump() if state.tailored else None,
            "grounding_warnings": state.grounding_warnings,
            "revisions": state.revisions,
            "max_revisions": MAX_REVISIONS,
        }
    )
    decision = ReviewDecision.model_validate(payload)
    if decision.action == "approve":
        return {"approved": True, "feedback": None}
    return {"feedback": decision.feedback, "revisions": state.revisions + 1}


def route_after_review(state: CopilotState) -> Literal["tailor", "__end__"]:
    if state.approved or state.revisions >= MAX_REVISIONS:
        return "__end__"
    return "tailor"
