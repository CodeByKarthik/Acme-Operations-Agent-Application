from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    database_url: str = Field(validation_alias="DATABASE_URL")
    keycloak_issuer: str = Field(validation_alias="KEYCLOAK_ISSUER")
    keycloak_client_id: str = Field(validation_alias="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: str = Field(validation_alias="KEYCLOAK_CLIENT_SECRET")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]