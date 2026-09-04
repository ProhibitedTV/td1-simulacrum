"""Command-line interface for the TD-1 Simulacrum."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assembler import assemble
from .corpus import CorpusSnapshot, compare_snapshots
from .geometry import GeometryProfile, build_geometry_scene
from .glyphs import word_to_glyph_ids
from .machine import Machine
from .render_state import RenderMode, RenderState, project_render_state
from .semantic import StateWeave
from .ternary import TernaryWord


def _run_program(path: Path, max_steps: int) -> int:
    program = assemble(path.read_text(encoding="utf-8"))
    machine = Machine().run(program, max_steps=max_steps)
    print(json.dumps(machine.snapshot().as_dict(), indent=2))
    print(f"state_digest={machine.state_digest()}")
    return 0


def _render_program(path: Path, max_steps: int, mode: str) -> int:
    program = assemble(path.read_text(encoding="utf-8"))
    machine = Machine().run(program, max_steps=max_steps)
    state = RenderState.capture(machine)
    projection = project_render_state(state, RenderMode(mode))
    print(json.dumps(projection, indent=2, sort_keys=True))
    return 0


def _geometry_program(
    path: Path,
    max_steps: int,
    corpus_path: Path | None,
    corpus_threshold: int,
    weave_text: str | None,
) -> int:
    program = assemble(path.read_text(encoding="utf-8"))
    machine = Machine().run(program, max_steps=max_steps)
    weave = StateWeave.parse(weave_text) if weave_text is not None else None
    state = RenderState.capture(machine, weave=weave)

    profile = None
    if corpus_path is not None:
        snapshot = CorpusSnapshot.from_json(corpus_path.read_text(encoding="utf-8"))
        profile = GeometryProfile.from_snapshot(
            snapshot,
            threshold_milli=corpus_threshold,
        )

    scene = build_geometry_scene(state, profile=profile)
    print(json.dumps(scene.as_dict(), indent=2, sort_keys=True))
    return 0


def _show_glyphs(text: str) -> int:
    word = TernaryWord.parse(text)
    print(" ".join(f"G{glyph_id:02d}" for glyph_id in word_to_glyph_ids(word)))
    return 0


def _validate_corpus(path: Path) -> int:
    snapshot = CorpusSnapshot.from_json(path.read_text(encoding="utf-8"))
    payload = {
        "snapshot_id": snapshot.snapshot_id,
        "digest": snapshot.digest(),
        "records": len(snapshot.records),
        "annotations": len(snapshot.annotations),
        "motif_counts": snapshot.motif_counts(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _corpus_delta(before_path: Path, after_path: Path) -> int:
    before = CorpusSnapshot.from_json(before_path.read_text(encoding="utf-8"))
    after = CorpusSnapshot.from_json(after_path.read_text(encoding="utf-8"))
    print(json.dumps(compare_snapshots(before, after).as_dict(), indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="td1-sim",
        description="TD-1 Simulacrum reference emulator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="assemble and execute a TD-1 source file")
    run_parser.add_argument("path", type=Path)
    run_parser.add_argument("--max-steps", type=int, default=100_000)

    render_parser = subparsers.add_parser(
        "render",
        help="execute a TD-1 source file and emit a deterministic render projection",
    )
    render_parser.add_argument("path", type=Path)
    render_parser.add_argument(
        "--mode",
        choices=[mode.value for mode in RenderMode],
        default=RenderMode.ENGINEERING.value,
    )
    render_parser.add_argument("--max-steps", type=int, default=100_000)

    geometry_parser = subparsers.add_parser(
        "geometry",
        help="emit deterministic native geometry for an executed TD-1 program",
    )
    geometry_parser.add_argument("path", type=Path)
    geometry_parser.add_argument(
        "--corpus",
        type=Path,
        help="optional frozen VB-TD1 corpus snapshot used to admit geometry rules",
    )
    geometry_parser.add_argument(
        "--corpus-threshold",
        type=int,
        default=750,
        help="minimum motif confidence in milli-units (0..1000, default: 750)",
    )
    geometry_parser.add_argument(
        "--weave",
        help="optional canonical State Weave such as TIME>REFERENCE:+",
    )
    geometry_parser.add_argument("--max-steps", type=int, default=100_000)

    glyph_parser = subparsers.add_parser("glyph", help="map a ternary word to microglyph IDs")
    glyph_parser.add_argument("word")

    corpus_parser = subparsers.add_parser(
        "corpus-validate",
        help="validate a frozen TD-1 corpus snapshot and print its digest",
    )
    corpus_parser.add_argument("path", type=Path)

    delta_parser = subparsers.add_parser(
        "corpus-delta",
        help="compare two frozen TD-1 corpus snapshots",
    )
    delta_parser.add_argument("before", type=Path)
    delta_parser.add_argument("after", type=Path)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run":
        return _run_program(args.path, args.max_steps)
    if args.command == "render":
        return _render_program(args.path, args.max_steps, args.mode)
    if args.command == "geometry":
        return _geometry_program(
            args.path,
            args.max_steps,
            args.corpus,
            args.corpus_threshold,
            args.weave,
        )
    if args.command == "glyph":
        return _show_glyphs(args.word)
    if args.command == "corpus-validate":
        return _validate_corpus(args.path)
    if args.command == "corpus-delta":
        return _corpus_delta(args.before, args.after)
    raise RuntimeError(f"unknown command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
