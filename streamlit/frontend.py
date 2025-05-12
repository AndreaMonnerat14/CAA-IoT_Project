import streamlit as st
import requests
import pandas as pd
import datetime
import os

PASSWD = os.environ.get("HASH_PASSWD")
API_BASE_URL = "https://caa-iot-project-1008838592938.europe-west6.run.app"

st.set_page_config(page_title="IoT Dashboard", layout="wide")
st.title("🌡️ IoT Weather Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["📍 Current State", "📈 History", "🌤️ Forecast", "🏠 Control"])

# --- Tab 1: Current State ---
with tab1:
    st.header("Current Indoor & Outdoor Conditions")
    res = requests.post(f"{API_BASE_URL}/get-all-data", json={"passwd": PASSWD})
    data = res.json().get("data", [])
    if data:
        latest = data[0]
        st.metric("Indoor Temp", f"{latest.get('indoor_temp', '?')} °C")
        st.metric("Outdoor Temp", f"{latest.get('outdoor_temp', '?')} °C")
        st.metric("Indoor Humidity", f"{latest.get('indoor_humidity', '?')} %")
        st.metric("TVOC", f"{latest.get('tvoc', '?')} ppm")
        st.metric("eCO2", f"{latest.get('eco2', '?')} ppm")
        st.caption(f"Date: {latest.get('date')} — Heure: {latest.get('time')}")
    else:
        st.warning("No data available")

# --- Tab 2: Historical Graphs ---
with tab2:
    st.header("Historical Sensor Data")
    res = requests.post(f"{API_BASE_URL}/get-all-data", json={"passwd": PASSWD})
    data = res.json().get("data", [])
    if data:
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values("timestamp")

        st.line_chart(df.set_index("timestamp")[['indoor_temp', 'outdoor_temp']])
        st.line_chart(df.set_index("timestamp")[['indoor_humidity']])
        st.line_chart(df.set_index("timestamp")[['tvoc', 'eco2']])
    else:
        st.warning("No historical data found")

# --- Tab 3: Weather Forecast ---
with tab3:
    st.header("Weather Forecast")
    city = st.text_input("Enter your city", value="Lausanne")
    if st.button("Get Forecast"):
        res = requests.post(f"{API_BASE_URL}/get-weather-forecast", json={"passwd": PASSWD, "city": city})
        forecast = res.json().get("forecast", {})
        if forecast:
            forecasts = forecast.get("list", [])[:8]  # next 24 hours (3h interval)
            for entry in forecasts:
                dt = entry["dt_txt"]
                temp = entry["main"]["temp"]
                desc = entry["weather"][0]["description"]
                st.write(f"**{dt}** — {temp}°C — {desc}")
        else:
            st.error("No forecast found")

# --- Tab 4: Control ---
with tab4:
    st.header("Household Controls (Mock)")
    if st.button("💡 Turn Lights ON"):
        st.success("Lights turned ON (simulated)")
    if st.button("🌡️ Turn Heater ON"):
        st.success("Heater turned ON (simulated)")
    if st.button("🪟 Open Windows"):
        st.success("Windows opened (simulated)")
