import secrets

from pydantic import HttpUrl, computed_field
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
        if self.USE_HTTPS:
            return f"https://{self.DOMAIN}"
        return f"http://{self.DOMAIN}"

    PROJECT_NAME: str = "Merchants"
    SENTRY_DSN: HttpUrl | None = None

    SQLALCHEMY_DATABASE_URL: str = "sqlite:///merchants.db"

    ALLOWED_DOMAINS: list[str] | None = None

    PROCESS_ON_SAVE: bool = True


settings = Settings()  # type: ignore
