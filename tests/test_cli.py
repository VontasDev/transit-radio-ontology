"""End-to-end CLI tests via typer's CliRunner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from transit_radio_ontology.cli import app

runner = CliRunner()

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


def test_cli_validate_radio_check() -> None:
    result = runner.invoke(app, ["validate", str(EXAMPLES / "radio-check.json")])
    assert result.exit_code == 0, result.output
    assert "OK" in result.output


def test_cli_validate_accident_case_file() -> None:
    result = runner.invoke(
        app, ["validate", str(EXAMPLES / "accident-case-file.json")]
    )
    assert result.exit_code == 0, result.output


def test_cli_inspect() -> None:
    result = runner.invoke(app, ["inspect", str(EXAMPLES / "radio-check.json")])
    assert result.exit_code == 0, result.output
    assert "entities:" in result.output
    assert "events:" in result.output
    assert "PTTEvent" in result.output


def test_cli_schema_vehicle() -> None:
    result = runner.invoke(app, ["schema", "Vehicle"])
    assert result.exit_code == 0, result.output
    assert '"title": "Vehicle"' in result.output


def test_cli_unknown_schema_exits_nonzero() -> None:
    result = runner.invoke(app, ["schema", "DoesNotExist"])
    assert result.exit_code != 0


def test_cli_list_schemas() -> None:
    result = runner.invoke(app, ["list-schemas"])
    assert result.exit_code == 0, result.output
    assert "Vehicle" in result.output
    assert "PTTEvent" in result.output
