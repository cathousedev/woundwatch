"""FHIR mapping. Phase 5.

to_observation(assessment, patient_ref) -> fhir.resources Observation.
One Observation per image (not per case). Free-text concepts map through a
local controlled SNOMED lookup; unmapped terms are flagged, never trusted.
"""
