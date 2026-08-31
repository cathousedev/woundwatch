"""Phase 1 unit tests: domain schema validation (models/schemas.py).

Instantiate each schema with valid data and confirm Pydantic catches bad
SNOMED code formats, negative measurements, out-of-range confidence, missing
required fields, and wrong types.
"""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models.schemas import WoundAssessment, WoundCase, WoundImage
from models.status import CaseStatus

NOW = datetime(2025, 1, 15, 10, 30, tzinfo=timezone.utc)


def valid_image() -> dict:
    return {
        "id": uuid.uuid4(),
        "patient_ref": "Patient/synthetic-001",
        "image_path": "/data/woundwatch/images/2025/01/15/img1.jpg",
        "captured_at": NOW,
        "body_site": "left heel",
    }


def valid_assessment(image_id: uuid.UUID) -> dict:
    return {
        "image_id": image_id,
        "snomed_codes": ["409274009", "125549000"],
        "wound_type": "pressure injury",
        "length_cm": 2.5,
        "width_cm": 1.8,
        "depth_cm": 0.4,
        "tissue_description": "70% granulation tissue",
        "exudate": "moderate serosanguinous",
        "surrounding_skin": "intact, mild erythema",
        "narrative": "Stage 3 pressure injury on left heel, granulating.",
        "model_confidence": 0.92,
        "raw_model_output": {"model": "mock", "prompt_version": "v1"},
    }


# --- WoundImage ---


def test_wound_image_valid():
    img = WoundImage(**valid_image())
    assert img.image_path.startswith("/data/woundwatch/images/")
    assert img.body_site == "left heel"


def test_wound_image_body_site_optional():
    data = valid_image()
    del data["body_site"]
    img = WoundImage(**data)
    assert img.body_site is None


@pytest.mark.parametrize("field", ["id", "patient_ref", "image_path", "captured_at"])
def test_wound_image_missing_required(field):
    data = valid_image()
    del data[field]
    with pytest.raises(ValidationError):
        WoundImage(**data)


def test_wound_image_rejects_non_uuid_id():
    data = valid_image()
    data["id"] = "not-a-uuid"
    with pytest.raises(ValidationError):
        WoundImage(**data)


# --- WoundAssessment ---


def test_wound_assessment_valid():
    image = WoundImage(**valid_image())
    assessment = WoundAssessment(**valid_assessment(image.id))
    assert assessment.snomed_codes == ["409274009", "125549000"]
    assert assessment.length_cm == 2.5
    assert assessment.model_confidence == 0.92


def test_wound_assessment_measurements_optional():
    data = valid_assessment(uuid.uuid4())
    for field in ("length_cm", "width_cm", "depth_cm", "model_confidence"):
        del data[field]
    assessment = WoundAssessment(**data)
    assert assessment.length_cm is None


@pytest.mark.parametrize(
    "bad_code",
    ["abc12345", "409274009x", "1234567", "SNOMED:409274009", "409274009.5"],
)
def test_wound_assessment_rejects_bad_snomed_formats(bad_code):
    data = valid_assessment(uuid.uuid4())
    data["snomed_codes"] = [bad_code]
    with pytest.raises(ValidationError):
        WoundAssessment(**data)


@pytest.mark.parametrize("field", ["length_cm", "width_cm", "depth_cm"])
def test_wound_assessment_rejects_negative_measurements(field):
    data = valid_assessment(uuid.uuid4())
    data[field] = -0.1
    with pytest.raises(ValidationError):
        WoundAssessment(**data)


@pytest.mark.parametrize("bad_confidence", [1.5, -0.2])
def test_wound_assessment_rejects_out_of_range_confidence(bad_confidence):
    data = valid_assessment(uuid.uuid4())
    data["model_confidence"] = bad_confidence
    with pytest.raises(ValidationError):
        WoundAssessment(**data)


@pytest.mark.parametrize("field", ["image_id", "snomed_codes", "wound_type", "tissue_description", "narrative", "raw_model_output"])
def test_wound_assessment_missing_required(field):
    data = valid_assessment(uuid.uuid4())
    del data[field]
    with pytest.raises(ValidationError):
        WoundAssessment(**data)


# --- WoundCase ---


def test_wound_case_valid():
    image = WoundImage(**valid_image())
    assessment = WoundAssessment(**valid_assessment(image.id))
    case = WoundCase(
        id=uuid.uuid4(),
        patient_ref="Patient/synthetic-001",
        images=[image],
        assessments=[assessment],
        created_at=NOW,
    )
    assert case.status is CaseStatus.pending_assessment  # default
    assert case.fhir_observation_id is None


def test_wound_case_accepts_every_status():
    for status in CaseStatus:
        case = WoundCase(
            id=uuid.uuid4(),
            patient_ref="Patient/synthetic-001",
            images=[WoundImage(**valid_image())],
            created_at=NOW,
            status=status,
        )
        assert case.status is status


def test_wound_case_rejects_unknown_status():
    with pytest.raises(ValidationError):
        WoundCase(
            id=uuid.uuid4(),
            patient_ref="Patient/synthetic-001",
            images=[WoundImage(**valid_image())],
            created_at=NOW,
            status="banana",
        )


def test_wound_case_requires_images():
    with pytest.raises(ValidationError):
        WoundCase(
            id=uuid.uuid4(),
            patient_ref="Patient/synthetic-001",
            images=[],
            created_at=NOW,
        )


def test_wound_case_rejects_nested_invalid_assessment():
    # Pass the bad assessment as a raw dict so WoundCase itself performs the
    # nested validation (not the explicit WoundAssessment construction).
    bad = valid_assessment(uuid.uuid4())
    bad["length_cm"] = -1
    with pytest.raises(ValidationError):
        WoundCase(
            id=uuid.uuid4(),
            patient_ref="Patient/synthetic-001",
            images=[WoundImage(**valid_image())],
            assessments=[bad],
            created_at=NOW,
        )
