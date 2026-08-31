"""Phase 1 unit tests: review schemas (models/review.py).

Valid + invalid approve/reject/edit payloads. Cuts across:
- decision type and reviewer identity,
- reject requires a non-empty reason,
- edits are approve-only,
- edited fields get the same validation as the core domain model
  (SNOMED identifier shape, non-negative measurements).
"""
import uuid

import pytest
from pydantic import ValidationError

from models.review import ReviewDecision, ReviewEditRequest

VALIDATOR = str(uuid.uuid4())


# ---------------------------------------------------------------- approve ---

def test_approve_with_reason_and_no_edits():
    d = ReviewDecision(decision="approve", reviewer=VALIDATOR, reason="looks right")
    assert d.decision == "approve"
    assert d.edits is None


def test_approve_with_no_reason_is_allowed():
    d = ReviewDecision(decision="approve", reviewer=VALIDATOR)
    assert d.reason is None


def test_approve_with_full_edits():
    d = ReviewDecision(
        decision="approve",
        reviewer=VALIDATOR,
        edits=ReviewEditRequest(
            snomed_codes=["409274009"],
            wound_type="pressure injury",
            length_cm=2.5,
            width_cm=1.2,
            depth_cm=0.0,
            tissue_description="granulation",
            exudate="moderate",
            surrounding_skin="intact",
            narrative="corrected narrative",
            review_notes="measured with ruler in photo",
        ),
    )
    assert d.edits is not None
    assert d.edits.as_diff()["length_cm"] == 2.5


# ---------------------------------------------------------------- reject ---

def test_reject_with_reason():
    d = ReviewDecision(
        decision="reject",
        reviewer=VALIDATOR,
        reason="assessment does not match the photo",
    )
    assert d.reason is not None


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_reject_requires_non_empty_reason(reason):
    with pytest.raises(ValidationError):
        ReviewDecision(decision="reject", reviewer=VALIDATOR, reason=reason)


def test_reject_with_edits_is_rejected():
    with pytest.raises(ValidationError):
        ReviewDecision(
            decision="reject",
            reviewer=VALIDATOR,
            reason="bad",
            edits=ReviewEditRequest(wound_type="surgical"),
        )


def test_reject_with_review_notes_in_edits_is_still_rejected():
    # Even an "innocuous" note-only edit is a reject + edits combination.
    with pytest.raises(ValidationError):
        ReviewDecision(
            decision="reject",
            reviewer=VALIDATOR,
            reason="bad",
            edits=ReviewEditRequest(review_notes="filed under QA"),
        )


# ------------------------------------------------------------- reviewer ---

def test_reject_with_missing_reason():
    with pytest.raises(ValidationError):
        ReviewDecision(decision="reject", reviewer=VALIDATOR)


@pytest.mark.parametrize("reviewer", [None, "", " "])
def test_reviewer_required_and_non_empty(reviewer):
    with pytest.raises(ValidationError):
        ReviewDecision(decision="approve", reviewer=reviewer)


def test_decision_must_be_approve_or_reject():
    with pytest.raises(ValidationError):
        ReviewDecision(decision="maybe", reviewer=VALIDATOR)


# ------------------------------------------------------ edits validation ---

@pytest.mark.parametrize("codes", [["409274009", "125549000"], ["12345678"]])
def test_valid_snomed_codes_accepted(codes):
    assert ReviewEditRequest(snomed_codes=codes).snomed_codes == codes


@pytest.mark.parametrize("codes", [["4092740"], ["4092740099"], ["abc123"]])
def test_invalid_snomed_codes_rejected(codes):
    with pytest.raises(ValidationError):
        ReviewEditRequest(snomed_codes=codes)


@pytest.mark.parametrize("field", ["length_cm", "width_cm", "depth_cm"])
@pytest.mark.parametrize("value", [-0.1, -1.0, -99])
def test_negative_measurements_rejected(field, value):
    with pytest.raises(ValidationError):
        ReviewEditRequest(**{field: value})


def test_zero_measurements_accepted():
    e = ReviewEditRequest(length_cm=0.0, width_cm=0.0, depth_cm=0.0)
    assert e.as_diff() == {"length_cm": 0.0, "width_cm": 0.0, "depth_cm": 0.0}


def test_blank_wound_type_rejected():
    with pytest.raises(ValidationError):
        ReviewEditRequest(wound_type="")


# ------------------------------------------------------------ as_diff ------

def test_as_diff_contains_only_provided_fields():
    e = ReviewEditRequest(narrative="edited")
    assert e.as_diff() == {"narrative": "edited"}


def test_as_diff_excludes_unset_fields():
    e = ReviewEditRequest(exudate="scant")
    diff = e.as_diff()
    assert "exudate" in diff
    for key in ("snomed_codes", "wound_type", "length_cm", "tissue_description",
                "review_notes"):
        assert key not in diff
