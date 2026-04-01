"""Tests for merchants.sqlalchemy.mixins – pydantic_mixin_from_model."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import Any

import pytest
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from pydantic import BaseModel, Field

from merchants.models import get_sa_metadata
from merchants.sqlalchemy import PydanticToSAMixinConfig, pydantic_mixin_from_model

# ---------------------------------------------------------------------------
# Sample Pydantic schemas
# ---------------------------------------------------------------------------


class UserSchema(BaseModel):
    email: str = Field(json_schema_extra={"sa": {"unique": True, "varchar_len": 320}})
    is_active: bool = True
    age: int | None = None


class AddressSchema(BaseModel):
    street: str
    city: str
    zip_code: str | None = None


class OrderSchema(BaseModel):
    order_ref: str
    amount: Decimal
    currency: str = "USD"
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProfileSchema(BaseModel):
    user_id: uuid.UUID
    bio: str | None = None


class NestedSchema(BaseModel):
    name: str
    address: AddressSchema


class AllTypesSchema(BaseModel):
    an_int: int
    a_str: str
    a_bool: bool
    a_float: float
    a_decimal: Decimal
    a_bytes: bytes
    a_dt: datetime.datetime
    a_date: datetime.date
    a_time: datetime.time
    a_uuid: uuid.UUID


# ---------------------------------------------------------------------------
# Tests: get_sa_metadata
# ---------------------------------------------------------------------------


class TestGetSaMetadata:
    def test_returns_empty_when_no_extra(self):
        class M(BaseModel):
            x: int

        assert get_sa_metadata(M.model_fields["x"]) == {}

    def test_returns_empty_for_non_dict_extra(self):
        class M(BaseModel):
            x: int = Field(json_schema_extra="not a dict")  # type: ignore[arg-type]

        assert get_sa_metadata(M.model_fields["x"]) == {}

    def test_namespaced_sa_key(self):
        class M(BaseModel):
            email: str = Field(
                json_schema_extra={"sa": {"unique": True, "varchar_len": 320}}
            )

        result = get_sa_metadata(M.model_fields["email"])
        assert result == {"unique": True, "varchar_len": 320}

    def test_flat_dict_fallback(self):
        class M(BaseModel):
            slug: str = Field(json_schema_extra={"unique": True, "index": True})

        result = get_sa_metadata(M.model_fields["slug"])
        assert result == {"unique": True, "index": True}

    def test_json_schema_keys_excluded_from_flat_fallback(self):
        class M(BaseModel):
            x: str = Field(
                json_schema_extra={"title": "My Title", "description": "A field"}
            )

        # Should NOT treat standard JSON-schema keys as SA metadata
        assert get_sa_metadata(M.model_fields["x"]) == {}


# ---------------------------------------------------------------------------
# Tests: happy path – basic mixin generation
# ---------------------------------------------------------------------------


class TestPydanticMixinFromModelHappyPath:
    def test_mixin_has_expected_attributes(self):
        Mixin = pydantic_mixin_from_model(UserSchema)
        assert hasattr(Mixin, "email")
        assert hasattr(Mixin, "is_active")
        assert hasattr(Mixin, "age")

    def test_mixin_name_default(self):
        Mixin = pydantic_mixin_from_model(UserSchema)
        assert Mixin.__name__ == "UserSchemaSAMixin"

    def test_mixin_name_custom(self):
        Mixin = pydantic_mixin_from_model(UserSchema, mixin_name="UserMixin")
        assert Mixin.__name__ == "UserMixin"

    def test_annotations_use_mapped(self):
        Mixin = pydantic_mixin_from_model(UserSchema)
        annotations = Mixin.__annotations__
        for key in ("email", "is_active", "age"):
            assert key in annotations
            # Mapped[...] wraps the original type
            assert hasattr(annotations[key], "__class_getitem__") or "Mapped" in str(
                annotations[key]
            )

    def test_email_unique(self):
        Mixin = pydantic_mixin_from_model(UserSchema)
        col = Mixin.email
        assert isinstance(col, sa_orm.MappedColumn)
        assert col.column.unique is True

    def test_email_varchar_320(self):
        Mixin = pydantic_mixin_from_model(UserSchema)
        col = Mixin.email
        col_type = col.column.type
        assert isinstance(col_type, sa.String)
        assert col_type.length == 320

    def test_age_nullable(self):
        Mixin = pydantic_mixin_from_model(UserSchema)
        col = Mixin.age
        assert col.column.nullable is True

    def test_email_not_nullable(self):
        Mixin = pydantic_mixin_from_model(UserSchema)
        col = Mixin.email
        # email is required (no default, not Optional) → nullable=False
        assert col.column.nullable is False

    def test_is_active_has_default(self):
        Mixin = pydantic_mixin_from_model(UserSchema)
        col = Mixin.is_active
        assert col.column.default is not None
        assert col.column.default.arg is True

    def test_auto_exclude_skips_id(self):
        class M(BaseModel):
            id: int
            name: str

        Mixin = pydantic_mixin_from_model(M)
        assert not hasattr(Mixin, "id")
        assert hasattr(Mixin, "name")


# ---------------------------------------------------------------------------
# Tests: include / exclude
# ---------------------------------------------------------------------------


class TestIncludeExclude:
    def test_exclude_removes_field(self):
        Mixin = pydantic_mixin_from_model(UserSchema, exclude={"email"})
        assert not hasattr(Mixin, "email")
        assert hasattr(Mixin, "is_active")
        assert hasattr(Mixin, "age")

    def test_include_keeps_only_specified(self):
        Mixin = pydantic_mixin_from_model(UserSchema, include={"email"})
        assert hasattr(Mixin, "email")
        assert not hasattr(Mixin, "is_active")
        assert not hasattr(Mixin, "age")

    def test_include_and_exclude_together(self):
        Mixin = pydantic_mixin_from_model(
            UserSchema, include={"email", "is_active"}, exclude={"email"}
        )
        assert not hasattr(Mixin, "email")
        assert hasattr(Mixin, "is_active")


# ---------------------------------------------------------------------------
# Tests: type mapping
# ---------------------------------------------------------------------------


class TestTypeMapping:
    def test_int_maps_to_integer(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.an_int.column.type, sa.Integer)

    def test_str_maps_to_string(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.a_str.column.type, sa.String)

    def test_bool_maps_to_boolean(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.a_bool.column.type, sa.Boolean)

    def test_float_maps_to_float(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.a_float.column.type, sa.Float)

    def test_decimal_maps_to_numeric(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.a_decimal.column.type, sa.Numeric)

    def test_bytes_maps_to_largebinary(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.a_bytes.column.type, sa.LargeBinary)

    def test_datetime_maps_to_datetime(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.a_dt.column.type, sa.DateTime)

    def test_date_maps_to_date(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.a_date.column.type, sa.Date)

    def test_time_maps_to_time(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        assert isinstance(Mixin.a_time.column.type, sa.Time)

    def test_uuid_maps_to_string36(self):
        Mixin = pydantic_mixin_from_model(AllTypesSchema)
        col_type = Mixin.a_uuid.column.type
        assert isinstance(col_type, sa.String)
        assert col_type.length == 36

    def test_list_maps_to_json(self):
        Mixin = pydantic_mixin_from_model(OrderSchema)
        assert isinstance(Mixin.tags.column.type, sa.JSON)

    def test_dict_maps_to_json(self):
        Mixin = pydantic_mixin_from_model(OrderSchema)
        assert isinstance(Mixin.metadata.column.type, sa.JSON)

    def test_nested_model_maps_to_json(self):
        Mixin = pydantic_mixin_from_model(NestedSchema)
        assert isinstance(Mixin.address.column.type, sa.JSON)

    def test_no_json_fallback_raises_for_list(self):
        config = PydanticToSAMixinConfig(json_fallback=False)
        with pytest.raises(TypeError, match="No SQLAlchemy"):
            pydantic_mixin_from_model(OrderSchema, config=config)

    def test_numeric_with_precision_scale(self):
        class M(BaseModel):
            price: Decimal = Field(json_schema_extra={"sa": {"numeric": (12, 2)}})

        Mixin = pydantic_mixin_from_model(M)
        col_type = Mixin.price.column.type
        assert isinstance(col_type, sa.Numeric)
        assert col_type.precision == 12
        assert col_type.scale == 2

    def test_explicit_type_override(self):
        class M(BaseModel):
            code: str = Field(json_schema_extra={"sa": {"type": sa.String(10)}})

        Mixin = pydantic_mixin_from_model(M)
        col_type = Mixin.code.column.type
        assert isinstance(col_type, sa.String)
        assert col_type.length == 10


# ---------------------------------------------------------------------------
# Tests: config options
# ---------------------------------------------------------------------------


class TestConfigOptions:
    def test_auto_exclude_can_be_disabled(self):
        class M(BaseModel):
            id: int
            name: str

        config = PydanticToSAMixinConfig(auto_exclude=frozenset())
        Mixin = pydantic_mixin_from_model(M, config=config)
        assert hasattr(Mixin, "id")
        assert hasattr(Mixin, "name")

    def test_default_string_len(self):
        config = PydanticToSAMixinConfig(default_string_len=255)

        class M(BaseModel):
            name: str

        Mixin = pydantic_mixin_from_model(M, config=config)
        col_type = Mixin.name.column.type
        assert isinstance(col_type, sa.String)
        assert col_type.length == 255

    def test_uuid_as_string_false(self):
        config = PydanticToSAMixinConfig(uuid_as_string=False)

        class M(BaseModel):
            uid: uuid.UUID

        Mixin = pydantic_mixin_from_model(M, config=config)
        col_type = Mixin.uid.column.type
        # Should be Uuid type (not String)
        assert isinstance(col_type, sa.Uuid)

    def test_nullable_override(self):
        class M(BaseModel):
            name: str = Field(json_schema_extra={"sa": {"nullable": True}})

        Mixin = pydantic_mixin_from_model(M)
        # name is required but we override nullable=True
        assert Mixin.name.column.nullable is True

    def test_index_flag(self):
        class M(BaseModel):
            slug: str = Field(json_schema_extra={"sa": {"index": True}})

        Mixin = pydantic_mixin_from_model(M)
        assert Mixin.slug.column.index is True

    def test_primary_key_flag(self):
        config = PydanticToSAMixinConfig(auto_exclude=frozenset())

        class M(BaseModel):
            code: str = Field(json_schema_extra={"sa": {"primary_key": True}})

        Mixin = pydantic_mixin_from_model(M, config=config)
        assert Mixin.code.column.primary_key is True


# ---------------------------------------------------------------------------
# Tests: integration – real SQLite table creation
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_real_orm_model_creates_table(self):
        """Compose a real ORM model from the mixin and create a SQLite table."""
        UserMixin = pydantic_mixin_from_model(
            UserSchema,
            mixin_name="IntegTestUserMixin",
        )

        class Base(sa_orm.DeclarativeBase): ...

        class User(Base, UserMixin):
            __tablename__ = "user"
            id: sa_orm.Mapped[int] = sa_orm.mapped_column(primary_key=True)

        engine = sa.create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = sa.inspect(engine)
        assert "user" in inspector.get_table_names()
        cols = {c["name"] for c in inspector.get_columns("user")}
        assert "id" in cols
        assert "email" in cols
        assert "is_active" in cols
        assert "age" in cols

    def test_insert_and_query(self):
        """Insert a row and query it back using the generated mixin."""
        OrderMixin = pydantic_mixin_from_model(
            OrderSchema,
            mixin_name="IntegTestOrderMixin",
        )

        class Base2(sa_orm.DeclarativeBase): ...

        class Order(Base2, OrderMixin):
            __tablename__ = "order"
            id: sa_orm.Mapped[int] = sa_orm.mapped_column(primary_key=True)

        engine = sa.create_engine("sqlite:///:memory:")
        Base2.metadata.create_all(engine)

        with sa_orm.Session(engine) as session:
            session.add(Order(order_ref="ORD-001", amount=Decimal("99.99")))
            session.commit()

        with sa_orm.Session(engine) as session:
            result = session.scalars(sa.select(Order)).one()
            assert result.order_ref == "ORD-001"
            assert result.currency == "USD"  # default applied


# ---------------------------------------------------------------------------
# Tests: str-subclass type mapping (e.g. str Enum → String)
# ---------------------------------------------------------------------------


class TestStrSubclassMapping:
    def test_str_enum_maps_to_string(self):
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class M(BaseModel):
            status: Status = Status.ACTIVE

        Mixin = pydantic_mixin_from_model(M)
        assert isinstance(Mixin.status.column.type, sa.String)

    def test_str_enum_with_varchar_len(self):
        from enum import Enum

        class Color(str, Enum):
            RED = "red"
            GREEN = "green"

        class M(BaseModel):
            color: Color = Field(
                default=Color.RED,
                json_schema_extra={"sa": {"varchar_len": 16}},
            )

        Mixin = pydantic_mixin_from_model(M)
        col_type = Mixin.color.column.type
        assert isinstance(col_type, sa.String)
        assert col_type.length == 16


# ---------------------------------------------------------------------------
# Tests: PaymentModel mixin generation
# ---------------------------------------------------------------------------


class TestPaymentModelMixin:
    def test_mixin_has_all_expected_columns(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel, mixin_name="PaymentMixin")
        for field in (
            "merchants_id",
            "transaction_id",
            "provider",
            "amount",
            "currency",
            "state",
            "email",
            "extra_args",
            "request_payload",
            "response_payload",
            "payment_object",
            "success_url",
            "cancel_url",
        ):
            assert hasattr(Mixin, field), f"Expected column '{field}' not found"

    def test_amount_is_numeric(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        col_type = Mixin.amount.column.type
        assert isinstance(col_type, sa.Numeric)
        assert col_type.precision == 19
        assert col_type.scale == 4

    def test_currency_varchar_3(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        col_type = Mixin.currency.column.type
        assert isinstance(col_type, sa.String)
        assert col_type.length == 3

    def test_state_is_string(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        col_type = Mixin.state.column.type
        assert isinstance(col_type, sa.String)
        assert col_type.length == 32

    def test_state_has_index(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        assert Mixin.state.column.index is True

    def test_merchants_id_unique_and_indexed(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        assert Mixin.merchants_id.column.unique is True
        assert Mixin.merchants_id.column.index is True

    def test_merchants_id_varchar_36(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        col_type = Mixin.merchants_id.column.type
        assert isinstance(col_type, sa.String)
        assert col_type.length == 36

    def test_transaction_id_unique_and_indexed(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        assert Mixin.transaction_id.column.unique is True
        assert Mixin.transaction_id.column.index is True

    def test_transaction_id_nullable(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        assert Mixin.transaction_id.column.nullable is True

    def test_email_has_index(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        assert Mixin.email.column.index is True

    def test_json_columns(self):
        from merchants.models import PaymentModel

        Mixin = pydantic_mixin_from_model(PaymentModel)
        for field in (
            "extra_args",
            "request_payload",
            "response_payload",
            "payment_object",
        ):
            assert isinstance(
                getattr(Mixin, field).column.type, sa.JSON
            ), f"Expected {field} to be JSON"

    def test_integration_creates_table(self):
        from merchants.models import PaymentModel

        PaymentMixin = pydantic_mixin_from_model(
            PaymentModel, mixin_name="IntegPaymentMixin"
        )

        class Base(sa_orm.DeclarativeBase): ...

        class Payment(Base, PaymentMixin):
            __tablename__ = "payments"
            id: sa_orm.Mapped[int] = sa_orm.mapped_column(primary_key=True)

        engine = sa.create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = sa.inspect(engine)
        assert "payments" in inspector.get_table_names()
        cols = {c["name"] for c in inspector.get_columns("payments")}
        expected = {
            "id",
            "merchants_id",
            "transaction_id",
            "provider",
            "amount",
            "currency",
            "state",
            "email",
            "extra_args",
            "request_payload",
            "response_payload",
            "payment_object",
            "success_url",
            "cancel_url",
        }
        assert expected.issubset(cols)
