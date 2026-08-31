"""Review-specific request/response schemas. Phase 1.

Keeps the RN review payloads (approve / reject / edit) separate from the core
domain model in models/schemas.py, per the roadmap. The review workflow
(Phase 7) builds `POST /review/{case_id}/approve` and `.../reject` on these
shapes, and a decision's `reviewer` becomes the `actor` for the Phase 2
transition() helper — so a human decision lands in the same `case_events`
audit log as automated transitions.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from models.schemas import SNOMED_CODE_RE

DecisionType = Literal["approve", "reject"]


class ReviewEditRequest(BaseModel):
    """Optional corrections an RN may apply to a WoundAssessment on approval.

    All fields are optional — the caller sends only the fields actually
    changed, and the review layer (Phase 7) applies them over the AI's draft.
    Validation mirrors models/schemas.py: SNOMED identifier shape and
    non-negative measurements.
    """

    snomed_codes: list[str] | None = None
    wound_type: str | None = Field(default=None, min_length=1)
    length_cm: float | None = Field(default=None, ge=0)
    width_cm: float | None = Field(default=None, ge=0)
    depth_cm: float | None = Field(default=None, ge=0)
    tissue_description: str | None = None
    exudate: str | None = None
    surrounding_skin: str | None = None
    narrative: str | None = None
    review_notes: str | None = None

    @field_validator("snomed_codes")
    @classmethod
    def _validate_snomed_codes(cls, codes: list[str] | None) -> list[str] | None:
        if codes is None:
            return None
        for code in codes:
            if not SNOMED_CODE_RE.fullmatch(code):
                raise ValueError(
                    f"invalid SNOMED code format: {code!r} "
                    "(expected an 8-9 digit SNOMED CT identifier, e.g. '409274009')"
                )
        return codes

    def as_diff(self) -> dict[str, Any]:
        """Only the fields explicitly provided (the changes to apply)."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class ReviewDecision(BaseModel):
    """An RN's decision on a case in `pending_review` (Phase 7 applies it).

    - approve: transitions the case to `approved` (then `posting`); may carry
      edits correcting the AI's draft assessment.
    - reject: transitions the case to `rejected`; a non-empty reason is
      required so the rejection is auditable.
    `reviewer` is the `actor` passed to the Phase 2 transition() helper.
    """

    decision: DecisionType
    reviewer: str = Field(min_length=1)
    reason: str | None = None
    edits: ReviewEditRequest | None = None

    @model_validator(mode="after")
    def _validate_decision(self) -> "ReviewDecision":
        if not self.reviewer.strip():
            raise ValueError("reviewer must be a non-blank actor identifier")
        if self.decision == "reject" and not (self.reason and self.reason.strip()):
            raise ValueError("a non-empty rejection reason is required when decision == 'reject'")
        if self.decision == "reject" and self.edits is not None:
            raise ValueError("edits are only allowed on approval, not rejection")
        return self
