import streamlit as st
import requests
import datetime
import os

# 🔐 Mot de passe hashé
PASSWD = os.environ.get("HASH_PASSWD", "your_default_hash_here")

# 🌍 URL de ton backend Flask déployé (Cloud Run)
API_BASE_URL = "https://caa-iot-project-1008838592938.europe-west6.run.app"

# 📌 Fonctions API
def get_latest_values():
    r = requests.post(f"{API_BASE_URL}/get-latest-values", json={"passwd": PASSWD})
    return r.json()

def get_outdoor_weather():
    r = requests.get(f"{API_BASE_URL}/get_outdoor_weather")
    return r.json()

def get_indoor_data(start_date=None, end_date=None, limit=100):
    body = {
        "passwd": PASSWD,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
    }
    r = requests.post(f"{API_BASE_URL}/get-indoor-data", json=body)
    return r.json()

# 🎛️ UI
st.set_page_config(page_title="IoT Dashboard", layout="wide")
st.title("🌡️ IoT Weather Dashboard")

tab1, tab2, tab3 = st.tabs(["🔍 Latest Values", "📊 History", "🌤️ Outdoor Weather"])

# ✅ Tab 1: Latest
with tab1:
    st.subheader("Latest Indoor Values")
    data = get_latest_values()
    if data["status"] == "success" and data["data"]:
        vals = data["data"]
        st.metric("🌡️ Température intérieure", f"{vals.get('indoor_temp', '?')} °C")
        st.metric("💧 Humidité intérieure", f"{vals.get('indoor_humidity', '?')} %")
        st.metric("🟡 TVOC", f"{vals.get('tvoc', '?')} ppm")
        st.metric("🟢 eCO₂", f"{vals.get('eco2', '?')} ppm")
        st.caption(f"Date: {vals.get('date')} — Heure: {vals.get('time')}")
    else:
        st.error("Aucune donnée disponible.")

# ✅ Tab 2: Historical Data
with tab2:
    st.subheader("History")
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Start date", value=datetime.date.today() - datetime.timedelta(days=3))
    with col2:
        end = st.date_input("End date", value=datetime.date.today())
    limit = st.slider("Nombre de lignes à afficher", 10, 500, 100)

    if st.button("Charger l'historique"):
        hist = get_indoor_data(str(start), str(end), limit)
        if hist["status"] == "success":
            df = hist["data"]
            if df:
                import pandas as pd
                df = pd.DataFrame(df)
                st.dataframe(df)
            else:
                st.warning("Aucune donnée pour cette période.")
        else:
            st.error(hist.get("message", "Erreur inconnue"))

# ✅ Tab 3: Outdoor Weather
with tab3:
    st.subheader("Météo extérieure actuelle")
    out = get_outdoor_weather()
    if out["status"] == "success":
        st.metric("🌡️ Température", f"{out['outdoor_temp']} °C")
        st.metric("💧 Humidité", f"{out['outdoor_humidity']} %")
        st.text(f"🌥️ {out['weather_description']}")
    else:
        st.error(out.get("message", "Erreur de récupération météo."))

# ✅ Lancer automatiquement sur port 8080 pour Cloud Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    os.system(f"streamlit run app.py --server.port={port} --server.enableCORS=false")