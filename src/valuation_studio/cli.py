"""Command-line interface (CLI) for executing valuation pipelines."""
from pathlib import Path

import typer
from rich.console import Console

from valuation_studio.dcf import DCFEngine
from valuation_studio.excel_bridge import ExcelBridge
from valuation_studio.loaders import DataLoader
from valuation_studio.reporting import Reporter
from valuation_studio.scenarios import ScenarioManager
from valuation_studio.statements import FinancialModel

app = typer.Typer(help="Valuation Studio CLI: Institutional 3-Statement & DCF Engine.")
console = Console()


@app.command()  # type: ignore[misc]
def run(
    ticker: str = typer.Option("NVDA", "--ticker", "-t", help="Stock ticker symbol."),
    scenario: str = typer.Option(
        "bull", "--scenario", "-s", help="Scenario case: bull, base, bear."
    ),
    output: Path = typer.Option(
        Path("models/examples/sample_valuation_nvda.xlsx"),
        "--output",
        "-o",
        help="Excel output path."
    )
) -> None:
    """Runs end-to-end valuation pipeline and exports synchronized Excel model."""
    console.print(f"[bold green]Initiating Valuation Engine for {ticker.upper()}...[/bold green]")

    # 1. Load Data
    try:
        data = DataLoader.from_yfinance(ticker)
    except Exception:
        console.print(
            "[yellow]API connection fallback: Generating synthetic financial profile.[/yellow]"
        )
        from valuation_studio.loaders import FinancialStatementSchema
        data = FinancialStatementSchema(
            years=[2023, 2024, 2025],
            revenue=[26974.0, 60922.0, 125000.0],
            cogs=[11618.0, 16621.0, 31250.0],
            opex=[8130.0, 11329.0, 15000.0],
            da=[1500.0, 2000.0, 3000.0],
            initial_cash=25980.0,
            initial_debt=11000.0,
            shares_outstanding=2460.0,
            current_price=130.0
        )

    # 2. Select Scenario
    scenarios = ScenarioManager.get_defaults()
    selected_scen = scenarios.get(scenario.lower(), scenarios["base"])

    # 3. Build Projections
    model = FinancialModel(data)
    proj = model.project(
        forecast_years=5,
        rev_growth=selected_scen.rev_growth,
        ebitda_margin=selected_scen.ebitda_margin
    )

    # 4. Execute Unlevered DCF
    dcf_res = DCFEngine.value(
        proj=proj,
        wacc=selected_scen.wacc,
        terminal_growth=selected_scen.terminal_growth,
        shares_outstanding=data.shares_outstanding,
        current_cash=proj.cash[-1],
        current_debt=proj.debt[-1]
    )

    # 5. Export to Excel
    output.parent.mkdir(parents=True, exist_ok=True)
    ExcelBridge.write_model(output, ticker, proj, dcf_res)
    console.print(f"[green]Successfully synchronized Excel model to:[/green] [bold]{output}[/bold]")

    # 6. Print Executive Briefing
    reporter = Reporter()
    reporter.print_executive_summary(ticker, scenario, proj, dcf_res)


if __name__ == "__main__":
    app()
