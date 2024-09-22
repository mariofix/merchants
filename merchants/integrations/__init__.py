import secrets
from dataclasses import dataclass

from ..base import BaseIntegration


@dataclass
class DummyIntegration(BaseIntegration):
    name: str = "Dummy"
    version: str = "0.0.1"
    author: str = "mariofix"

    def process(self):
        data = {
            "token": secrets.token_urlsafe(32),
            "headers": None,
            "data": None,
        }
        return data

    def refund(self): ...


@dataclass
class StripeCheckoutIntegration(BaseIntegration):
    name: str = "Stripe Checkout"
    version: str = "0.0.1"
    author: str = "mariofix"
    api_key: str = "sk_test_26PHem9AhJZvU623DfE1x4sd"

    def process(self):
        import stripe

        stripe.api_key = self.api_key

        data = {
            "token": secrets.token_urlsafe(32),
            "headers": None,
            "data": None,
        }
        return data

    def refund(self): ...
