from __future__ import annotations

from pydantic import BaseModel, Field


class RubricItem(BaseModel, frozen=True):
    """A single rubric criterion used for grading."""

    name: str
    description: str
    max_points: float


class RubricEvaluation(BaseModel, frozen=True):
    """Result of evaluating one rubric item against a submission."""

    rubric_item_name: str
    points_awarded: float
    max_points: float
    feedback: str


class GradingResult(BaseModel, frozen=True):
    """Aggregate grading result for an entire assignment."""

    points_awarded: float
    max_points: float
    feedback: str
    rubric_evaluations: list[RubricEvaluation] = Field(default_factory=list)
