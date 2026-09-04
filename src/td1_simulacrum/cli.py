"""Command-line interface for the TD-1 Simulacrum."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assembler import assemble
from .corpus import CorpusSnapshot, compare_snapshots
from .geometry import GeometryProfile, GeometryScene, build_geometry_scene
from .glyphs import word_to_glyph_ids
from .lowering import OperandBindings, lower_state_weave, supported_lowerings
from .machine import Instruction, Machine, Op
from .render_state import RenderMode, RenderState, project_render_state
from .semantic import StateWeave
from .ternary import TernaryWord
from .trace import ExecutionTrace, diff_geometry, trace_program, verify_execution_trace


def _run_program(path: Path, max_steps: int) -> int:
    program = assemble(path.read_text(encoding="utf-8"))
    machine = Machine().run(program, max_steps=max_steps)
    print(json.dumps(machine.snapshot().as_dict(), indent=2))
    print(f"state_digest={machine.state_digest()}")
    return 0


def _trace_program(path: Path, max_steps: int) -> int:
    program = assemble(path.read_text(encoding="utf-8"))
    trace = trace_program(program, max_steps=max_steps)
    print(json.dumps(trace.as_dict(), indent=2, sort_keys=True))
    return 0


def _verify_trace(path: Path, trace_path: Path) -> int:
    program = assemble(path.read_text(encoding="utf-8"))
    trace = ExecutionTrace.from_json(trace_path.read_text(encoding="utf-8"))
    verify_execution_trace(program, trace)
    print(json.dumps({"verified": True, "trace_digest": trace.digest()}, sort_keys=True))
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


def _geometry_delta(before_path: Path, after_path: Path) -> int:
    before = GeometryScene.from_json(before_path.read_text(encoding="utf-8"))
    after = GeometryScene.from_json(after_path.read_text(encoding="utf-8"))
    print(json.dumps(diff_geometry(before, after).as_dict(), indent=2, sort_keys=True))
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


def _parse_register(text: str) -> int:
    normalized = text.strip().upper()
    if normalized.startswith("R"):
        normalized = normalized[1:]
    try:
        return int(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("register must look like R0..R8 or 0..8") from exc


def _lower_weave(args: argparse.Namespace) -> int:
    bindings = OperandBindings(
        target_register=args.target,
        source_register=args.source,
        left_register=args.left,
        right_register=args.right,
        base_register=args.base,
        offset=args.offset,
    )
    lowered = lower_state_weave(StateWeave.parse(args.weave), bindings)
    payload: dict[str, object] = {"lowering": lowered.as_dict(), "digest": lowered.digest()}
    if args.execute:
        program = list(lowered.instructions)
        if program[-1].op is not Op.HALT:
            program.append(Instruction(Op.HALT))
        machine = Machine().run(program)
        payload["execution"] = {
            "snapshot": machine.snapshot().as_dict(),
            "machine_digest": machine.state_digest(),
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _list_lowerings() -> int:
    print(
        json.dumps(
            {"schema": "td1.semantic-lowering-support", "version": 1,
             "forms": [form.as_dict() for form in supported_lowerings()]},
            indent=2,
            sort_keys=True,
        )
    )
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

    trace_parser = subparsers.add_parser(
        "trace",
        help="execute a TD-1 source file and emit a deterministic logical transition trace",
    )
    trace_parser.add_argument("path", type=Path)
    trace_parser.add_argument("--max-steps", type=int, default=100_000)

    verify_parser = subparsers.add_parser(
        "trace-verify",
        help="replay and verify a saved execution trace against a TD-1 source file",
    )
    verify_parser.add_argument("path", type=Path)
    verify_parser.add_argument("trace", type=Path)

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

    geometry_delta_parser = subparsers.add_parser(
        "geometry-delta",
        help="classify deterministic changes between two saved TD-1 geometry scenes",
    )
    geometry_delta_parser.add_argument("before", type=Path)
    geometry_delta_parser.add_argument("after", type=Path)

    lower_parser = subparsers.add_parser(
        "lower",
        help="lower one supported State Weave into logical TD-1 instructions",
    )
    lower_parser.add_argument("weave", help="canonical State Weave such as MEMORY:0")
    lower_parser.add_argument("--target", type=_parse_register)
    lower_parser.add_argument("--source", type=_parse_register)
    lower_parser.add_argument("--left", type=_parse_register)
    lower_parser.add_argument("--right", type=_parse_register)
    lower_parser.add_argument("--base", type=_parse_register)
    lower_parser.add_argument("--offset", type=int)
    lower_parser.add_argument(
        "--execute",
        action="store_true",
        help="execute the lowered fragment on a zeroed reference machine",
    )

    subparsers.add_parser(
        "lowerings",
        help="list the complete supported v1 State Weave lowering surface",
    )

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
    if args.command == "trace":
        return _trace_program(args.path, args.max_steps)
    if args.command == "trace-verify":
        return _verify_trace(args.path, args.trace)
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
    if args.command == "geometry-delta":
        return _geometry_delta(args.before, args.after)
    if args.command == "lower":
        return _lower_weave(args)
    if args.command == "lowerings":
        return _list_lowerings()
    if args.command == "glyph":
        return _show_glyphs(args.word)
    if args.command == "corpus-validate":
        return _validate_corpus(args.path)
    if args.command == "corpus-delta":
        return _corpus_delta(args.before, args.after)
    raise RuntimeError(f"unknown command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
