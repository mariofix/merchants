"""Result types: Success[T] and Failure[E]."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Success(Generic[T]):
    """Represents a successful outcome carrying a value."""

    value: T
    ok: bool = True

    def unwrap(self) -> T:
        return self.value


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Represents a failed outcome carrying an error."""

    error: E
    ok: bool = False

    def unwrap(self) -> T:  # type: ignore[type-var]
        raise ValueError(f"Called unwrap() on a Failure: {self.error!r}")


# Convenient union alias
Result = Success[T] | Failure[E]
