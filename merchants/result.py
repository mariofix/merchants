"""Success/Failure result types."""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


class Success(Generic[T]):
    """Represents a successful operation result."""

    ok: bool = True

    def __init__(self, value: T) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Success({self.value!r})"


class Failure(Generic[E]):
    """Represents a failed operation result (parse/validation failure, not transport)."""

    ok: bool = False

    def __init__(self, error: E) -> None:
        self.error = error

    def __repr__(self) -> str:
        return f"Failure({self.error!r})"


# Union type alias for annotating return types
Result = Success[T] | Failure[E]
