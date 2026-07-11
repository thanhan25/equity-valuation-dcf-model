"""Discounted Cash Flow (DCF) valuation engine and sensitivity matrix generator."""
from dataclasses import dataclass

import numpy as np

from valuation_studio.statements import Projections


@dataclass
class DCFResult:
    wacc: float
    pv_explicit_cf: float
    terminal_value_gordon: float
    pv_tv_gordon: float
    enterprise_value_gordon: float
    equity_value_gordon: float
    implied_share_price_gordon: float
    implied_ev_ebitda_multiple: float
    sensitivity_matrix: np.ndarray  # WACC vs Terminal Growth Rate
    wacc_range: np.ndarray
    growth_range: np.ndarray


class DCFEngine:
    """Executes valuation modeling, discounting, and two-variable sensitivity testing."""
    @staticmethod
    def calculate_wacc(cost_of_equity: float, cost_of_debt: float, tax_rate: float,
                       equity_val: float, debt_val: float) -> float:
        total_cap = equity_val + debt_val
        if total_cap == 0:
            return 0.10
        we = equity_val / total_cap
        wd = debt_val / total_cap
        return float(we * cost_of_equity + wd * cost_of_debt * (1.0 - tax_rate))

    @classmethod
    def value(cls, proj: Projections, wacc: float, terminal_growth: float,
              shares_outstanding: float, current_cash: float, current_debt: float) -> DCFResult:

        n_years = len(proj.fcff)
        # Mid-year convention discounting: t = 0.5, 1.5, ..., n - 0.5
        discount_factors = np.array([
            1.0 / ((1.0 + wacc) ** (t - 0.5)) for t in range(1, n_years + 1)
        ])
        pv_cf = np.sum(proj.fcff * discount_factors)

        # Gordon Growth Terminal Value
        final_fcff = proj.fcff[-1]
        tv_gordon = (final_fcff * (1.0 + terminal_growth)) / (wacc - terminal_growth)
        pv_tv_gordon = tv_gordon / ((1.0 + wacc) ** n_years)

        ev_gordon = float(pv_cf + pv_tv_gordon)
        net_debt = current_debt - current_cash
        eq_gordon = ev_gordon - net_debt
        share_price_gordon = max(0.0, eq_gordon / shares_outstanding)

        implied_multiple = ev_gordon / proj.ebitda[-1] if proj.ebitda[-1] > 0 else 0.0

        # Generate 2D Sensitivity Matrix (WACC rows vs Growth Rate columns)
        wacc_steps = np.linspace(max(0.04, wacc - 0.02), wacc + 0.02, 5)
        growth_steps = np.linspace(max(0.005, terminal_growth - 0.01), terminal_growth + 0.01, 5)
        matrix = np.zeros((5, 5))

        for r, w in enumerate(wacc_steps):
            for c, g in enumerate(growth_steps):
                if w <= g:
                    matrix[r, c] = 0.0
                    continue
                df_sens = np.array([
                    1.0 / ((1.0 + w) ** (t - 0.5)) for t in range(1, n_years + 1)
                ])
                pv_c = np.sum(proj.fcff * df_sens)
                tv_c = (proj.fcff[-1] * (1.0 + g)) / (w - g)
                pv_tv_c = tv_c / ((1.0 + w) ** n_years)
                ev_c = pv_c + pv_tv_c
                eq_c = ev_c - net_debt
                matrix[r, c] = max(0.0, eq_c / shares_outstanding)

        return DCFResult(
            wacc=wacc,
            pv_explicit_cf=float(pv_cf),
            terminal_value_gordon=float(tv_gordon),
            pv_tv_gordon=float(pv_tv_gordon),
            enterprise_value_gordon=ev_gordon,
            equity_value_gordon=eq_gordon,
            implied_share_price_gordon=share_price_gordon,
            implied_ev_ebitda_multiple=implied_multiple,
            sensitivity_matrix=matrix,
            wacc_range=wacc_steps,
            growth_range=growth_steps
        )
