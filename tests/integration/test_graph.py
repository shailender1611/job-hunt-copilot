from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from copilot.graph.builder import build_graph
from copilot.schemas import (
    Experience,
    FitAssessment,
    JobPosting,
    Resume,
    RewrittenBullet,
    SkillMatch,
    TailoredApplication,
)
from tests.fakes import FakeLLMFactory

FIXTURES = Path(__file__).parent.parent / "fixtures"

BULLET = "Built Kafka-based event pipeline processing 2M events/day"
RESUME = Resume(
    name="Jane Doe",
    skills=["Java", "Spring Boot", "Kafka", "PostgreSQL"],
    experience=[Experience(company="Globex", title="Engineer", highlights=[BULLET])],
)
JOB = JobPosting(
    title="Senior Backend Engineer",
    must_have_skills=["Java", "Spring Boot", "Kafka", "PostgreSQL"],
    nice_to_have_skills=["Kubernetes", "LangChain"],
)
FIT = FitAssessment(
    overall_score=82,
    verdict="strong",
    summary="Strong backend match.",
    strengths=["Kafka at scale"],
    experience_fit="6 years vs 5+ required",
)
TAILORED = TailoredApplication(
    tailored_summary="Backend engineer specialising in event-driven Java systems.",
    bullets=[
        RewrittenBullet(
            original=BULLET,
            rewritten="Designed event-driven Kafka pipeline handling 2M events/day",
            rationale="event-driven architecture",
        ),
        RewrittenBullet(original="Invented bullet", rewritten="x", rationale="r"),
    ],
    cover_letter="Dear Acme Lending...",
    recruiter_message="Hi! I'd love to chat about the backend role.",
)


def make_fake() -> FakeLLMFactory:
    return FakeLLMFactory(
        {Resume: RESUME, JobPosting: JOB, FitAssessment: FIT, TailoredApplication: TAILORED}
    )


INPUTS = {
    "resume_text": (FIXTURES / "sample_resume.md").read_text(encoding="utf-8"),
    "jd_text": (FIXTURES / "sample_jd.md").read_text(encoding="utf-8"),
}


def run(fake: FakeLLMFactory) -> dict[str, Any]:
    """Run until the human-review interrupt."""
    return build_graph(llm_factory=fake).invoke(INPUTS, {"configurable": {"thread_id": "t"}})


def test_graph_runs_until_review() -> None:
    fake = make_fake()
    result = run(fake)

    assert "__interrupt__" in result
    assert not result.get("approved")  # output only holds keys a node has written
    assert result["resume"] == RESUME
    assert result["job"] == JOB
    assert result["fit"] == FIT
    assert isinstance(result["skill_match"], SkillMatch)
    assert result["skill_match"].missing_must_have == []
    assert result["skill_match"].coverage_score == 80  # all must-haves, no nice-to-haves

    # Both parsers run before analysis; tailoring runs last.
    called = fake.schemas_called()
    assert set(called[:2]) == {Resume, JobPosting}
    assert called[2:] == [FitAssessment, TailoredApplication]


def test_grounding_guard_applied_in_graph() -> None:
    result = run(make_fake())
    assert [b.original for b in result["tailored"].bullets] == [BULLET]
    assert len(result["grounding_warnings"]) == 1


def test_fit_prompt_includes_keyword_match() -> None:
    fake = make_fake()
    run(fake)
    _, messages = fake.calls[2]
    assert "<keyword_match>" in messages[1].content
    assert "Kubernetes" in messages[1].content


def test_review_payload_shows_draft_and_warnings() -> None:
    (pending,) = run(make_fake())["__interrupt__"]
    assert pending.value["tailored"]["cover_letter"].startswith("Dear Acme")
    assert len(pending.value["grounding_warnings"]) == 1


def test_approve_finishes_run() -> None:
    fake = make_fake()
    graph = build_graph(llm_factory=fake)
    config: RunnableConfig = {"configurable": {"thread_id": "approve"}}
    graph.invoke(INPUTS, config)

    result = graph.invoke(Command(resume={"action": "approve"}), config)

    assert "__interrupt__" not in result
    assert result["approved"] is True
    assert fake.schemas_called().count(TailoredApplication) == 1


def test_revise_regenerates_with_feedback_then_approve() -> None:
    fake = make_fake()
    graph = build_graph(llm_factory=fake)
    config: RunnableConfig = {"configurable": {"thread_id": "revise"}}
    graph.invoke(INPUTS, config)

    result = graph.invoke(Command(resume={"action": "revise", "feedback": "Shorter"}), config)
    assert "__interrupt__" in result  # paused again for the new draft
    assert result["revisions"] == 1

    # The second tailoring call sees the reviewer's feedback and previous draft.
    _, messages = fake.calls[-1]
    assert "<reviewer_feedback>\nShorter" in messages[1].content
    assert "<previous_draft>" in messages[1].content

    result = graph.invoke(Command(resume={"action": "approve"}), config)
    assert result["approved"] is True


def test_threads_are_isolated() -> None:
    graph = build_graph(llm_factory=make_fake())
    graph.invoke(INPUTS, {"configurable": {"thread_id": "a"}})
    graph.invoke(Command(resume={"action": "approve"}), {"configurable": {"thread_id": "a"}})

    other = graph.get_state({"configurable": {"thread_id": "b"}})
    assert other.values == {}
