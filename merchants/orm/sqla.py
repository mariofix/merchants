import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Numeric, String, event
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
from sqlalchemy.sql import func

from merchants.core.schemas import ModelStatus

# from merchants.integrations import local_factory


@declarative_mixin
class PaymentMixin:
    """
    A mixin class for handling payment-related attributes and functionality.

    This abstract class provides common fields and methods for payment processing,
    including account information, transaction details, and payment status.
    """

    __abstract__ = True

    account: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    """The account identifier associated with the payment."""

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    """The payment amount."""

    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    """The currency code for the payment (e.g., 'USD', 'EUR')."""

    extra_info: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    """Additional information about the payment stored as JSON."""

    modified: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), server_default=func.now())
    """Timestamp of the last modification to the payment record."""

    payment_token: Mapped[str] = mapped_column(String(512), index=True, nullable=True)
    """Token provided by the payment processor, if applicable."""

    response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    """Response from the payment processor stored as JSON."""

    status: Mapped[ModelStatus] = mapped_column(
        SQLAlchemyEnum(ModelStatus),
        nullable=False,
        default=ModelStatus.CREATED,
    )
    """Current status of the payment."""

    transaction_id: Mapped[str] = mapped_column(String(512), index=True, nullable=True)
    """Unique identifier for the transaction."""

    created: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    """Timestamp of when the payment record was created."""

    def make_payment(self):
        """
        Process the payment.

        This method should be implemented to handle the actual payment processing logic.
        It will be called automatically before inserting a new payment record.
        """
        raise NotImplementedError("You must implement make_payment in your payment Class")

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, "before_insert", cls.process_payment)

    @staticmethod
    def process_payment(mapper, connection, target):
        """
        SQLAlchemy event listener that calls make_payment before inserting a new record.

        :param mapper: The Mapper object which is the target of this event
        :param connection: The Connection being used for the operation
        :param target: The mapped instance being persisted
        """
        if target.status == "CREATED":
            target.make_payment()
