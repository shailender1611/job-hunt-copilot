from pathlib import Path

from copilot.graph.builder import build_graph
from copilot.schemas import FitAssessment, JobPosting, Resume, SkillMatch
from tests.fakes import FakeLLMFactory

FIXTURES = Path(__file__).parent.parent / "fixtures"

RESUME = Resume(name="Jane Doe", skills=["Java", "Spring Boot", "Kafka", "PostgreSQL"])
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


def test_graph_parses_both_documents_then_analyzes_fit() -> None:
    fake = FakeLLMFactory({Resume: RESUME, JobPosting: JOB, FitAssessment: FIT})
    graph = build_graph(llm_factory=fake)

    result = graph.invoke(
        {
            "resume_text": (FIXTURES / "sample_resume.md").read_text(encoding="utf-8"),
            "jd_text": (FIXTURES / "sample_jd.md").read_text(encoding="utf-8"),
        }
    )

    assert result["resume"] == RESUME
    assert result["job"] == JOB
    assert result["fit"] == FIT
    assert isinstance(result["skill_match"], SkillMatch)
    assert result["skill_match"].missing_must_have == []
    assert result["skill_match"].coverage_score == 80  # all must-haves, no nice-to-haves

    # Both parsers run before the fit assessment.
    called = fake.schemas_called()
    assert set(called[:2]) == {Resume, JobPosting}
    assert called[2] is FitAssessment


def test_fit_prompt_includes_keyword_match() -> None:
    fake = FakeLLMFactory({Resume: RESUME, JobPosting: JOB, FitAssessment: FIT})
    build_graph(llm_factory=fake).invoke({"resume_text": "r", "jd_text": "j"})

    _, messages = fake.calls[-1]
    assert "<keyword_match>" in messages[1].content
    assert "Kubernetes" in messages[1].content
