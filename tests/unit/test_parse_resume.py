from typing import Any

import pytest
from langchain_core.runnables import RunnableLambda

from copilot.graph.nodes.parse_resume import MAX_RESUME_CHARS, parse_resume
from copilot.schemas import Resume

SAMPLE = Resume(name="Jane Doe", skills=["Java", "Kafka"])


def fake_llm(captured: list[Any], output: Any = SAMPLE) -> RunnableLambda[Any, Any]:
    def run(messages: Any) -> Any:
        captured.append(messages)
        return output

    return RunnableLambda(run)


def test_returns_structured_resume() -> None:
    captured: list[Any] = []
    result = parse_resume("Jane Doe\nJava, Kafka", llm=fake_llm(captured))
    assert result == SAMPLE

    system, human = captured[0]
    assert "Never invent" in system.content
    assert human.content.startswith("<resume>")
    assert "Jane Doe" in human.content


def test_truncates_long_input() -> None:
    captured: list[Any] = []
    parse_resume("x" * (MAX_RESUME_CHARS + 500), llm=fake_llm(captured))
    assert captured[0][1].content.count("x") == MAX_RESUME_CHARS


def test_empty_text_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_resume("   ", llm=fake_llm([]))


def test_wrong_llm_output_type_rejected() -> None:
    with pytest.raises(TypeError, match="Expected Resume"):
        parse_resume("Jane", llm=fake_llm([], output={"name": "Jane"}))
