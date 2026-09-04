"""Balanced-ternary primitives for TD-1.

Engineering trits are represented internally as integers: -1, 0, +1.
Strings use '-', '0', '+' for readability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

TRIT_SYMBOLS = {-1: "-", 0: "0", 1: "+"}
SYMBOL_TRITS = {v: k for k, v in TRIT_SYMBOLS.items()}


def _validate_trits(trits: Iterable[int]) -> tuple[int, ...]:
    values = tuple(int(t) for t in trits)
    if any(t not in (-1, 0, 1) for t in values):
        raise ValueError("balanced ternary trits must be -1, 0, or +1")
    return values


def trits_to_int(trits: Sequence[int]) -> int:
    """Convert most-significant-trit-first balanced ternary to an integer."""
    value = 0
    for trit in _validate_trits(trits):
        value = value * 3 + trit
    return value


def wrap_int(value: int, width: int) -> int:
    """Wrap an integer into the signed range representable by *width* trits."""
    if width <= 0:
        raise ValueError("width must be positive")
    modulus = 3**width
    half_range = (modulus - 1) // 2
    return ((int(value) + half_range) % modulus) - half_range


def int_to_trits(value: int, width: int) -> tuple[int, ...]:
    """Convert an integer to a fixed-width, MS-trit-first balanced-ternary tuple.

    Values outside the representable range wrap modulo 3**width, matching the
    intended fixed-width machine arithmetic of TD-1.
    """
    value = wrap_int(value, width)
    out: list[int] = []
    n = value
    for _ in range(width):
        n, rem = divmod(n, 3)
        if rem == 2:
            rem = -1
            n += 1
        out.append(rem)
    out.reverse()
    return tuple(out)


@dataclass(frozen=True, slots=True)
class TernaryWord:
    """Immutable fixed-width balanced-ternary word."""

    trits: tuple[int, ...]

    def __post_init__(self) -> None:
        validated = _validate_trits(self.trits)
        if not validated:
            raise ValueError("word must contain at least one trit")
        object.__setattr__(self, "trits", validated)

    @classmethod
    def zero(cls, width: int = 12) -> "TernaryWord":
        return cls((0,) * width)

    @classmethod
    def from_int(cls, value: int, width: int = 12) -> "TernaryWord":
        return cls(int_to_trits(value, width))

    @classmethod
    def parse(cls, text: str) -> "TernaryWord":
        try:
            return cls(tuple(SYMBOL_TRITS[ch] for ch in text.strip()))
        except KeyError as exc:
            raise ValueError("ternary text may contain only '-', '0', '+'") from exc

    @property
    def width(self) -> int:
        return len(self.trits)

    @property
    def value(self) -> int:
        return trits_to_int(self.trits)

    @property
    def sign(self) -> int:
        return (self.value > 0) - (self.value < 0)

    def __str__(self) -> str:
        return "".join(TRIT_SYMBOLS[t] for t in self.trits)

    def _coerce(self, other: int | "TernaryWord") -> int:
        if isinstance(other, TernaryWord):
            if other.width != self.width:
                raise ValueError("word widths must match")
            return other.value
        return int(other)

    def __add__(self, other: int | "TernaryWord") -> "TernaryWord":
        return TernaryWord.from_int(self.value + self._coerce(other), self.width)

    def __sub__(self, other: int | "TernaryWord") -> "TernaryWord":
        return TernaryWord.from_int(self.value - self._coerce(other), self.width)

    def __neg__(self) -> "TernaryWord":
        # Balanced ternary negation is a sign inversion of every trit.
        return TernaryWord(tuple(-t for t in self.trits))
