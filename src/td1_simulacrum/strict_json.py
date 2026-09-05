"""Strict validation helpers for versioned canonical TD-1 JSON artifacts.

Human-facing parsers may intentionally coerce text. Persisted canonical artifacts
must not: loading a saved artifact is an integrity boundary, so JSON value types
and redundant serialized fields must survive parsing unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping


class CanonicalArtifactError(ValueError):
    """Raised when canonical artifact JSON relies on coercion or normalization."""


def json_exact(actual: object, expected: object) -> bool:
    """Compare JSON-compatible values with exact scalar types and container shape."""
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        if not isinstance(expected, dict) or actual.keys() != expected.keys():
            return False
        return all(json_exact(actual[key], expected[key]) for key in actual)
    if isinstance(actual, list):
        if not isinstance(expected, list) or len(actual) != len(expected):
            return False
        return all(
            json_exact(left, right)
            for left, right in zip(actual, expected, strict=True)
        )
    return actual == expected


def require_canonical_mapping(
    raw: Mapping[str, object],
    canonical: Mapping[str, object],
    *,
    label: str,
) -> None:
    """Require a parsed artifact to reproduce the exact received JSON object.

    This catches numeric strings accepted by ``int()``, stringified booleans,
    Python's ``True == 1`` behavior, omitted/defaulted fields, ignored redundant
    fields, reordered/deduplicated lists, and unknown extra fields.
    """
    if not json_exact(dict(raw), dict(canonical)):
        raise CanonicalArtifactError(
            f"{label} must use canonical JSON values, fields, and value types"
        )
