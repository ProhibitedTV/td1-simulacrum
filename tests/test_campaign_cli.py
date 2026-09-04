import json
import sys

from td1_simulacrum.campaign import ParityCampaign, ParityCampaignRun
from td1_simulacrum.campaign_cli import main


def _write_program(tmp_path):
    path = tmp_path / "campaign.td1"
    path.write_text(
        """
LDI R0, 2
LDI R1, 3
ADD R0, R1
ADDI R0, -1
NEG R0
HALT
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def test_campaign_cli_build_verify_loopbacks_and_run_verify(tmp_path, monkeypatch, capsys) -> None:
    program = _write_program(tmp_path)
    campaign_path = tmp_path / "campaign.json"
    run_path = tmp_path / "campaign-run.json"
    wire_run_path = tmp_path / "campaign-wire-run.json"

    monkeypatch.setattr(
        sys,
        "argv",
        ["td1-parity", "build", str(program), "--output", str(campaign_path)],
    )
    assert main() == 0
    build_summary = json.loads(capsys.readouterr().out)
    assert build_summary["entries"] == 5
    campaign = ParityCampaign.from_json(campaign_path.read_text(encoding="utf-8"))
    assert build_summary["campaign_digest"] == campaign.digest()

    monkeypatch.setattr(sys, "argv", ["td1-parity", "verify", str(campaign_path)])
    assert main() == 0
    verify_summary = json.loads(capsys.readouterr().out)
    assert verify_summary["verified"] is True
    assert verify_summary["campaign_digest"] == campaign.digest()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "td1-parity",
            "loopback",
            str(campaign_path),
            "--output",
            str(run_path),
        ],
    )
    assert main() == 0
    run_summary = json.loads(capsys.readouterr().out)
    assert run_summary["passed"] is True
    assert run_summary["transport"] == "reference-loopback"
    run = ParityCampaignRun.from_json(run_path.read_text(encoding="utf-8"))
    assert run_summary["run_digest"] == run.digest()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "td1-parity",
            "wire-loopback",
            str(campaign_path),
            "--output",
            str(wire_run_path),
        ],
    )
    assert main() == 0
    wire_summary = json.loads(capsys.readouterr().out)
    assert wire_summary["passed"] is True
    assert wire_summary["transport"] == "td1.parity-wire/v1"
    wire_run = ParityCampaignRun.from_json(wire_run_path.read_text(encoding="utf-8"))
    assert wire_summary["run_digest"] == wire_run.digest()
    assert wire_run.report.capabilities.target_id == "simulacrum.wire-loopback"

    monkeypatch.setattr(sys, "argv", ["td1-parity", "run-verify", str(wire_run_path)])
    assert main() == 0
    verified_run = json.loads(capsys.readouterr().out)
    assert verified_run["verified"] is True
    assert verified_run["run_digest"] == wire_run.digest()


def test_campaign_cli_loopbacks_expose_capability_rejection(tmp_path, monkeypatch, capsys) -> None:
    program = _write_program(tmp_path)
    campaign_path = tmp_path / "campaign.json"

    monkeypatch.setattr(
        sys,
        "argv",
        ["td1-parity", "build", str(program), "--output", str(campaign_path)],
    )
    assert main() == 0
    capsys.readouterr()

    for command in ("loopback", "wire-loopback"):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "td1-parity",
                command,
                str(campaign_path),
                "--target-max-width",
                "3",
            ],
        )
        assert main() == 2
        payload = json.loads(capsys.readouterr().out)
        report = payload["report"]
        assert report["summary"]["passed"] is False
        assert all(
            record["response"]["status"] == "unsupported" for record in report["records"]
        )
