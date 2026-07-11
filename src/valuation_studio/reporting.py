"""Executive console reporting and Markdown/HTML document generation."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from valuation_studio.dcf import DCFResult
from valuation_studio.statements import Projections


class Reporter:
    """Generates visual terminal tables and boardroom summary reports."""
    def __init__(self) -> None:
        self.console = Console()

    def print_executive_summary(
        self, ticker: str, scenario: str, proj: Projections, dcf: DCFResult
    ) -> None:
        self.console.print(
            f"\n[bold navy]VALUATION STUDIO: EXECUTIVE BRIEFING — {ticker.upper()}[/bold navy]"
        )
        self.console.print(
            f"Active Scenario: [bold cyan]{scenario.upper()}[/bold cyan] | "
            f"Model Version: [green]Production 1.0.0[/green]\n"
        )

        # Table 1: Financial Projections
        t_proj = Table(
            title="3-Statement Summary ($M)",
            show_header=True,
            header_style="bold white on #1F497D"
        )
        t_proj.add_column("Line Item", style="bold")
        for yr in proj.years:
            t_proj.add_column(f"FY{yr}", justify="right")

        t_proj.add_row("Revenue", *[f"${v:,.1f}" for v in proj.revenue])
        t_proj.add_row("EBITDA", *[f"${v:,.1f}" for v in proj.ebitda])
        t_proj.add_row("EBIT", *[f"${v:,.1f}" for v in proj.ebit])
        t_proj.add_row("Net Income", *[f"${v:,.1f}" for v in proj.net_income])
        t_proj.add_row("FCFF", *[f"${v:,.1f}" for v in proj.fcff], style="bold green")
        self.console.print(t_proj)

        # Table 2: DCF Output & Multiple Comparison
        t_dcf = Table(
            title="Valuation Architecture & Multiples",
            show_header=True,
            header_style="bold white on #1F497D"
        )
        t_dcf.add_column("Valuation Metric", style="bold")
        t_dcf.add_column("Model Output", justify="right", style="bold cyan")

        t_dcf.add_row("Discount Rate (WACC)", f"{dcf.wacc * 100:.2f}%")
        t_dcf.add_row("Enterprise Value (EV)", f"${dcf.enterprise_value_gordon:,.1f}M")
        t_dcf.add_row("Equity Value", f"${dcf.equity_value_gordon:,.1f}M")
        t_dcf.add_row("Implied Share Price", f"${dcf.implied_share_price_gordon:,.2f}")
        t_dcf.add_row("Implied Exit Multiple", f"{dcf.implied_ev_ebitda_multiple:.1f}x")
        self.console.print(t_dcf)

        # Print Panel Box
        panel_text = (
            f" [bold]Valuation Verdict:[/bold] In the [cyan]{scenario}[/cyan] scenario, "
            f"{ticker.upper()} is valued at an intrinsic equity price of "
            f"[bold green]${dcf.implied_share_price_gordon:,.2f}[/bold green] per share, "
            f"supported by an operational WACC of {dcf.wacc*100:.1f}% and an implied exit "
            f"EBITDA multiple of {dcf.implied_ev_ebitda_multiple:.1f}x."
        )
        self.console.print(
            Panel(
                panel_text,
                title="[bold white]Boardroom Summary[/bold white]",
                border_style="cyan"
            )
        )
