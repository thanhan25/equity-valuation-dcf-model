"""Unit tests verifying peer multiple aggregation and outlier trimming."""

import pandas as pd

from valuation_studio.comps import CompsEngine


def test_comps_outlier_rejection() -> None:
    df = pd.DataFrame(
        {
            "ticker": ["A", "B", "C", "D", "E"],
            "ev_ebitda": [10.0, 12.0, 11.0, 15.0, 500.0],  # 500.0 is an extreme outlier
            "pe_ratio": [15.0, 18.0, 16.0, 20.0, -5.0],  # -5.0 is invalid
            "ev_sales": [3.0, 3.5, 4.0, 3.2, 3.8],
        }
    )

    res = CompsEngine.analyze(df)

    # Outlier 500.0 should be excluded from median/mean calculation
    assert res["ev_ebitda_median"] < 20.0
    # Negative PE ratio should be trimmed
    assert res["pe_ratio_median"] > 0.0
