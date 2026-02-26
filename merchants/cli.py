"""merchants CLI – a Typer/Click example for the merchants SDK.

Install the CLI extra to use this app::

    pip install "merchants[cli]"

Then run::

    merchants --help
    merchants version
    merchants providers
    merchants info dummy
    merchants payments checkout --provider dummy --amount 9.99 --currency USD \\
        --success-url https://example.com/ok --cancel-url https://example.com/cancel
    merchants payments get <payment_id> --provider dummy
    merchants payments webhook --file payload.json --provider dummy
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import typer

from merchants.providers import (
    Provider,
    describe_providers,
    get_provider,
    list_providers,
)
from merchants.version import __version__

app = typer.Typer(
    name="merchants",
    help="merchants – framework-agnostic hosted-checkout payment SDK.",
    no_args_is_help=True,
)

payments_app = typer.Typer(
    name="payments",
    help="Create checkout sessions, retrieve payment status, and parse webhooks.",
    no_args_is_help=True,
)
app.add_typer(payments_app, name="payments")


# ---------------------------------------------------------------------------
# Provider resolution helper
# ---------------------------------------------------------------------------


def _resolve_provider(key: str) -> Provider:
    """Resolve a provider by key.

    Resolution order:

    1. Registry (pre-registered instances via :func:`~merchants.providers.register_provider`).
    2. Known built-in providers configured via environment variables.
    3. ``dummy`` provider (no credentials required).

    Raises :class:`typer.Exit` with code 1 on any configuration error.
    """
    # 1. Registry first
    try:
        return get_provider(key)
    except KeyError:
        pass

    # 2. Built-in providers from environment
    if key == "dummy":
        from merchants.providers.dummy import DummyProvider

        return DummyProvider()

    if key == "stripe":
        api_key = os.environ.get("STRIPE_API_KEY", "")
        if not api_key:
            typer.echo("STRIPE_API_KEY environment variable is not set.", err=True)
            raise typer.Exit(1)
        from merchants.providers.stripe import StripeProvider

        return StripeProvider(api_key=api_key)

    if key == "paypal":
        token = os.environ.get("PAYPAL_ACCESS_TOKEN", "")
        if not token:
            typer.echo("PAYPAL_ACCESS_TOKEN environment variable is not set.", err=True)
            raise typer.Exit(1)
        from merchants.providers.paypal import PayPalProvider

        return PayPalProvider(access_token=token)

    if key == "generic":
        checkout_url = os.environ.get("GENERIC_CHECKOUT_URL", "")
        payment_url = os.environ.get("GENERIC_PAYMENT_URL", "")
        if not checkout_url or not payment_url:
            typer.echo(
                "GENERIC_CHECKOUT_URL and GENERIC_PAYMENT_URL environment variables are required.",
                err=True,
            )
            raise typer.Exit(1)
        from merchants.providers.generic import GenericProvider

        return GenericProvider(checkout_url, payment_url)

    typer.echo(
        f"Provider {key!r} is not registered and has no built-in configuration.\n"
        "Register it first with merchants.register_provider(), or use 'dummy' for testing.",
        err=True,
    )
    raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Show the merchants package version."""
    typer.echo(f"merchants {__version__}")


@app.command()
def providers(
    output: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format: 'table' or 'json'.",
        metavar="FORMAT",
    ),
) -> None:
    """List all registered payment providers."""
    keys = list_providers()
    if not keys:
        typer.echo("No providers are currently registered.")
        typer.echo(
            "Register one first, e.g.:  merchants.register_provider(DummyProvider())"
        )
        raise typer.Exit()

    infos = describe_providers()

    if output == "json":
        typer.echo(json.dumps([i.model_dump() for i in infos], indent=2))
        return

    # Default: table
    col_widths = (12, 20, 18, 10)
    header = (
        f"{'Key':<{col_widths[0]}} {'Name':<{col_widths[1]}} "
        f"{'Author':<{col_widths[2]}} {'Version':<{col_widths[3]}}"
    )
    separator = "-" * sum(col_widths + (3,) * len(col_widths))
    typer.echo(header)
    typer.echo(separator)
    for info in infos:
        typer.echo(
            f"{info.key:<{col_widths[0]}} "
            f"{info.name:<{col_widths[1]}} "
            f"{info.author:<{col_widths[2]}} "
            f"{info.version:<{col_widths[3]}}"
        )


