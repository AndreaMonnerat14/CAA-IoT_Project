#%%
from flask import Flask, request
import os
import dotenv
from flask.cli import load_dotenv
from google.cloud import bigquery
import requests
from datetime import datetime
import pandas as pd

load_dotenv()
# You only need to uncomment the line below if you want to run your flask app locally.
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
HASH_PASSWD = os.environ.get("HASH_PASSWD")
# Initialize BigQuery client
try:
    client = bigquery.Client(project="assignment1-452312", location="europe-west6")
except Exception as e:
    print(f"Error initializing BigQuery client: {e}")
    client = None

#%%
app = Flask(__name__)

#%%
@app.route('/send-to-bigquery', methods=['GET', 'POST'])
def send_to_bigquery():
    if request.method == 'GET':
        return {"status": "ready", "message": "Send POST data to store in BigQuery"}

    if request.method == 'POST':
        try:
            body = request.get_json(force=True)

            # Auth check
            if not body or "passwd" not in body:
                return {"status": "failed", "message": "Missing password"}, 400
            if body["passwd"] != HASH_PASSWD:
                return {"status": "failed", "message": "Incorrect password"}, 403

            # Data presence check
            data = body.get("values")
            if not data:
                return {"status": "failed", "message": "Missing 'values' field"}, 400

            # Add current date/time if not present
            if "date" not in data:
                data["date"] = datetime.utcnow().date().isoformat()
            if "time" not in data:
                data["time"] = datetime.utcnow().time().strftime("%H:%M:%S")

            # Enrich with outdoor weather from OpenWeatherMap
            try:
                city = data["city"] if "city" in data and data["city"] else "Lausanne"
                data.pop("city", None)
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={OPENWEATHER_API_KEY}&lang=fr"
                response = requests.get(url)
                weather_json = response.json()
                data["outdoor_temp"] = weather_json["main"]["temp"]
                data["outdoor_humidity"] = weather_json["main"]["humidity"]
                data["outdoor_weather"] = weather_json["weather"][0]["main"]
            except Exception as e:
                print(f"[WARN] Failed to fetch outdoor weather: {e}")

            # Get column types
            schema_query = """
            SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather-records` LIMIT 1
            """
            query_job = client.query(schema_query)
            df = query_job.to_dataframe()

            # Build insert query
            names = ""
            values = ""
            for k, v in data.items():
                names += f"{k},"
                if df.dtypes[k] == float:
                    values += f"{v},"
                else:
                    values += f"'{v}',"
            names = names.rstrip(",")
            values = values.rstrip(",")
            insert_q = f"""INSERT INTO `assignment1-452312.Lab4_IoT_datasets.weather-records` ({names}) VALUES({values})"""

            # Execute insert
            client.query(insert_q)

            return {"status": "success", "data": data}

        except Exception as e:
            return {"status": "failed", "message": str(e)}, 500

    return {"status": "failed", "message": "Method not allowed"}, 405


# Météo extérieur pour streamlit
@app.route('/get_outdoor_weather', methods=['GET', 'POST'])
def get_outdoor_weather():
    if request.get_json(force=True).get("passwd") != HASH_PASSWD:
        return {"status": "failed", "message": "Incorrect password"}, 403
    if 'passwd' not in request.get_json(force=True):
        return {"status": "failed", "message": "Missing password"}, 400

    try:
        lat, lon = 46.4, 6.3  # Rolle par exemple

        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}&lang=fr"
        )

        response = requests.get(url)
        weather = response.json()

        return {
            "status": "success",
            "outdoor_temp": weather["main"]["temp"],
            "outdoor_humidity": weather["main"]["humidity"],
            "weather_description": weather["weather"][0]["description"]
        }

    except Exception as e:
        return {"status": "failed", "message": str(e)}, 500

# Pour afficher les données indoor sur le streamlit
@app.route('/get-indoor-data', methods=['GET', 'POST'])
def get_indoor_data():
    if request.method == 'POST':
        body = request.get_json(force=True)

        if not body or "passwd" not in body:
            return {"status": "failed", "message": "Missing password"}, 400
        if body["passwd"] != HASH_PASSWD:
            return {"status": "failed", "message": "Incorrect password"}, 403

        start_date = body.get("start_date")  # ex: "2025-05-01"
        end_date = body.get("end_date")      # ex: "2025-05-04"
        limit = int(body.get("limit", 100))

        # Build query
        base_q = "SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather-records`"
        conditions = []

        if start_date:
            conditions.append(f"timestamp >= '{start_date}'")
        if end_date:
            conditions.append(f"timestamp <= '{end_date}'")

        if conditions:
            base_q += " WHERE " + " AND ".join(conditions)

        base_q += f" ORDER BY timestamp DESC LIMIT {limit}"

        try:
            df = client.query(base_q).to_dataframe()
            data = df.to_dict(orient="records")
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "failed", "message": str(e)}, 500

    return {"status": "failed", "message": "Method not allowed"}, 405


# Pour afficher les dernières valeurs du m5stack au redémarrage
@app.route('/get-latest-values', methods=['GET', 'POST'])
def get_latest_values():
    if request.method == 'POST':
        body = request.get_json(force=True)

        if not body or "passwd" not in body:
            return {"status": "failed", "message": "Missing password"}, 400
        if body["passwd"] != HASH_PASSWD:
            return {"status": "failed", "message": "Incorrect password"}, 403

    try:
        q = """
        SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather-records`
        ORDER BY timestamp DESC
        LIMIT 1
        """
        df = client.query(q).to_dataframe()

        if df.empty:
            return {"status": "success", "message": "No data yet", "data": {}}

        latest = df.iloc[0].to_dict()
        return {"status": "success", "data": latest}

    except Exception as e:
        return {"status": "failed", "message": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)