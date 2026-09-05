import json
import sys

import pytest

from td1_simulacrum.hardware_characterization import (
    BenchNodeRole,
    BenchNodeVoltage,
    HardwareCharacterizationError,
    InstrumentRef,
    SwitchingDirection,
    SwitchingObservation,
    TritBenchObservation,
    TritCellCharacterization,
    TritStimulus,
)
from td1_simulacrum.hardware_cli import main as hardware_main
from td1_simulacrum.strict_json import CanonicalArtifactError


def _characterization() -> TritCellCharacterization:
    return TritCellCharacterization(
        board_revision="BENCH-CELL-A",
        unit_id="UNIT-001",
        bench_id="BENCH-GREELEY-01",
        instruments=(
            InstrumentRef("dmm", "DMM-A"),
            InstrumentRef("scope", "SCOPE-A"),
        ),
        node_voltages=(
            BenchNodeVoltage("rail_negative", BenchNodeRole.SUPPLY, -1_800_000),
            BenchNodeVoltage("rail_positive", BenchNodeRole.SUPPLY, 1_800_000),
            BenchNodeVoltage("reference_center", BenchNodeRole.REFERENCE, 12_000),
        ),
        observations=(
            TritBenchObservation(
                0,
                TritStimulus.NEGATIVE,
                -740_000,
                "scope_1M",
                load_ohms=1_000_000,
                settle_us=18,
                comparator_code="N",
                temperature_millic=22_500,
            ),
            TritBenchObservation(
                1,
                TritStimulus.ZERO,
                8_000,
                "scope_1M",
                load_ohms=1_000_000,
                settle_us=14,
                comparator_code="Z",
                temperature_millic=22_500,
            ),
            TritBenchObservation(
                2,
                TritStimulus.POSITIVE,
                755_000,
                "scope_1M",
                load_ohms=1_000_000,
                settle_us=19,
                comparator_code="P",
                temperature_millic=22_500,
            ),
            TritBenchObservation(
                3,
                TritStimulus.NEGATIVE,
                -702_000,
                "load_10k",
                load_ohms=10_000,
            ),
            TritBenchObservation(
                4,
                TritStimulus.ZERO,
                6_000,
                "load_10k",
                load_ohms=10_000,
            ),
            TritBenchObservation(
                5,
                TritStimulus.POSITIVE,
                711_000,
                "load_10k",
                load_ohms=10_000,
            ),
        ),
        switching_observations=(
            SwitchingObservation(0, "CMP-A", SwitchingDirection.RISING, -310_000, "N", "Z"),
            SwitchingObservation(1, "CMP-A", SwitchingDirection.FALLING, -335_000, "Z", "N"),
            SwitchingObservation(2, "CMP-B", SwitchingDirection.RISING, 326_000, "Z", "P"),
            SwitchingObservation(3, "CMP-B", SwitchingDirection.FALLING, 301_000, "P", "Z"),
        ),
    )


def test_characterization_round_trips_signed_measured_values() -> None:
    original = _characterization()
    restored = TritCellCharacterization.from_json(original.canonical_json())

    assert restored == original
    assert restored.digest() == original.digest()
    assert restored.node_voltages[0].voltage_uv < 0
    assert restored.observations[0].output_uv < 0
    assert restored.switching_observations[0].threshold_uv < 0


def test_voltage_summary_is_descriptive_only() -> None:
    summary = _characterization().voltage_summary()

    assert summary == (
        {"stimulus": -1, "count": 2, "min_uv": -740_000, "max_uv": -702_000},
        {"stimulus": 0, "count": 2, "min_uv": 6_000, "max_uv": 8_000},
        {"stimulus": 1, "count": 2, "min_uv": 711_000, "max_uv": 755_000},
    )
    assert all("threshold" not in item for item in summary)


def test_characterization_requires_all_three_logical_stimuli() -> None:
    source = _characterization()
    with pytest.raises(HardwareCharacterizationError, match=r"-1, 0, and \+1"):
        TritCellCharacterization(
            board_revision=source.board_revision,
            unit_id=source.unit_id,
            bench_id=source.bench_id,
            instruments=source.instruments,
            node_voltages=source.node_voltages,
            observations=source.observations[:2],
        )


def test_characterization_rejects_coercive_json_values() -> None:
    payload = json.loads(_characterization().canonical_json())
    payload["observations"][0]["output_uv"] = "-740000"

    with pytest.raises(HardwareCharacterizationError, match="output_uv must be an integer"):
        TritCellCharacterization.from_dict(payload)

    payload = json.loads(_characterization().canonical_json())
    payload["version"] = True
    with pytest.raises(HardwareCharacterizationError, match="version must be an integer"):
        TritCellCharacterization.from_dict(payload)


def test_characterization_rejects_missing_or_extra_canonical_fields() -> None:
    payload = json.loads(_characterization().canonical_json())
    del payload["observations"][0]["settle_us"]
    with pytest.raises(CanonicalArtifactError, match="canonical JSON"):
        TritCellCharacterization.from_dict(payload)

    payload = json.loads(_characterization().canonical_json())
    payload["invented_nominal_voltage_uv"] = 750_000
    with pytest.raises(CanonicalArtifactError, match="canonical JSON"):
        TritCellCharacterization.from_dict(payload)


def test_switching_observation_requires_real_code_transition() -> None:
    with pytest.raises(HardwareCharacterizationError, match="change comparator code"):
        SwitchingObservation(
            0,
            "CMP-X",
            SwitchingDirection.RISING,
            123_000,
            "Z",
            "Z",
        )


def test_characterization_cli_verifies_and_summarizes_without_acceptance_inference(
    tmp_path, monkeypatch, capsys
) -> None:
    artifact = tmp_path / "cell.characterization.json"
    source = _characterization()
    artifact.write_text(source.canonical_json(), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["td1-characterize", "verify", str(artifact)])
    assert hardware_main() == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["verified"] is True
    assert verified["digest"] == source.digest()
    assert verified["observations"] == 6

    monkeypatch.setattr(sys, "argv", ["td1-characterize", "summary", str(artifact)])
    assert hardware_main() == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["acceptance_inferred"] is False
    assert summary["voltage_summary"][0]["stimulus"] == -1
