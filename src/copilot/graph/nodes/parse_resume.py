"""Turn raw resume text into a structured `Resume` with the LLM."""

from typing import Any

from langchain_core.runnables import Runnable

from copilot.graph.nodes._extract import extract_structured
from copilot.schemas import Resume

# Keeps token usage bounded; a long resume is ~10k characters.
MAX_RESUME_CHARS = 30_000


def parse_resume(text: str, llm: Runnable[Any, Any] | None = None) -> Resume:
    """Extract a `Resume` from text. `llm` is injectable for tests."""
    return extract_structured(
        text,
        schema=Resume,
        prompt="parse_resume",
        tag="resume",
        max_chars=MAX_RESUME_CHARS,
        llm=llm,
    )
