"""Fit analysis between a resume and a job posting."""

from typing import Literal

from pydantic import BaseModel, Field


class SkillMatch(BaseModel):
    """Deterministic keyword coverage, computed without the LLM."""

    matched_must_have: list[str] = Field(default_factory=list)
    missing_must_have: list[str] = Field(default_factory=list)
    matched_nice_to_have: list[str] = Field(default_factory=list)
    missing_nice_to_have: list[str] = Field(default_factory=list)
    coverage_score: int = Field(
        ge=0, le=100, description="Weighted keyword coverage: must-have 80%, nice-to-have 20%"
    )


class SkillGap(BaseModel):
    skill: str
    severity: Literal["blocker", "important", "minor"]
    suggestion: str = Field(description="Concrete way to close or reframe the gap")


class FitAssessment(BaseModel):
    """LLM judgement that goes beyond keywords (seniority, domain, depth)."""

    overall_score: int = Field(ge=0, le=100)
    verdict: Literal["strong", "moderate", "weak"]
    summary: str = Field(description="Two or three sentences a recruiter would write")
    strengths: list[str] = Field(default_factory=list)
    gaps: list[SkillGap] = Field(default_factory=list)
    experience_fit: str = Field(description="How years and seniority compare to the role")
