from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None)

    database_url: str = Field(alias="DATABASE_URL")
    env: str = Field(default="dev", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @model_validator(mode="after")
    def _enforce_prod_log_policy(self) -> "Settings":
        # In production, never allow DEBUG logging (even if misconfigured).
        if str(self.env).lower() == "prod" and str(self.log_level).upper() == "DEBUG":
            self.log_level = "INFO"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
