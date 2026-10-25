"""Generate tailored application material and guard it against hallucination."""

import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from copilot.llm import get_llm
from copilot.prompts import load_prompt
from copilot.schemas import FitAssessment, JobPosting, Resume, TailoredApplication

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def _bullet_key(text: str) -> str:
    """Compare bullets on words only: case, punctuation and spacing don't matter."""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def generate_tailored(
    resume: Resume,
    job: JobPosting,
    fit: FitAssessment,
    llm: Runnable[Any, Any] | None = None,
    *,
    previous: TailoredApplication | None = None,
    feedback: str | None = None,
) -> TailoredApplication:
    """Draft application material; on a revision, pass the previous draft and feedback."""
    llm = llm or get_llm(schema=TailoredApplication)
    content = (
        f"<resume>\n{resume.model_dump_json(exclude_none=True)}\n</resume>\n"
        f"<job_posting>\n{job.model_dump_json(exclude_none=True)}\n</job_posting>\n"
        f"<fit_assessment>\n{fit.model_dump_json()}\n</fit_assessment>"
    )
    if previous is not None and feedback:
        content += (
            f"\n<previous_draft>\n{previous.model_dump_json()}\n</previous_draft>\n"
            f"<reviewer_feedback>\n{feedback}\n</reviewer_feedback>\n"
            "Revise the previous draft to address the reviewer feedback. "
            "The truthfulness rules still apply."
        )
    messages = [SystemMessage(load_prompt("tailor")), HumanMessage(content)]
    result = llm.invoke(messages)
    if not isinstance(result, TailoredApplication):
        raise TypeError(f"Expected TailoredApplication from LLM, got {type(result).__name__}")
    return result


def enforce_grounding(
    resume: Resume, tailored: TailoredApplication
) -> tuple[TailoredApplication, list[str]]:
    """Drop bullets that don't trace back to the resume and flag invented numbers.

    LLMs are good at rewriting and bad at not embellishing; this check is
    deterministic so it can't be talked out of its job by the model.
    """
    known = {_bullet_key(h) for exp in resume.experience for h in exp.highlights}
    known |= {_bullet_key(p.description) for p in resume.projects if p.description}

    kept, warnings = [], []
    for bullet in tailored.bullets:
        if _bullet_key(bullet.original) not in known:
            warnings.append(f"Dropped bullet not found in resume: {bullet.original!r}")
            continue
        invented = set(_NUMBER.findall(bullet.rewritten)) - set(_NUMBER.findall(bullet.original))
        if invented:
            warnings.append(
                f"Rewritten bullet introduces numbers {sorted(invented)} "
                f"not in the original: {bullet.rewritten!r}"
            )
        kept.append(bullet)

    return tailored.model_copy(update={"bullets": kept}), warnings
