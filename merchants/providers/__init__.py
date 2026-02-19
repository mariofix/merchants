"""Provider registry and factory.

Usage
-----
Register a provider instance under a name and retrieve it later::

    from merchants.providers import registry
    from merchants.providers.mock import MockProvider

    registry.register("mock", MockProvider())
    provider = registry.get("mock")

Or pass the provider name to :class:`~merchants.client.MerchantsClient`::

    from merchants.client import MerchantsClient
    client = MerchantsClient(provider="mock")
"""

from __future__ import annotations

from merchants.errors import ProviderNotFoundError
from merchants.providers.base import BaseProvider


class ProviderRegistry:
    """Simple name-based registry for :class:`~merchants.providers.base.BaseProvider` instances."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        """Register *provider* under *name*.

        Parameters
        ----------
        name:
            Arbitrary string key (e.g., ``"stripe"``, ``"paypal"``).
        provider:
            A :class:`~merchants.providers.base.BaseProvider` instance.
        """
        self._providers[name] = provider

    def get(self, name: str) -> BaseProvider:
        """Return the provider registered as *name*.

        Raises
        ------
        ProviderNotFoundError
            When *name* is not in the registry.
        """
        try:
            return self._providers[name]
        except KeyError:
            raise ProviderNotFoundError(name)

    def names(self) -> list[str]:
        """Return a list of all registered provider names."""
        return list(self._providers.keys())


# Module-level default registry instance
registry = ProviderRegistry()

# Pre-register the built-in mock provider
from merchants.providers.mock import MockProvider  # noqa: E402

registry.register("mock", MockProvider())

__all__ = [
    "BaseProvider",
    "ProviderRegistry",
    "registry",
    "MockProvider",
]
