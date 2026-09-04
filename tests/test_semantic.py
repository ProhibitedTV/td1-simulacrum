import pytest

from td1_simulacrum import Modifier, SemanticRoot, StateWeave


def test_state_weave_parse_canonical_and_lowering() -> None:
    weave = StateWeave.parse("time>reference:+")
    assert weave.roots == (SemanticRoot.TIME, SemanticRoot.REFERENCE)
    assert weave.modifier is Modifier.POSITIVE
    assert weave.canonical == "TIME>REFERENCE:+"
    assert weave.lower().as_dict() == {
        "version": 1,
        "roots": ["TIME", "REFERENCE"],
        "modifier": 1,
    }


def test_state_weave_v1_rejects_duplicates_and_unknown_roots() -> None:
    with pytest.raises(ValueError):
        StateWeave((SemanticRoot.TIME, SemanticRoot.TIME))
    with pytest.raises(ValueError):
        StateWeave.parse("TIME>NOPE:+")
