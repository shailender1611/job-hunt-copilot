from pathlib import Path
from typing import Any

import pytest
from langchain_core.runnables import RunnableLambda

from copilot.graph.nodes.parse_jd import MAX_JD_CHARS, parse_jd
from copilot.schemas import JobPosting

FIXTURES = Path(__file__).parent.parent / "fixtures"
SAMPLE = JobPosting(
    title="Senior Backend Engineer",
    must_have_skills=["Java", "Spring Boot", "Kafka"],
    nice_to_have_skills=["Kubernetes"],
)


def fake_llm(captured: list[Any], output: Any = SAMPLE) -> RunnableLambda[Any, Any]:
    def run(messages: Any) -> Any:
        captured.append(messages)
        return output

    return RunnableLambda(run)


def test_returns_structured_job() -> None:
    captured: list[Any] = []
    jd = (FIXTURES / "sample_jd.md").read_text(encoding="utf-8")
    assert parse_jd(jd, llm=fake_llm(captured)) == SAMPLE

    system, human = captured[0]
    assert "nice_to_have_skills" in system.content
    assert human.content.startswith("<job_description>")
    assert "Acme Lending" in human.content


def test_truncates_long_input() -> None:
    captured: list[Any] = []
    parse_jd("y" * (MAX_JD_CHARS + 10), llm=fake_llm(captured))
    assert captured[0][1].content.count("y") == MAX_JD_CHARS


def test_empty_text_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_jd("\n", llm=fake_llm([]))


def test_defaults_for_unstated_fields() -> None:
    job = JobPosting(title="Engineer")
    assert job.seniority == "unknown"
    assert job.work_mode == "unknown"
    assert job.must_have_skills == []
