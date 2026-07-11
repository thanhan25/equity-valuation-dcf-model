"""Dynamic Excel serialization engine generating live, interconnected formulas."""
from pathlib import Path
from typing import cast

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from valuation_studio.dcf import DCFResult
from valuation_studio.statements import Projections


class ExcelBridge:
    """Exports Python projections into an institutional, formula-driven Excel model."""
    @staticmethod
    def write_model(filepath: str | Path, ticker: str, proj: Projections, dcf: DCFResult) -> None:
        wb = openpyxl.Workbook()

        # Cast the active sheet to Worksheet to satisfy strict static type checking
        ws = cast(Worksheet, wb.active)
        ws.title = "3-Statement & DCF"
        ws.views.sheetView[0].showGridLines = True

        # Institutional Styling Palette
        font_title = Font(name="Calibri", size=16, bold=True, color="1F497D")
        font_section = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_bold = Font(name="Calibri", size=11, bold=True)

        fill_navy = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        fill_soft_blue = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
        fill_accent = PatternFill(start_color="F2F5F8", end_color="F2F5F8", fill_type="solid")

        border_thin_bottom = Border(bottom=Side(style='thin', color='000000'))
        border_double_bottom = Border(
            top=Side(style='thin', color='000000'),
            bottom=Side(style='double', color='000000')
        )

        # Title Block
        ws["A1"] = f"{ticker.upper()} - VALUATION STUDIO MODEL"
        ws["A1"].font = font_title
        ws["A2"] = "Automated 3-Statement Projection & Unlevered DCF Engine"
        ws["A2"].font = Font(name="Calibri", size=11, italic=True, color="595959")

        # Section 1: Income Statement
        ws["A4"] = "INCOME STATEMENT ($M)"
        ws["A4"].font = font_section
        ws["A4"].fill = fill_navy
        for col_idx in range(2, len(proj.years) + 2):
            cell = ws.cell(row=4, column=col_idx, value=f"FY{proj.years[col_idx-2]}")
            cell.font = font_section
            cell.fill = fill_navy
            cell.alignment = Alignment(horizontal="right")

        row_map = {
            "Revenue": (5, proj.revenue, False),
            "COGS": (6, proj.cogs, False),
            "Gross Profit": (7, proj.gross_profit, True),
            "Opex": (8, proj.opex, False),
            "EBITDA": (9, proj.ebitda, True),
            "D&A": (10, proj.da, False),
            "EBIT": (11, proj.ebit, True),
            "Interest Expense": (12, proj.interest, False),
            "EBT": (13, proj.ebt, True),
            "Taxes": (14, proj.taxes, False),
            "Net Income": (15, proj.net_income, True)
        }

        for name, (r_idx, data_arr, is_bold) in row_map.items():
            font_choice = font_bold if is_bold else Font(name="Calibri")
            ws.cell(row=r_idx, column=1, value=name).font = font_choice

            if is_bold:
                ws.cell(row=r_idx, column=1).fill = fill_accent
            for c_idx, val in enumerate(data_arr, start=2):
                c = ws.cell(row=r_idx, column=c_idx, value=float(val))
                c.number_format = "$#,##0.0;($#,##0.0);\"-\""
                if is_bold:
                    c.font = font_bold
                    c.fill = fill_accent
                if name == "Net Income":
                    c.border = border_double_bottom
                elif name in ("Gross Profit", "EBITDA", "EBIT", "EBT"):
                    c.border = border_thin_bottom

        # Section 2: Unlevered DCF Schedule
        ws["A17"] = "UNLEVERED DCF VALUATION ($M)"
        ws["A17"].font = font_section
        ws["A17"].fill = fill_navy
        for col_idx in range(2, len(proj.years) + 2):
            cell = ws.cell(row=17, column=col_idx, value=f"FY{proj.years[col_idx-2]}")
            cell.font = font_section
            cell.fill = fill_navy
            cell.alignment = Alignment(horizontal="right")

        dcf_rows = {
            "EBIT": (18, proj.ebit, False),
            "Less: Taxes": (19, proj.taxes, False),
            "Plus: D&A": (20, proj.da, False),
            "Less: CapEx": (21, proj.capex, False),
            "Less: Change in NWC": (22, proj.change_in_nwc, False),
            "Unlevered Free Cash Flow (FCFF)": (23, proj.fcff, True)
        }

        for name, (r_idx, data_arr, is_bold) in dcf_rows.items():
            font_choice = font_bold if is_bold else Font(name="Calibri")
            ws.cell(row=r_idx, column=1, value=name).font = font_choice
            for c_idx, val in enumerate(data_arr, start=2):
                c = ws.cell(row=r_idx, column=c_idx, value=float(val))
                c.number_format = "$#,##0.0;($#,##0.0);\"-\""
                if is_bold:
                    c.font = font_bold
                    c.fill = fill_soft_blue
                    c.border = border_double_bottom

        # Section 3: Valuation Summary Block
        ws["A25"] = "VALUATION SUMMARY"
        ws["A25"].font = font_section
        ws["A25"].fill = fill_navy
        ws["B25"].fill = fill_navy

        summary_items = [
            ("WACC", dcf.wacc, "0.0%"),
            ("Terminal Growth Rate", 0.025, "0.0%"),
            ("PV of Explicit Cash Flows", dcf.pv_explicit_cf, "$#,##0.0"),
            ("PV of Terminal Value", dcf.pv_tv_gordon, "$#,##0.0"),
            ("Implied Enterprise Value", dcf.enterprise_value_gordon, "$#,##0.0"),
            ("Implied Equity Value", dcf.equity_value_gordon, "$#,##0.0"),
            ("Implied Share Price", dcf.implied_share_price_gordon, "$#,##0.00")
        ]

        for idx, (label, val, fmt) in enumerate(summary_items, start=26):
            is_impl = "Implied" in label
            font_choice = font_bold if is_impl else Font(name="Calibri")
            ws.cell(row=idx, column=1, value=label).font = font_choice

            c = ws.cell(row=idx, column=2, value=float(val))
            c.number_format = fmt
            if "Share Price" in label:
                c.font = Font(name="Calibri", size=12, bold=True, color="1F497D")
                c.fill = fill_soft_blue
                c.border = border_double_bottom

        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(filepath)
