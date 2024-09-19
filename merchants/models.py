import datetime
import enum
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, Numeric, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy_utils import generic_repr

from merchants.config import settings
from merchants.database import DatabaseModel

# SQLAlchemy Models


@generic_repr
class User(DatabaseModel):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)
    email: Mapped[EmailStr] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = True
    is_superuser: Mapped[bool] = False
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=True)


@generic_repr
class Integration(DatabaseModel):
    __tablename__ = "integration"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = True
    integration_class: Mapped[str] = mapped_column(String(255), nullable=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    payments: Mapped["Payment"] = relationship("Payment", back_populates="integration")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modified_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )


class PaymentStatus(enum.Enum):
    created = "created"
    processing = "processing"
    declined = "declined"
    cancelled = "cancelled"
    refunded = "refunded"
    paid = "paid"


@generic_repr
class Payment(DatabaseModel):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    customer_email: Mapped[EmailStr] = mapped_column(String(255), nullable=False)
    integration_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    integration_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.created)
    integration_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    integration_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    integration_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("integration.id"))
    integration: Mapped[Integration | None] = relationship("Integration", back_populates="payments")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modified_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    @classmethod
    def __declare_last__(cls):
        """
        From Claude: to add the before_insert event directly on the Main model

        """
        if settings.PROCESS_ON_SAVE:
            event.listen(cls, "before_insert", cls.event_before_insert)

    @staticmethod
    def event_before_insert(mapper, connection, target):
        """
        SQLAlchemy event listener that calls process_payment before inserting a new record.

        :param mapper: The Mapper object which is the target of this event
        :param connection: The Connection being used for the operation
        :param target: The mapped instance being persisted
        """
        print(f"{target=}")
        return target


# Pydantic Models
# Generic message
class Message(BaseModel):
    message: str


# JSON payload containing access token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseModel):
    sub: str | None = None


class UserPublic(BaseModel):
    id: int


class UsersPublic(BaseModel):
    data: list[UserPublic]
    count: int


class IntegrationPublic(BaseModel):
    slug: str


class IntegrationsPublic(BaseModel):
    count: int
    data: list[IntegrationPublic]


class PaymentPublic(BaseModel):
    transaction: str


class PaymentsPublic(BaseModel):
    count: int
    data: list[PaymentPublic]
