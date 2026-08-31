"""Case status machine. Phase 1.

CaseStatus enum + ALLOWED_TRANSITIONS + can_transition(). All status changes
elsewhere go through the single transition() helper (Phase 2) so a change and
its audit row can never drift apart. Direct assignment to a case's status is
forbidden everywhere except that helper.
"""
from enum import Enum


class CaseStatus(str, Enum):
    pending_assessment = "pending_assessment"
    assessment_failed = "assessment_failed"
    pending_review = "pending_review"
    approved = "approved"
    posting = "posting"
    posted = "posted"
    post_failed = "post_failed"
    rejected = "rejected"


ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.pending_assessment: {CaseStatus.pending_review, CaseStatus.assessment_failed},
    CaseStatus.assessment_failed: {CaseStatus.pending_assessment, CaseStatus.rejected},
    CaseStatus.pending_review: {CaseStatus.approved, CaseStatus.rejected},
    CaseStatus.approved: {CaseStatus.posting},
    CaseStatus.posting: {CaseStatus.posted, CaseStatus.post_failed},
    CaseStatus.post_failed: {CaseStatus.posting},
    # `posted` and `rejected` are terminal: no outgoing transitions.
}


def can_transition(current: CaseStatus, target: CaseStatus) -> bool:
    """True if moving `current` -> `target` is a legal transition."""
    return target in ALLOWED_TRANSITIONS.get(current, set())
