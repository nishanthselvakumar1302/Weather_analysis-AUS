# weather_insights_csv.py
import re
import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# APP CONFIG & STYLES
# =========================
st.set_page_config(page_title=" Weather Insights – Australia", layout="wide")

st.markdown(
    """
    <style>
      [data-testid="stSidebar"] { min-width: 300px; max-width: 360px; }
      .kpi {
        border-radius: 14px; padding: 16px 16px; background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.10);
      }
      .kpi .label { font-size: 0.9rem; color: #9aa6b2; margin-bottom: 6px; }
      .kpi .value { font-size: 1.6rem; font-weight: 700; }
      .block-container { padding-top: 0.75rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<h1 style='text-align: center; color: #FFFFFF;'>WEATHER INSIGHTS DASHBOARD – AUSTRALIA</h1>",
    unsafe_allow_html=True
)

# =========================
# HELPERS (robust column detection)
# =========================
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())

def _build_norm_map(cols):
    return {_norm(c): c for c in cols}

def _pick_col(df: pd.DataFrame, candidates=None, contains=None):
    """
    Pick the first column that matches:
      1) any of 'candidates' (exact, after normalization), else
      2) the first col whose normalized name contains ANY of the tokens in 'contains'
    Returns real column name or None.
    """
    if df is None or df.empty:
        return None
    norm_map = _build_norm_map(df.columns)
    if candidates:
        for cand in candidates:
            nc = _norm(cand)
            if nc in norm_map:
                return norm_map[nc]
    if contains:
        tokens = [_norm(t) for t in contains]
        for c in df.columns:
            nc = _norm(c)
            if any(t in nc for t in tokens):
                return c
    return None

def _ensure_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c and c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

def _ensure_yes_no(series: pd.Series):
    if series is None:
        return None
    s = series.astype(str).str.strip().str.lower()
    # Map common truthy/falsy to Yes/No
    yes = {"yes", "y", "true", "1"}
    no = {"no", "n", "false", "0"}
    mapped = s.map(lambda v: "Yes" if v in yes else ("No" if v in no else None))
    return mapped

# =========================
# LOAD DATA (CSV)
# =========================
@st.cache_data(show_spinner=False)
def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # normalize headers to keep original names but help detection
    # (we DON'T rename here; we detect dynamically)
    return df

st.sidebar.header("🗂 Data")
csv_path = st.sidebar.text_input(
    "CSV file path",
    value="weatherAUS_rainfall_prediction_dataset_cleaned.csv",
    help="Enter the path to your CSV file."
)

try:
    df = load_data(csv_path)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

if df.empty:
    st.warning("CSV loaded but it's empty.")
    st.stop()

# =========================
# DETECT KEY COLUMNS
# =========================
# Required-ish columns
date_col      = _pick_col(df, candidates=["date"], contains=["date"])
location_col  = _pick_col(df, candidates=["location", "city", "town"], contains=["location","city","town"])
rainfall_col  = _pick_col(df, candidates=["rainfall"], contains=["rain"])

# Nice-to-have columns
maxtemp_col   = _pick_col(df, candidates=["maxtemp","max_temp","tempmax","tmax","temp3pm","temp"], contains=["maxtemp","temp3pm","temp"])
humidity_col  = _pick_col(df, candidates=["humidity3pm","humidity_3pm","humidity"], contains=["humidity"])
windspeed_col = _pick_col(df, candidates=["windspeed3pm","wind_speed_3pm","windspeed","wind_speed","windgustspeed"], contains=["windspeed","wind"])
raintoday_col = _pick_col(df, candidates=["raintoday","rain_today"], contains=["raintoday"])
raintom_col   = _pick_col(df, candidates=["raintomorrow","rain_tomorrow"], contains=["raintomorrow"])

# Validate essentials
missing_essentials = []
if date_col is None:     missing_essentials.append("date")
if location_col is None: missing_essentials.append("location")
if rainfall_col is None: missing_essentials.append("rainfall")

if missing_essentials:
    st.error(
        "Your CSV is missing required columns. "
        f"Couldn’t find: {', '.join(missing_essentials)}.\n\n"
        "Tip: Make sure your headers include something like Date, Location, Rainfall "
        "(capitalization doesn’t matter)."
    )
    st.write("Detected columns:", list(df.columns))
    st.stop()

# Parse date
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col])  # drop rows without a valid date

# Ensure numeric
_ensure_numeric(df, [rainfall_col, maxtemp_col, humidity_col, windspeed_col])

# Normalize rain flags if present
if raintoday_col:
    df[raintoday_col] = _ensure_yes_no(df[raintoday_col])
if raintom_col:
    df[raintom_col] = _ensure_yes_no(df[raintom_col])

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("🔎 Filters")

all_locations = sorted(df[location_col].dropna().astype(str).unique().tolist())
dmin = pd.to_datetime(df[date_col].min()).date()
dmax = pd.to_datetime(df[date_col].max()).date()

# Temperature slider limits (fallback if maxtemp_col missing)
if maxtemp_col:
    tmin = int(pd.to_numeric(df[maxtemp_col], errors="coerce").min(skipna=True))
    tmax = int(pd.to_numeric(df[maxtemp_col], errors="coerce").max(skipna=True))
else:
    tmin, tmax = -10, 50  # generic range

selected_locations = st.sidebar.multiselect(
    "Select Cities", options=all_locations, default=all_locations if all_locations else []
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(dmin, dmax) if dmin and dmax else ()
)

season = st.sidebar.selectbox("Season", ["All", "Summer", "Autumn", "Winter", "Spring"])

rain_today_choice = st.sidebar.selectbox(
    "Rain Today?",
    ["All", "Yes", "No"] if raintoday_col else ["N/A"],
    index=0
)

rain_tomorrow_choice = st.sidebar.selectbox(
    "Rain Tomorrow?",
    ["All", "Yes", "No"] if raintom_col else ["N/A"],
    index=0
)

temp_range = st.sidebar.slider(
    "Max Temperature (°C)",
    tmin, tmax, (tmin, tmax),
    disabled=(maxtemp_col is None)
)

basemap = st.sidebar.selectbox(
    "Map Style",
    ["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain", "stamen-toner"],
    index=0
)

# =========================
# APPLY FILTERS
# =========================
filtered_df = df.copy()

# locations
if selected_locations:
    filtered_df = filtered_df[filtered_df[location_col].astype(str).isin(selected_locations)]

# date range
if isinstance(date_range, (list, tuple)) and len(date_range) == 2 and date_range[0] and date_range[1]:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = filtered_df[(filtered_df[date_col] >= start_date) & (filtered_df[date_col] <= end_date)]

# season (southern hemisphere)
if season != "All":
    season_map = {
        "Summer": (12, 1, 2),
        "Autumn": (3, 4, 5),
        "Winter": (6, 7, 8),
        "Spring": (9, 10, 11),
    }
    months = season_map[season]
    filtered_df = filtered_df[filtered_df[date_col].dt.month.isin(months)]

# rain Today/Tomorrow filters
if raintoday_col and rain_today_choice in ("Yes", "No"):
    filtered_df = filtered_df[filtered_df[raintoday_col] == rain_today_choice]

if raintom_col and rain_tomorrow_choice in ("Yes", "No"):
    filtered_df = filtered_df[filtered_df[raintom_col] == rain_tomorrow_choice]

# temp slider
if maxtemp_col:
    filtered_df = filtered_df[
        (filtered_df[maxtemp_col] >= temp_range[0]) & (filtered_df[maxtemp_col] <= temp_range[1])
    ]

# =========================
# KPIs
# =========================
c1, c2, c3, c4 = st.columns(4)

if not filtered_df.empty:
    # Average Temperature (fallback to NaN if no maxtemp_col)
    avg_temp = round(filtered_df[maxtemp_col].mean(), 1) if maxtemp_col else float("nan")
    # Average Humidity (if missing, show NaN)
    avg_hum = round(filtered_df[humidity_col].mean(), 0) if humidity_col else float("nan")
    # Total Rainfall
    total_rain = round(filtered_df[rainfall_col].sum(), 1)
    # Rainy Days Today
    rainy_days = int((filtered_df[raintoday_col] == "Yes").sum()) if raintoday_col else 0

    c1.markdown(f'<div class="kpi"><div class="label">Average Temperature</div><div class="value">{avg_temp} °C</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi"><div class="label">Average Humidity</div><div class="value">{avg_hum} %</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi"><div class="label">Total Rainfall</div><div class="value">{total_rain} mm</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi"><div class="label">Rainy Days (Today)</div><div class="value">{rainy_days}</div></div>', unsafe_allow_html=True)
else:
    st.info("No data after filters; adjust your selections.")

st.markdown("---")

# =========================
# ROW 1 → 3 CHARTS
# =========================
r1c1, r1c2, r1c3 = st.columns(3)

# 1) Top 5 Rainiest Cities (by average rainfall)
with r1c1:
    if not filtered_df.empty:
        df1 = (filtered_df.groupby(location_col)[rainfall_col]
               .mean()
               .nlargest(5)
               .reset_index(name="avg_rain"))
        if not df1.empty:
            fig = px.bar(df1, x=location_col, y="avg_rain", color="avg_rain",
                         color_continuous_scale="blues", title="Top 5 Rainiest Cities")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for current filters.")
    else:
        st.info("No data for current filters.")

# 2) Average Rainfall by Month
with r1c2:
    if not filtered_df.empty:
        df2 = (filtered_df
               .assign(month=filtered_df[date_col].dt.month)
               .groupby("month")[rainfall_col].mean()
               .reset_index())
        if not df2.empty:
            fig = px.line(df2, x="month", y=rainfall_col, markers=True, title="Average Rainfall by Month")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for current filters.")
    else:
        st.info("No data for current filters.")

# 3) Temperature vs Rainfall (color by humidity)
with r1c3:
    if not filtered_df.empty and maxtemp_col:
        if humidity_col:
            fig = px.scatter(filtered_df, x=maxtemp_col, y=rainfall_col, color=humidity_col,
                             color_continuous_scale="viridis",
                             title="Temperature vs Rainfall (Colored by Humidity)")
        else:
            fig = px.scatter(filtered_df, x=maxtemp_col, y=rainfall_col,
                             title="Temperature vs Rainfall")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need a temperature column to show this chart.")

# =========================
# ROW 2 → 2 CHARTS
# =========================
r2c1, r2c2 = st.columns(2)

# 4) Extreme Rain Days (>100mm)
with r2c1:
    if not filtered_df.empty:
        df3 = (filtered_df[filtered_df[rainfall_col] > 100]
               .groupby(location_col)
               .size()
               .nlargest(5)
               .reset_index(name="extreme_rain_days"))
        if not df3.empty:
            fig = px.bar(df3, x=location_col, y="extreme_rain_days", color="extreme_rain_days",
                         color_continuous_scale="reds", title="Days with Extreme Rain (>100mm)")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No extreme rain days in current filters.")
    else:
        st.info("No data for current filters.")

# 5) Annual Rainfall Trend (average)
with r2c2:
    if not filtered_df.empty:
        df4 = (filtered_df
               .assign(year=filtered_df[date_col].dt.year)
               .groupby("year")[rainfall_col].mean()
               .reset_index())
        if not df4.empty:
            fig = px.line(df4, x="year", y=rainfall_col, markers=True, title="Annual Rainfall Trend")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for current filters.")
    else:
        st.info("No data for current filters.")

# =========================
# ROW 3 → 2 CHARTS
# =========================
r3c1, r3c2 = st.columns(2)

# 6) Rain Probability by Humidity Level
with r3c1:
    if not filtered_df.empty and humidity_col and raintom_col:
        tmp = filtered_df[[humidity_col, raintom_col]].dropna()
        if not tmp.empty:
            cats = pd.cut(
                tmp[humidity_col],
                bins=[-1, 50, 80, 200],
                labels=["Low", "Medium", "High"]
            )
            prob = (tmp.assign(humidity_category=cats)
                        .groupby("humidity_category")[raintom_col]
                        .apply(lambda s: (s == "Yes").mean() * 100)
                        .reset_index(name="rain_probability"))
            fig = px.bar(prob, x="humidity_category", y="rain_probability",
                         color="rain_probability", color_continuous_scale="teal",
                         title="Rain Probability by Humidity Level")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to calculate humidity-based probability.")
    else:
        st.info("Need humidity and RainTomorrow columns to show this chart.")

# 7) Rain Probability by Wind Strength
with r3c2:
    if not filtered_df.empty and windspeed_col and raintom_col:
        tmp = filtered_df[[windspeed_col, raintom_col]].dropna()
        if not tmp.empty:
            cats = pd.cut(
                tmp[windspeed_col],
                bins=[-1, 15, 30, 1e6],
                labels=["Calm", "Moderate", "Strong"]
            )
            prob = (tmp.assign(wind_category=cats)
                        .groupby("wind_category")[raintom_col]
                        .apply(lambda s: (s == "Yes").mean() * 100)
                        .reset_index(name="rain_probability"))
            fig = px.bar(prob, x="wind_category", y="rain_probability",
                         color="rain_probability", color_continuous_scale="cividis",
                         title="Rain Probability by Wind Strength")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to calculate wind-based probability.")
    else:
        st.info("Need wind speed and RainTomorrow columns to show this chart.")

# =========================
# ROW 4 → FULL-WIDTH MAP
# =========================
st.subheader("🗺️ Top 10 Rainiest Cities (Map)")

# average rainfall per city
df_map = (filtered_df.groupby(location_col)[rainfall_col]
          .mean()
          .reset_index(name="avg_rain")
          .sort_values("avg_rain", ascending=False)
          .head(10))

if not df_map.empty:
    # Fallback coordinates for common AU cities (extend as needed)
    location_coords = {
        "Sydney": (-33.8688, 151.2093),
        "SydneyAirport": (-33.9461, 151.1772),
        "Melbourne": (-37.8136, 144.9631),
        "MelbourneAirport": (-37.6653, 144.8320),
        "Brisbane": (-27.4698, 153.0251),
        "Perth": (-31.9505, 115.8605),
        "Adelaide": (-34.9285, 138.6007),
        "Darwin": (-12.4634, 130.8456),
        "Cairns": (-16.9203, 145.7700),
        "Hobart": (-42.8821, 147.3272),
        "Canberra": (-35.2809, 149.1300),
        "GoldCoast": (-28.0167, 153.4000),
        "Wollongong": (-34.4278, 150.8931),
        "CoffsHarbour": (-30.2963, 153.1157),
        "Townsville": (-19.2589, 146.8169),
        "Albury": (-36.0806, 146.9156),
        "Ballarat": (-37.5622, 143.8503),
        "Bendigo": (-36.7570, 144.2794),
        "Newcastle": (-32.9283, 151.7817),
        "NorahHead": (-33.2810, 151.5790),
        "Richmond": (-33.6000, 150.7500),
        "WaggaWagga": (-35.1080, 147.3700),
        "Williamtown": (-32.7950, 151.8400),
        "Sale": (-38.1092, 147.0687),
        "Mildura": (-34.2050, 142.1240),
        "Portland": (-38.3420, 141.6060),
        "Watsonia": (-37.7167, 145.0833),
        "Moree": (-29.4653, 149.8417),
        "Penrith": (-33.7510, 150.6900),
        "Tuggeranong": (-35.4240, 149.0880),
        "MountGinini": (-35.5290, 148.7720),
        "PearceRAAF": (-31.6670, 116.0160),
        "PerthAirport": (-31.9403, 115.9672),
        "Albany": (-35.0228, 117.8814),
        "Witchcliffe": (-34.0126, 115.1013),
        "SalmonGums": (-32.9833, 121.6333),
        "Walpole": (-34.9766, 116.7334),
        "Launceston": (-41.4332, 147.1441),
        "AliceSprings": (-23.6980, 133.8807),
        "Katherine": (-14.4650, 132.2630),
        "Uluru": (-25.3444, 131.0369),
        "Cobar": (-31.4988, 145.8440),
        "BadgerysCreek": (-33.8850, 150.6900),
        "Nhil": (-36.3333, 141.6500),
        "Dartmoor": (-37.9170, 141.2720),
        "Nuriootpa": (-34.4690, 138.9960),
        "Woomera": (-31.1980, 136.8250),
    }

    # map coords
    df_map["lat"] = df_map[location_col].map(lambda x: location_coords.get(str(x), (None, None))[0])
    df_map["lon"] = df_map[location_col].map(lambda x: location_coords.get(str(x), (None, None))[1])
    df_map = df_map.dropna(subset=["lat", "lon"])

    if df_map.empty:
        st.info("Map coordinates not found for the current top cities. Add missing cities to the dictionary.")
    else:
        fig = px.scatter_mapbox(
            df_map, lat="lat", lon="lon",
            size="avg_rain", color="avg_rain", color_continuous_scale="blues",
            hover_name=location_col, zoom=3, mapbox_style="carto-darkmatter",
            title="Top Rainiest Cities in Australia"
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for current filters.")
