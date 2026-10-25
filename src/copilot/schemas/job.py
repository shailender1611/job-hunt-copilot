"""Structured representation of a job description."""

from typing import Literal

from pydantic import BaseModel, Field

Seniority = Literal["intern", "junior", "mid", "senior", "staff", "principal", "manager", "unknown"]


class JobPosting(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    work_mode: Literal["onsite", "hybrid", "remote", "unknown"] = "unknown"
    seniority: Seniority = "unknown"
    min_years_experience: float | None = Field(
        default=None, description="Minimum years of experience required, if stated"
    )
    must_have_skills: list[str] = Field(
        default_factory=list, description="Skills stated as required / mandatory"
    )
    nice_to_have_skills: list[str] = Field(
        default_factory=list, description="Skills stated as preferred / a plus / bonus"
    )
    responsibilities: list[str] = Field(default_factory=list)
    domain: str | None = Field(default=None, description="Business domain, e.g. 'fintech'")
