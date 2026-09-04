import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from td1_simulacrum import (
    Machine,
    Modifier,
    ObserverState,
    RenderMode,
    RenderPlane,
    RenderState,
    SemanticRoot,
    StateWeave,
    TernaryWord,
    project_render_state,
)


FIXTURE = Path(__file__).parent / "fixtures" / "render_state_v1.json"


def _golden_machine() -> Machine:
    machine = Machine()
    machine.registers[0] = TernaryWord.from_int(5)
    machine.registers[1] = TernaryWord.from_int(-2)
    machine.registers[8] = TernaryWord.from_int(42)
    machine.memory[10] = TernaryWord.from_int(7)
    machine.memory[728] = TernaryWord.from_int(-9)
    machine.ip = 4
    machine.cond = -1
    machine.steps = 11
    return machine


def test_render_state_v1_golden_fixture() -> None:
    state = RenderState.capture(_golden_machine())
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert state.as_dict() == expected
    assert state.digest() == "58658e84e7ed421279052a37c577811da263564ab665030b7a42aa16ec955675"
    assert state.machine_digest == (
        "c6c733c271c1eae871cc65bbed19d3207c6ce108e2d5bba337ac2e6bb5c9f5cd"
    )


def test_render_state_serialization_and_machine_restore_round_trip() -> None:
    state = RenderState.capture(_golden_machine())
    restored_state = RenderState.from_json(state.canonical_json())
    restored_machine = restored_state.restore_machine()

    assert restored_state == state
    assert restored_state.canonical_json() == state.canonical_json()
    assert restored_machine.state_digest() == state.machine_digest


def test_engineering_and_relic_modes_share_one_source_state() -> None:
    observer = ObserverState(
        datetime(2026, 9, 4, 16, 0, tzinfo=UTC),
        latitude_deg=40.4233,
        longitude_deg=-104.7091,
        altitude_m=1420.0,
    )
    weave = StateWeave(
        (SemanticRoot.TIME, SemanticRoot.REFERENCE),
        Modifier.POSITIVE,
    )
    state = RenderState.capture(_golden_machine(), observer=observer, weave=weave)

    engineering = project_render_state(state, RenderMode.ENGINEERING)
    relic = project_render_state(state, RenderMode.RELIC)

    assert engineering["source_digest"] == relic["source_digest"] == state.digest()
    assert state.active_planes == (
        RenderPlane.CARRIER,
        RenderPlane.MACHINE,
        RenderPlane.SEMANTIC,
        RenderPlane.OBSERVER,
    )
    assert engineering["semantic"]["weave"] == "TIME>REFERENCE:+"  # type: ignore[index]
    assert relic["semantic"]["roots"] == [2, 3]  # type: ignore[index]
    assert relic["semantic"]["modifier"] == 1  # type: ignore[index]

    # Relic projection carries semantic IDs instead of human semantic names.
    relic_json = json.dumps(relic, sort_keys=True)
    assert "TIME" not in relic_json
    assert "REFERENCE" not in relic_json


def test_relic_register_glyphs_preserve_machine_words() -> None:
    state = RenderState.capture(_golden_machine())
    relic = project_render_state(state, "relic")

    registers = relic["machine"]["registers"]  # type: ignore[index]
    assert registers[0]["glyphs"] == [13, 13, 13, 18]
    assert registers[1]["glyphs"] == [13, 13, 13, 11]
    assert registers[8]["glyphs"] == [13, 13, 15, 1]


def test_corrupt_redundant_glyph_data_is_rejected() -> None:
    payload = RenderState.capture(_golden_machine()).as_dict()
    payload["registers"][0]["glyph_ids"][3] = 0  # type: ignore[index]

    with pytest.raises(ValueError, match="inconsistent register render state"):
        RenderState.from_dict(payload)


def test_unknown_render_mode_is_rejected() -> None:
    state = RenderState.capture(_golden_machine())

    with pytest.raises(ValueError):
        project_render_state(state, "dream-sequence")
