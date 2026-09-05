"""First-hardware fixed parity vector suites.

These suites exist independently from trace-derived workload campaigns. The first
physical TD-1 target is expected to prove one ternary state cell before broader
register or ALU capability is advertised.
"""

from __future__ import annotations

from .parity import ParityVector, golden_register_vectors, golden_trit_vectors


def golden_suite(name: str, *, width: int = 12) -> tuple[ParityVector, ...]:
    """Select one explicit fixed-vector suite for bench execution."""
    normalized = name.strip().lower()
    if normalized == "trit":
        return golden_trit_vectors()
    if normalized == "register":
        return golden_register_vectors(width)
    raise ValueError(f"unsupported golden suite {name!r}")
