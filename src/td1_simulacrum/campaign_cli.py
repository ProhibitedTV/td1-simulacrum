"""Command-line workflows for trace-derived TD-1 parity campaigns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .assembler import assemble
from .campaign import (
    ParityCampaign,
    ParityCampaignRun,
    build_parity_campaign,
    run_parity_campaign,
)
from .parity import ReferenceLoopbackTransport
from .trace import trace_program
from .wire import InMemoryParityLineIO, JsonLineParityTransport, ParityWireDevice
from .wire_transcript import (
    ParityBenchRun,
    ParityWireTranscript,
    RecordingParityLineIO,
    replay_bench_run,
)


def _write_json(payload: dict[str, object], output: Path | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")


def _build(program_path: Path, max_steps: int, output: Path | None) -> int:
    program = assemble(program_path.read_text(encoding="utf-8"))
    campaign = build_parity_campaign(trace_program(program, max_steps=max_steps))
    if output is None:
        _write_json(campaign.as_dict(), None)
    else:
        _write_json(campaign.as_dict(), output)
        print(
            json.dumps(
                {
                    "output": str(output),
                    "campaign_digest": campaign.digest(),
                    "trace_digest": campaign.trace.digest(),
                    "vector_set_digest": campaign.vector_set_digest,
                    "entries": len(campaign.entries),
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def _verify(path: Path) -> int:
    campaign = ParityCampaign.from_json(path.read_text(encoding="utf-8"))
    payload = {
        "verified": True,
        "campaign_digest": campaign.digest(),
        "trace_digest": campaign.trace.digest(),
        "initial_machine_digest": campaign.initial_checkpoint.machine_digest,
        "final_machine_digest": campaign.final_checkpoint.machine_digest,
        "vector_set_digest": campaign.vector_set_digest,
        "entries": len(campaign.entries),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _emit_run(run: ParityCampaignRun, output: Path | None, *, transport: str) -> int:
    if output is None:
        _write_json(run.as_dict(), None)
    else:
        _write_json(run.as_dict(), output)
        print(
            json.dumps(
                {
                    "output": str(output),
                    "transport": transport,
                    "run_digest": run.digest(),
                    "campaign_digest": run.campaign.digest(),
                    "report_digest": run.report.digest(),
                    "passed": run.report.passed,
                    "passed_count": run.report.passed_count,
                    "failed_count": run.report.failed_count,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0 if run.report.passed else 2


def _loopback(
    path: Path,
    target_max_width: int,
    target_id: str,
    output: Path | None,
) -> int:
    campaign = ParityCampaign.from_json(path.read_text(encoding="utf-8"))
    transport = ReferenceLoopbackTransport(
        target_id=target_id,
        max_width=target_max_width,
    )
    run = run_parity_campaign(transport, campaign)
    return _emit_run(run, output, transport="reference-loopback")


def _wire_loopback(
    path: Path,
    target_max_width: int,
    target_id: str,
    output: Path | None,
    transcript_output: Path | None,
    bench_output: Path | None,
) -> int:
    campaign = ParityCampaign.from_json(path.read_text(encoding="utf-8"))
    target = ReferenceLoopbackTransport(
        target_id=target_id,
        max_width=target_max_width,
    )
    line_io = InMemoryParityLineIO(ParityWireDevice(target))
    recording = RecordingParityLineIO(line_io)
    transport = JsonLineParityTransport(recording)
    run = run_parity_campaign(transport, campaign)
    transcript = recording.transcript()
    bench = ParityBenchRun(run, transcript)

    if transcript_output is not None:
        _write_json(transcript.as_dict(), transcript_output)
    if bench_output is not None:
        _write_json(bench.as_dict(), bench_output)

    if output is None:
        _write_json(run.as_dict(), None)
    else:
        _write_json(run.as_dict(), output)
        payload: dict[str, object] = {
            "output": str(output),
            "transport": "td1.parity-wire/v1",
            "run_digest": run.digest(),
            "campaign_digest": run.campaign.digest(),
            "report_digest": run.report.digest(),
            "transcript_digest": transcript.digest(),
            "bench_run_digest": bench.digest(),
            "passed": run.report.passed,
            "passed_count": run.report.passed_count,
            "failed_count": run.report.failed_count,
        }
        if transcript_output is not None:
            payload["transcript_output"] = str(transcript_output)
        if bench_output is not None:
            payload["bench_output"] = str(bench_output)
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if run.report.passed else 2


def _verify_run(path: Path) -> int:
    run = ParityCampaignRun.from_json(path.read_text(encoding="utf-8"))
    payload = {
        "verified": True,
        "run_digest": run.digest(),
        "campaign_digest": run.campaign.digest(),
        "report_digest": run.report.digest(),
        "passed": run.report.passed,
        "entries": len(run.campaign.entries),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if run.report.passed else 2


def _verify_transcript(path: Path) -> int:
    transcript = ParityWireTranscript.from_json(path.read_text(encoding="utf-8"))
    payload = {
        "verified": True,
        "transcript_digest": transcript.digest(),
        "records": len(transcript.records),
        "exchanges": transcript.exchange_count,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _replay_bench(path: Path) -> int:
    bench = ParityBenchRun.from_json(path.read_text(encoding="utf-8"))
    replayed = replay_bench_run(bench)
    payload = {
        "verified": True,
        "replayed": True,
        "bench_run_digest": bench.digest(),
        "transcript_digest": bench.transcript.digest(),
        "campaign_run_digest": replayed.digest(),
        "report_digest": replayed.report.digest(),
        "passed": replayed.report.passed,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if replayed.report.passed else 2


def _add_target_options(parser: argparse.ArgumentParser, *, default_id: str) -> None:
    parser.add_argument("--target-max-width", type=int, default=12)
    parser.add_argument("--target-id", default=default_id)
    parser.add_argument("--output", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="td1-parity",
        description="TD-1 trace-derived physical parity campaign tooling",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build",
        help="execute a logical program and package encountered subsystem parity vectors",
    )
    build_parser.add_argument("path", type=Path, help="TD-1 assembly source")
    build_parser.add_argument("--max-steps", type=int, default=100_000)
    build_parser.add_argument("--output", type=Path)

    verify_parser = subparsers.add_parser(
        "verify",
        help="reconstruct and verify a saved td1.parity-campaign",
    )
    verify_parser.add_argument("path", type=Path)

    loopback_parser = subparsers.add_parser(
        "loopback",
        help="run a saved campaign through the reference loopback parity target",
    )
    loopback_parser.add_argument("path", type=Path)
    _add_target_options(loopback_parser, default_id="simulacrum.trace-loopback")

    wire_loopback_parser = subparsers.add_parser(
        "wire-loopback",
        help="run a saved campaign through canonical td1.parity-wire framing",
    )
    wire_loopback_parser.add_argument("path", type=Path)
    _add_target_options(wire_loopback_parser, default_id="simulacrum.wire-loopback")
    wire_loopback_parser.add_argument(
        "--transcript-output",
        type=Path,
        help="optional td1.parity-wire-transcript artifact path",
    )
    wire_loopback_parser.add_argument(
        "--bench-output",
        type=Path,
        help="optional td1.parity-bench-run artifact path",
    )

    run_verify_parser = subparsers.add_parser(
        "run-verify",
        help="verify a saved td1.parity-campaign-run artifact",
    )
    run_verify_parser.add_argument("path", type=Path)

    transcript_verify_parser = subparsers.add_parser(
        "wire-transcript-verify",
        help="verify exact canonical frame evidence in a saved wire transcript",
    )
    transcript_verify_parser.add_argument("path", type=Path)

    bench_replay_parser = subparsers.add_parser(
        "bench-run-replay",
        help="verify and replay a saved td1.parity-bench-run through transcript bytes",
    )
    bench_replay_parser.add_argument("path", type=Path)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "build":
        return _build(args.path, args.max_steps, args.output)
    if args.command == "verify":
        return _verify(args.path)
    if args.command == "loopback":
        return _loopback(
            args.path,
            args.target_max_width,
            args.target_id,
            args.output,
        )
    if args.command == "wire-loopback":
        return _wire_loopback(
            args.path,
            args.target_max_width,
            args.target_id,
            args.output,
            args.transcript_output,
            args.bench_output,
        )
    if args.command == "run-verify":
        return _verify_run(args.path)
    if args.command == "wire-transcript-verify":
        return _verify_transcript(args.path)
    if args.command == "bench-run-replay":
        return _replay_bench(args.path)
    raise RuntimeError(f"unknown command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
