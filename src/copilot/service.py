"""Application service: the only entry point UIs and APIs use to drive the graph.

Hides LangGraph details (thread ids, interrupts, Command) behind three calls:
start(), review() and get().
"""

import uuid
from dataclasses import dataclass
from typing import Any

from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel

from copilot.config import Settings, get_settings
from copilot.graph.builder import LLMFactory, build_graph
from copilot.llm import get_llm
from copilot.observability import configure_tracing
from copilot.schemas import ReviewDecision
from copilot.schemas.state import CopilotState


@dataclass(frozen=True)
class RunSnapshot:
    thread_id: str
    state: CopilotState
    awaiting_review: bool


class CopilotService:
    def __init__(
        self,
        settings: Settings | None = None,
        llm_factory: LLMFactory | None = None,
    ) -> None:
        settings = settings or get_settings()
        configure_tracing(settings)

        def factory(schema: type[BaseModel]) -> Runnable[Any, Any]:
            return get_llm(settings, schema=schema)

        self._graph = build_graph(llm_factory=llm_factory or factory)

    @staticmethod
    def _config(thread_id: str) -> RunnableConfig:
        return {"configurable": {"thread_id": thread_id}}

    def start(self, resume_text: str, jd_text: str) -> RunSnapshot:
        """Analyse and draft; returns paused at human review."""
        thread_id = uuid.uuid4().hex
        self._graph.invoke(
            {"resume_text": resume_text, "jd_text": jd_text}, self._config(thread_id)
        )
        return self.get(thread_id)

    def review(self, thread_id: str, decision: ReviewDecision) -> RunSnapshot:
        if not self.get(thread_id).awaiting_review:
            raise ValueError(f"Run {thread_id} is not awaiting review")
        self._graph.invoke(Command(resume=decision.model_dump()), self._config(thread_id))
        return self.get(thread_id)

    def get(self, thread_id: str) -> RunSnapshot:
        snapshot = self._graph.get_state(self._config(thread_id))
        if not snapshot.values:
            raise KeyError(f"Unknown run {thread_id}")
        return RunSnapshot(
            thread_id=thread_id,
            state=CopilotState.model_validate(snapshot.values),
            awaiting_review=bool(snapshot.next),
        )


def render_markdown(state: CopilotState) -> str:
    """Export the final application pack as Markdown."""
    if state.tailored is None:
        return ""
    t = state.tailored
    title = state.job.title if state.job else "Role"
    company = f" at {state.job.company}" if state.job and state.job.company else ""
    lines = [f"# Application pack: {title}{company}", ""]
    if state.fit:
        lines += [f"**Fit:** {state.fit.overall_score}/100 ({state.fit.verdict})", ""]
    lines += ["## Summary", "", t.tailored_summary, "", "## Resume bullets", ""]
    lines += [f"- {b.rewritten}" for b in t.bullets]
    lines += ["", "## Cover letter", "", t.cover_letter, ""]
    lines += ["## Recruiter message", "", t.recruiter_message, ""]
    return "\n".join(lines)
