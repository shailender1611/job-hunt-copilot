"""Wire the nodes into a LangGraph StateGraph.

    START ─┬─► parse_resume ─┐
           └─► parse_jd ─────┴─► analyze_fit ─► END

parse_resume and parse_jd have no dependency on each other, so LangGraph runs
them in the same superstep (in parallel); analyze_fit waits for both.
"""

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from copilot.graph.nodes.analyze_fit import assess_fit
from copilot.graph.nodes.parse_jd import parse_jd
from copilot.graph.nodes.parse_resume import parse_resume
from copilot.graph.skills import compute_skill_match
from copilot.llm import get_llm
from copilot.schemas import FitAssessment, JobPosting, Resume
from copilot.schemas.state import CopilotState

# Given an output schema, return a runnable that produces it. Tests inject fakes.
LLMFactory = Callable[[type[BaseModel]], Runnable[Any, Any]]


def default_llm_factory(schema: type[BaseModel]) -> Runnable[Any, Any]:
    return get_llm(schema=schema)


def build_graph(
    llm_factory: LLMFactory = default_llm_factory,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    def parse_resume_node(state: CopilotState) -> dict[str, Any]:
        return {"resume": parse_resume(state.resume_text, llm=llm_factory(Resume))}

    def parse_jd_node(state: CopilotState) -> dict[str, Any]:
        return {"job": parse_jd(state.jd_text, llm=llm_factory(JobPosting))}

    def analyze_fit_node(state: CopilotState) -> dict[str, Any]:
        assert state.resume is not None and state.job is not None
        match = compute_skill_match(state.resume, state.job)
        fit = assess_fit(state.resume, state.job, match, llm=llm_factory(FitAssessment))
        return {"skill_match": match, "fit": fit}

    graph = StateGraph(CopilotState)
    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("parse_jd", parse_jd_node)
    graph.add_node("analyze_fit", analyze_fit_node)

    graph.add_edge(START, "parse_resume")
    graph.add_edge(START, "parse_jd")
    graph.add_edge(["parse_resume", "parse_jd"], "analyze_fit")
    graph.add_edge("analyze_fit", END)
    return graph.compile()
