"""Phase 1 unit tests: status machine (models/status.py).

Every listed valid transition succeeds; a sample of invalid transitions is
rejected; terminal states have no outgoing transitions.
"""
import pytest

from models.status import ALLOWED_TRANSITIONS, CaseStatus, can_transition

VALID_TRANSITIONS = [
    (CaseStatus.pending_assessment, CaseStatus.pending_review),
    (CaseStatus.pending_assessment, CaseStatus.assessment_failed),
    (CaseStatus.assessment_failed, CaseStatus.pending_assessment),
    (CaseStatus.assessment_failed, CaseStatus.rejected),
    (CaseStatus.pending_review, CaseStatus.approved),
    (CaseStatus.pending_review, CaseStatus.rejected),
    (CaseStatus.approved, CaseStatus.posting),
    (CaseStatus.posting, CaseStatus.posted),
    (CaseStatus.posting, CaseStatus.post_failed),
    (CaseStatus.post_failed, CaseStatus.posting),
]

INVALID_TRANSITIONS = [
    (CaseStatus.pending_assessment, CaseStatus.posted),
    (CaseStatus.pending_assessment, CaseStatus.approved),
    (CaseStatus.rejected, CaseStatus.approved),
    (CaseStatus.rejected, CaseStatus.pending_assessment),
    (CaseStatus.posted, CaseStatus.posting),
    (CaseStatus.pending_review, CaseStatus.posting),
]


@pytest.mark.parametrize("current,target", VALID_TRANSITIONS)
def test_valid_transitions_allowed(current, target):
    assert can_transition(current, target)


@pytest.mark.parametrize("current,target", INVALID_TRANSITIONS)
def test_invalid_transitions_rejected(current, target):
    assert not can_transition(current, target)


def test_terminal_states_have_no_outgoing_transitions():
    for target in CaseStatus:
        assert not can_transition(CaseStatus.posted, target)
        assert not can_transition(CaseStatus.rejected, target)


def test_can_transition_matches_table_exhaustively():
    # can_transition() must agree with ALLOWED_TRANSITIONS for every pair,
    # including pairs never listed explicitly.
    for current in CaseStatus:
        for target in CaseStatus:
            expected = target in ALLOWED_TRANSITIONS.get(current, set())
            assert can_transition(current, target) is expected
