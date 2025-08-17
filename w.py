import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="Weather Insights Dashboard", layout="wide")

# --- Load Data ---
df = pd.read_csv("weatherAUS_rainfall_prediction_dataset_cleaned.csv")
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
# --- Dashboard Title ---
st.markdown("<h1 style='text-align: center;'>🌦️ WEATHER INSIGHTS DASHBOARD – AUSTRALIA</h1>", unsafe_allow_html=True)

# --- Sidebar Filters (Slicers) ---
import streamlit as st
import pandas as pd

# Load your dataset

with st.expander("🔍 Filters / Slicers", expanded=True):

    # First row (2 slicers)
    col1, col2 = st.columns(2)
    with col1:
        locations = df["Location"].unique().tolist()   # dynamically extract cities
        location = st.multiselect("📍 Location", ["All"] + locations, default="All")

    with col2:
        date_range = st.date_input(
            "📅 Date Range",
            [df["Date"].min(), df["Date"].max()]  # min and max from dataset
        )

    # Second row (2 slicers)
    col3, col4 = st.columns(2)
    with col3:
        season = st.selectbox("🍂 Season", ["All", "Summer", "Autumn", "Winter", "Spring"])

    with col4:
        rain_today = st.selectbox("🌧 Rain Today?", ["All", "Yes", "No"])


# --- Apply Filters ---
filtered_df = df.copy()

if "All" not in locations:
    filtered_df = filtered_df[filtered_df["Location"].isin(locations)]

if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["Date"] >= pd.to_datetime(date_range[0])) &
        (filtered_df["Date"] <= pd.to_datetime(date_range[1]))
    ]

if rain_today != "All":
    filtered_df = filtered_df[filtered_df["RainToday"] == rain_today]

# (Optional) Apply season filter
if season != "All":
    # Simple mapping for Australia
    month_to_season = {
        12: "Summer", 1: "Summer", 2: "Summer",
        3: "Autumn", 4: "Autumn", 5: "Autumn",
        6: "Winter", 7: "Winter", 8: "Winter",
        9: "Spring", 10: "Spring", 11: "Spring"
    }
    filtered_df["Season"] = filtered_df["Month"].map(month_to_season)
    filtered_df = filtered_df[filtered_df["Season"] == season]

# --- KPI Calculations ---
avg_temp = filtered_df["MaxTemp"].mean()
avg_humidity = filtered_df["Humidity3pm"].mean()
total_rainfall = filtered_df["Rainfall"].sum()
rainy_days = filtered_df[filtered_df["RainToday"] == "Yes"].shape[0]


# --- KPI Cards ---
import streamlit as st

# --- Custom CSS for KPI cards ---
import streamlit as st

# --- Custom CSS for KPI cards ---
st.markdown(
    """
    <style>
    .kpi-container {
        display: flex;
        justify-content: space-between;
        align-items: stretch;
        flex-wrap: nowrap; /* force same row */
        gap: 20px;
        margin-bottom: 20px;
    }
    .kpi-card {
        flex: 1;
        padding: 15px;
        border-radius: 15px;
        background-color: #1e1e1e;
        text-align: center;
        height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.4);
    }
    .kpi-title {
        font-size: 16px;
        color: #bbbbbb;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: bold;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- KPI Cards Layout (all in one HTML block) ---
st.markdown(
    """
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">🌡️ Average Temp (°C)</div>
            <div class="kpi-value">23.2</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">💧 Average Humidity (%)</div>
            <div class="kpi-value">52.0%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">🌧️ Total Rainfall (mm)</div>
            <div class="kpi-value">1315638.1</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">☔ Rainy Days</div>
            <div class="kpi-value">122162</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Row 1: Trend Charts ---
st.markdown("## 📊 Weather Trends")
tab1, tab2, tab3 = st.tabs(["🌡️ Temperature Trend", "🌧️ Rainfall Trend", "💧 Humidity Trend"])

with tab1:
    if not filtered_df.empty:
        fig = px.line(filtered_df, x="Date", y="MaxTemp", color="Location", title="Temperature Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

with tab2:
    if not filtered_df.empty:
        fig = px.line(filtered_df, x="Date", y="Rainfall", color="Location", title="Rainfall Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

with tab3:
    if not filtered_df.empty:
        fig = px.line(filtered_df, x="Date", y="Humidity3pm", color="Location", title="Humidity Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# --- Row 2: Analysis Charts ---
st.markdown("## 📈 Deeper Analysis")
tab4, tab5, tab6 = st.tabs(["🏆 Top 5 Rainiest Cities", "📅 Annual Rainfall Trend", "☁️ Rain Probability by Humidity"])

# Chart 4: Top 5 Rainiest Cities
with tab4:
    if not filtered_df.empty:
        top5 = (
            filtered_df.groupby("Location")["Rainfall"].mean()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
        )
        fig = px.bar(top5, x="Location", y="Rainfall", title="Top 5 Rainiest Cities", color="Rainfall")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available.")

# Chart 5: Annual Rainfall Trend
with tab5:
    if not filtered_df.empty:
        annual = filtered_df.groupby("Year")["Rainfall"].mean().reset_index()
        fig = px.line(annual, x="Year", y="Rainfall", title="Annual Rainfall Trend", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available.")

# Chart 6: Rain Probability by Humidity
with tab6:
    if not filtered_df.empty:
        rain_prob = (
            filtered_df.groupby(pd.cut(filtered_df["Humidity3pm"], bins=5))
            ["RainTomorrow"].apply(lambda x: (x == "Yes").mean() * 100)
            .reset_index()
        )
        rain_prob.columns = ["Humidity Level", "Rain Probability (%)"]

        # Convert Interval to string for Plotly
        rain_prob["Humidity Level"] = rain_prob["Humidity Level"].astype(str)

        fig = px.bar(
            rain_prob,
            x="Humidity Level",
            y="Rain Probability (%)",
            title="Rain Probability by Humidity Level",
            color="Rain Probability (%)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available.")
        
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# 10 cities with coordinates + dummy weather data
data = {
    "City": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Hobart", "Darwin", "Canberra", "Gold Coast", "Cairns"
    ],
    "Lat": [
        -33.8688, -37.8136, -27.4698, -31.9505, -34.9285,
        -42.8821, -12.4634, -35.2809, -28.0167, -16.9186
    ],
    "Lon": [
        151.2093, 144.9631, 153.0251, 115.8605, 138.6007,
        147.3272, 130.8456, 149.1300, 153.4000, 145.7781
    ],
    "Temp": [24, 20, 27, 25, 22, 18, 30, 21, 26, 29],
    "Humidity": [65, 55, 70, 60, 50, 68, 75, 52, 66, 80],
}
df = pd.DataFrame(data)

# Weather Map Section
st.subheader("🌍 Weather Map - Major Australian Cities")

# Center the map based on average lat/lon
m = folium.Map(
    location=[df["Lat"].mean(), df["Lon"].mean()],
    zoom_start=4,
    tiles="CartoDB dark_matter"
)

# Add city markers
for _, row in df.iterrows():
    popup_text = f"""
    <b>{row['City']}</b><br>
    🌡 Temp: {row['Temp']} °C<br>
    💧 Humidity: {row['Humidity']}%
    """
    folium.Marker(
        location=[row["Lat"], row["Lon"]],
        popup=popup_text,
        icon=folium.Icon(color="blue", icon="cloud")
    ).add_to(m)

# Show map in Streamlit
st_folium(m, width=950, height=550)
