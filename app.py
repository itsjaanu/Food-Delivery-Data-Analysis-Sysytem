import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="FoodLens — Zomato Restaurant Analytics",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .stApp { background: #0b1020; }
    [data-testid="stSidebar"] { background: #111827; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px; }
    .hero {
        padding: 1.4rem 1.6rem;
        border: 1px solid #263247;
        border-radius: 18px;
        background: linear-gradient(135deg, #121a2b, #18233a);
        margin-bottom: 1rem;
    }
    .hero h1 { margin: 0; font-size: 2.3rem; }
    .hero p { color: #aeb9cc; margin: .45rem 0 0; }
    .metric-card {
        background: #121a2b;
        border: 1px solid #263247;
        border-radius: 14px;
        padding: 1rem;
    }
    .section-title { margin-top: .6rem; margin-bottom: .3rem; }
    div[data-testid="stMetric"] {
        background: #121a2b;
        border: 1px solid #263247;
        padding: 12px;
        border-radius: 14px;
    }
</style>
""", unsafe_allow_html=True)

DATA_PATH = "data/Zomato_Restaurant_Data2024_202612.csv"

EXPECTED = [
    "Order_ID", "Order_Date", "Year", "Customer_ID", "Restaurant_ID",
    "Restaurant_Name", "City", "Area", "Cuisine", "Rating", "Rating_Count",
    "Average_Cost_for_Two_INR", "Online_Delivery", "Table_Booking",
    "Restaurant_Type", "Orders_Count", "Average_Order_Value_INR",
    "Discount_Percent", "Discount_Amount_INR", "Delivery_Fee_INR",
    "Estimated_Delivery_Minutes", "Order_Status", "Payment_Method",
    "Gross_Order_Value_INR", "Net_Order_Value_INR"
]

@st.cache_data(show_spinner="Loading the 1,000,000-row Zomato dataset…")
def load_data(path):
    df = pd.read_csv(path, low_memory=False)
    missing = [c for c in EXPECTED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    df["Order_Date"] = pd.to_datetime(df["Order_Date"], dayfirst=True, errors="coerce")

    numeric_cols = [
        "Year", "Rating", "Rating_Count", "Average_Cost_for_Two_INR",
        "Orders_Count", "Average_Order_Value_INR", "Discount_Percent",
        "Discount_Amount_INR", "Delivery_Fee_INR",
        "Estimated_Delivery_Minutes", "Gross_Order_Value_INR",
        "Net_Order_Value_INR"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Keep a clean copy for analysis.
    df = df.dropna(subset=["Order_ID"]).copy()
    return df

try:
    df = load_data(DATA_PATH)
except Exception as e:
    st.error(f"Could not load the Zomato dataset: {e}")
    st.stop()

# ---------- Sidebar ----------
st.sidebar.title("🍽️ FoodLens")
st.sidebar.caption("Zomato Restaurant Data Analytics")
st.sidebar.divider()

page = st.sidebar.radio(
    "Dashboard",
    ["Overview", "Revenue", "Customers", "Delivery", "Restaurants & Food", "Data Explorer", "About"]
)

st.sidebar.divider()
st.sidebar.markdown("### Dataset")
st.sidebar.write(f"**Rows:** {len(df):,}")
st.sidebar.write(f"**Columns:** {len(df.columns)}")
if df["Order_Date"].notna().any():
    st.sidebar.write(
        f"**Period:** {df['Order_Date'].min():%d %b %Y} – {df['Order_Date'].max():%d %b %Y}"
    )

# ---------- Filters ----------
st.sidebar.markdown("### Filters")

years = sorted(df["Year"].dropna().astype(int).unique().tolist())
selected_years = st.sidebar.multiselect("Year", years, default=years)

cities = sorted(df["City"].dropna().astype(str).unique())
selected_cities = st.sidebar.multiselect(
    "City", cities, default=cities[:10] if len(cities) > 10 else cities
)

statuses = sorted(df["Order_Status"].dropna().astype(str).unique())
selected_statuses = st.sidebar.multiselect("Order Status", statuses, default=statuses)

filtered = df.copy()
if selected_years:
    filtered = filtered[filtered["Year"].isin(selected_years)]
if selected_cities:
    filtered = filtered[filtered["City"].isin(selected_cities)]
if selected_statuses:
    filtered = filtered[filtered["Order_Status"].isin(selected_statuses)]

# ---------- Helpers ----------
def money(x):
    if pd.isna(x):
        return "₹0"
    return f"₹{x:,.0f}"

def pct(x):
    if pd.isna(x):
        return "0.0%"
    return f"{x:.1f}%"

def kpi_row(data):
    orders = len(data)
    revenue = data["Net_Order_Value_INR"].sum()
    avg_order = data["Average_Order_Value_INR"].mean()
    rating = data["Rating"].mean()
    delivery = data["Estimated_Delivery_Minutes"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Orders", f"{orders:,}")
    c2.metric("Net Revenue", money(revenue))
    c3.metric("Avg Order Value", money(avg_order))
    c4.metric("Avg Rating", f"{rating:.2f} / 5")
    c5.metric("Avg Delivery", f"{delivery:.1f} min")

def chart(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=55, b=20),
        legend_title_text=""
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- Header ----------
st.markdown("""
<div class="hero">
    <h1>🍽️ FoodLens</h1>
    <p>Zomato Restaurant Data Analysis System · 1,000,000 order records · 2024–2026 dataset</p>
</div>
""", unsafe_allow_html=True)

if filtered.empty:
    st.warning("No records match the selected filters. Please broaden the filters.")
    st.stop()

# ---------- Overview ----------
if page == "Overview":
    st.subheader("📊 Overview")
    kpi_row(filtered)

    st.markdown("### Revenue & Order Trends")
    monthly = (
        filtered.dropna(subset=["Order_Date"])
        .set_index("Order_Date")
        .resample("ME")
        .agg(
            Orders=("Order_ID", "count"),
            Revenue=("Net_Order_Value_INR", "sum")
        )
        .reset_index()
    )

    c1, c2 = st.columns(2)
    with c1:
        chart(px.line(monthly, x="Order_Date", y="Revenue", markers=True,
                      title="Monthly Net Revenue (₹)"))
    with c2:
        chart(px.bar(monthly, x="Order_Date", y="Orders",
                     title="Monthly Order Volume"))

    st.markdown("### Business Snapshot")
    c1, c2 = st.columns(2)

    with c1:
        city = filtered.groupby("City", as_index=False)["Net_Order_Value_INR"].sum()
        city = city.sort_values("Net_Order_Value_INR", ascending=False).head(10)
        chart(px.bar(city, x="Net_Order_Value_INR", y="City", orientation="h",
                     title="Top Cities by Net Revenue"))

    with c2:
        cuisine = filtered.groupby("Cuisine", as_index=False)["Net_Order_Value_INR"].sum()
        cuisine = cuisine.sort_values("Net_Order_Value_INR", ascending=False).head(10)
        chart(px.bar(cuisine, x="Cuisine", y="Net_Order_Value_INR",
                     title="Top Cuisines by Net Revenue"))

# ---------- Revenue ----------
elif page == "Revenue":
    st.subheader("💰 Revenue Analysis")
    kpi_row(filtered)

    c1, c2 = st.columns(2)
    with c1:
        city_rev = filtered.groupby("City", as_index=False).agg(
            Revenue=("Net_Order_Value_INR", "sum"),
            Orders=("Order_ID", "count")
        ).sort_values("Revenue", ascending=False).head(15)
        chart(px.bar(city_rev, x="City", y="Revenue",
                     hover_data=["Orders"], title="Revenue by City"))

    with c2:
        pay = filtered.groupby("Payment_Method", as_index=False).agg(
            Revenue=("Net_Order_Value_INR", "sum"),
            Orders=("Order_ID", "count")
        ).sort_values("Revenue", ascending=False)
        chart(px.pie(pay, names="Payment_Method", values="Revenue",
                     title="Net Revenue by Payment Method", hole=.45))

    monthly = (
        filtered.dropna(subset=["Order_Date"])
        .set_index("Order_Date")
        .resample("ME")
        .agg(
            Gross=("Gross_Order_Value_INR", "sum"),
            Discount=("Discount_Amount_INR", "sum"),
            Net=("Net_Order_Value_INR", "sum")
        )
        .reset_index()
    )
    chart(px.line(monthly, x="Order_Date", y=["Gross", "Discount", "Net"],
                  markers=True, title="Gross Value, Discounts & Net Value Over Time"))

    st.markdown("### Discount Analysis")
    d1, d2 = st.columns(2)
    with d1:
        chart(px.histogram(filtered, x="Discount_Percent", nbins=20,
                           title="Distribution of Discount Percent"))
    with d2:
        disc = filtered.groupby("Discount_Percent", as_index=False)["Net_Order_Value_INR"].mean()
        chart(px.line(disc, x="Discount_Percent", y="Net_Order_Value_INR",
                      markers=True, title="Average Net Order Value by Discount %"))

# ---------- Customers ----------
elif page == "Customers":
    st.subheader("👥 Customer Analysis")

    customer = filtered.groupby("Customer_ID", as_index=False).agg(
        Orders=("Order_ID", "count"),
        Total_Spend=("Net_Order_Value_INR", "sum"),
        Avg_Order_Value=("Average_Order_Value_INR", "mean")
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Unique Customers", f"{customer['Customer_ID'].nunique():,}")
    c2.metric("Avg Orders / Customer", f"{customer['Orders'].mean():.2f}")
    c3.metric("Avg Customer Spend", money(customer["Total_Spend"].mean()))

    c1, c2 = st.columns(2)
    with c1:
        chart(px.histogram(customer, x="Orders", nbins=20,
                           title="Orders per Customer"))
    with c2:
        top_customers = customer.nlargest(15, "Total_Spend")
        chart(px.bar(top_customers, x="Total_Spend", y="Customer_ID",
                     orientation="h", title="Top Customers by Net Spend"))

    st.markdown("### Customer Segmentation")
    customer["Segment"] = pd.cut(
        customer["Orders"],
        bins=[-1, 1, 3, 7, np.inf],
        labels=["1 order", "2–3 orders", "4–7 orders", "8+ orders"]
    )
    segments = customer.groupby("Segment", observed=False).size().reset_index(name="Customers")
    chart(px.pie(segments, names="Segment", values="Customers",
                 title="Customers by Order-Frequency Segment", hole=.45))

# ---------- Delivery ----------
elif page == "Delivery":
    st.subheader("🛵 Delivery Analysis")

    delivered = filtered[filtered["Order_Status"].astype(str).str.lower().eq("delivered")]
    kpi_row(filtered)

    c1, c2 = st.columns(2)
    with c1:
        chart(px.histogram(filtered, x="Estimated_Delivery_Minutes", nbins=30,
                           title="Estimated Delivery Time Distribution"))
    with c2:
        city_delivery = filtered.groupby("City", as_index=False).agg(
            Avg_Delivery=("Estimated_Delivery_Minutes", "mean"),
            Orders=("Order_ID", "count")
        ).sort_values("Avg_Delivery", ascending=False).head(15)
        chart(px.bar(city_delivery, x="City", y="Avg_Delivery",
                     hover_data=["Orders"], title="Average Delivery Time by City"))

    status = filtered.groupby("Order_Status", as_index=False).size()
    status.columns = ["Order_Status", "Orders"]
    chart(px.pie(status, names="Order_Status", values="Orders",
                 title="Order Status Distribution", hole=.45))

    if not delivered.empty:
        st.markdown("### Delivery Time vs Rating")
        sample = delivered[["Estimated_Delivery_Minutes", "Rating"]].dropna()
        if len(sample) > 50000:
            sample = sample.sample(50000, random_state=42)
        chart(px.scatter(sample, x="Estimated_Delivery_Minutes", y="Rating",
                         opacity=.35, title="Delivery Time vs Rating"))

# ---------- Restaurants & Food ----------
elif page == "Restaurants & Food":
    st.subheader("🍛 Restaurant & Food Analysis")
    kpi_row(filtered)

    c1, c2 = st.columns(2)
    with c1:
        cuisine = filtered.groupby("Cuisine", as_index=False).agg(
            Orders=("Order_ID", "count"),
            Revenue=("Net_Order_Value_INR", "sum"),
            Rating=("Rating", "mean")
        ).sort_values("Orders", ascending=False).head(15)
        chart(px.bar(cuisine, x="Cuisine", y="Orders",
                     hover_data=["Revenue", "Rating"],
                     title="Most Ordered Cuisines"))
    with c2:
        rating = filtered.groupby("Rating", as_index=False)["Order_ID"].count()
        rating.columns = ["Rating", "Orders"]
        chart(px.bar(rating, x="Rating", y="Orders",
                     title="Rating Distribution"))

    st.markdown("### Restaurant Performance")
    restaurant = filtered.groupby(
        ["Restaurant_ID", "Restaurant_Name"], as_index=False
    ).agg(
        Orders=("Order_ID", "count"),
        Revenue=("Net_Order_Value_INR", "sum"),
        Avg_Rating=("Rating", "mean"),
        Avg_Delivery=("Estimated_Delivery_Minutes", "mean")
    ).sort_values("Revenue", ascending=False).head(20)

    chart(px.bar(restaurant.sort_values("Revenue"), x="Revenue", y="Restaurant_Name",
                  orientation="h", hover_data=["Orders", "Avg_Rating", "Avg_Delivery"],
                  title="Top Restaurants by Net Revenue"))

    c1, c2 = st.columns(2)
    with c1:
        area = filtered.groupby("Area", as_index=False)["Net_Order_Value_INR"].sum()
        area = area.nlargest(15, "Net_Order_Value_INR")
        chart(px.bar(area, x="Net_Order_Value_INR", y="Area", orientation="h",
                     title="Top Areas by Net Revenue"))
    with c2:
        rt = filtered.groupby("Restaurant_Type", as_index=False).size()
        rt.columns = ["Restaurant_Type", "Orders"]
        chart(px.pie(rt, names="Restaurant_Type", values="Orders",
                     title="Orders by Restaurant Type", hole=.45))

# ---------- Data Explorer ----------
elif page == "Data Explorer":
    st.subheader("🔎 Dataset Explorer")
    st.caption("The dashboard uses the actual Zomato_Restaurant_Data2024_2026 dataset.")

    search = st.text_input("Search restaurant, city, cuisine, area or customer ID")
    display = filtered

    if search:
        mask = (
            display["Restaurant_Name"].astype(str).str.contains(search, case=False, na=False)
            | display["City"].astype(str).str.contains(search, case=False, na=False)
            | display["Cuisine"].astype(str).str.contains(search, case=False, na=False)
            | display["Area"].astype(str).str.contains(search, case=False, na=False)
            | display["Customer_ID"].astype(str).str.contains(search, case=False, na=False)
        )
        display = display[mask]

    st.write(f"Showing **{min(len(display), 1000):,}** rows of **{len(display):,}** matching records.")
    st.dataframe(display.head(1000), use_container_width=True, height=520)

    st.download_button(
        "⬇️ Download filtered data",
        data=display.to_csv(index=False).encode("utf-8"),
        file_name="foodlens_filtered_zomato_data.csv",
        mime="text/csv"
    )

# ---------- About ----------
elif page == "About":
    st.subheader("ℹ️ About FoodLens")

    st.markdown("""
    **FoodLens — Zomato Restaurant Data Analysis System** is a Streamlit-based
    analytics dashboard built for the Zomato restaurant/order dataset.

    ### Dataset
    - **Records:** 1,000,000
    - **Fields:** 25
    - **Coverage:** 2024–2026 dataset
    - **Source file:** `Zomato_Restaurant_Data2024_2026.csv`

    ### Analysis areas
    - Revenue and order trends
    - Customer behaviour
    - Delivery performance
    - Restaurant and cuisine performance
    - Payment methods
    - Discounts
    - Ratings
    - Cities and areas
    - Interactive data exploration

    ### Technology
    **Python · Pandas · NumPy · Plotly · Streamlit**
    """)

    st.markdown("### Dataset Columns")
    st.dataframe(pd.DataFrame({"Column": df.columns}), use_container_width=True)

st.caption("FoodLens • Zomato Restaurant Data Analysis System")
