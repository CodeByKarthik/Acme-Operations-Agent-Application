from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = Field(validation_alias="DATABASE_URL")
    keycloak_issuer: str = Field(validation_alias="KEYCLOAK_ISSUER")
    keycloak_client_id: str = Field(validation_alias="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: str = Field(validation_alias="KEYCLOAK_CLIENT_SECRET")
    keycloak_jwt_algorithm: str = Field(validation_alias="KEYCLOAK_JWT_ALGORITHM")
    keycloak_jwks_url: str = Field(validation_alias="KEYCLOAK_JWKS_URL")
    mcp_host: str = Field(validation_alias="MCP_HOST")
    mcp_port: int = Field(validation_alias="MCP_PORT")
    api_host: str = Field(validation_alias="API_HOST")
    api_port: int = Field(validation_alias="API_PORT")


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]