@app.command()
def info(
    key: str = typer.Argument(..., help="Provider key (e.g. 'stripe', 'dummy')."),
    output: str = typer.Option(
        "text",
        "--output",
        "-o",
        help="Output format: 'text' or 'json'.",
        metavar="FORMAT",
    ),
) -> None:
    """Show metadata for a registered provider."""
    try:
        provider = get_provider(key)
    except KeyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    provider_info = provider.get_info()

    if output == "json":
        typer.echo(provider_info.model_dump_json(indent=2))
        return

    typer.echo(f"Key         : {provider_info.key}")
    typer.echo(f"Name        : {provider_info.name}")
    typer.echo(f"Author      : {provider_info.author}")
    typer.echo(f"Version     : {provider_info.version}")
    typer.echo(f"Description : {provider_info.description}")
    typer.echo(f"URL         : {provider_info.url}")


# ---------------------------------------------------------------------------
# payments sub-commands
# ---------------------------------------------------------------------------


@payments_app.command("checkout")
def payments_checkout(
    provider_key: str = typer.Option(
        "dummy",
        "--provider",
        "-p",
        help="Provider key (e.g. 'stripe', 'dummy'). "
        "Built-in providers read credentials from environment variables.",
        metavar="KEY",
    ),
    amount: str = typer.Option(
        ..., "--amount", "-a", help="Payment amount (e.g. '19.99')."
    ),
    currency: str = typer.Option(
        "USD", "--currency", "-c", help="ISO-4217 currency code."
    ),
    success_url: str = typer.Option(
        "https://example.com/success",
        "--success-url",
        help="Redirect URL after successful payment.",
    ),
    cancel_url: str = typer.Option(
        "https://example.com/cancel",
        "--cancel-url",
        help="Redirect URL when the user cancels.",
    ),
    metadata: str | None = typer.Option(
        None,
        "--metadata",
        "-m",
        help='JSON string of key-value metadata (e.g. \'{"key": "value"}\').',
    ),
    output: str = typer.Option(
        "text",
        "--output",
        "-o",
        help="Output format: 'text' or 'json'.",
        metavar="FORMAT",
    ),
) -> None:
    """Create a hosted-checkout session and print the redirect URL."""
    from decimal import Decimal, InvalidOperation

    provider = _resolve_provider(provider_key)

    try:
        amount_decimal = Decimal(amount)
    except InvalidOperation:
        typer.echo(f"Invalid amount: {amount!r}", err=True)
        raise typer.Exit(1)

    meta: dict = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError as exc:
            typer.echo(f"Invalid JSON in --metadata: {exc}", err=True)
            raise typer.Exit(1)

    from merchants.providers import UserError

    try:
        session = provider.create_checkout(
            amount_decimal, currency, success_url, cancel_url, meta or None
        )
    except UserError as exc:
        typer.echo(f"Payment error: {exc}", err=True)
        raise typer.Exit(1)

    if output == "json":
        typer.echo(
            json.dumps(
                {
                    "session_id": session.session_id,
                    "redirect_url": session.redirect_url,
                    "provider": session.provider,
                    "amount": str(session.amount),
                    "currency": session.currency,
                    "metadata": session.metadata,
                },
                indent=2,
            )
        )
        return

    typer.echo(f"Session ID  : {session.session_id}")
    typer.echo(f"Redirect URL: {session.redirect_url}")
    typer.echo(f"Provider    : {session.provider}")
    typer.echo(f"Amount      : {session.amount} {session.currency}")


