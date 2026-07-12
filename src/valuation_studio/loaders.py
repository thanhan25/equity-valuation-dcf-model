"""Data ingestion module for pulling standardized financials from APIs or CSVs."""

from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
from pydantic import BaseModel, Field


class FinancialStatementSchema(BaseModel):
    """Enforces rigorous schema validation on historical financials and estimates."""

    years: list[int] = Field(..., min_length=3)
    revenue: list[float]
    cogs: list[float]
    opex: list[float]
    da: list[float]
    tax_rate: float = Field(default=0.21, ge=0.0, le=0.50)
    capex_pct_rev: float = Field(default=0.05)
    nwc_pct_rev: float = Field(default=0.10)
    initial_cash: float
    initial_debt: float
    shares_outstanding: float
    current_price: float

    # Wall Street Consensus Estimates
    consensus_growth_y1: float = Field(default=0.15)
    consensus_growth_y2: float = Field(default=0.10)
    wall_st_target: float = Field(default=0.0)


class DataLoader:
    """Handles data fetching, standardization, and schema verification."""

    @staticmethod
    def from_csv(filepath: str | Path) -> FinancialStatementSchema:
        df = pd.read_csv(filepath)
        required_cols = {"metric", "y1", "y2", "y3"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"CSV missing required columns: {required_cols - set(df.columns)}")

        data_map: dict[str, Any] = {}
        for _, row in df.iterrows():
            data_map[str(row["metric"]).lower()] = [
                float(row["y1"]),
                float(row["y2"]),
                float(row["y3"]),
            ]

        return FinancialStatementSchema(
            years=[int(x) for x in df.columns[1:4]],
            revenue=data_map["revenue"],
            cogs=data_map["cogs"],
            opex=data_map["opex"],
            da=data_map["da"],
            initial_cash=data_map.get("cash", [1000.0])[0],
            initial_debt=data_map.get("debt", [2000.0])[0],
            shares_outstanding=data_map.get("shares", [1000.0])[0],
            current_price=data_map.get("price", [100.0])[0],
        )

    @staticmethod
    def from_yfinance(ticker: str) -> FinancialStatementSchema:
        stock = yf.Ticker(ticker)
        inc = stock.financials
        bs = stock.balance_sheet
        info = stock.info

        if inc.empty or bs.empty:
            raise RuntimeError(f"Could not retrieve complete financials for {ticker}")

        years = [int(str(col)[:4]) for col in inc.columns[:3]][::-1]

        def get_row(df: pd.DataFrame, names: list[str], default: float = 0.0) -> list[float]:
            for name in names:
                if name in df.index:
                    vals = df.loc[name].iloc[:3].values[::-1]
                    return [float(x) if pd.notna(x) else default for x in vals]
            return [default] * 3

        revenue = get_row(inc, ["Total Revenue", "Operating Revenue"])
        cogs = get_row(inc, ["Cost Of Revenue", "Reconciled Cost Of Revenue"])
        opex = get_row(inc, ["Operating Expense", "Selling General And Administration"])
        da = get_row(inc, ["Reconciled Depreciation", "Depreciation And Amortization"])

        cash = (
            float(bs.loc["Cash And Cash Equivalents"].iloc[0])
            if "Cash And Cash Equivalents" in bs.index
            else 5000.0
        )
        debt = float(bs.loc["Total Debt"].iloc[0]) if "Total Debt" in bs.index else 10000.0
        shares = float(info.get("sharesOutstanding") or 1e9)
        price = float(info.get("currentPrice") or 100.0)

        # Dynamic Consensus Extraction (Graceful Fallbacks)
        y1_growth = float(info.get("revenueGrowth") or 0.15)
        earn_growth = float(info.get("earningsGrowth") or y1_growth)
        y2_growth = (y1_growth + earn_growth) / 2.0  # Blend towards earnings growth
        target_price = float(info.get("targetMeanPrice") or price)

        return FinancialStatementSchema(
            years=years,
            revenue=revenue,
            cogs=cogs,
            opex=opex,
            da=da,
            initial_cash=cash,
            initial_debt=debt,
            shares_outstanding=shares,
            current_price=price,
            consensus_growth_y1=y1_growth,
            consensus_growth_y2=y2_growth,
            wall_st_target=target_price,
        )
