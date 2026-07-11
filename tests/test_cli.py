"""Integration tests verifying CLI execution and Excel file output."""
from pathlib import Path

from typer.testing import CliRunner
from valuation_studio.cli import app

runner = CliRunner()


def test_cli_run_generation(tmp_path: Path) -> None:
    out_file = tmp_path / "test_nvda_model.xlsx"
    result = runner.invoke(
        app,
        ["--ticker", "NVDA", "--scenario", "bull", "--output", str(out_file)]
    )

    assert result.exit_code == 0
    assert "Initiating Valuation Engine" in result.stdout
    assert out_file.exists()
    assert out_file.stat().st_size > 0
