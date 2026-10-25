"""Structured representation of a candidate's resume."""

from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: str
    title: str
    start: str | None = Field(default=None, description="Start date as written, e.g. 'Jan 2021'")
    end: str | None = Field(default=None, description="End date as written, or 'Present'")
    highlights: list[str] = Field(
        default_factory=list, description="Achievement bullets, verbatim or lightly cleaned"
    )


class Project(BaseModel):
    name: str
    description: str = ""
    tech: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str | None = None
    year: str | None = None


class Resume(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    total_years_experience: float | None = Field(
        default=None, description="Total professional experience in years, if inferable"
    )
    skills: list[str] = Field(default_factory=list, description="Technical skills, deduplicated")
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
