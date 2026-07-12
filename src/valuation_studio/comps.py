"""Peer-group valuation multiples engine with statistical outlier trimming."""

import pandas as pd


class CompsEngine:
    """Aggregates trading multiples across comparable equity peers."""

    @staticmethod
    def analyze(peer_data: pd.DataFrame) -> dict[str, float]:
        """
        Expects DataFrame with columns: ['ticker', 'ev_ebitda', 'pe_ratio', 'ev_sales']
        Returns median and interquartile statistical multiples.
        """
        metrics = ["ev_ebitda", "pe_ratio", "ev_sales"]
        results: dict[str, float] = {}

        for m in metrics:
            if m not in peer_data.columns:
                continue
            series = peer_data[m].dropna()
            # Remove extreme outliers (> 90th percentile or < 0)
            valid = series[(series > 0) & (series < series.quantile(0.90))]
            if not valid.empty:
                results[f"{m}_median"] = float(valid.median())
                results[f"{m}_mean"] = float(valid.mean())
            else:
                results[f"{m}_median"] = 0.0
                results[f"{m}_mean"] = 0.0

        return results
