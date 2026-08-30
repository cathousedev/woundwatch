"""Central configuration for WoundWatch.

All values are sourced from the environment (or a `.env` file) so the app can
be run locally, in the compose stack, or on the homelab with the same code.

DB note: WoundWatch runs its **own dedicated Postgres** (its own container),
fully independent of the FHIR server — so WoundWatch can stand on its own and
is FHIR-server-agnostic. This DB is a staging area, not the FHIR source of
truth (the canonical record lives on the FHIR server once a case is approved).
The FHIR server is a pluggable external dependency (Aidbox today), addressed
by `fhir_base_url`; nothing in WoundWatch assumes a specific FHIR product.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Every field overridable via env var of the same name."""

    # --- Core service ---
    app_name: str = "woundwatch"
    env: str = Field(default="development", description="development / production")

    # --- Datastores ---
    # WoundWatch's OWN Postgres (its own container — independent of the FHIR
    # server). In the compose stack the service overrides this to point at the
    # `db` container; for local dev point at localhost.
    database_url: str = Field(
        default="postgresql://woundwatch:CHANGE_ME@localhost:5432/woundwatch",
        description="SQLAlchemy/psycopg2 DSN for WoundWatch's own Postgres container",
    )

    # --- FHIR server (Aidbox) ---
    # Existing Aidbox deployment; synthetic patients live here. Auth is a
    # single Bearer API-key/JWT (Aidbox does NOT use HAPI basic-auth).
    fhir_base_url: str = Field(
        default="http://localhost:27017/api",
        description="Base URL of the existing Aidbox FHIR server",
    )
    fhir_api_key: str | None = Field(
        default=None,
        description="Aidbox Bearer API-key/JWT for POST /Observation",
    )

    # Local MedGemma inference endpoint (Phase 4). OpenAI-compatible base.
    medgemma_endpoint: str = Field(
        default="http://localhost:8001/v1",
        description="Base URL of the local MedGemma serving endpoint",
    )
    medgemma_model_name: str = Field(
        default="medgemma", description="Model identifier sent to the MedGemma endpoint"
    )
    medgemma_timeout_s: float = Field(
        default=30.0, description="Per-request timeout for a single MedGemma call"
    )

    # Which VisionModelAdapter the pipeline uses (Phase 3). "mock" | "medgemma".
    vision_adapter: str = Field(
        default="mock", description="'mock' or 'medgemma'"
    )

    # --- Storage ---
    # Where uploaded wound photos are written. In production this is a volume
    # mounted into the container (see docker-compose.yml).
    image_storage_path: str = Field(
        default="/data/woundwatch/images",
        description="Directory for stored wound photos",
    )

    # --- Auth (write endpoints; Phase 9) ---
    # Single API key gating mutating endpoints. Clinical data even in a homelab.
    api_key: str | None = Field(
        default=None, description="Bearer API key required on write endpoints"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached accessor. `lru_cache` so config is read once per process."""
    return Settings()


# Convenience module-level default instance (import as `config.get_settings()`).
settings = Settings()
