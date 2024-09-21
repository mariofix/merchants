from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROCESS_ON_SAVE: bool = True
    """Process the payment before commiting to database."""

    LOAD_FROM_DATABASE: bool = False
    """Retrieves Integrations from database."""

    API_ROUTER_PREFIX: str = "/merchants"
    """Base URI for Application."""


settings = Settings()  # type: ignore
