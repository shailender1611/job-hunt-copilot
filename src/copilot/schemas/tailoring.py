"""Generated application material: rewritten bullets, cover letter, outreach."""

from pydantic import BaseModel, Field


class RewrittenBullet(BaseModel):
    original: str = Field(description="The resume bullet exactly as it appears in the resume")
    rewritten: str
    rationale: str = Field(description="Which job requirement this rewrite targets")


class TailoredApplication(BaseModel):
    tailored_summary: str = Field(description="3-4 line professional summary for this role")
    bullets: list[RewrittenBullet] = Field(default_factory=list)
    cover_letter: str
    recruiter_message: str = Field(description="Short LinkedIn/email note, under 300 characters")