@payments_app.command("get")
def payments_get(
    payment_id: str = typer.Argument(
        ..., help="Provider-specific payment or session ID."
    ),
    provider_key: str = typer.Option(
        "dummy",
        "--provider",
        "-p",
        help="Provider key used to look up the payment.",
        metavar="KEY",
    ),
    output: str = typer.Option(
        "text",
        "--output",
        "-o",
        help="Output format: 'text' or 'json'.",
        metavar="FORMAT",
    ),
) -> None:
    """Retrieve and display the status of a payment."""
    from merchants.providers import UserError

    provider = _resolve_provider(provider_key)

    try:
        status = provider.get_payment(payment_id)
    except UserError as exc:
        typer.echo(f"Payment error: {exc}", err=True)
        raise typer.Exit(1)

    if output == "json":
        typer.echo(
            json.dumps(
                {
                    "payment_id": status.payment_id,
                    "state": status.state.value,
                    "provider": status.provider,
                    "amount": str(status.amount) if status.amount is not None else None,
                    "currency": status.currency,
                    "is_final": status.is_final,
                    "is_success": status.is_success,
                },
                indent=2,
            )
        )
        return

    typer.echo(f"Payment ID  : {status.payment_id}")
    typer.echo(f"State       : {status.state.value}")
    typer.echo(f"Provider    : {status.provider}")
    if status.amount is not None:
        typer.echo(f"Amount      : {status.amount} {status.currency or ''}")
    typer.echo(f"Final       : {'yes' if status.is_final else 'no'}")
    typer.echo(f"Success     : {'yes' if status.is_success else 'no'}")


@payments_app.command("webhook")
def payments_webhook(
    file: Path | None = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to the webhook payload file. Reads from stdin if omitted.",
    ),
    provider_key: str = typer.Option(
        "unknown",
        "--provider",
        "-p",
        help="Provider name hint for normalisation.",
        metavar="KEY",
    ),
    secret: str | None = typer.Option(
        None,
        "--secret",
        help="Webhook signing secret for HMAC-SHA256 signature verification.",
    ),
    signature: str | None = typer.Option(
        None,
        "--signature",
        help="Signature header value to verify (e.g. 'sha256=abc123…').",
    ),
    output: str = typer.Option(
        "text",
        "--output",
        "-o",
        help="Output format: 'text' or 'json'.",
        metavar="FORMAT",
    ),
) -> None:
    """Parse and optionally verify a webhook payload."""
    from merchants.webhooks import (
        WebhookVerificationError,
        parse_event,
        verify_signature,
    )

    # Read payload
    if file is not None:
        try:
            payload = Path(file).read_bytes()
        except OSError as exc:
            typer.echo(f"Cannot read file: {exc}", err=True)
            raise typer.Exit(1)
    else:
        payload = sys.stdin.buffer.read()

    # Signature verification (optional)
    if secret and signature:
        try:
            verify_signature(payload, secret, signature)
        except WebhookVerificationError as exc:
            typer.echo(f"Signature verification failed: {exc}", err=True)
            raise typer.Exit(1)
        verified = True
    else:
        verified = False

    # Parse via registered provider if available, else generic parse_event
    try:
        provider = get_provider(provider_key)
        event = provider.parse_webhook(payload, {})
    except KeyError:
        event = parse_event(payload, provider=provider_key)

    if output == "json":
        typer.echo(
            json.dumps(
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "payment_id": event.payment_id,
                    "state": event.state.value,
                    "provider": event.provider,
                    "verified": verified,
                },
                indent=2,
            )
        )
        return

    typer.echo(f"Event ID    : {event.event_id or '(none)'}")
    typer.echo(f"Event Type  : {event.event_type}")
    typer.echo(f"Payment ID  : {event.payment_id or '(none)'}")
    typer.echo(f"State       : {event.state.value}")
    typer.echo(f"Provider    : {event.provider}")
    typer.echo(f"Verified    : {'yes' if verified else 'no (no secret provided)'}")


if __name__ == "__main__":
    app()
