"""SQLAlchemy mixin generator from Pydantic v2 models.

This module provides :func:`pydantic_mixin_from_model`, which generates a
**SQLAlchemy 2.0 typed mixin class** at runtime from a **Pydantic v2
``BaseModel``**.

Typical usage (in a Flask or FastAPI app that has SQLAlchemy installed)::

    from merchants.sqlalchemy import pydantic_mixin_from_model
    from myapp.schemas import UserSchema
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    UserMixin = pydantic_mixin_from_model(UserSchema)

    class Base(DeclarativeBase): ...

    class User(Base, UserMixin):
        __tablename__ = "user"
        id: Mapped[int] = mapped_column(primary_key=True)

.. note::
    This module requires **SQLAlchemy >= 2.0** to be installed.
    Install the optional extra::

        pip install merchants-sdk[sqlalchemy]
"""

from __future__ import annotations

import dataclasses
import datetime
import inspect
import types
import typing
import uuid
from decimal import Decimal
from typing import Any, Union, get_args, get_origin

import pydantic
import pydantic.fields

try:
    import sqlalchemy as sa
    import sqlalchemy.orm as sa_orm
except ImportError as exc:
    raise ImportError(
        "SQLAlchemy >= 2.0 is required for merchants.sqlalchemy. "
        "Install it with: pip install merchants-sdk[sqlalchemy]"
    ) from exc

from merchants.models import get_sa_metadata

# ---------------------------------------------------------------------------
# Module-level lookup table: simple 1-to-1 Python type → SA type class
# (callable with no arguments to produce a fresh type instance)
# ---------------------------------------------------------------------------
_PRIMITIVE_TYPE_MAP: dict[type, Any] = {
    int: sa.Integer,
    bool: sa.Boolean,
    float: sa.Float,
    Decimal: sa.Numeric,
    bytes: sa.LargeBinary,
    datetime.datetime: sa.DateTime,
    datetime.date: sa.Date,
    datetime.time: sa.Time,
}

# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class PydanticToSAMixinConfig:
    """Configuration for :func:`pydantic_mixin_from_model`.

    Attributes:
        json_fallback: When ``True`` (default), unknown Python types are mapped
            to ``JSON()``. When ``False``, an unsupported type raises
            :exc:`TypeError`.
        uuid_as_string: When ``True`` (default), ``uuid.UUID`` fields are
            stored as ``String(36)`` for broad database portability.
        default_string_len: Optional default length for ``String`` columns.
            When ``None`` (default), ``String()`` is used without a length.
        auto_exclude: Set of field names to skip automatically.  Defaults to
            ``{"id", "created_at", "updated_at"}`` so that ORM models can
            define those columns themselves.
    """

    json_fallback: bool = True
    uuid_as_string: bool = True
    default_string_len: int | None = None
    auto_exclude: frozenset[str] = dataclasses.field(
        default_factory=lambda: frozenset({"id", "created_at", "updated_at"})
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG = PydanticToSAMixinConfig()


def _unwrap_optional(py_type: Any) -> tuple[Any, bool]:
    """Return ``(inner_type, is_optional)`` for a Python annotation.

    ``Optional[T]`` and ``T | None`` are both detected as optional.
    """
    origin = get_origin(py_type)
    if origin is Union or origin is types.UnionType:
        args = [a for a in get_args(py_type) if a is not type(None)]
        if len(args) == 1:
            return args[0], True
        # Union[A, B] – not simply optional; return as-is
        return py_type, False
    return py_type, False


def _is_subclass_safe(py_type: Any, base: type) -> bool:
    """Return ``True`` if ``py_type`` is a subclass of ``base``, safely."""
    try:
        return isinstance(py_type, type) and issubclass(py_type, base)
    except TypeError:
        return False


def _json_or_raise(py_type: Any, label: str, json_fallback: bool) -> sa.JSON:
    """Return ``JSON()`` when *json_fallback* is enabled, otherwise raise.

    Args:
        py_type: The Python type that has no direct SA mapping.
        label: Human-readable category name used in the error message.
        json_fallback: Whether to silently fall back to ``JSON()``.

    Raises:
        TypeError: When *json_fallback* is ``False``.
    """
    if json_fallback:
        return sa.JSON()
    raise TypeError(
        f"No SQLAlchemy mapping for {label} {py_type!r}. "
        "Set json_fallback=True in PydanticToSAMixinConfig to use JSON()."
    )


def _sa_type_for(
    py_type: Any,
    sa_hints: dict[str, Any],
    config: PydanticToSAMixinConfig,
) -> Any:
    """Return a SQLAlchemy column type for *py_type*.

    Args:
        py_type: The Python type annotation (already unwrapped from Optional).
        sa_hints: SQLAlchemy metadata dict extracted from the field.
        config: Generator configuration.

    Returns:
        A SQLAlchemy type instance.

    Raises:
        TypeError: When the type is unsupported and ``config.json_fallback``
            is ``False``.
    """
    # Explicit type override from field metadata
    if "type" in sa_hints:
        return sa_hints["type"]

    # Numeric with precision/scale
    if "numeric" in sa_hints:
        precision, scale = sa_hints["numeric"]
        return sa.Numeric(precision, scale)

    # Simple 1:1 primitive mapping (replaces ~8 individual if-branches)
    if py_type in _PRIMITIVE_TYPE_MAP:
        return _PRIMITIVE_TYPE_MAP[py_type]()

    # str: may carry an explicit length from sa_hints or config
    if py_type is str:
        length = sa_hints.get("varchar_len") or config.default_string_len
        return sa.String(length)  # sa.String(None) == sa.String()

    # UUID: portability choice between String(36) and native Uuid
    if py_type is uuid.UUID:
        return sa.String(36) if config.uuid_as_string else sa.Uuid()

    # Generic container types (list[x], dict[k, v]) → JSON
    if get_origin(py_type) in (list, dict):
        return _json_or_raise(py_type, "container type", config.json_fallback)

    # Nested Pydantic models → JSON
    if _is_subclass_safe(py_type, pydantic.BaseModel):
        return _json_or_raise(py_type, "nested Pydantic model", config.json_fallback)

    # Final catch-all
    return _json_or_raise(py_type, "Python type", config.json_fallback)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def pydantic_mixin_from_model(
    pyd_model: type[pydantic.BaseModel],
    *,
    mixin_name: str | None = None,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
    config: PydanticToSAMixinConfig | None = None,
) -> type:
    """Generate a SQLAlchemy 2.0 typed mixin class from a Pydantic v2 model.

    The returned class is a plain Python class (no declarative base) that
    defines :class:`~sqlalchemy.orm.Mapped` annotations and
    :func:`~sqlalchemy.orm.mapped_column` values for each selected field.
    Downstream ORM models can inherit from it alongside a declarative
    ``Base``.

    Example::

        from merchants.sqlalchemy import pydantic_mixin_from_model
        from myapp.schemas import UserSchema

        UserMixin = pydantic_mixin_from_model(
            UserSchema,
            exclude={"password_hash"},
        )

        class User(Base, UserMixin):
            __tablename__ = "user"
            id: Mapped[int] = mapped_column(primary_key=True)

    Args:
        pyd_model: A Pydantic v2 ``BaseModel`` subclass.
        mixin_name: Name for the generated class.  Defaults to
            ``"<ModelName>SAMixin"``.
        include: If given, only generate columns for these field names (after
            applying ``auto_exclude``).
        exclude: If given, skip these field names (takes precedence over
            ``include``).
        config: Optional :class:`PydanticToSAMixinConfig` instance.  Uses
            sensible defaults when omitted.

    Returns:
        A dynamically generated mixin class.

    Raises:
        TypeError: When a field's type has no SQLAlchemy mapping and
            ``config.json_fallback`` is ``False``.
    """
    if config is None:
        config = _DEFAULT_CONFIG

    name = mixin_name or f"{pyd_model.__name__}SAMixin"

    # Resolve type hints once (handles forward refs)
    try:
        hints = typing.get_type_hints(pyd_model)
    except Exception:
        hints = {k: v.annotation for k, v in pyd_model.model_fields.items()}

    # Determine which fields to include
    all_field_names = list(pyd_model.model_fields.keys())
    selected = [f for f in all_field_names if f not in config.auto_exclude]
    if include is not None:
        selected = [f for f in selected if f in include]
    if exclude is not None:
        selected = [f for f in selected if f not in exclude]

    namespace: dict[str, Any] = {"__annotations__": {}}

    for field_name in selected:
        field_info: pydantic.fields.FieldInfo = pyd_model.model_fields[field_name]
        raw_type = hints.get(field_name, field_info.annotation)

        # Determine optionality
        inner_type, is_optional = _unwrap_optional(raw_type)

        # SA metadata from json_schema_extra
        sa_hints = get_sa_metadata(field_info)

        # Determine nullability
        if "nullable" in sa_hints:
            nullable = bool(sa_hints["nullable"])
        else:
            is_required = field_info.is_required()
            nullable = is_optional or not is_required

        # Determine SA column type
        col_type = _sa_type_for(inner_type, sa_hints, config)

        # Build mapped_column kwargs
        col_kwargs: dict[str, Any] = {"nullable": nullable}
        if sa_hints.get("primary_key"):
            col_kwargs["primary_key"] = True
        if sa_hints.get("unique"):
            col_kwargs["unique"] = True
        if sa_hints.get("index"):
            col_kwargs["index"] = True

        # Default value (only when field is not required)
        if not field_info.is_required():
            default = field_info.default
            if default is not pydantic.fields.PydanticUndefined and default is not inspect.Parameter.empty:
                col_kwargs["default"] = default
            elif field_info.default_factory is not None:
                col_kwargs["default"] = field_info.default_factory

        # Annotate with Mapped[raw_type]
        namespace["__annotations__"][field_name] = sa_orm.Mapped[raw_type]  # type: ignore[valid-type]
        namespace[field_name] = sa_orm.mapped_column(col_type, **col_kwargs)

    return type(name, (), namespace)
