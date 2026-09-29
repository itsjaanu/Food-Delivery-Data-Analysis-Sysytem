
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="FoodLens — Delivery Analytics",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Styling --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0b1020; }
.block-container { padding: 1.8rem 3rem 3rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #10172b; border-right: 1px solid #202943; }
[data-testid="stSidebar"] * { color: #e8edf8; }
h1,h2,h3,h4 { font-family: 'Space Grotesk', sans-serif; color: #f7f9fc; }
p, label, .stMarkdown { color: #aeb8cc; }
.hero {
    background: linear-gradient(135deg, #151d38 0%, #10172b 60%, #182441 100%);
    border: 1px solid #263250; border-radius: 24px; padding: 30px 34px;
    box-shadow: 0 20px 60px rgba(0,0,0,.18);
}
.eyebrow { color:#8fa3ff; font-weight:700; letter-spacing:.12em; text-transform:uppercase; font-size:.75rem; }
.hero-title { font-family:'Space Grotesk'; font-size:2.65rem; line-height:1.05; color:#fff; margin:.45rem 0 .8rem; }
.hero-copy { font-size:1rem; color:#aeb8cc; max-width:720px; }
.kpi {
    background: linear-gradient(180deg,#141d34,#11182b);
    border:1px solid #263250; border-radius:18px; padding:20px;
    min-height:125px;
}
.kpi-label { color:#8e9bb3; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
.kpi-value { color:#fff; font-family:'Space Grotesk'; font-size:1.8rem; font-weight:700; margin-top:7px; }
.kpi-note { color:#6fd6b1; font-size:.78rem; margin-top:5px; }
.section { margin-top: 28px; margin-bottom: 12px; }
.insight {
    background:#121a2d; border:1px solid #263250; border-left:4px solid #8fa3ff;
    padding:16px 18px; border-radius:14px; margin-bottom:10px;
}
.insight b { color:#fff; }
.small { font-size:.85rem; color:#8794ab; }
div[data-testid="stMetric"] { background:#141d34; border:1px solid #263250; padding:14px 16px; border-radius:16px; }
div[data-testid="stMetric"] label { color:#8e9bb3; }
div[data-testid="stMetricValue"] { color:#fff; }
.stButton>button { border-radius:12px; border:1px solid #33415f; background:#19233d; color:#fff; }
.stButton>button:hover { border-color:#8fa3ff; color:#fff; }
</style>
""", unsafe_allow_html=True)

# -------------------- Data --------------------
@st.cache_data
def load_sample():
    return pd.read_csv(Path("data/food_delivery_sample.csv"), parse_dates=["order_date"])

def normalize_columns(data):
    d = data.copy()
    d.columns = [str(c).strip().lower().replace(" ", "_") for c in d.columns]
    return d

def prep_data(data):
    d = normalize_columns(data)
    if "order_date" in d.columns:
        d["order_date"] = pd.to_datetime(d["order_date"], errors="coerce")
    numeric = ["items","subtotal","delivery_fee","discount","total_amount","delivery_time_min","rating"]
    for c in numeric:
        if c in d.columns: d[c] = pd.to_numeric(d[c], errors="coerce")
    if "order_status" not in d.columns: d["order_status"] = "Delivered"
    if "total_amount" not in d.columns:
        if "subtotal" in d.columns: d["total_amount"] = d["subtotal"].fillna(0)
        else: d["total_amount"] = 0
    return d.dropna(how="all")

uploaded = st.sidebar.file_uploader("Upload your CSV dataset", type=["csv"])
data = prep_data(pd.read_csv(uploaded) if uploaded else load_sample())

st.sidebar.markdown("### Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Revenue", "Customers", "Delivery", "Food & Locations", "Dataset", "About"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown("**FoodLens**")
st.sidebar.caption("Food Delivery Data Analysis System")
st.sidebar.caption(f"{len(data):,} records loaded")

# -------------------- Helpers --------------------
def money(v):
    v = float(v or 0)
    if abs(v) >= 1_000_000: return f"₹{v/1_000_000:.2f}M"
    if abs(v) >= 100_000: return f"₹{v/100_000:.2f}L"
    return f"₹{v:,.0f}"

def delivered(d):
    if "order_status" in d:
        return d[d["order_status"].astype(str).str.lower().eq("delivered")].copy()
    return d.copy()

d = delivered(data)
total_orders = len(data)
revenue = d["total_amount"].sum()
avg_order = d["total_amount"].mean() if len(d) else 0
avg_rating = d["rating"].mean() if "rating" in d else 0
customers = d["customer_id"].nunique() if "customer_id" in d else 0

# -------------------- Overview --------------------
if page == "Overview":
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">FOOD DELIVERY INTELLIGENCE</div>
      <div class="hero-title">Turn delivery data into decisions. 🍔</div>
      <div class="hero-copy">FoodLens transforms raw order records into an interactive analytics workspace for revenue, customers, food preferences, locations, ratings and delivery performance.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section"></div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    cards = [
        ("TOTAL ORDERS", f"{total_orders:,}", "All records"),
        ("REVENUE", money(revenue), "Delivered orders"),
        ("AVG ORDER", money(avg_order), "Per delivered order"),
        ("CUSTOMERS", f"{customers:,}", "Unique customers"),
        ("AVG RATING", f"{avg_rating:.1f} ★", "Customer rating"),
    ]
    for col,(lab,val,note) in zip([c1,c2,c3,c4,c5],cards):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{lab}</div><div class="kpi-value">{val}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)

    st.markdown("### Performance snapshot")
    left,right = st.columns([1.6,1])
    with left:
        if "order_date" in d:
            trend = d.groupby(pd.Grouper(key="order_date", freq="MS")).agg(orders=("order_id","count"), revenue=("total_amount","sum")).reset_index()
            fig = px.area(trend, x="order_date", y="orders", template="plotly_dark", title="Monthly order volume")
            fig.update_traces(line_color="#8fa3ff", fillcolor="rgba(143,163,255,.18)")
            fig.update_layout(height=350, margin=dict(l=10,r=10,t=50,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with right:
        if "food_category" in d:
            cat = d.groupby("food_category").agg(orders=("order_id","count"), revenue=("total_amount","sum")).reset_index().sort_values("orders", ascending=False)
            fig = px.bar(cat.head(7), x="orders", y="food_category", orientation="h", template="plotly_dark", title="Top food categories")
            fig.update_layout(height=350, margin=dict(l=10,r=10,t=50,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_traces(marker_color="#ff9f6e")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Key insights")
    insights = []
    if "food_category" in d and len(d):
        x = d["food_category"].value_counts().index[0]
        insights.append(f"<b>Most ordered category:</b> {x} leads the order mix.")
    if "city" in d and len(d):
        x = d.groupby("city")["total_amount"].sum().idxmax()
        insights.append(f"<b>Revenue hotspot:</b> {x} contributes the most revenue in this dataset.")
    if "delivery_time_min" in d and "rating" in d and len(d) > 2:
        corr = d["delivery_time_min"].corr(d["rating"])
        direction = "negative" if corr < 0 else "positive"
        insights.append(f"<b>Delivery & ratings:</b> the Pearson correlation is {corr:.2f}, indicating a {direction} relationship.")
    if "order_status" in data:
        cancel = (data["order_status"].astype(str).str.lower()=="cancelled").mean()*100
        insights.append(f"<b>Cancellation rate:</b> {cancel:.1f}% of all recorded orders are marked cancelled.")
    for i in insights:
        st.markdown(f'<div class="insight">💡 {i}</div>', unsafe_allow_html=True)

# -------------------- Revenue --------------------
elif page == "Revenue":
    st.title("Revenue Intelligence 💰")
    st.caption("Understand how order volume translates into revenue.")
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Revenue", money(revenue))
    with c2: st.metric("Average order value", money(avg_order))
    with c3: st.metric("Discounts", money(d["discount"].sum()) if "discount" in d else "—")

    if "order_date" in d:
        monthly = d.groupby(pd.Grouper(key="order_date", freq="MS")).agg(revenue=("total_amount","sum"), orders=("order_id","count")).reset_index()
        fig = px.line(monthly, x="order_date", y="revenue", markers=True, template="plotly_dark", title="Revenue trend")
        fig.update_traces(line_color="#6fd6b1")
        fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    a,b = st.columns(2)
    with a:
        if "city" in d:
            city_rev = d.groupby("city")["total_amount"].sum().sort_values(ascending=False).reset_index()
            fig = px.bar(city_rev, x="city", y="total_amount", template="plotly_dark", title="Revenue by city")
            fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with b:
        if "payment_method" in d:
            pay = d["payment_method"].value_counts().reset_index()
            pay.columns = ["payment_method","orders"]
            fig = px.pie(pay, names="payment_method", values="orders", hole=.58, template="plotly_dark", title="Payment method mix")
            fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

# -------------------- Customers --------------------
elif page == "Customers":
    st.title("Customer Analytics 👥")
    st.caption("Explore customer frequency, spending and repeat behavior.")
    if "customer_id" in d:
        cust = d.groupby("customer_id").agg(
            orders=("order_id","count"),
            spend=("total_amount","sum"),
            avg_order=("total_amount","mean"),
            avg_rating=("rating","mean") if "rating" in d else ("total_amount","mean")
        ).reset_index()
        repeat = (cust["orders"] > 1).mean()*100
        c1,c2,c3 = st.columns(3)
        c1.metric("Unique customers", f"{len(cust):,}")
        c2.metric("Repeat customer share", f"{repeat:.1f}%")
        c3.metric("Top customer spend", money(cust["spend"].max()))
        a,b = st.columns(2)
        with a:
            fig = px.histogram(cust, x="orders", nbins=max(8,int(cust["orders"].max())), template="plotly_dark", title="Orders per customer")
            fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with b:
            fig = px.scatter(cust, x="orders", y="spend", size="spend", hover_data=["customer_id"], template="plotly_dark", title="Customer frequency vs spending")
            fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Your dataset needs a customer_id column for customer analytics.")

# -------------------- Delivery --------------------
elif page == "Delivery":
    st.title("Delivery Performance 🚚")
    st.caption("Analyze speed, ratings and the relationship between delivery experience and satisfaction.")
    if "delivery_time_min" in d:
        c1,c2,c3 = st.columns(3)
        c1.metric("Average delivery", f"{d.delivery_time_min.mean():.1f} min")
        c2.metric("Fastest delivery", f"{d.delivery_time_min.min():.0f} min")
        c3.metric("Slowest delivery", f"{d.delivery_time_min.max():.0f} min")
        a,b = st.columns(2)
        with a:
            fig = px.histogram(d, x="delivery_time_min", nbins=20, template="plotly_dark", title="Delivery time distribution")
            fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with b:
            if "rating" in d:
                fig = px.scatter(d.sample(min(1500,len(d)), random_state=42), x="delivery_time_min", y="rating", trendline="ols", opacity=.55, template="plotly_dark", title="Delivery time vs rating")
                fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Your dataset needs delivery_time_min for delivery analytics.")

# -------------------- Food & Locations --------------------
elif page == "Food & Locations":
    st.title("Food & Location Intelligence 🍕📍")
    st.caption("See what people order and where the business performs.")
    a,b = st.columns(2)
    with a:
        if "food_category" in d:
            cat = d.groupby("food_category").agg(orders=("order_id","count"), revenue=("total_amount","sum")).reset_index().sort_values("revenue", ascending=False)
            fig = px.bar(cat, x="revenue", y="food_category", orientation="h", template="plotly_dark", title="Revenue by food category")
            fig.update_layout(height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with b:
        if "city" in d:
            city = d.groupby("city").agg(orders=("order_id","count"), revenue=("total_amount","sum")).reset_index().sort_values("orders", ascending=False)
            fig = px.bar(city, x="orders", y="city", orientation="h", template="plotly_dark", title="Orders by city")
            fig.update_layout(height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    if "restaurant" in d and "food_category" in d:
        rest = d.groupby("restaurant").agg(orders=("order_id","count"), revenue=("total_amount","sum")).reset_index().sort_values("revenue", ascending=False)
        st.subheader("Restaurant performance")
        st.dataframe(rest, use_container_width=True, hide_index=True)

# -------------------- Dataset --------------------
elif page == "Dataset":
    st.title("Dataset Explorer 📁")
    st.caption("Upload a CSV from the sidebar or inspect the included sample dataset.")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Rows", f"{len(data):,}")
    c2.metric("Columns", f"{len(data.columns):,}")
    c3.metric("Missing values", f"{int(data.isna().sum().sum()):,}")
    c4.metric("Duplicate rows", f"{int(data.duplicated().sum()):,}")
    st.subheader("Data preview")
    st.dataframe(data.head(100), use_container_width=True, hide_index=True)
    st.subheader("Column summary")
    summary = pd.DataFrame({
        "column": data.columns,
        "dtype": [str(data[c].dtype) for c in data.columns],
        "missing": [int(data[c].isna().sum()) for c in data.columns],
        "unique": [int(data[c].nunique(dropna=True)) for c in data.columns],
    })
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.download_button("Download current dataset", data=data.to_csv(index=False).encode("utf-8"), file_name="foodlens_dataset.csv", mime="text/csv")

# -------------------- About --------------------
else:
    st.title("About FoodLens 🍔")
    st.markdown("""
    **FoodLens** is a Python-based Food Delivery Data Analysis System designed as an academic project for **Data Analysis Essentials**.

    ### What the project demonstrates
    - Data loading and cleaning with **Pandas**
    - Descriptive and exploratory data analysis
    - Interactive visualization with **Plotly**
    - Customer, revenue, food, location and delivery analytics
    - CSV dataset upload and automatic dashboard refresh
    - A responsive, presentation-ready analytics interface

    ### Expected dataset columns
    The sample dataset uses:
    `order_id`, `order_date`, `customer_id`, `city`, `restaurant`,
    `food_category`, `items`, `subtotal`, `delivery_fee`, `discount`,
    `total_amount`, `delivery_time_min`, `rating`, `payment_method`, `order_status`.

    You can upload a CSV with similar columns. The dashboard gracefully hides analyses when a required field is missing.
    """)
    st.info("Tip: For your final college presentation, explain the pipeline as Raw Data → Cleaning → Analysis → Visualization → Insights.")
