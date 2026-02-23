"""
Example 2 – Custom httpx transport
====================================

The SDK ships with a ``requests``-based transport, but you can plug in any
HTTP library by implementing the ``Transport`` protocol.

This example shows how to wrap ``httpx`` (sync client) so you can use features
like connection pooling, timeouts, retries, and proxies from httpx.

Install httpx first:  pip install httpx
"""
from __future__ import annotations

from typing import Any

import merchants
from merchants.providers.dummy import DummyProvider
from merchants.transport import HttpResponse, Transport

try:
    import httpx
except ImportError:
    raise SystemExit("This example requires httpx.  Run: pip install httpx")


class HttpxTransport(Transport):
    """Minimal Transport implementation backed by httpx.Client."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client()

    def send(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        params: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse:
        from merchants.transport import TransportError

        try:
            resp = self._client.request(
                method,
                url,
                headers=headers,
                json=json,
                params=params,
                timeout=timeout,
            )
        except httpx.RequestError as exc:
            raise TransportError(str(exc)) from exc

        try:
            body = resp.json()
        except ValueError:
            body = resp.text

        return HttpResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            body=body,
        )


# ---------------------------------------------------------------------------
# Use the custom transport with any provider
# ---------------------------------------------------------------------------
transport = HttpxTransport(
    httpx.Client(
        timeout=httpx.Timeout(10.0),
        follow_redirects=True,
    )
)

# DummyProvider doesn't make real HTTP calls, but the transport is wired in.
# Replace DummyProvider with StripeProvider / PayPalProvider / etc. and
# the custom transport will be used for all requests.
client = merchants.Client(
    provider=DummyProvider(),
    transport=transport,
)

session = client.payments.create_checkout(
    amount="19.99",
    currency="EUR",
    success_url="https://example.com/ok",
    cancel_url="https://example.com/cancel",
)
print("Redirect URL:", session.redirect_url)
