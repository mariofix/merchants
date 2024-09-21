from typing import Any

# Intentionally the same structure as django-payments for compatibility reasons
INTEGRATIONS: dict[str, tuple[str, dict]] = {
    "default": (
        "merchants.integrations.dummy",
        {},
    ),
}


INTEGRATIONS_CACHE: dict[str, Any] = {}
