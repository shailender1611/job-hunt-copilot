"""Turn raw job-description text into a structured `JobPosting` with the LLM."""

from typing import Any

from langchain_core.runnables import Runnable

from copilot.graph.nodes._extract import extract_structured
from copilot.schemas import JobPosting

# JDs are usually shorter than resumes; anything longer is boilerplate.
MAX_JD_CHARS = 20_000


def parse_jd(text: str, llm: Runnable[Any, Any] | None = None) -> JobPosting:
    """Extract a `JobPosting` from text. `llm` is injectable for tests."""
    return extract_structured(
        text,
        schema=JobPosting,
        prompt="parse_jd",
        tag="job_description",
        max_chars=MAX_JD_CHARS,
        llm=llm,
    )
