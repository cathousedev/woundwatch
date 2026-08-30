"""Pipeline orchestration. Phase 6.

run_pipeline(case): capture -> vision -> FHIR draft, case-level, with every
status change going through the status machine + audit log.
"""
