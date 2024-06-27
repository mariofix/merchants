from dataclasses import dataclass

__version__ = "0.1.0"
__merchants_name__ = "dummy"
__merchants_slug__ = "dummy"


@dataclass
class Settings:
    endpoint: str = "https://api.example.com"
    api_key: str = "key_123456"
    api_secret: str = "secret_123456"


settings = Settings()
