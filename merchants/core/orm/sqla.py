from typing import Any, Literal, Optional

from sqlalchemy import JSON, Enum, String
from sqlalchemy.orm import DeclarativeBase, Mapped, column_property, declared_attr, mapped_column

from merchants.providers import factory

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
    provider_response: Mapped[JSON] = mapped_column(JSON, nullable=True, default=None)
    provider_error_response: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum("Created", "Paid", "Rejected", name="payment_status_choices"),
        nullable=False,
        default="Created",
    )
    payment_payload: Mapped[JSON] = mapped_column(JSON, nullable=True, default=None)

    name_column: Optional[str] = "name"
    email_column: Optional[str] = "email"

    def make_payment(self):
        provider = factory(self.provider)
        return f"{provider}"
