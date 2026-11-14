import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from analysis import load_and_prepare, calculate_kpis

def test_kpi_calculations():
    sample = pd.DataFrame([{
        "Date":"2026-01-01","Platform":"Amazon","Product":"Demo","Category":"Home",
        "Campaign":"Test","Clicks":100,"Orders":5,"Sales_INR":5000,
        "Commission_Earned_INR":250,"Reversals_INR":20,"Marketing_Expenses_INR":30
    }])
    prepared = load_and_prepare(sample.to_csv(index=False).encode("utf-8"))
    k = calculate_kpis(prepared)
    assert k["sales"] == 5000
    assert k["net_commission"] == 230
    assert k["net_profit"] == 200
    assert k["conversion_rate_pct"] == 5
