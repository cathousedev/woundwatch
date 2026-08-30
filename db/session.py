"""Database session factory. Phase 2.

Engine + session factory reading config.database_url (shared Aidbox Postgres,
own `woundwatch` schema). Plus log_assessment_run / log_case_event helpers and
the single transition(case, target_status, actor, action) helper.
"""
