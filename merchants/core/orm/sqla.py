from typing import Any, Literal
from sqlalchemy import String, JSON
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import column_property

PaymentStatus = Literal["Created", "Paid", "Rejected", "Refunded"]

# class PaymentMixin(DeclarativeBase):
#     __abstract__ = True

#     provider: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
#     provider_transaction_id: Mapped[str] = mapped_column(String(512), index=True, nullable=True, default=None)

#     payment_status: Mapped[PaymentStatus] = mapped_column(PaymentStatus, default="Created")
#     payment_payload: Mapped[JSON] = mapped_column(JSON, nullable=True, default=None)

#     @declared_attr
#     def create(cls) -> Any:
#         # return relationship("Table")
#         return {"provider": "actions"}
