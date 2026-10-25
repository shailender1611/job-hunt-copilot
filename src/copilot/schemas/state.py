"""State passed between LangGraph nodes. Each node returns a partial update."""

from pydantic import BaseModel

from copilot.schemas.analysis import FitAssessment, SkillMatch
from copilot.schemas.job import JobPosting
from copilot.schemas.resume import Resume


class CopilotState(BaseModel):
    # inputs
    resume_text: str
    jd_text: str

    # produced by nodes
    resume: Resume | None = None
    job: JobPosting | None = None
    skill_match: SkillMatch | None = None
    fit: FitAssessment | None = None
