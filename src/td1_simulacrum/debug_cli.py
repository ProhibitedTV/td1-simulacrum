"""CLI for deterministic TD-1 live stop/breakpoint debugging."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .assembler import assemble
from .debug import DebugRun, DebugStopSpec, run_debug, verify_debug_run
from .machine import MEMORY_WORDS, REGISTER_COUNT, Op
from .machine_state import MachineState


def _parse_register(text: str) -> int:
    normalized = text.strip().upper()
    if normalized.startswith("R"):
        normalized = normalized[1:]
    try:
        value = int(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("register must look like R0..R8 or 0..8") from exc
    if not 0 <= value < REGISTER_COUNT:
        raise argparse.ArgumentTypeError(f"register must be within R0..R{REGISTER_COUNT - 1}")
    return value


def _parse_memory(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("memory address must be an integer") from exc
    if not 0 <= value < MEMORY_WORDS:
        raise argparse.ArgumentTypeError(f"memory address must be within 0..{MEMORY_WORDS - 1}")
    return value


def _run(args: argparse.Namespace) -> int:
    program = assemble(args.program.read_text(encoding="utf-8"))
    initial_machine = None
    if args.checkpoint is not None:
        initial_machine = MachineState.from_json(
            args.checkpoint.read_text(encoding="utf-8")
        ).restore_machine()

    stop_spec = DebugStopSpec(
        instruction_indices=tuple(args.break_ip or ()),
        operations=tuple(args.break_op or ()),
        registers=tuple(args.watch_register or ()),
        memory_addresses=tuple(args.watch_memory or ()),
    )
    run = run_debug(
        program,
        stop_spec=stop_spec,
        initial_machine=initial_machine,
        max_events=args.max_events,
        skip_initial_breakpoint=args.skip_initial_breakpoint,
    )
    text = json.dumps(run.as_dict(), indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(text)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "debug_run_digest": run.digest(),
                "trace_digest": run.trace.digest(),
                "stop_kind": run.stop_kind.value,
                "position": run.position,
                "machine_digest": run.trace.final_state.machine_digest,
                "matches": list(run.matches),
                "halted": run.trace.final_state.halted,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _verify(args: argparse.Namespace) -> int:
    program = assemble(args.program.read_text(encoding="utf-8"))
    run = DebugRun.from_json(args.debug_run.read_text(encoding="utf-8"))
    verify_debug_run(program, run)
    print(
        json.dumps(
            {
                "verified": True,
                "debug_run_digest": run.digest(),
                "trace_digest": run.trace.digest(),
                "stop_kind": run.stop_kind.value,
                "position": run.position,
                "machine_digest": run.trace.final_state.machine_digest,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="td1-debug",
        description=(
            "Deterministic TD-1 debugger: break before instructions, watch real state changes, "
            "and preserve exact execution-trace prefixes"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="execute until one deterministic stop condition")
    run_parser.add_argument("program", type=Path)
    run_parser.add_argument(
        "--break-ip",
        action="append",
        type=int,
        help="stop before this logical instruction index; may be repeated",
    )
    run_parser.add_argument(
        "--break-op",
        action="append",
        choices=[op.name for op in Op],
        help="stop before this logical opcode; may be repeated",
    )
    run_parser.add_argument(
        "--watch-register",
        action="append",
        type=_parse_register,
        help="stop after an event changes this register; may be repeated",
    )
    run_parser.add_argument(
        "--watch-memory",
        action="append",
        type=_parse_memory,
        help="stop after an event changes this memory address; may be repeated",
    )
    run_parser.add_argument(
        "--max-events",
        type=int,
        default=100_000,
        help="deterministic event budget for this debugger continuation",
    )
    run_parser.add_argument(
        "--checkpoint",
        type=Path,
        help="optional td1.machine-state checkpoint used as the initial machine boundary",
    )
    run_parser.add_argument(
        "--skip-initial-breakpoint",
        action="store_true",
        help="execute past a breakpoint at the supplied initial boundary before evaluating it again",
    )
    run_parser.add_argument("--output", type=Path, help="write the td1.debug-run artifact")

    verify_parser = subparsers.add_parser(
        "verify",
        help="replay a td1.debug-run and require exact stop/artifact equality",
    )
    verify_parser.add_argument("program", type=Path)
    verify_parser.add_argument("debug_run", type=Path)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run":
        return _run(args)
    if args.command == "verify":
        return _verify(args)
    raise RuntimeError(f"unknown command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
