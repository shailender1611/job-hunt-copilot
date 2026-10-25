"""State passed between LangGraph nodes. Each node returns a partial update."""

from pydantic import BaseModel, Field

from copilot.schemas.analysis import FitAssessment, SkillMatch
from copilot.schemas.job import JobPosting
from copilot.schemas.resume import Resume
from copilot.schemas.tailoring import TailoredApplication


class CopilotState(BaseModel):
    # inputs
    resume_text: str
    jd_text: str

    # produced by nodes
    resume: Resume | None = None
    job: JobPosting | None = None
    skill_match: SkillMatch | None = None
    fit: FitAssessment | None = None
    tailored: TailoredApplication | None = None
    grounding_warnings: list[str] = Field(default_factory=list)

    # human-in-the-loop
    feedback: str | None = None
    revisions: int = 0
    approved: bool = False
