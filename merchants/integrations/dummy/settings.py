from dataclasses import dataclass


@dataclass
class Settings:
    endpoint: str = "https://api.example.com"
    api_key: str = "key_123456"
    api_secret: str = "secret_123456"


settings = Settings()
