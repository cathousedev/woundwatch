"""Pydantic domain schemas. Phase 1.

Defines WoundImage, WoundAssessment, WoundCase — the typed contracts every
other phase builds against. See references/roadmap.md Phase 1.

Validation notes:
- SNOMED codes arriving here come from the vision model as free-text-derived
  identifiers. We only enforce the SNOMED CT identifier *shape* (8-9 digit
  numeric) so malformed model output fails fast at the boundary. The actual
  free-text -> code mapping is the controlled lookup table of Phase 5, and
  unmapped terms are flagged there, never silently accepted.
- Wound measurements are non-negative by construction; Pydantic rejects
  negative values here rather than letting them reach the DB or FHIR layer.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from models.status import CaseStatus

# SNOMED CT concept identifiers are 8- or 9-digit numeric strings
# (e.g. "409274009" = pressure injury, "125549000" = pressure ulcer stage 3).
SNOMED_CODE_RE = re.compile(r"^\d{8,9}$")


class WoundImage(BaseModel):
    """One photographed wound image attached to a case."""

    id: UUID
    patient_ref: str
    image_path: str
    captured_at: datetime
    body_site: str | None = None  # free text now, SNOMED body-site code later


class WoundAssessment(BaseModel):
    """Structured assessment drafted by a VisionModelAdapter for one image."""

    image_id: UUID
    snomed_codes: list[str]
    wound_type: str  # e.g. "pressure injury", "surgical", "diabetic ulcer"
    length_cm: float | None = Field(default=None, ge=0)
    width_cm: float | None = Field(default=None, ge=0)
    depth_cm: float | None = Field(default=None, ge=0)
    tissue_description: str
    exudate: str | None = None
    surrounding_skin: str | None = None
    narrative: str
    model_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    raw_model_output: dict[str, Any]  # keep the unparsed response for audit/debug

    @field_validator("snomed_codes")
    @classmethod
    def _validate_snomed_codes(cls, codes: list[str]) -> list[str]:
        for code in codes:
            if not SNOMED_CODE_RE.fullmatch(code):
                raise ValueError(
                    f"invalid SNOMED code format: {code!r} "
                    "(expected an 8-9 digit SNOMED CT identifier, e.g. '409274009')"
                )
        return codes


class WoundCase(BaseModel):
    """Top-level unit of work: one patient, one or more wound images.

    `status` is never assigned directly anywhere in the codebase — every
    change goes through the single transition() helper (Phase 2), which
    checks models.status.can_transition() and writes the audit row.
    """

    id: UUID
    patient_ref: str
    images: list[WoundImage] = Field(min_length=1)  # a case with no images is meaningless
    assessments: list[WoundAssessment] = []
    status: CaseStatus = CaseStatus.pending_assessment
    created_at: datetime
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    fhir_observation_id: str | None = None  # set after successful POST to Aidbox
