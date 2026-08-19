"""Config-driven provider auto-loading.

Declares *which providers apply to this deployment* instead of hand-writing
an ``if app.config.get("X_API_KEY")`` chain per provider. A provider is
instantiated only when its required config keys are present, and its
module is only imported at that point — so a store that never configures
Flow never needs ``pyflowcl`` installed, and vice versa.

Each entry may be:

- a built-in provider's short key (``"flow"``, ``"stripe"``, ``"paypal"``, ``"khipu"``), or
- a dotted path to any custom :class:`~merchants.providers.Provider` subclass,
  e.g. ``"own_app.providers.webpay:MerchantsWebpay"``.

Either way, the resolved class must declare ``config_required`` (and
optionally ``config_optional``) — see :class:`~merchants.providers.Provider`.
Nothing about autoload needs to know whether a provider ships with the SDK
or lives in application code; that distinction only affects how the class
is imported.

Usage::

    import merchants
    from merchants.autoload import load_providers_from_config

    load_providers_from_config(app.config)   # registers whatever is configured

    # or restrict to an explicit allowlist (e.g. one deployment env per store copy):
    load_providers_from_config(
        app.config,
        active=["flow", "khipu", "own_app.providers.webpay:MerchantsWebpay"],
    )
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Mapping
from typing import Any

from merchants.providers import Provider, register_provider

logger = logging.getLogger(__name__)

# Short key -> dotted "module:ClassName" for providers shipped in the SDK.
# Custom providers skip this table entirely and pass their own dotted path
# directly as an `active` entry.
_BUILTIN_PROVIDERS: dict[str, str] = {
    "flow": "merchants.providers.flow:FlowProvider",
    "khipu": "merchants.providers.khipu:KhipuProvider",
    "stripe": "merchants.providers.stripe:StripeProvider",
    "paypal": "merchants.providers.paypal:PayPalProvider",
}


def _resolve(entry: str) -> type[Provider] | None:
    """Resolve a built-in key or ``"module:ClassName"`` path to a Provider class."""
    # `entry` is either a short built-in key ("flow") or already a dotted
    # path ("own_app.providers.webpay:MerchantsWebpay"). `.get(entry, entry)`
    # expands the former via the lookup table and passes the latter through
    # unchanged — either way, `dotted` ends up as "module.path:ClassName".
    dotted = _BUILTIN_PROVIDERS.get(entry, entry)
    module_path, _, class_name = dotted.partition(":")
    if not class_name:
        raise ValueError(
            f"Invalid autoload entry {entry!r}. Use a built-in key "
            f"({list(_BUILTIN_PROVIDERS)}) or a dotted path 'module:ClassName'."
        )
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        logger.warning(
            "Provider %r configured but its module/dependency isn't importable "
            "— skipping (%s)",
            entry,
            module_path,
        )
        return None
    return getattr(module, class_name)


def load_providers_from_config(
    config: Mapping[str, Any],
    *,
    active: list[str] | None = None,
    register: bool = True,
) -> list[Provider]:
    """Instantiate every provider (built-in or custom) whose config keys are present.

    Args:
        config: Any mapping (typically ``app.config``) holding provider
            credentials under the keys each provider declares via
            ``config_required`` / ``config_optional``.
        active: Provider entries to consider — built-in short keys and/or
            dotted ``"module:ClassName"`` paths to custom providers.
            Defaults to every built-in key; custom providers must always be
            listed explicitly here since there's no way to discover them
            otherwise. A provider is skipped automatically when its
            required config keys are absent.
        register: When ``True`` (default), also call
            :func:`merchants.register_provider` for each instantiated
            provider.

    Returns:
        The list of instantiated providers, in ``active`` order.
    """
    entries = active if active is not None else list(_BUILTIN_PROVIDERS)
    instantiated: list[Provider] = []

    for entry in entries:
        provider_cls = _resolve(entry)
        if provider_cls is None:
            continue

        required = provider_cls.config_required
        if required is None:
            logger.debug(
                "Provider %r has no config_required mapping — not autoloadable, skipping",
                entry,
            )
            continue

        missing = [cfg_key for cfg_key in required.values() if not config.get(cfg_key)]
        if missing:
            logger.debug(
                "Skipping provider %r — missing config keys: %s", entry, missing
            )
            continue  # not configured for this deployment

        kwargs = {kwarg: config[cfg_key] for kwarg, cfg_key in required.items()}
        kwargs |= {
            kwarg: config[cfg_key]
            for kwarg, cfg_key in provider_cls.config_optional.items()
            if config.get(cfg_key)
        }
        provider = provider_cls(**kwargs)
        if register:
            register_provider(provider)
        instantiated.append(provider)

    return instantiated
