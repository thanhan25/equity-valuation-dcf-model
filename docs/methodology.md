
# Valuation Methodology & Accounting Identities

## 1. Balance Sheet Balancing Mechanism

To prevent balance sheet divergence during multi-year projections, the model implements an automated Cash and Revolving Credit Facility (Revolver) plug:

* **Operational Cash Requirement:** Maintained at a minimum baseline of $5\%$ of projected revenue.
* **Cash Deficits:** When Free Cash Flow to Equity ($FCFE$) is insufficient to maintain baseline operating cash, the deficit is automatically borrowed from the Revolver line item.
* **Cash Surpluses:** Excess cash generated above operating requirements is prioritized to pay down existing debt obligations before accumulating in Cash & Cash Equivalents.

## 2. Terminal Value Calculations

The model implements a dual-methodology valuation cross-check:

1. **Gordon Growth Perpetuity Method:**

   $$
   TV_{Gordon} = \frac{FCFF_{t+1}}{WACC - g}
   $$
2. **Exit Multiple Method:** Implies enterprise value based on prevailing peer median $EV/EBITDA$ trading multiples:

   $$
   TV_{Multiple} = EBITDA_t \cdot (EV/EBITDA)_{target}
   $$
