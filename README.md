# WoundWatch

AI-assisted wound documentation, replacing the earlier n8n workflow.

A nurse photographs a wound → a vision model drafts a structured clinical
assessment → an RN reviews and approves it → **only then** is it posted to the
existing Aidbox FHIR server as an `Observation`.

**Non-negotiable:** human review is mandatory. No case reaches HAPI FHIR
without an approved review record. AI output is never posted automatically.

## Status

Phase-by-phase build plan: see the project roadmap. Currently **Phase 0** —
FastAPI skeleton with a `/health` endpoint, dependency management, Docker, and
a compose file.

## Development

```bash
# deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# run locally
uvicorn main:app --reload

# tests
pytest
```

Copy `.env.example` to `.env` and fill in real values before wiring the real
services. WoundWatch reuses the existing Aidbox FHIR Postgres instance under
its own `woundwatch` schema (a staging area, not the FHIR source of truth).
Aidbox is Postgres-backed, so WoundWatch's staging tables share the same
Postgres host but live in an isolated schema.

## Production

`woundwatch.cathousedev.com`, fronted by Caddy (Cloudflare DNS-01 TLS),
running in the Komodo-managed compose stack. See `docker-compose.yml`.
