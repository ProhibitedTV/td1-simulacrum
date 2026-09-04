"""Native semantic primitives for TD-1 State Weaves.

This is a deliberately conservative first intermediate representation. It
defines identity, ordering, modifier state, validation, and serialization
without pretending the final geometric grammar is already known.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class SemanticRoot(str, Enum):
    OBSERVER = "OBSERVER"
    ORIGIN = "ORIGIN"
    TIME = "TIME"
    REFERENCE = "REFERENCE"
    MOTION = "MOTION"
    MEMORY = "MEMORY"
    LINK = "LINK"
    STATE = "STATE"
    FRAME = "FRAME"
    AXIS = "AXIS"
    SIGNAL = "SIGNAL"
    COGNITION = "COGNITION"
    EXECUTION = "EXECUTION"
    TRANSFORM = "TRANSFORM"
    ISOLATION = "ISOLATION"
    DOMAIN = "DOMAIN"


class Modifier(IntEnum):
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1

    @property
    def symbol(self) -> str:
        return {-1: "-", 0: "0", 1: "+"}[int(self)]


@dataclass(frozen=True, slots=True)
class SemanticIR:
    """Versioned, renderer-independent semantic representation."""

    roots: tuple[str, ...]
    modifier: int
    version: int = 1

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "roots": list(self.roots),
            "modifier": self.modifier,
        }


@dataclass(frozen=True, slots=True)
class StateWeave:
    """Ordered composition of semantic roots under one ternary modifier."""

    roots: tuple[SemanticRoot, ...]
    modifier: Modifier = Modifier.NEUTRAL

    def __post_init__(self) -> None:
        if not self.roots:
            raise ValueError("a State Weave requires at least one semantic root")
        if len(self.roots) > 4:
            raise ValueError("State Weave v1 supports at most four roots")
        if len(set(self.roots)) != len(self.roots):
            raise ValueError("State Weave v1 does not permit duplicate roots")

    @property
    def canonical(self) -> str:
        chain = ">".join(root.value for root in self.roots)
        return f"{chain}:{self.modifier.symbol}"

    def lower(self) -> SemanticIR:
        return SemanticIR(
            roots=tuple(root.value for root in self.roots),
            modifier=int(self.modifier),
        )

    @classmethod
    def parse(cls, text: str) -> "StateWeave":
        """Parse canonical form such as ``TIME>REFERENCE:+``."""
        try:
            root_text, modifier_text = text.strip().rsplit(":", 1)
        except ValueError as exc:
            raise ValueError("State Weave must contain a ':' modifier separator") from exc

        roots: list[SemanticRoot] = []
        for item in root_text.split(">"):
            token = item.strip().upper()
            if not token:
                raise ValueError("empty semantic root in State Weave")
            try:
                roots.append(SemanticRoot(token))
            except ValueError as exc:
                raise ValueError(f"unknown semantic root {token!r}") from exc

        modifiers = {"-": Modifier.NEGATIVE, "0": Modifier.NEUTRAL, "+": Modifier.POSITIVE}
        try:
            modifier = modifiers[modifier_text.strip()]
        except KeyError as exc:
            raise ValueError("State Weave modifier must be '-', '0', or '+'") from exc

        return cls(tuple(roots), modifier)
