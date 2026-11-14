import sys
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from analysis import load_and_prepare, calculate_kpis, build_product_summary

st.set_page_config(page_title="Smart Finds Telugu | Affiliate Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top:1.5rem; padding-bottom:2rem;}
[data-testid="stMetric"] {background:#f5f7fb;border:1px solid #e5e9f2;padding:13px 15px;border-radius:12px;}
div[data-testid="stMetricValue"] {font-size:1.45rem;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Smart Finds Telugu")
st.subheader("Affiliate Marketing Analytics Dashboard")
st.caption("Amazon · Flipkart · Meesho | Track traffic, orders, commissions and profitability")

DEFAULT_CSV = ROOT / "data" / "sample_affiliate_data.csv"

with st.sidebar:
    st.header("Data & filters")
    uploaded_file = st.file_uploader("Upload your affiliate CSV", type=["csv"])
    st.caption("Use the included sample data to explore the dashboard, or upload your own report.")
    st.divider()

try:
    raw = pd.read_csv(uploaded_file) if uploaded_file is not None else pd.read_csv(DEFAULT_CSV)
    data = load_and_prepare(raw.to_csv(index=False).encode("utf-8"))
except Exception as exc:
    st.error(f"Could not load data: {exc}")
    st.stop()

if data.empty:
    st.warning("The selected data contains no valid rows.")
    st.stop()

date_min = data["Date"].min().date()
date_max = data["Date"].max().date()
with st.sidebar:
    date_range = st.date_input("Date range", value=(date_min, date_max), min_value=date_min, max_value=date_max)
    platforms = sorted(data["Platform"].dropna().unique().tolist())
    selected_platforms = st.multiselect("Platform", platforms, default=platforms)
    products = sorted(data["Product"].dropna().unique().tolist())
    selected_products = st.multiselect("Product", products, default=products)
    campaigns = sorted(data["Campaign"].dropna().unique().tolist())
    selected_campaigns = st.multiselect("Campaign", campaigns, default=campaigns)

filtered = data.copy()
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start = pd.Timestamp(date_range[0])
    end = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    filtered = filtered[(filtered["Date"] >= start) & (filtered["Date"] <= end)]
filtered = filtered[
    filtered["Platform"].isin(selected_platforms)
    & filtered["Product"].isin(selected_products)
    & filtered["Campaign"].isin(selected_campaigns)
]

if filtered.empty:
    st.info("No rows match the current filters. Adjust the selections in the sidebar.")
    st.stop()

is_demo = uploaded_file is None
if is_demo:
    st.warning("DEMO DATA: All included clicks, orders, sales and commissions are synthetic examples, not actual affiliate earnings.")

k = calculate_kpis(filtered)
fmt = lambda value: f"₹{value:,.2f}"

st.markdown("### Business overview")
a,b,c,d = st.columns(4)
a.metric("Product sales", fmt(k["sales"]))
b.metric("Affiliate clicks", f'{k["clicks"]:,}')
c.metric("Orders", f'{k["orders"]:,}')
d.metric("Conversion rate", f'{k["conversion_rate_pct"]:.2f}%')

e,f,g,h = st.columns(4)
e.metric("Commission earned", fmt(k["commission"]))
f.metric("Commission reversals", fmt(k["reversals"]))
g.metric("Marketing expenses", fmt(k["expenses"]))
h.metric("Net profit", fmt(k["net_profit"]), help="Commission earned − reversals − recorded marketing expenses")

st.caption(f"Net commission: {fmt(k['net_commission'])}  |  Reporting rows: {len(filtered):,}")
st.divider()

left, right = st.columns(2)
with left:
    st.markdown("### Monthly sales and commission")
    monthly = filtered.set_index("Date").resample("MS")[["Sales_INR","Commission_Earned_INR","Reversals_INR","Marketing_Expenses_INR"]].sum()
    monthly = monthly.rename(columns={
        "Sales_INR":"Product sales",
        "Commission_Earned_INR":"Commission",
        "Reversals_INR":"Reversals",
        "Marketing_Expenses_INR":"Expenses"
    })
    st.line_chart(monthly)
with right:
    st.markdown("### Commission by platform")
    by_platform = filtered.groupby("Platform")[["Commission_Earned_INR","Reversals_INR","Marketing_Expenses_INR"]].sum()
    by_platform = by_platform.rename(columns={
        "Commission_Earned_INR":"Commission",
        "Reversals_INR":"Reversals",
        "Marketing_Expenses_INR":"Marketing expenses"
    })
    st.bar_chart(by_platform)

left, right = st.columns(2)
with left:
    st.markdown("### Top products by attributed sales")
    product_sales = filtered.groupby("Product")["Sales_INR"].sum().sort_values(ascending=False).head(10)
    st.bar_chart(product_sales)
with right:
    st.markdown("### Campaign clicks and orders")
    campaign_summary = filtered.groupby("Campaign")[["Clicks","Orders"]].sum().sort_values("Clicks", ascending=False)
    st.bar_chart(campaign_summary)

st.markdown("### Product performance detail")
product_summary = build_product_summary(filtered)
st.dataframe(product_summary, use_container_width=True, hide_index=True)

st.markdown("### Filtered transaction data")
st.dataframe(filtered.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
st.download_button(
    "⬇️ Download filtered records (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="smart_finds_filtered_affiliate_data.csv",
    mime="text/csv"
)

with st.expander("Metric definitions and data assumptions"):
    st.markdown("""
    - **Product sales:** attributed order value. This is not the affiliate's income.
    - **Commission earned:** commission amount entered in the report.
    - **Reversals:** commission removed due to returns, cancellations or rejected orders.
    - **Net commission:** commission earned minus reversals.
    - **Marketing expenses:** recorded promotion, advertising or content costs.
    - **Net profit:** net commission minus recorded marketing expenses. This is a simplified contribution measure before tax and unrecorded costs.
    - **Conversion rate:** total orders divided by total clicks, multiplied by 100.

    Actual affiliate attribution, commission rates, reporting fields and payment rules differ by platform. The sample rates are illustrative only.
    """)

st.caption("Built with Python · Pandas · NumPy · Streamlit | Smart Finds Telugu")
