"""Reusable data loading, validation and KPI calculations."""
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "Date", "Platform", "Product", "Category", "Campaign", "Clicks", "Orders",
    "Sales_INR", "Commission_Earned_INR", "Reversals_INR", "Marketing_Expenses_INR"
]
NUMERIC_COLUMNS = [
    "Clicks", "Orders", "Sales_INR", "Commission_Earned_INR",
    "Reversals_INR", "Marketing_Expenses_INR"
]

def load_and_prepare(source):
    """Load a CSV path or file-like object and return validated analytics data."""
    df = pd.read_csv(source)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing))
    df = df[REQUIRED_COLUMNS].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df.dropna(subset=["Date"])
    for col in ["Clicks", "Orders", "Sales_INR", "Commission_Earned_INR",
                "Reversals_INR", "Marketing_Expenses_INR"]:
        df[col] = df[col].clip(lower=0)
    df["Net_Commission_INR"] = df["Commission_Earned_INR"] - df["Reversals_INR"]
    df["Net_Profit_INR"] = df["Net_Commission_INR"] - df["Marketing_Expenses_INR"]
    df["Conversion_Rate_Pct"] = np.where(
        df["Clicks"] > 0, df["Orders"] / df["Clicks"] * 100, 0
    )
    return df

def calculate_kpis(df):
    clicks = int(df["Clicks"].sum())
    orders = int(df["Orders"].sum())
    commission = float(df["Commission_Earned_INR"].sum())
    reversals = float(df["Reversals_INR"].sum())
    expenses = float(df["Marketing_Expenses_INR"].sum())
    return {
        "sales": float(df["Sales_INR"].sum()),
        "clicks": clicks,
        "orders": orders,
        "conversion_rate_pct": (orders / clicks * 100) if clicks else 0.0,
        "commission": commission,
        "reversals": reversals,
        "net_commission": commission - reversals,
        "expenses": expenses,
        "net_profit": commission - reversals - expenses,
    }

def build_product_summary(df):
    result = df.groupby(["Product", "Platform"], as_index=False).agg(
        Clicks=("Clicks", "sum"),
        Orders=("Orders", "sum"),
        Product_Sales_INR=("Sales_INR", "sum"),
        Commission_INR=("Commission_Earned_INR", "sum"),
        Reversals_INR=("Reversals_INR", "sum"),
        Marketing_Expenses_INR=("Marketing_Expenses_INR", "sum"),
    )
    result["Net_Profit_INR"] = (
        result["Commission_INR"] - result["Reversals_INR"] - result["Marketing_Expenses_INR"]
    )
    result["Conversion_Rate_Pct"] = np.where(
        result["Clicks"] > 0, result["Orders"] / result["Clicks"] * 100, 0
    )
    return result.sort_values("Product_Sales_INR", ascending=False)
