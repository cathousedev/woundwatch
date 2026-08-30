"""Case status machine. Phase 1.

CaseStatus enum + ALLOWED_TRANSITIONS + can_transition(). All status changes
elsewhere go through the single transition() helper (Phase 2) so a change and
its audit row can never drift apart.
"""
