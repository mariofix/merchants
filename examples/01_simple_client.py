"""
Example 1 – Simple client setup
================================

Shows the quickest way to get a checkout redirect URL using the Stripe provider.
Run this script with a real Stripe test key to try it out, or use the DummyProvider
(no credentials needed) to simulate a payment locally.
"""
from decimal import Decimal

import merchants
from merchants.providers.dummy import DummyProvider
from merchants.providers.stripe import StripeProvider

# ---------------------------------------------------------------------------
# Option A: real Stripe provider
# ---------------------------------------------------------------------------
# Uncomment and replace with your test key:
# stripe = StripeProvider(api_key="sk_test_...")
# client = merchants.Client(provider=stripe)

# ---------------------------------------------------------------------------
# Option B: dummy provider (no credentials, random data)
# ---------------------------------------------------------------------------
dummy = DummyProvider()
client = merchants.Client(provider=dummy)

# Create a checkout session
try:
    session = client.payments.create_checkout(
        amount=Decimal("49.99"),
        currency="USD",
        success_url="https://myshop.example.com/success",
        cancel_url="https://myshop.example.com/cart",
        metadata={"order_id": "ORD-001"},
    )
    print("Session ID  :", session.session_id)
    print("Redirect URL:", session.redirect_url)
    # In a real web app you would redirect the user here:
    # return redirect(session.redirect_url)
except merchants.UserError as e:
    print("Payment setup failed:", e)

# Check payment status after the user returns
status = client.payments.get(session.session_id)
print("State       :", status.state)
print("Is final    :", status.is_final)
print("Is success  :", status.is_success)
