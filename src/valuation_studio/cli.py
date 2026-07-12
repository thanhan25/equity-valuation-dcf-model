"""Command-line interface (CLI) for executing valuation pipelines."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from valuation_studio.dcf import DCFEngine
from valuation_studio.excel_bridge import ExcelBridge
from valuation_studio.loaders import DataLoader
from valuation_studio.reporting import Reporter
from valuation_studio.scenarios import ScenarioManager
from valuation_studio.statements import FinancialModel

app = typer.Typer(help="Valuation Studio CLI: Institutional 3-Statement & DCF Engine.")
console = Console()


@app.command() # type: ignore[misc]
def run(
    ticker: str = typer.Option("NVDA", "--ticker", "-t", help="Stock ticker symbol."),
    scenario: str = typer.Option(
        "base", "--scenario", "-s", help="Scenario case: bull, base, bear."
    ),
    output: Path = typer.Option(
        Path("models/examples/sample_valuation_nvda.xlsx"),
        "--output",
        "-o",
        help="Excel output path.",
    ),
    synthetic: bool = typer.Option(False, "--synthetic", help="Force synthetic data."),
) -> None:
    """Runs end-to-end valuation pipeline and exports synchronized Excel model."""
    console.print(f"[bold green]Initiating Valuation Engine for {ticker.upper()}...[/bold green]")

    data = None
    if not synthetic:
        try:
            data = DataLoader.from_yfinance(ticker)
        except Exception:
            console.print("[yellow]API connection failed: Falling back to synthetic.[/yellow]")
            synthetic = True

    if synthetic:
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
            current_price=130.0,
            consensus_growth_y1=0.80,
            consensus_growth_y2=0.40,
            wall_st_target=150.0,
        )

    # Strictly inform MyPy that data is successfully populated
    assert data is not None, "Critical Error: Financial data failed to initialize."

    scenarios = ScenarioManager.get_defaults()
    selected_scen = scenarios.get(scenario.lower(), scenarios["base"])

    # Dynamic Scenario Delta anchoring
    base_curve = [data.consensus_growth_y1, data.consensus_growth_y2]
    if scenario.lower() == "bull":
        curve = [g + 0.05 for g in base_curve]
    elif scenario.lower() == "bear":
        curve = [max(0.0, g - 0.05) for g in base_curve]
    else:
        curve = base_curve

    model = FinancialModel(data)
    proj = model.project(
        forecast_years=5, rev_growth=curve, ebitda_margin=selected_scen.ebitda_margin
    )

    dcf_res = DCFEngine.value(
        proj=proj,
        wacc=selected_scen.wacc,
        terminal_growth=selected_scen.terminal_growth,
        shares_outstanding=data.shares_outstanding,
        current_cash=proj.cash[-1],
        current_debt=proj.debt[-1],
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    ExcelBridge.write_model(output, ticker, proj, dcf_res)
    console.print(f"[green]Successfully synchronized Excel model to:[/green] [bold]{output}[/bold]")

    reporter = Reporter()
    reporter.print_executive_summary(ticker, scenario, proj, dcf_res)


@app.command() # type: ignore[misc]
def screen(
    tickers: str = typer.Option(
        "AAPL,MSFT,NVDA,META", "--tickers", help="Comma-separated tickers."
    ),
    scenario: str = typer.Option(
        "base", "--scenario", "-s", help="Scenario case: bull, base, bear."
    ),
) -> None:
    """Batch processes multiple equities to identify valuation dislocations (Margin of Safety)."""
    console.print("\n[bold navy]VALUATION STUDIO: BATCH SCREENER[/bold navy]")
    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    table = Table(show_header=True, header_style="bold white on #1F497D")
    table.add_column("Ticker", style="bold cyan")
    table.add_column("Market Price", justify="right")
    table.add_column("Wall St Target", justify="right", style="dim")
    table.add_column("Consensus Y1", justify="right", style="magenta")
    table.add_column("Implied Value", justify="right", style="bold green")
    table.add_column("Margin of Safety", justify="right")

    scenarios = ScenarioManager.get_defaults()
    selected_scen = scenarios.get(scenario.lower(), scenarios["base"])

    for ticker in ticker_list:
        try:
            data = DataLoader.from_yfinance(ticker)

            base_curve = [data.consensus_growth_y1, data.consensus_growth_y2]
            if scenario.lower() == "bull":
                curve = [g + 0.05 for g in base_curve]
            elif scenario.lower() == "bear":
                curve = [max(0.0, g - 0.05) for g in base_curve]
            else:
                curve = base_curve

            model = FinancialModel(data)
            proj = model.project(
                forecast_years=5, rev_growth=curve, ebitda_margin=selected_scen.ebitda_margin
            )
            dcf_res = DCFEngine.value(
                proj=proj,
                wacc=selected_scen.wacc,
                terminal_growth=selected_scen.terminal_growth,
                shares_outstanding=data.shares_outstanding,
                current_cash=proj.cash[-1],
                current_debt=proj.debt[-1],
            )

            upside = (dcf_res.implied_share_price_gordon / data.current_price) - 1.0
            upside_color = "green" if upside > 0 else "red"

            target_str = f"${data.wall_st_target:.2f}" if data.wall_st_target > 0 else "N/A"
            table.add_row(
                ticker,
                f"${data.current_price:.2f}",
                target_str,
                f"{data.consensus_growth_y1 * 100:.1f}%",
                f"${dcf_res.implied_share_price_gordon:.2f}",
                f"[{upside_color}]{upside * 100:+.1f}%[/{upside_color}]",
            )
        except Exception:
            table.add_row(ticker, "ERROR", "ERROR", "ERROR", "ERROR", "[red]Data/API Failure[/red]")

    console.print(table)
    console.print(
        "\n[italic]*Note: Growth anchored to dynamic analyst consensus. "
        "Margins bound by selected scenario.[/italic]"
    )


if __name__ == "__main__":
    app()
