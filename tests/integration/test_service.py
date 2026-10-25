import os

import pytest

from copilot.config import Settings
from copilot.observability import configure_tracing
from copilot.schemas import ReviewDecision
from copilot.service import CopilotService, render_markdown
from tests.integration.test_graph import JOB, make_fake


def service() -> CopilotService:
    return CopilotService(settings=Settings(_env_file=None), llm_factory=make_fake())  # type: ignore[call-arg]


def test_start_pauses_for_review() -> None:
    run = service().start("resume", "jd")
    assert run.awaiting_review
    assert run.state.fit is not None
    assert run.state.tailored is not None


def test_approve_completes_run() -> None:
    svc = service()
    run = svc.start("resume", "jd")
    done = svc.review(run.thread_id, ReviewDecision(action="approve"))
    assert not done.awaiting_review
    assert done.state.approved


def test_revise_keeps_run_open() -> None:
    svc = service()
    run = svc.start("resume", "jd")
    again = svc.review(run.thread_id, ReviewDecision(action="revise", feedback="More Kafka"))
    assert again.awaiting_review
    assert again.state.revisions == 1


def test_review_after_completion_rejected() -> None:
    svc = service()
    run = svc.start("resume", "jd")
    svc.review(run.thread_id, ReviewDecision(action="approve"))
    with pytest.raises(ValueError, match="not awaiting review"):
        svc.review(run.thread_id, ReviewDecision(action="approve"))


def test_unknown_run() -> None:
    with pytest.raises(KeyError):
        service().get("missing")


def test_render_markdown() -> None:
    run = service().start("resume", "jd")
    md = render_markdown(run.state)
    assert md.startswith(f"# Application pack: {JOB.title}")
    assert "## Cover letter" in md
    assert "2M events/day" in md


@pytest.fixture
def isolated_tracing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # setenv records the original value (even "unset"), then delenv clears it, so
    # whatever configure_tracing writes is rolled back instead of leaking.
    for var in ("LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"):
        monkeypatch.setenv(var, "placeholder")
        monkeypatch.delenv(var)


@pytest.mark.usefixtures("isolated_tracing_env")
def test_tracing_disabled_without_key() -> None:
    assert not configure_tracing(Settings(_env_file=None, langsmith_tracing=True))  # type: ignore[call-arg]
    assert os.environ["LANGSMITH_TRACING"] == "false"


@pytest.mark.usefixtures("isolated_tracing_env")
def test_tracing_enabled_with_key() -> None:
    settings = Settings(_env_file=None, langsmith_tracing=True, langsmith_api_key="ls-test")  # type: ignore[call-arg]
    assert configure_tracing(settings)
    assert os.environ["LANGSMITH_PROJECT"] == "job-hunt-copilot"
