import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------
# Load Data
# --------------------
@st.cache_data
def load_data():
    df = pd.read_csv("weatherAUS_rainfall_prediction_dataset_cleaned.csv")   # <--- Replace with your CSV filename
    # Convert date column if exists
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

df = load_data()

st.set_page_config(page_title="🌦 Weather Insights Dashboard", layout="wide")

# --------------------
# Sidebar Filters
# --------------------
st.sidebar.header("🔎 Filters")

locations = st.sidebar.multiselect("Select Location(s):", options=df["location"].unique(), default=df["location"].unique())
date_range = st.sidebar.date_input("Select Date Range:", [df["date"].min(), df["date"].max()])

filtered_df = df[
    (df["location"].isin(locations)) &
    (df["date"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
]

# --------------------
# KPIs
# --------------------
st.title("🌦 Weather Insights Dashboard")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Avg Temp 🌡", f"{filtered_df['temp3pm'].mean():.1f} °C")
with col2:
    st.metric("Total Rainfall 🌧", f"{filtered_df['rainfall'].sum():.1f} mm")
with col3:
    st.metric("Avg Humidity 💧", f"{filtered_df['humidity3pm'].mean():.1f} %")
with col4:
    st.metric("Avg Wind Speed 🌬", f"{filtered_df['windspeed3pm'].mean():.1f} km/h")

# --------------------
# Charts Layout
# --------------------
st.subheader("📊 Weather Trends & Patterns")

# Row 1: 3 charts
row1_col1, row1_col2, row1_col3 = st.columns(3)
with row1_col1:
    fig1 = px.line(filtered_df, x="date", y="temp3pm", color="location", title="Temperature Trend")
    st.plotly_chart(fig1, use_container_width=True)

with row1_col2:
    fig2 = px.bar(filtered_df, x="date", y="rainfall", color="location", title="Rainfall Over Time")
    st.plotly_chart(fig2, use_container_width=True)

with row1_col3:
    fig3 = px.line(filtered_df, x="date", y="humidity3pm", color="location", title="Humidity Trend")
    st.plotly_chart(fig3, use_container_width=True)

# Row 2: 2 charts
row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    fig4 = px.box(filtered_df, x="location", y="temp3pm", title="Temperature Distribution by Location")
    st.plotly_chart(fig4, use_container_width=True)

with row2_col2:
    fig5 = px.bar(filtered_df, x="location", y="rainfall", title="Total Rainfall by Location")
    st.plotly_chart(fig5, use_container_width=True)

# Row 3: 2 charts
row3_col1, row3_col2 = st.columns(2)
with row3_col1:
    fig6 = px.scatter(filtered_df, x="humidity3pm", y="temp3pm", color="location", title="Humidity vs Temperature")
    st.plotly_chart(fig6, use_container_width=True)

with row3_col2:
    fig7 = px.histogram(filtered_df, x="windspeed3pm", nbins=30, title="Wind Speed Distribution")
    st.plotly_chart(fig7, use_container_width=True)

# Row 4: Full-width Map
st.subheader("🗺 Weather Map")
if "lat" in filtered_df.columns and "lon" in filtered_df.columns:
    st.map(filtered_df[["lat", "lon"]])
else:
    st.info("No latitude/longitude columns found for map display.")

