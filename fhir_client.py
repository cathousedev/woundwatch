"""Aidbox FHIR client. Phase 8.

Thin httpx wrapper: POST /Observation against config.fhir_base_url with a
Bearer API-key/JWT (Aidbox, not HAPI basic-auth). Approved cases post here;
the returned resource id is stored on the case row.
"""
