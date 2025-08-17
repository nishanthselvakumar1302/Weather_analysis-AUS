# weather_insights.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title=" Weather Insights – Australia", layout="wide")

# =========================
# DB CONNECTION (YOUR DETAILS)
# =========================
DB_USER = "postgres"
DB_PASS = "Nishant1302"   # ⚠️ For production, store in st.secrets
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "weather"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
)

# =========================
# STYLES
# =========================
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
    "<h1 style='text-align: center; color: 	#FFFFFF;'>Weather Insights Dashboard – Australia</h1>",
    unsafe_allow_html=True
)


# =========================
# HELPERS
# =========================
@st.cache_data(show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    try:
        with engine.connect() as conn:
            return pd.read_sql_query(text(sql), conn)
    except Exception as e:
        st.error(f"Error running query: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def get_locations() -> list:
    df = run_query("SELECT DISTINCT location FROM weather_rain_au ORDER BY location;")
    return df["location"].tolist() if not df.empty else []

@st.cache_data(show_spinner=False)
def get_date_limits():
    df = run_query("SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM weather_rain_au;")
    if df.empty or pd.isna(df.loc[0, "min_date"]) or pd.isna(df.loc[0, "max_date"]):
        return None, None
    return pd.to_datetime(df.loc[0, "min_date"]).date(), pd.to_datetime(df.loc[0, "max_date"]).date()

@st.cache_data(show_spinner=False)
def get_temp_limits():
    df = run_query("SELECT FLOOR(MIN(maxtemp)) AS tmin, CEIL(MAX(maxtemp)) AS tmax FROM weather_rain_au;")
    if df.empty or pd.isna(df.loc[0,"tmin"]) or pd.isna(df.loc[0,"tmax"]):
        return 0, 50
    return int(df.loc[0,"tmin"]), int(df.loc[0,"tmax"])

def _escape_list(values):
    return "', '".join([str(v).replace("'", "''") for v in values])

def build_where_clause(date_range, locations, rain_today, rain_tomorrow, season, temp_range):
    conditions = []

    # Date range (safe handling)
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2 and date_range[0] and date_range[1]:
        start_date, end_date = date_range
        conditions.append(f"date BETWEEN '{start_date}' AND '{end_date}'")

    # Locations
    if locations:
        conditions.append(f"location IN ('{_escape_list(locations)}')")

    # Rain Today / Tomorrow
    if rain_today != "All":
        conditions.append(f"raintoday = '{rain_today}'")
    if rain_tomorrow != "All":
        conditions.append(f"raintomorrow = '{rain_tomorrow}'")

    # Season (southern hemisphere months)
    if season != "All":
        season_map = {
            "Summer": (12, 1, 2),
            "Autumn": (3, 4, 5),
            "Winter": (6, 7, 8),
            "Spring": (9, 10, 11),
        }
        months = season_map[season]
        if 12 in months:
            conditions.append("EXTRACT(MONTH FROM date) IN (12,1,2)")
        else:
            m = ", ".join(str(mo) for mo in months)
            conditions.append(f"EXTRACT(MONTH FROM date) IN ({m})")

    # Temperature range (MaxTemp)
    if isinstance(temp_range, (list, tuple)) and len(temp_range) == 2:
        conditions.append(f"maxtemp BETWEEN {int(temp_range[0])} AND {int(temp_range[1])}")

    return "WHERE " + " AND ".join(conditions) if conditions else ""

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("🔎 Filters")

all_locations = get_locations()
dmin, dmax = get_date_limits()
tmin, tmax = get_temp_limits()

selected_locations = st.sidebar.multiselect(
    "Select Cities", options=all_locations, default=all_locations if all_locations else []
)

# Date range with safe default (prevents IndexError)
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(dmin, dmax) if dmin and dmax else ()
)

season = st.sidebar.selectbox("Season", ["All", "Summer", "Autumn", "Winter", "Spring"])
rain_today = st.sidebar.selectbox("Rain Today?", ["All", "Yes", "No"])
rain_tomorrow = st.sidebar.selectbox("Rain Tomorrow?", ["All", "Yes", "No"])

temp_range = st.sidebar.slider("Max Temperature (°C)", tmin, tmax, (tmin, tmax))

basemap = st.sidebar.selectbox(
    "Map Style",
    ["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain", "stamen-toner"]
)

where_clause = build_where_clause(date_range, selected_locations, rain_today, rain_tomorrow, season, temp_range)

# =========================
# KPIs
# =========================
kpi_sql = f"""
    SELECT
      ROUND(AVG(maxtemp)::numeric,1) AS avg_temp,
      ROUND(AVG(humidity3pm)::numeric,0) AS avg_humidity,
      ROUND(SUM(rainfall)::numeric,1) AS total_rain,
      COUNT(*) FILTER (WHERE raintoday='Yes') AS rainy_days
    FROM weather_rain_au
    {where_clause};
"""
kpi_df = run_query(kpi_sql)

c1, c2, c3, c4 = st.columns(4)
if not kpi_df.empty:
    c1.markdown(f'<div class="kpi"><div class="label">Average Temperature</div><div class="value">{kpi_df.loc[0,"avg_temp"]} °C</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi"><div class="label">Average Humidity</div><div class="value">{kpi_df.loc[0,"avg_humidity"]} %</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi"><div class="label">Total Rainfall</div><div class="value">{kpi_df.loc[0,"total_rain"]} mm</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi"><div class="label">Rainy Days (Today)</div><div class="value">{int(kpi_df.loc[0,"rainy_days"] or 0)}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# =========================
# ROW 1 → 3 CHARTS
# =========================
r1c1, r1c2, r1c3 = st.columns(3)

# 1) Top 5 Rainiest Cities
with r1c1:
    sql = f"""
        SELECT location, ROUND(AVG(rainfall)::numeric,2) AS avg_rain
        FROM weather_rain_au
        {where_clause}
        GROUP BY location
        ORDER BY avg_rain DESC
        LIMIT 5;
    """
    df = run_query(sql)
    if not df.empty:
        fig = px.bar(df, x="location", y="avg_rain", color="avg_rain",
                     color_continuous_scale="blues", title="Top 5 Rainiest Cities")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for current filters.")

# 2) Average Rainfall by Month
with r1c2:
    sql = f"""
        SELECT EXTRACT(MONTH FROM date) AS month, ROUND(AVG(rainfall)::numeric,2) AS avg_rain
        FROM weather_rain_au
        {where_clause}
        GROUP BY month
        ORDER BY month;
    """
    df = run_query(sql)
    if not df.empty:
        fig = px.line(df, x="month", y="avg_rain", markers=True, title="Average Rainfall by Month")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for current filters.")

# 3) Temperature vs Rainfall (color by humidity)
with r1c3:
    sql = f"""
        SELECT maxtemp AS temp, rainfall, humidity3pm AS humidity
        FROM weather_rain_au
        {where_clause}
        LIMIT 8000;
    """
    df = run_query(sql)
    if not df.empty:
        fig = px.scatter(df, x="temp", y="rainfall", color="humidity",
                         color_continuous_scale="viridis",
                         title="Temperature vs Rainfall (Colored by Humidity)")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for current filters.")

# =========================
# ROW 2 → 2 CHARTS
# =========================
r2c1, r2c2 = st.columns(2)

# 4) Extreme Rain Days (>100mm)
with r2c1:
    extra = "rainfall > 100"
    where_full = f"{where_clause} AND {extra}" if where_clause else f"WHERE {extra}"
    sql = f"""
        SELECT location, COUNT(*) AS extreme_rain_days
        FROM weather_rain_au
        {where_full}
        GROUP BY location
        ORDER BY extreme_rain_days DESC
        LIMIT 5;
    """
    df = run_query(sql)
    if not df.empty:
        fig = px.bar(df, x="location", y="extreme_rain_days", color="extreme_rain_days",
                     color_continuous_scale="reds", title="Days with Extreme Rain (>100mm)")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for current filters.")

# 5) Annual Rainfall Trend
with r2c2:
    sql = f"""
        SELECT EXTRACT(YEAR FROM date) AS year, ROUND(AVG(rainfall)::numeric,2) AS avg_rain
        FROM weather_rain_au
        {where_clause}
        GROUP BY year
        ORDER BY year;
    """
    df = run_query(sql)
    if not df.empty:
        fig = px.line(df, x="year", y="avg_rain", markers=True, title="Annual Rainfall Trend")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for current filters.")

# =========================
# ROW 3 → 2 CHARTS
# =========================
r3c1, r3c2 = st.columns(2)

# 6) Rain Probability by Humidity Level
with r3c1:
    sql = f"""
        SELECT CASE 
                 WHEN humidity3pm > 80 THEN 'High'
                 WHEN humidity3pm BETWEEN 50 AND 80 THEN 'Medium'
                 ELSE 'Low'
               END AS humidity_category,
               ROUND(COUNT(*) FILTER (WHERE raintomorrow='Yes') * 100.0 / NULLIF(COUNT(*),0), 2) AS rain_probability
        FROM weather_rain_au
        {where_clause}
        GROUP BY humidity_category
        ORDER BY rain_probability DESC;
    """
    df = run_query(sql)
    if not df.empty:
        fig = px.bar(df, x="humidity_category", y="rain_probability",
                     color="rain_probability", color_continuous_scale="teal",
                     title="Rain Probability by Humidity Level")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for current filters.")

# 7) Rain Probability by Wind Strength
with r3c2:
    sql = f"""
        SELECT CASE 
                 WHEN windspeed3pm > 30 THEN 'Strong'
                 WHEN windspeed3pm BETWEEN 15 AND 30 THEN 'Moderate'
                 ELSE 'Calm'
               END AS wind_category,
               ROUND(COUNT(*) FILTER (WHERE raintomorrow='Yes') * 100.0 / NULLIF(COUNT(*),0), 2) AS rain_probability
        FROM weather_rain_au
        {where_clause}
        GROUP BY wind_category
        ORDER BY rain_probability DESC;
    """
    df = run_query(sql)
    if not df.empty:
        fig = px.bar(df, x="wind_category", y="rain_probability",
                     color="rain_probability", color_continuous_scale="cividis",
                     title="Rain Probability by Wind Strength")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for current filters.")

# =========================
# ROW 4 → FULL-WIDTH MAP
# =========================
st.subheader("🗺️ Top 5 Rainiest Cities (Map)")

sql = f"""
    SELECT location, ROUND(AVG(rainfall)::numeric, 2) AS avg_rain
    FROM weather_rain_au
    {where_clause}
    GROUP BY location
    ORDER BY avg_rain DESC
    LIMIT 10;
"""
df_map = run_query(sql)

if not df_map.empty:
    # Fallback lat/lon dictionary for common AU cities
    location_coords = {
        "Sydney": (-33.8688, 151.2093),
        "Melbourne": (-37.8136, 144.9631),
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
        "Townsville": (-19.2589, 146.8169)
    }
    df_map["lat"] = df_map["location"].map(lambda x: location_coords.get(x, (None, None))[0])
    df_map["lon"] = df_map["location"].map(lambda x: location_coords.get(x, (None, None))[1])
    df_map = df_map.dropna(subset=["lat", "lon"])

    if df_map.empty:
        st.info("Map coordinates not found for the current top cities.")
    else:
        fig = px.scatter_mapbox(
            df_map, lat="lat", lon="lon",
            size="avg_rain", color="avg_rain", color_continuous_scale="blues",
            hover_name="location", zoom=3, mapbox_style="carto-darkmatter",
            title="Top 5 Rainiest Cities in Australia"
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for current filters.")
