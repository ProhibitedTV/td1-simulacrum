"""CLI for validating and inspecting measured TD-1 hardware characterization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .hardware_characterization import TritCellCharacterization


def _load(path: str) -> TritCellCharacterization:
    return TritCellCharacterization.from_json(Path(path).read_text(encoding="utf-8"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="td1-characterize",
        description="Validate measured TD-1 ternary-cell characterization evidence.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser(
        "verify",
        help="strictly validate one td1.trit-cell-characterization artifact",
    )
    verify.add_argument("artifact")

    summary = subparsers.add_parser(
        "summary",
        help="print descriptive observed voltage ranges without acceptance inference",
    )
    summary.add_argument("artifact")
    return parser


def main() -> int:
    args = _parser().parse_args()
    characterization = _load(args.artifact)

    if args.command == "verify":
        print(
            json.dumps(
                {
                    "verified": True,
                    "schema": characterization.schema,
                    "version": characterization.version,
                    "board_revision": characterization.board_revision,
                    "unit_id": characterization.unit_id,
                    "bench_id": characterization.bench_id,
                    "digest": characterization.digest(),
                    "observations": len(characterization.observations),
                    "switching_observations": len(
                        characterization.switching_observations
                    ),
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "summary":
        print(
            json.dumps(
                {
                    "schema": characterization.schema,
                    "version": characterization.version,
                    "board_revision": characterization.board_revision,
                    "unit_id": characterization.unit_id,
                    "digest": characterization.digest(),
                    "voltage_summary": list(characterization.voltage_summary()),
                    "acceptance_inferred": False,
                },
                sort_keys=True,
            )
        )
        return 0

    raise AssertionError("unreachable characterization CLI command")
