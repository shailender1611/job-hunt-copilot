"""The human reviewer's decision when the graph pauses for approval."""

from typing import Literal

from pydantic import BaseModel, model_validator


class ReviewDecision(BaseModel):
    action: Literal["approve", "revise"]
    feedback: str | None = None

    @model_validator(mode="after")
    def _revise_needs_feedback(self) -> "ReviewDecision":
        if self.action == "revise" and not (self.feedback and self.feedback.strip()):
            raise ValueError("feedback is required when requesting a revision")
        return self
