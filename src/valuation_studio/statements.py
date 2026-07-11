"""Three-statement projection engine with dynamic balance sheet plug (Cash/Revolver)."""
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class Projections:
    years: list[int]
    revenue: np.ndarray = field(default_factory=lambda: np.array([]))
    cogs: np.ndarray = field(default_factory=lambda: np.array([]))
    gross_profit: np.ndarray = field(default_factory=lambda: np.array([]))
    opex: np.ndarray = field(default_factory=lambda: np.array([]))
    ebitda: np.ndarray = field(default_factory=lambda: np.array([]))
    da: np.ndarray = field(default_factory=lambda: np.array([]))
    ebit: np.ndarray = field(default_factory=lambda: np.array([]))
    interest: np.ndarray = field(default_factory=lambda: np.array([]))
    ebt: np.ndarray = field(default_factory=lambda: np.array([]))
    taxes: np.ndarray = field(default_factory=lambda: np.array([]))
    net_income: np.ndarray = field(default_factory=lambda: np.array([]))

    # Balance Sheet & Cash Flow
    capex: np.ndarray = field(default_factory=lambda: np.array([]))
    nwc: np.ndarray = field(default_factory=lambda: np.array([]))
    change_in_nwc: np.ndarray = field(default_factory=lambda: np.array([]))
    fcff: np.ndarray = field(default_factory=lambda: np.array([]))
    cash: np.ndarray = field(default_factory=lambda: np.array([]))
    debt: np.ndarray = field(default_factory=lambda: np.array([]))


class FinancialModel:
    """Projects Income Statement, Balance Sheet, and Cash Flow Statement."""
    def __init__(self, schema_data: Any):
        self.data = schema_data

    def project(self, forecast_years: int = 5, rev_growth: float = 0.15,
                ebitda_margin: float = 0.40, tax_rate: float = 0.21,
                interest_rate: float = 0.05) -> Projections:

        last_yr = self.data.years[-1]
        proj_years = [last_yr + i for i in range(1, forecast_years + 1)]

        # Revenue progression
        base_rev = self.data.revenue[-1]
        rev = np.array([base_rev * ((1 + rev_growth) ** i) for i in range(1, forecast_years + 1)])

        # Core margins
        ebitda = rev * ebitda_margin
        da = rev * 0.04
        ebit = ebitda - da

        # Working capital and CapEx
        capex = rev * self.data.capex_pct_rev
        nwc = rev * self.data.nwc_pct_rev
        prev_nwc = self.data.revenue[-1] * self.data.nwc_pct_rev
        change_nwc = np.zeros(forecast_years)
        for i in range(forecast_years):
            curr = nwc[i]
            change_nwc[i] = curr - (prev_nwc if i == 0 else nwc[i - 1])

        # Debt and Cash balancing schedule (Iterative plug)
        cash = np.zeros(forecast_years)
        debt = np.zeros(forecast_years)
        interest = np.zeros(forecast_years)
        ebt = np.zeros(forecast_years)
        taxes = np.zeros(forecast_years)
        net_income = np.zeros(forecast_years)
        fcff = np.zeros(forecast_years)

        curr_cash = self.data.initial_cash
        curr_debt = self.data.initial_debt
        min_cash_req = rev * 0.05  # Maintain 5% of revenue as operational cash

        for i in range(forecast_years):
            # Interest based on beginning debt balance
            intr = curr_debt * interest_rate
            interest[i] = intr

            ebt_val = ebit[i] - intr
            tax_val = max(0.0, ebt_val * tax_rate)
            ni_val = ebt_val - tax_val

            ebt[i] = ebt_val
            taxes[i] = tax_val
            net_income[i] = ni_val

            # Unlevered Free Cash Flow (FCFF) calculation
            # FCFF = EBIT * (1 - t) + D&A - CapEx - Delta NWC
            nopat = ebit[i] * (1.0 - tax_rate)
            fcff[i] = nopat + da[i] - capex[i] - change_nwc[i]

            # Cash Flow Available for Debt Service / Cash Accumulation
            # Free Cash Flow to Equity (FCFE proxy before borrowing/repayment)
            fcfe_pre = ni_val + da[i] - capex[i] - change_nwc[i]

            tentative_cash = curr_cash + fcfe_pre
            if tentative_cash < min_cash_req[i]:
                # Draw on revolver/debt to meet minimum operating cash
                borrowing = min_cash_req[i] - tentative_cash
                curr_debt += borrowing
                curr_cash = min_cash_req[i]
            else:
                # Pay down debt with excess cash above minimum requirements
                excess_cash = tentative_cash - min_cash_req[i]
                paydown = min(curr_debt, excess_cash)
                curr_debt -= paydown
                curr_cash = tentative_cash - paydown

            cash[i] = curr_cash
            debt[i] = curr_debt

        cogs = rev * (1.0 - ebitda_margin - 0.10)
        gross_profit = rev - cogs
        opex = gross_profit - ebitda

        return Projections(
            years=proj_years, revenue=rev, cogs=cogs, gross_profit=gross_profit,
            opex=opex, ebitda=ebitda, da=da, ebit=ebit, interest=interest,
            ebt=ebt, taxes=taxes, net_income=net_income, capex=capex,
            nwc=nwc, change_in_nwc=change_nwc, fcff=fcff, cash=cash, debt=debt
        )
