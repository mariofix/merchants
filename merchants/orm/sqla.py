from typing import Literal

from sqlalchemy import JSON, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from merchants.integrations import local_factory

PaymentStatus = Literal["Created", "Paid", "Rejected"]


class PaymentMixin:
    __abstract__ = True

    provider: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    provider_transaction_id: Mapped[str] = mapped_column(
        String(512),
        index=True,
        nullable=True,
        default=None,
    )
    provider_response: Mapped[JSON | None]
    provider_error_response: Mapped[str | None]
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum("Created", "Paid", "Rejected", name="payment_status_choices"),
        nullable=False,
        default="Created",
        index=True,
    )
    payment_payload: Mapped[JSON | None]

    name_column: str | None = "name"
    email_column: str | None = "email"

    def make_payment(self):
        provider = local_factory(self.provider)
        return f"{provider}"
