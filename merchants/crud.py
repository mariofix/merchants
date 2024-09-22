from merchants.base import INTEGRATIONS


def get_integration(slug: str) -> dict:
    if slug not in INTEGRATIONS.keys():
        raise AttributeError(f"Integration {slug} does not exist in the config file.")

    integration_data = {
        "slug": slug,
        "integration_class": INTEGRATIONS[slug][0],
        "config": INTEGRATIONS[slug][1],
    }
    return integration_data
