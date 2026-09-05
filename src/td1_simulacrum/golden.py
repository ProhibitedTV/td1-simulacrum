"""First-hardware fixed parity vector suites.

These suites exist independently from trace-derived workload campaigns. The first
physical TD-1 target is expected to prove one ternary state cell before broader
register or ALU capability is advertised.
"""

from __future__ import annotations

from .parity import ParityOperation, ParityVector, golden_register_vectors


def golden_trit_vectors() -> tuple[ParityVector, ...]:
    """Return exactly the three deterministic one-trit hold vectors."""
    return (
        ParityVector.create("TRIT-NEG", ParityOperation.TRIT_HOLD, 1, ("-",)),
        ParityVector.create("TRIT-ZERO", ParityOperation.TRIT_HOLD, 1, ("0",)),
        ParityVector.create("TRIT-POS", ParityOperation.TRIT_HOLD, 1, ("+",)),
    )


def golden_register_suite(width: int = 12) -> tuple[ParityVector, ...]:
    """Return the backward-compatible register suite with an explicit trit prefix.

    The legacy `golden_register_vectors()` remains the stable reference set. This
    first-hardware selector rebuilds its trit prefix from `golden_trit_vectors()`
    so the one-trit campaign has a single explicit source while preserving exact
    vector identity and ordering for existing callers.
    """
    legacy = golden_register_vectors(width)
    register_vectors = tuple(
        vector for vector in legacy if vector.operation is ParityOperation.REGISTER_LOAD
    )
    suite = golden_trit_vectors() + register_vectors
    if suite != legacy:
        raise RuntimeError("first-hardware register suite drifted from legacy golden vectors")
    return suite


def golden_suite(name: str, *, width: int = 12) -> tuple[ParityVector, ...]:
    """Select one explicit fixed-vector suite for bench execution."""
    normalized = name.strip().lower()
    if normalized == "trit":
        return golden_trit_vectors()
    if normalized == "register":
        return golden_register_suite(width)
    raise ValueError(f"unsupported golden suite {name!r}")
