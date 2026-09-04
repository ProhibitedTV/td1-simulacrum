"""Deterministic microglyph identifiers derived from balanced-ternary state.

The renderer is intentionally not defined here. This module establishes the
reversible data mapping that any future glyph geometry must preserve.
"""

from __future__ import annotations

from collections.abc import Iterable

from .ternary import TernaryWord, int_to_trits, trits_to_int

TRIAD_WIDTH = 3
GLYPH_STATES = 27
GLYPH_OFFSET = 13


def triad_to_glyph_id(triad: Iterable[int]) -> int:
    """Map one 3-trit state to a stable glyph identifier in ``0..26``."""
    values = tuple(int(t) for t in triad)
    if len(values) != TRIAD_WIDTH:
        raise ValueError("microglyph triads must contain exactly 3 trits")
    return trits_to_int(values) + GLYPH_OFFSET


def glyph_id_to_triad(glyph_id: int) -> tuple[int, int, int]:
    """Invert ``triad_to_glyph_id``."""
    if not 0 <= glyph_id < GLYPH_STATES:
        raise ValueError("glyph_id must be in range 0..26")
    values = int_to_trits(glyph_id - GLYPH_OFFSET, TRIAD_WIDTH)
    return values[0], values[1], values[2]


def word_to_glyph_ids(word: TernaryWord) -> tuple[int, ...]:
    """Partition a word into 3-trit cells and return stable microglyph IDs."""
    if word.width % TRIAD_WIDTH:
        raise ValueError("word width must be divisible by 3")
    return tuple(
        triad_to_glyph_id(word.trits[index : index + TRIAD_WIDTH])
        for index in range(0, word.width, TRIAD_WIDTH)
    )


def glyph_ids_to_word(glyph_ids: Iterable[int]) -> TernaryWord:
    """Reconstruct a ternary word from its stable microglyph identifiers."""
    ids = tuple(int(glyph_id) for glyph_id in glyph_ids)
    if not ids:
        raise ValueError("at least one glyph ID is required")
    trits: list[int] = []
    for glyph_id in ids:
        trits.extend(glyph_id_to_triad(glyph_id))
    return TernaryWord(tuple(trits))
