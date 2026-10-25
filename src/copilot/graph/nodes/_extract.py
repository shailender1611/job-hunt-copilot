"""Shared helper: run a prompt over untrusted document text and get a typed result."""

from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from copilot.llm import get_llm
from copilot.prompts import load_prompt

T = TypeVar("T", bound=BaseModel)


def extract_structured(
    text: str,
    *,
    schema: type[T],
    prompt: str,
    tag: str,
    max_chars: int,
    llm: Runnable[Any, Any] | None = None,
) -> T:
    """Extract `schema` from `text` using the system prompt file `prompt`.

    The text is truncated to `max_chars` (bounds token cost) and wrapped in
    `<tag>` delimiters so the model can tell instructions from untrusted data.
    """
    if not text.strip():
        raise ValueError(f"{tag} text is empty")

    llm = llm or get_llm(schema=schema)
    messages = [
        SystemMessage(load_prompt(prompt)),
        HumanMessage(f"<{tag}>\n{text[:max_chars]}\n</{tag}>"),
    ]
    result = llm.invoke(messages)
    if not isinstance(result, schema):
        raise TypeError(f"Expected {schema.__name__} from LLM, got {type(result).__name__}")
    return result
