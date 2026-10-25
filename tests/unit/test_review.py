import pytest
from pydantic import ValidationError

from copilot.graph.nodes.human_review import MAX_REVISIONS, route_after_review
from copilot.schemas import ReviewDecision
from copilot.schemas.state import CopilotState


def state(**kw: object) -> CopilotState:
    return CopilotState(resume_text="r", jd_text="j", **kw)  # type: ignore[arg-type]


def test_revise_requires_feedback() -> None:
    with pytest.raises(ValidationError, match="feedback is required"):
        ReviewDecision(action="revise", feedback="  ")


def test_approve_needs_no_feedback() -> None:
    assert ReviewDecision(action="approve").feedback is None


def test_route_ends_when_approved() -> None:
    assert route_after_review(state(approved=True)) == "__end__"


def test_route_loops_back_for_revision() -> None:
    assert route_after_review(state(revisions=1)) == "tailor"


def test_route_stops_at_revision_limit() -> None:
    assert route_after_review(state(revisions=MAX_REVISIONS)) == "__end__"
