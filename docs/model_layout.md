
# 🗺️ Excel Architecture & Line-Item Map

The `ExcelBridge` module programmatically generates an institutional `.xlsx` file. It does not use macros (`.xlsm`); instead, it injects direct values and standard accounting formulas.

## Sheet 1: 3-Statement & DCF

This single-sheet, fully integrated view prevents analysts from having to jump between tabs, matching the layout preferred by tier-one private equity and investment banking teams.

### Section A: Income Statement (Rows 4-15)

* **Revenue:** Driven by the dynamic consensus fade curve.
* **COGS & Opex:** Pegged to selected scenario margin targets.
* **Interest Expense:** Circularity-free formula based on the *beginning* debt balance of the period.

### Section B: Unlevered DCF (Rows 17-23)

* Calculates **Free Cash Flow to the Firm (FCFF)**.
* Reconciles NOPAT by subtracting changes in Net Working Capital (NWC) and Capital Expenditures.

### Section C: Valuation Summary (Rows 25-32)

* **WACC:** Displays the active discount rate.
* **PV of Cash Flows:** Uses standard Mid-Year Discounting factors.
* **Implied Share Price:** The final output, styled with an institutional Navy/Soft Blue highlight.

*Note: All cells containing assumptions are styled with standard blue font to indicate hardcodes, while formulas remain black, adhering to strict IB formatting standards.*
