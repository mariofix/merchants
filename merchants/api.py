import rich


def integration_factory(slug: str, config: dict):
    rich.print(f"Creating integration {slug} ...")

    return {}


def find_integration(slug: str):
    rich.print(f"Searching for integration: {slug} ...")

    return {
        "name": "Simple Integration",
        "slug": "dummy",
        "is_active": True,
        "integration_class": "merchants.integrations.dummy",
        "config": {
            "not_needed": True,
        },
    }


def load_integration(slug: str):
    rich.print(f"Loading {slug} to cache...")


def process_payment(payment):
    rich.print(payment)

    if payment.status not in ["created"]:
        raise AttributeError("Only created payments can start the process.")

    integration, _ = find_integration(payment.integration_slug)
    # if not payment.integration_id:
    #     if getattr(settings, "LOAD_FROM_DATABASE", None):
    #         integration_config = None
    #     else:
    #         integration_config = getattr(settings, payment.integration_slug, None)
    # else:
    #     rich.print(f"Using integration: {payment.integration} ...")
    #     integration_config = payment.integration.config

    rich.print(f"{integration = }")

    return payment
