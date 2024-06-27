from ..config import base_settings


def local_factory(slug: str):
    if slug not in base_settings.available_providers:
        raise NotImplementedError(f"The provider {slug} is not supported.")

    return slug


def create_provider(slug: str):
    if slug not in base_settings.available_providers:
        raise NotImplementedError(f"The provider {slug} is not supported.")

    return slug
