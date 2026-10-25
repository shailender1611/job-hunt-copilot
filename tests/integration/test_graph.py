from pathlib import Path

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


def run(fake: FakeLLMFactory) -> dict:  # type: ignore[type-arg]
    return build_graph(llm_factory=fake).invoke(
        {
            "resume_text": (FIXTURES / "sample_resume.md").read_text(encoding="utf-8"),
            "jd_text": (FIXTURES / "sample_jd.md").read_text(encoding="utf-8"),
        }
    )


def test_graph_runs_end_to_end() -> None:
    fake = make_fake()
    result = run(fake)

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
