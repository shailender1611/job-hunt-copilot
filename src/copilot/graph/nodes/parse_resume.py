"""Turn raw resume text into a structured `Resume` with the LLM."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from copilot.llm import get_llm
from copilot.prompts import load_prompt
from copilot.schemas import Resume

# Keeps token usage bounded; a long resume is ~10k characters.
MAX_RESUME_CHARS = 30_000


def parse_resume(text: str, llm: Runnable[Any, Any] | None = None) -> Resume:
    """Extract a `Resume` from text. `llm` is injectable for tests."""
    if not text.strip():
        raise ValueError("Resume text is empty")

    llm = llm or get_llm(schema=Resume)
    messages = [
        SystemMessage(load_prompt("parse_resume")),
        # Delimiters make the boundary between instructions and untrusted data explicit.
        HumanMessage(f"<resume>\n{text[:MAX_RESUME_CHARS]}\n</resume>"),
    ]
    result = llm.invoke(messages)
    if not isinstance(result, Resume):
        raise TypeError(f"Expected Resume from LLM, got {type(result).__name__}")
    return result
