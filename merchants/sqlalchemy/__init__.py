"""SQLAlchemy integration for merchants-sdk.

This package provides :func:`pydantic_mixin_from_model` and
:class:`PydanticToSAMixinConfig` for generating SQLAlchemy 2.0 typed mixin
classes from Pydantic v2 ``BaseModel`` schemas.

Requires SQLAlchemy >= 2.0 (install via ``pip install merchants-sdk[sqlalchemy]``).

Typical usage::

    from merchants.sqlalchemy import pydantic_mixin_from_model, PydanticToSAMixinConfig
"""

from __future__ import annotations

from merchants.sqlalchemy.mixins import (
    PydanticToSAMixinConfig,
    pydantic_mixin_from_model,
)

__all__ = [
    "PydanticToSAMixinConfig",
    "pydantic_mixin_from_model",
]
