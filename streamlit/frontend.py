import streamlit as st
import requests
import pandas as pd
import datetime
import os
import time
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from dotenv import load_dotenv


env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web_app', '.env')
load_dotenv(dotenv_path=env_path)

# Configuration
PASSWD = os.environ.get("HASH_PASSWD")
API_BASE_URL = "https://caa-iot-project-1008838592938.europe-west6.run.app"

# Page configuration
st.set_page_config(page_title="Smart Weather Monitor", page_icon="🌤️", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size:2.5rem; color:#1E88E5; text-align:center; margin-bottom:1rem; font-weight:600;}
    .sub-header {font-size:1.8rem; color:#0D47A1; margin-top:0.8rem; margin-bottom:1.2rem; font-weight:500;}
    .card {border-radius:10px; padding:1.5rem; background-color:#f8f9fa; box-shadow:0 4px 6px rgba(0,0,0,0.1); margin-bottom:1rem;}
    .important-metric {font-size:3rem; font-weight:bold; text-align:center; color:#1E88E5;}
    .metric-label {font-size:1.2rem; text-align:center; color:#555; margin-bottom:0.5rem;}
    .metric-unit {font-size:1.2rem; color:#555;}
    .info-box {background-color:#E3F2FD; border-left:5px solid #1E88E5; padding:1rem; margin-bottom:1rem;}
    .warning-box {background-color:#FFF8E1; border-left:5px solid #FFC107; padding:1rem; margin-bottom:1rem;}
    .success-box {background-color:#E8F5E9; border-left:5px solid #4CAF50; padding:1rem; margin-bottom:1rem;}
    .date-time {font-size:0.9rem; color:#666; text-align:center; margin-top:0.5rem;}
    .forecast-card {text-align:center; padding:10px; border-radius:8px; background-color:#f0f5ff; margin:5px;}
</style>
""", unsafe_allow_html=True)

# API Functions
@st.cache_data(ttl=300)
def get_all_data():
    try:
        response = requests.post(f"{API_BASE_URL}/get-all-data", json={"passwd": PASSWD})
        if response.ok:
            return response.json().get("data", [])
    except Exception as e:
        st.error(f"Unable to recover data: {e}")
    return None

@st.cache_data(ttl=1800)
def get_weather_forecast(city):
    try:
        res = requests.post(f"{API_BASE_URL}/get-weather-forecast", json={"passwd": PASSWD, "city": city})
        if res.status_code == 200:
            return res.json().get("forecast", {})
    except Exception as e:
        st.error(f"Error fetching forecast: {e}")
    return None

# Initialize session state
if 'current_data' not in st.session_state:
    st.session_state.current_data = get_all_data()

# Sidebar navigation
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/partly-cloudy-day.png", width=80)
    st.markdown("<h1 style='text-align:center;'>Smart Weather Monitor</h1>", unsafe_allow_html=True)

    selected = option_menu(
        menu_title="Navigation",
        options=["Dashboard", "Historical Data", "Weather Forecast", "Home Control"],
        icons=["speedometer2", "graph-up", "cloud-sun", "house-gear"],
        menu_icon="cast",
        default_index=0
    )

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.current_data = get_all_data()
        st.rerun()

    st.markdown("---")
    st.markdown(
        f"<div style='text-align:center;'>Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>",
        unsafe_allow_html=True)

# Get data
data = st.session_state.current_data

# --- Dashboard ---
if selected == "Dashboard":
    st.markdown("<h1 class='main-header'>Smart Home Environment Dashboard</h1>", unsafe_allow_html=True)

    if data:
        latest = data[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<p class='metric-label'>Indoor Temperature</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='important-metric'>{latest.get('indoor_temp', '?')}<span class='metric-unit'> °C</span></p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<p class='metric-label'>Outdoor Temperature</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='important-metric'>{latest.get('outdoor_temp', '?')}<span class='metric-unit'> °C</span></p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<p class='metric-label'>Humidity</p>", unsafe_allow_html=True)
            try:
                humidity = float(latest.get('indoor_humidity', 0))
            except ValueError:
                humidity = 0
            st.markdown(f"<p class='important-metric'>{humidity}<span class='metric-unit'> %</span></p>", unsafe_allow_html=True)

            if 40 <= humidity <= 60:
                st.markdown("<p style='text-align:center; color:#4CAF50;'>✓ Optimal</p>", unsafe_allow_html=True)
            elif humidity < 30 or humidity > 70:
                st.markdown("<p style='text-align:center; color:#F44336;'>⚠ Poor</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='text-align:center; color:#FF9800;'>⚠ Acceptable</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col4:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<p class='metric-label'>Air Quality</p>", unsafe_allow_html=True)
            try:
                eco2 = float(latest.get('eco2', 0))
            except ValueError:
                eco2 = 0.0

            quality = "Excellent" if eco2 < 800 else "Good" if eco2 < 1000 else "Fair" if eco2 < 1500 else "Poor"
            color = "#4CAF50" if eco2 < 800 else "#8BC34A" if eco2 < 1000 else "#FFC107" if eco2 < 1500 else "#F44336"

            st.markdown(f"<p class='important-metric' style='color:{color};'>{quality}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center;'>CO₂: {eco2:.0f} ppm</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<h2 class='sub-header'>Current Conditions</h2>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            city = latest.get('city', 'Your Location')
            st.markdown(f"<h3 style='margin-bottom:0.5rem;'>Weather in {city}</h3>", unsafe_allow_html=True)

            weather_details = {
                "Temperature": f"{latest.get('outdoor_temp', '?')} °C",
                "Description": latest.get('weather_desc', 'No data'),
                "Humidity": f"{latest.get('outdoor_humidity', '?')} %",
                "Wind": f"{latest.get('wind_speed', '?')} m/s",
                "Pressure": f"{latest.get('pressure', '?')} hPa"
            }

            detail_cols = st.columns(len(weather_details))
            for i, (label, value) in enumerate(weather_details.items()):
                with detail_cols[i]:
                    st.markdown(f"<p style='text-align:center; font-weight:bold;'>{label}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center;'>{value}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-bottom:0.5rem;'>Indoor Air Quality</h3>", unsafe_allow_html=True)

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=eco2,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "eCO₂ (ppm)"},
                gauge={
                    'axis': {'range': [None, 2000], 'tickwidth': 1},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 800], 'color': "lightgreen"},
                        {'range': [800, 1000], 'color': "yellow"},
                        {'range': [1000, 1500], 'color': "orange"},
                        {'range': [1500, 2000], 'color': "red"}
                    ],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 1500}
                }
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-bottom:0.5rem;'>Alerts & Recommendations</h3>", unsafe_allow_html=True)

            alerts = []
            if humidity < 40:
                alerts.append({"type": "warning", "message": "Low humidity detected. Consider using a humidifier."})
            if eco2 > 1200:
                alerts.append({"type": "warning", "message": "CO₂ levels are elevated. Improve ventilation."})
            if float(latest.get('indoor_temp', 22)) > 26:
                alerts.append({"type": "info", "message": "Room temperature is high. Consider turning on the AC."})
            if float(latest.get('tvoc', 0)) > 200:
                alerts.append({"type": "warning", "message": "VOC levels are elevated. Check for potential sources."})
            if 'rain' in latest.get('weather_desc', '').lower():
                alerts.append({"type": "info", "message": "Rain detected outside. Don't forget your umbrella!"})

            if alerts:
                for alert in alerts:
                    if alert["type"] == "warning":
                        st.markdown(f"<div class='warning-box'>{alert['message']}</div>", unsafe_allow_html=True)
                    elif alert["type"] == "info":
                        st.markdown(f"<div class='info-box'>{alert['message']}</div>", unsafe_allow_html=True)
                    elif alert["type"] == "success":
                        st.markdown(f"<div class='success-box'>{alert['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='success-box'>All measurements are within optimal ranges.</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<p class='date-time'>Last updated: {latest.get('date')} at {latest.get('time')}</p>", unsafe_allow_html=True)

    else:
        st.error("No data available. Please check your connection to the API or refresh the dashboard.")
        if st.button("Retry Connection"):
            st.session_state.current_data = get_all_data()
            st.rerun()

# --- Historical Data Page ---
elif selected == "Historical Data":
    st.markdown("<h1 class='main-header'>Historical Data Analysis</h1>", unsafe_allow_html=True)

    if data:
        # Convert data to DataFrame for analysis
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)  # Force timezone-aware
        df = df.sort_values("timestamp")
        df['indoor_temp'] = pd.to_numeric(df['indoor_temp'], errors='coerce')
        df['outdoor_temp'] = pd.to_numeric(df['outdoor_temp'], errors='coerce')
        df['indoor_humidity'] = pd.to_numeric(df['indoor_humidity'], errors='coerce')
        df['eco2'] = pd.to_numeric(df['eco2'], errors='coerce')
        df['tvoc'] = pd.to_numeric(df['tvoc'], errors='coerce')

        # Time range selector
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        time_period = st.radio(
            "Select Time Period:",
            ["Last 24 Hours", "Last Week", "Last Month", "All Data"],
            horizontal=True
        )

        # Ensure timezone-aware now
        now = pd.Timestamp.now(tz="UTC")

        # Filter data based on selected time period
        if time_period == "Last 24 Hours":
            filtered_df = df[df['timestamp'] > (now - pd.Timedelta(days=1))]
        elif time_period == "Last Week":
            filtered_df = df[df['timestamp'] > (now - pd.Timedelta(days=7))]
        elif time_period == "Last Month":
            filtered_df = df[df['timestamp'] > (now - pd.Timedelta(days=30))]
        else:
            filtered_df = df.copy()

        # Show available metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            show_temp = st.checkbox("Temperature", value=True)
        with col2:
            show_humidity = st.checkbox("Humidity", value=True)
        with col3:
            show_air_quality = st.checkbox("Air Quality", value=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Display selected charts
        if show_temp:
            st.markdown("<h2 class='sub-header'>Temperature Trends</h2>", unsafe_allow_html=True)
            st.markdown("<div class='card'>", unsafe_allow_html=True)

            fig = px.line(
                filtered_df,
                x="timestamp",
                y=["indoor_temp", "outdoor_temp"],
                labels={"value": "Temperature (°C)", "timestamp": "Date/Time", "variable": "Location"},
                title="Indoor vs Outdoor Temperature",
                color_discrete_map={"indoor_temp": "#FF5722", "outdoor_temp": "#2196F3"}
            )
            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            stats_cols = st.columns(4)
            with stats_cols[0]: st.metric("Indoor Avg", f"{filtered_df['indoor_temp'].mean():.1f} °C")
            with stats_cols[1]: st.metric("Indoor Max", f"{filtered_df['indoor_temp'].max():.1f} °C")
            with stats_cols[2]: st.metric("Outdoor Avg", f"{filtered_df['outdoor_temp'].mean():.1f} °C")
            with stats_cols[3]: st.metric("Outdoor Max", f"{filtered_df['outdoor_temp'].max():.1f} °C")

            st.markdown("</div>", unsafe_allow_html=True)

        if show_humidity:
            st.markdown("<h2 class='sub-header'>Humidity Analysis</h2>", unsafe_allow_html=True)
            st.markdown("<div class='card'>", unsafe_allow_html=True)

            fig = px.line(
                filtered_df,
                x="timestamp",
                y="indoor_humidity",
                labels={"indoor_humidity": "Humidity (%)", "timestamp": "Date/Time"},
                title="Indoor Humidity Levels"
            )

            fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Upper comfort limit")
            fig.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Lower comfort limit")
            fig.add_hrect(y0=40, y1=60, line_width=0, fillcolor="green", opacity=0.1)

            fig.update_layout(height=400)
            fig.update_traces(line=dict(width=3, color="#673AB7"))

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if show_air_quality:
            st.markdown("<h2 class='sub-header'>Air Quality Metrics</h2>", unsafe_allow_html=True)
            st.markdown("<div class='card'>", unsafe_allow_html=True)

            aq_tab1, aq_tab2 = st.tabs(["CO₂ Levels", "TVOC Levels"])

            with aq_tab1:
                fig = px.line(
                    filtered_df,
                    x="timestamp",
                    y="eco2",
                    labels={"eco2": "eCO₂ (ppm)", "timestamp": "Date/Time"},
                    title="Carbon Dioxide (CO₂) Levels"
                )

                fig.add_hline(y=1000, line_dash="dash", line_color="orange", annotation_text="Fair")
                fig.add_hline(y=1500, line_dash="dash", line_color="red", annotation_text="Poor")

                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            with aq_tab2:
                fig = px.line(
                    filtered_df,
                    x="timestamp",
                    y="tvoc",
                    labels={"tvoc": "TVOC (ppb)", "timestamp": "Date/Time"},
                    title="Total Volatile Organic Compounds (TVOC) Levels"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error("No data available for historical analysis.")

# --- Weather Forecast Page ---
elif selected == "Weather Forecast":
    st.markdown("<h1 class='main-header'>Weather Forecast</h1>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    city_try = data[0].get("city", "Your City") if data and len(data) > 0 else "Your City"

    col1, col2 = st.columns([3, 1])
    with col1:
        city = st.text_input("Enter your city", value=city_try)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_forecast = st.button("Get Forecast", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if fetch_forecast or 'forecast_data' in st.session_state:
        with st.spinner("Fetching weather forecast..."):
            if fetch_forecast or 'forecast_data' not in st.session_state:
                forecast_data = get_weather_forecast(city)
                if forecast_data:
                    st.session_state.forecast_data = forecast_data
                    st.session_state.forecast_city = city
            else:
                forecast_data = st.session_state.forecast_data
                city = st.session_state.forecast_city

        if forecast_data:
            forecasts = forecast_data.get("list", [])

            if forecasts:
                today = datetime.date.today().strftime("%Y-%m-%d")

                today_forecasts = [f for f in forecasts if f["dt_txt"].startswith(today)]
                future_forecasts = [f for f in forecasts if not f["dt_txt"].startswith(today)]

                # --- TODAY'S FORECAST ---
                st.markdown("<h2 class='sub-header'>Today's Forecast</h2>", unsafe_allow_html=True)
                st.markdown("<div class='card'>", unsafe_allow_html=True)

                if today_forecasts:
                    cols = st.columns(len(today_forecasts))
                    for i, entry in enumerate(today_forecasts):
                        with cols[i]:
                            time_str = entry["dt_txt"].split(" ")[1][:5]
                            temp = float(entry["main"]["temp"])
                            desc = entry["weather"][0].get("description", "No description")
                            icon = entry["weather"][0].get("icon", "01d")
                            icon_url = f"http://openweathermap.org/img/wn/{icon}@2x.png"

                            st.markdown("<div class='forecast-card'>", unsafe_allow_html=True)
                            st.markdown(f"<p style='font-weight:bold; font-size:1.2rem;'>{time_str}</p>", unsafe_allow_html=True)
                            st.image(icon_url, width=64)
                            st.markdown(f"<p style='font-size:1.5rem; font-weight:bold;'>{temp:.1f}°C</p>", unsafe_allow_html=True)
                            st.markdown(f"<p>{desc.capitalize()}</p>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No forecast data available for today.")

                st.markdown("</div>", unsafe_allow_html=True)

                # --- 5-DAY FORECAST ---
                st.markdown("<h2 class='sub-header'>5-Day Forecast</h2>", unsafe_allow_html=True)
                st.markdown("<div class='card'>", unsafe_allow_html=True)

                daily_summary = {}
                for entry in future_forecasts:
                    date = entry["dt_txt"].split(" ")[0]
                    temp = float(entry["main"]["temp"])
                    desc = entry["weather"][0]["description"]
                    icon = entry["weather"][0]["icon"]

                    if date not in daily_summary:
                        daily_summary[date] = {"temps": [], "desc": [], "icons": []}

                    daily_summary[date]["temps"].append(temp)
                    daily_summary[date]["desc"].append(desc)
                    daily_summary[date]["icons"].append(icon)

                days = list(daily_summary.items())[:5]
                cols = st.columns(len(days))

                for i, (date, info) in enumerate(days):
                    with cols[i]:
                        day_name = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%A")
                        most_common_desc = max(set(info["desc"]), key=info["desc"].count)
                        most_common_icon = max(set(info["icons"]), key=info["icons"].count)
                        icon_url = f"http://openweathermap.org/img/wn/{most_common_icon}@2x.png"

                        max_temp = max(info["temps"])
                        min_temp = min(info["temps"])

                        st.markdown("<div class='forecast-card'>", unsafe_allow_html=True)
                        st.markdown(f"<p style='font-weight:bold; font-size:1.2rem;'>{day_name}</p>", unsafe_allow_html=True)
                        st.image(icon_url, width=64)
                        st.markdown(f"<p>{most_common_desc.capitalize()}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='font-size:1.3rem; font-weight:bold;'>{max_temp:.1f}°C / {min_temp:.1f}°C</p>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.error("No forecast data available from the weather service.")
        else:
            st.error("Failed to retrieve forecast. Please try again later.")

# --- Home Control Page ---
elif selected == "Home Control":
    st.markdown("<h1 class='main-header'>Smart Home Control</h1>", unsafe_allow_html=True)

    # Create grid of control cards
    col1, col2 = st.columns(2)

    # Temperature Control Card
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>Temperature Control</h2>", unsafe_allow_html=True)

        try:
            current_temp = float(data[0].get('indoor_temp', 22)) if data and len(data) > 0 else 22
        except ValueError:
            current_temp = 22.0

        st.markdown(
            f"<p style='text-align:center; font-size:3rem; font-weight:bold; color:#1E88E5;'>{current_temp:.1f}°C</p>",
            unsafe_allow_html=True)

        st.markdown("<p style='text-align:center; font-size:1.2rem;'>Set Target Temperature</p>",
                    unsafe_allow_html=True)

        target_temp = st.slider("Target temperature", 18, 28, int(current_temp), 1, format="%d°C",
                                label_visibility="collapsed")

        mode = st.radio("Mode:", ["Off", "Heat", "Cool", "Auto"], horizontal=True)

        if st.button("Apply Settings", use_container_width=True):
            st.success(f"Temperature set to {target_temp}°C in {mode} mode (simulated)")

        st.markdown("</div>", unsafe_allow_html=True)

    # Humidity Control Card
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>Humidity Control</h2>", unsafe_allow_html=True)

        try:
            current_humidity = float(data[0].get('indoor_humidity', 45)) if data and len(data) > 0 else 45
        except ValueError:
            current_humidity = 45.0

        st.markdown(
            f"<p style='text-align:center; font-size:3rem; font-weight:bold; color:#673AB7;'>{current_humidity:.0f}%</p>",
            unsafe_allow_html=True)

        toggle_col1, toggle_col2 = st.columns(2)
        with toggle_col1:
            humidifier = st.toggle("Humidifier", value=False)
        with toggle_col2:
            dehumidifier = st.toggle("Dehumidifier", value=False)

        auto_mode = st.checkbox("Auto mode (maintain 40-60%)", value=True)

        if not auto_mode:
            target_humidity = st.slider("Target Humidity:", 30, 70, int(current_humidity), 5, format="%d%%")

        if st.button("Apply Humidity Settings", use_container_width=True):
            st.success("Humidity settings applied (simulated)")

        st.markdown("</div>", unsafe_allow_html=True)

    # Air Quality & Ventilation
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Air Quality & Ventilation</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        try:
            current_co2 = float(data[0].get('eco2', 800)) if data and len(data) > 0 else 800
        except ValueError:
            current_co2 = 800.0

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_co2,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CO₂ (ppm)"},
            gauge={
                'axis': {'range': [None, 2000], 'tickwidth': 1},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 800], 'color': "lightgreen"},
                    {'range': [800, 1000], 'color': "yellow"},
                    {'range': [1000, 1500], 'color': "orange"},
                    {'range': [1500, 2000], 'color': "red"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 1500}
            }
        ))

        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<h3 style='text-align:center; margin-top:20px;'>Ventilation Controls</h3>", unsafe_allow_html=True)

        fan_speed = st.select_slider("Fan Speed", options=["Off", "Low", "Medium", "High", "Turbo"], value="Off")
        auto_vent = st.checkbox("Auto Ventilation", value=True)

        if st.button("Apply Ventilation Settings", use_container_width=True):
            st.success(f"Ventilation set to {fan_speed} mode (simulated)")

    st.markdown("</div>", unsafe_allow_html=True)
