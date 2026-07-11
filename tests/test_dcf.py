"""Unit tests for valuation discounting and sensitivity grid dimensions."""
import numpy as np
from valuation_studio.dcf import DCFEngine
from valuation_studio.statements import Projections


def test_dcf_valuation_and_sensitivity() -> None:
    proj = Projections(
        years=[2024, 2025, 2026, 2027, 2028],
        ebitda=np.array([100.0, 110.0, 120.0, 130.0, 140.0]),
        fcff=np.array([50.0, 55.0, 60.0, 65.0, 70.0]),
        cash=np.array([20.0]*5),
        debt=np.array([10.0]*5)
    )

    wacc = 0.10
    g = 0.025
    shares = 10.0

    res = DCFEngine.value(proj, wacc, g, shares, current_cash=20.0, current_debt=10.0)

    # Verify PV is strictly positive
    assert res.pv_explicit_cf > 0.0
    assert res.enterprise_value_gordon > res.pv_explicit_cf

    # Verify net debt adjustment: Equity Value == Enterprise Value - (Debt - Cash)
    expected_eq = res.enterprise_value_gordon - (-10.0)
    assert np.isclose(res.equity_value_gordon, expected_eq, rtol=1e-5)

    # Verify 5x5 sensitivity matrix shape
    assert res.sensitivity_matrix.shape == (5, 5)
    assert np.all(res.sensitivity_matrix >= 0.0)
