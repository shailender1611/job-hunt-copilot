"""Combine deterministic skill matching with an LLM fit assessment."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from copilot.llm import get_llm
from copilot.prompts import load_prompt
from copilot.schemas import FitAssessment, JobPosting, Resume, SkillMatch


def assess_fit(
    resume: Resume,
    job: JobPosting,
    match: SkillMatch,
    llm: Runnable[Any, Any] | None = None,
) -> FitAssessment:
    llm = llm or get_llm(schema=FitAssessment)
    messages = [
        SystemMessage(load_prompt("analyze_fit")),
        HumanMessage(
            f"<resume>\n{resume.model_dump_json(exclude_none=True)}\n</resume>\n"
            f"<job_posting>\n{job.model_dump_json(exclude_none=True)}\n</job_posting>\n"
            f"<keyword_match>\n{match.model_dump_json()}\n</keyword_match>"
        ),
    ]
    result = llm.invoke(messages)
    if not isinstance(result, FitAssessment):
        raise TypeError(f"Expected FitAssessment from LLM, got {type(result).__name__}")
    return result
