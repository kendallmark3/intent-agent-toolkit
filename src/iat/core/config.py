"""Application settings.

All sensitive configuration is externalized to environment variables (prefix ``IAT_``) or a
local ``.env`` file that is git-ignored. The service fails closed: it refuses to start without
a signing secret, so there is no unauthenticated "developer mode".
"""

from __future__ import annotations

import datetime as dt
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "suppliers.json"
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="IAT_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Intent Agent Toolkit"
    log_level: str = "INFO"

    # --- Identity (local JWT issuer boundary; see docs/SECURITY.md) ---
    jwt_secret: SecretStr = Field(
        ..., description="HMAC secret used to verify bearer tokens. Required; min 32 chars."
    )
    jwt_issuer: str = "iat-local"
    jwt_audience: str = "iat-api"
    jwt_algorithm: str = "HS256"

    # --- Agent execution ---
    supplier_data_path: Path = DEFAULT_DATA_PATH
    assessment_date: dt.date | None = Field(
        default=None,
        description="Fixed 'as of' date for evidence expiry checks. Defaults to today (UTC).",
    )

    docs_enabled: bool = True

    @field_validator("jwt_secret")
    @classmethod
    def _secret_strength(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_SECRET_LENGTH:
            raise ValueError(f"IAT_JWT_SECRET must be at least {MIN_SECRET_LENGTH} characters")
        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def _algorithm_allowlist(cls, value: str) -> str:
        if value not in {"HS256", "HS384", "HS512"}:
            raise ValueError("Only HMAC algorithms are supported by the local verifier")
        return value

    def as_of(self) -> dt.date:
        return self.assessment_date or dt.datetime.now(dt.UTC).date()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # values come from the environment
