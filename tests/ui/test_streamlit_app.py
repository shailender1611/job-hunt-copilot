"""Headless UI tests: render the app with a pre-computed run (no LLM, no browser)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from copilot.config import Settings
from copilot.schemas import ReviewDecision
from copilot.service import CopilotService, RunSnapshot
from tests.integration.test_graph import make_fake

APP = str(Path(__file__).parents[2] / "ui" / "streamlit_app.py")


@pytest.fixture
def svc() -> CopilotService:
    return CopilotService(settings=Settings(_env_file=None), llm_factory=make_fake())  # type: ignore[call-arg]


def render(run: RunSnapshot | None = None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=30)
    if run is not None:
        at.session_state["run"] = run
    return at.run()


def test_empty_state_disables_analyze() -> None:
    at = render()
    assert not at.exception
    assert at.title[0].value == "🎯 Job-Hunt Copilot"
    assert at.button[0].disabled


def test_results_and_review_controls(svc: CopilotService) -> None:
    at = render(svc.start("resume", "jd"))
    assert not at.exception

    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Overall fit"] == "82/100"
    assert metrics["Keyword coverage"] == "80%"
    assert [t.label for t in at.tabs] == [
        "Summary",
        "Resume bullets",
        "Cover letter",
        "Recruiter message",
    ]
    assert any("not found in resume" in w.value for w in at.warning)  # grounding warning
    assert {b.label for b in at.button} >= {"✅ Approve", "🔁 Revise"}


def test_revise_without_feedback_shows_error(svc: CopilotService) -> None:
    at = render(svc.start("resume", "jd"))
    next(b for b in at.button if b.label == "🔁 Revise").click().run()
    assert any("what to change" in e.value for e in at.error)


def test_approved_run_offers_download(svc: CopilotService) -> None:
    run = svc.start("resume", "jd")
    at = render(svc.review(run.thread_id, ReviewDecision(action="approve")))
    assert not at.exception
    assert any("Approved" in s.value for s in at.success)
