import secrets
from typing import Annotated, Any

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")
    SECRET_KEY: str = secrets.token_urlsafe(32)
    USE_HTTPS: bool = False
    DOMAIN: str = "tardis.local"
    DEBUG: bool = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.USE_HTTPS:
            return f"https://{self.DOMAIN}"
        return f"http://{self.DOMAIN}"

    PROJECT_NAME: str = "Merchants"
    SENTRY_DSN: HttpUrl | None = None

    SQLALCHEMY_DATABASE_URI: str = "sqlite:///merchants.db"


settings = Settings()  # type: ignore
