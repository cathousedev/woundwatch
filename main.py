"""WoundWatch application entrypoint.

FastAPI app factory. Phase 0 only wires a `/health` endpoint so the service is
reachable and routable through Caddy. Subsequent phases mount their routers:

  - POST /cases, GET /cases/{id}          (Phase 6 / Phase 9)
  - /review/*                              (Phase 7)

Run locally:  uvicorn main:app --reload
Run in Docker: see Dockerfile / docker-compose.yml
"""
from fastapi import FastAPI

import config

app = FastAPI(
    title="WoundWatch",
    description=(
        "AI-assisted wound documentation: photo -> vision assessment -> RN "
        "review -> approved FHIR Observation. Human review is mandatory; "
        "no case reaches the Aidbox FHIR server without an approved review record."
    ),
    version="0.0.0",
)


@app.get("/health", tags=["ops"])
def health() -> dict:
    """Liveness probe. Returns 200 when the process is up.

    Intentionally cheap: does not touch the database or external services, so
    Caddy/Komodo health checks never fail on a downstream blip. A deeper
    /health/deep endpoint (DB reachable, adapter importable) can be added once
    Phase 2 lands.
    """
    return {
        "status": "ok",
        "service": config.settings.app_name,
        "env": config.settings.env,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.settings.env == "development",
    )
