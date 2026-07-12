"""Unit tests verifying accounting identities and balance sheet integrity."""

import numpy as np
from valuation_studio.loaders import FinancialStatementSchema
from valuation_studio.statements import FinancialModel


def test_accounting_identities() -> None:
    schema = FinancialStatementSchema(
        years=[2021, 2022, 2023],
        revenue=[100.0, 120.0, 150.0],
        cogs=[50.0, 55.0, 65.0],
        opex=[20.0, 22.0, 25.0],
        da=[5.0, 6.0, 8.0],
        initial_cash=10.0,
        initial_debt=20.0,
        shares_outstanding=10.0,
        current_price=50.0,
    )

    model = FinancialModel(schema)
    proj = model.project(forecast_years=5, rev_growth=0.10, ebitda_margin=0.40)

    # Verify array lengths match forecast horizon
    assert len(proj.revenue) == 5
    assert len(proj.net_income) == 5
    assert len(proj.fcff) == 5

    # Verify gross profit identity: Revenue - COGS == Gross Profit
    np.testing.assert_allclose(proj.revenue - proj.cogs, proj.gross_profit, rtol=1e-5)

    # Verify EBIT identity: Gross Profit - Opex == EBITDA; EBITDA - D&A == EBIT
    np.testing.assert_allclose(proj.gross_profit - proj.opex, proj.ebitda, rtol=1e-5)
    np.testing.assert_allclose(proj.ebitda - proj.da, proj.ebit, rtol=1e-5)

    # Verify non-negative operating cash plug
    assert np.all(proj.cash >= 0.0)
