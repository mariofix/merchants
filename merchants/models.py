"""Pydantic models for the merchants SDK."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo


class PaymentState(str, Enum):
    """Normalised payment lifecycle states."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    UNKNOWN = "unknown"


class CheckoutSession(BaseModel):
    """A hosted-checkout session returned by a provider."""

    session_id: str
    redirect_url: str
    provider: str
    amount: Decimal
    currency: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
    initial_state: PaymentState = PaymentState.PENDING


class PaymentStatus(BaseModel):
    """Normalised status of a payment retrieved from a provider."""

    payment_id: str
    state: PaymentState
    provider: str
    amount: Decimal | None = None
    currency: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_final(self) -> bool:
        """Return True when no further state transitions are expected."""
        return self.state in (
            PaymentState.SUCCEEDED,
            PaymentState.FAILED,
            PaymentState.CANCELLED,
            PaymentState.REFUNDED,
        )

    @property
    def is_success(self) -> bool:
        """Return True only when the payment definitively succeeded."""
        return self.state is PaymentState.SUCCEEDED


class WebhookEvent(BaseModel):
    """Parsed, normalised webhook event from a provider."""

    event_id: str | None = None
    event_type: str
    payment_id: str | None = None
    state: PaymentState = PaymentState.UNKNOWN
    provider: str = "unknown"
    raw: dict[str, Any] = Field(default_factory=dict)


class PaymentModel(BaseModel):
    """Pydantic model representing a stored payment record.

    This model mirrors the column layout used by *flask-merchants* and
    *fastapi-merchants* so that those packages can derive their
    ``PaymentMixin`` from it via
    :func:`merchants.sqlalchemy.pydantic_mixin_from_model` without
    duplicating field definitions::

        from merchants.models import PaymentModel
        from merchants.sqlalchemy import pydantic_mixin_from_model

        PaymentMixin = pydantic_mixin_from_model(PaymentModel, mixin_name="PaymentMixin")

    ``id``, ``created_at``, and ``updated_at`` are intentionally absent
    because they appear in the default ``auto_exclude`` set of
    :class:`~merchants.sqlalchemy.PydanticToSAMixinConfig` and are expected
    to be defined directly on the ORM model or mixin by the downstream
    package.
    """

    merchants_id: str = Field(
        description="Internal payment identifier (UUID4) assigned by the application.",
        json_schema_extra={"sa": {"unique": True, "index": True, "varchar_len": 36}},
    )
    transaction_id: str | None = Field(
        default=None,
        description="Provider-assigned session or payment identifier.",
        json_schema_extra={"sa": {"unique": True, "index": True, "varchar_len": 255}},
    )
    provider: str = Field(
        description='Payment provider key (e.g. "stripe", "khipu").',
        json_schema_extra={"sa": {"index": True, "varchar_len": 64}},
    )
    amount: Decimal = Field(
        description="Payment amount.",
        json_schema_extra={"sa": {"numeric": (19, 4)}},
    )
    currency: str = Field(
        description='ISO 4217 currency code (e.g. "USD").',
        json_schema_extra={"sa": {"varchar_len": 3}},
    )
    state: PaymentState = Field(
        default=PaymentState.PENDING,
        description="Current payment lifecycle state.",
        json_schema_extra={"sa": {"varchar_len": 32, "index": True}},
    )
    email: str | None = Field(
        default=None,
        description="Customer e-mail address.",
        json_schema_extra={"sa": {"index": True, "varchar_len": 255}},
    )
    extra_args: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific keyword arguments passed at checkout creation.",
    )
    request_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Full request payload sent to the payment provider.",
    )
    response_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw response payload returned by the payment provider.",
    )
    payment_object: dict[str, Any] = Field(
        default_factory=dict,
        description="Parsed payment object received from the provider.",
    )
    success_url: str | None = Field(
        default=None,
        description="URL the user is redirected to after a successful payment.",
        json_schema_extra={"sa": {"varchar_len": 2048}},
    )
    cancel_url: str | None = Field(
        default=None,
        description="URL the user is redirected to when cancelling.",
        json_schema_extra={"sa": {"varchar_len": 2048}},
    )


# Keys that are part of the standard JSON Schema vocabulary and must NOT be
# mistakenly treated as SQLAlchemy column metadata.
_JSON_SCHEMA_KEYS: frozenset[str] = frozenset(
    {"title", "description", "examples", "default", "deprecated"}
)


def get_sa_metadata(field: FieldInfo) -> dict[str, Any]:
    """Extract SQLAlchemy column metadata from a Pydantic ``FieldInfo``.

    Downstream packages (e.g. *flask-merchants*, *fastapi-merchants*) use this
    helper when generating SQLAlchemy mixin classes from Pydantic models.  The
    metadata is stored under the ``"sa"`` key of ``json_schema_extra``, but a
    flat dict is also accepted for brevity:

    .. code-block:: python

        # Preferred – namespaced:
        email: str = Field(json_schema_extra={"sa": {"unique": True, "varchar_len": 320}})

        # Also accepted – flat dict on json_schema_extra:
        email: str = Field(json_schema_extra={"unique": True, "varchar_len": 320})

    Supported keys inside the ``"sa"`` dict:

    +----------------+-------+-----------------------------------------------+
    | Key            | Type  | Meaning                                       |
    +================+=======+===============================================+
    | ``primary_key``| bool  | Mark as primary key column                    |
    +----------------+-------+-----------------------------------------------+
    | ``nullable``   | bool  | Explicit nullability override                 |
    +----------------+-------+-----------------------------------------------+
    | ``unique``     | bool  | Add a unique constraint                       |
    +----------------+-------+-----------------------------------------------+
    | ``index``      | bool  | Create a database index                       |
    +----------------+-------+-----------------------------------------------+
    | ``varchar_len``| int   | Length for ``String`` columns                 |
    +----------------+-------+-----------------------------------------------+
    | ``numeric``    | tuple | ``(precision, scale)`` for ``Numeric`` columns|
    +----------------+-------+-----------------------------------------------+
    | ``type``       | SA    | Explicit SQLAlchemy type instance (downstream)|
    +----------------+-------+-----------------------------------------------+

    .. note::
        The ``"type"`` key requires a SQLAlchemy type object and is therefore
        only meaningful in downstream packages that have SQLAlchemy installed.
        Do **not** import SQLAlchemy types inside *merchants-sdk*.

    Args:
        field: A Pydantic :class:`~pydantic.fields.FieldInfo` instance, as
            found in ``MyModel.model_fields.values()``.

    Returns:
        A plain :class:`dict` with the extracted SQLAlchemy metadata.
        Returns an empty dict when no metadata is present.
    """
    extra = field.json_schema_extra
    if not extra or not isinstance(extra, dict):
        return {}
    # Preferred: {"sa": {...}}
    if "sa" in extra and isinstance(extra["sa"], dict):
        return dict(extra["sa"])
    # Fallback: treat the whole dict as SA metadata (only if it looks like it)
    # We use a simple heuristic: none of the keys are standard json-schema keys.
    if not _JSON_SCHEMA_KEYS.intersection(extra.keys()):
        return dict(extra)
    return {}
