import streamlit as st
import requests
import pandas as pd
import datetime
import os
import time
from streamlit import session_state

PASSWD = os.environ.get("HASH_PASSWD")
API_BASE_URL = "https://caa-iot-project-1008838592938.europe-west6.run.app"

st.set_page_config(page_title="IoT Dashboard", layout="wide")

def get_all_data():
    try:
        response = requests.post(f"{API_BASE_URL}/get-all-data", json={"passwd": PASSWD})
        if response.ok:
            return response.json().get("data", [])
    except Exception as e:
        print(f"Unable to recover data: {e}")
    return None

st.title("🌡️ IoT Weather Dashboard")

if st.button("🔄 Refresh Data"):
    st.session_state.current_data = get_all_data()
    st.experimental_rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📍 Current State", "📈 History", "🌤️ Forecast", "🏠 Control"])

if 'bouncer' not in st.session_state:
    st.session_state.bouncer = 0

if 'current_data' not in st.session_state:
    st.session_state.current_data = get_all_data()

# --- Tab 1: Current State ---
with tab1:
    st.header("Current Indoor & Outdoor Conditions")
    data = st.session_state.current_data
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
    data = st.session_state.current_data
    if data:
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values("timestamp")

        st.line_chart(df.set_index("timestamp")[['indoor_temp']]) #, 'outdoor_temp']])
        st.line_chart(df.set_index("timestamp")[['indoor_humidity']])
        #st.line_chart(df.set_index("timestamp")[['tvoc', 'eco2']])
    else:
        st.warning("No historical data found")

# --- Tab 3: Weather Forecast ---
with tab3:
    st.header("🌤️ Weather Forecast")
    city = st.text_input("Enter your city", value="Lausanne")

    if st.button("Get Forecast"):
        res = requests.post(f"{API_BASE_URL}/get-weather-forecast", json={"passwd": PASSWD, "city": city})

        if res.status_code == 200:
            forecast_data = res.json().get("forecast", {})
            if forecast_data:
                forecasts = forecast_data.get("list", [])
                daily_summary = {}

                for entry in forecasts:
                    date = entry["dt_txt"].split(" ")[0]
                    temp = entry["main"]["temp"]
                    desc = entry["weather"][0]["description"]
                    icon = entry["weather"][0]["icon"]

                    if date not in daily_summary:
                        daily_summary[date] = {
                            "temps": [],
                            "desc": desc,
                            "icon": icon
                        }
                    daily_summary[date]["temps"].append(temp)

                for date, info in list(daily_summary.items())[:5]:  # Limit to 5 days
                    min_temp = min(info["temps"])
                    max_temp = max(info["temps"])
                    icon_url = f"http://openweathermap.org/img/wn/{info['icon']}@2x.png"
                    st.markdown(f"### 📅 {date}")
                    st.image(icon_url, width=80)
                    st.write(f"**{info['desc'].capitalize()}**")
                    st.metric("🌡️ Température max", f"{max_temp:.1f}°C")
                    st.metric("🌡️ Température min", f"{min_temp:.1f}°C")
                    st.markdown("---")
            else:
                st.warning("No forecast data found.")
        else:
            st.error("Failed to retrieve forecast.")

# --- Tab 4: Control ---
with tab4:
    st.header("Household Controls (Mock)")
    if st.button("💡 Turn Lights ON"):
        st.success("Lights turned ON (simulated)")
    if st.button("🌡️ Turn Heater ON"):
        st.success("Heater turned ON (simulated)")
    if st.button("🪟 Open Windows"):
        st.success("Windows opened (simulated)")


