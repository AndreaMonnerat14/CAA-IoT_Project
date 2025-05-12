#%%
from flask import Flask, request, send_file, jsonify
import os
import dotenv
from flask.cli import load_dotenv
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from google.cloud import texttospeech
import requests
from datetime import datetime
import tempfile
import pandas as pd
import pytz

load_dotenv()
# You only need to uncomment the line below if you want to run your flask app locally.
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
HASH_PASSWD = os.environ.get("HASH_PASSWD")
# Initialize BigQuery client
try:
    client = bigquery.Client(project="assignment1-452312", location="europe-west6")
    print("BigQuery client initialized.")
except DefaultCredentialsError as e:
    print(f"Missing credentials: {e}")
    client = None
except Exception as e:
    print(f"Failed to initialize BigQuery client: {e}")
    client = None

#%%
app = Flask(__name__)

def get_local_datetime_info(timezone_str="Europe/Zurich"):
    now = datetime.now(ZoneInfo(timezone_str))
    return {
        "date": now.date().isoformat(),
        "time": now.time().strftime("%H:%M:%S"),
        "timestamp": now.isoformat()
    }

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
            datetime_info = get_local_datetime_info()
            data["date"] = datetime_info["date"]
            data["time"] = datetime_info["time"]
            data["timestamp"] = datetime_info["timestamp"] #using correct timestamp

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
@app.route('/get_outdoor_weather', methods=['POST'])
def get_outdoor_weather():
    try:
        # Parse the request body (assuming it's JSON)
        body = request.get_json(force=True)

        if not body or 'passwd' not in body:
            return {"status": "failed", "message": "Missing password"}, 400
        if body["passwd"] != HASH_PASSWD:
            return {"status": "failed", "message": "Incorrect password"}, 403

        lat = float(body.get("lat", 46.4))  # Default latitude
        lon = float(body.get("lon", 6.3))   # Default longitude

    except Exception as e:
        return {"status": "failed", "message": f"Invalid request: {str(e)}"}, 400

    try:
        # Construct the weather API request URL
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
@app.route('/get-indoor-data', methods=['POST'])
def get_indoor_data():
    try:
        # Parse the request body (assuming it's JSON)
        body = request.get_json(force=True)

        # Check if the password is provided and correct
        if not body or "passwd" not in body:
            return {"status": "failed", "message": "Missing password"}, 400
        if body["passwd"] != HASH_PASSWD:
            return {"status": "failed", "message": "Incorrect password"}, 403

        # Get parameters from the request body
        start_date = body.get("start_date")  # ex: "2025-05-01"
        end_date = body.get("end_date")      # ex: "2025-05-04"
        limit = int(body.get("limit", 100))  # Default limit is 100

        # Build the query for the database
        base_q = "SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather-records`"
        conditions = []

        # Add conditions based on the provided start and end dates
        if start_date:
            conditions.append(f"date >= '{start_date}'")
        if end_date:
            conditions.append(f"date <= '{end_date}'")

        if conditions:
            base_q += " WHERE " + " AND ".join(conditions)

        base_q += f" ORDER BY timestamp DESC LIMIT {limit}"

        # Try to query the database and return data
        try:
            df = client.query(base_q).to_dataframe()
            df = df.astype(str)
            data = df.to_dict(orient="records")
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "failed", "message": str(e)}, 500

    except Exception as e:
        return {"status": "failed", "message": "Invalid request or method not allowed"}, 400




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
        ORDER BY date DESC
        LIMIT 1
        """
        df = client.query(q).to_dataframe()

        if df.empty:
            return {"status": "success", "message": "No data yet", "data": {}}

        df = df.astype(str)
        latest = df.iloc[0].to_dict()
        return {"status": "success", "data": latest}

    except Exception as e:
        return {"status": "failed", "message": str(e)}, 500


@app.route('/get-all-data', methods=['POST'])
def get_all_data():
    body = request.get_json(force=True)
    if not body or body.get("passwd") != HASH_PASSWD:
        return {"status": "failed", "message": "Authentication error"}, 403
    try:
        query = "SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather-records` ORDER BY date DESC"
        df = client.query(query).to_dataframe()
        df = df.astype(str)
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        return {"status": "failed", "message": str(e)}, 500

@app.route('/get-weather-forecast', methods=['POST'])
def get_weather_forecast():
    try:
        body = request.get_json(force=True)
        if not body or body.get("passwd") != HASH_PASSWD:
            return {"status": "failed", "message": "Authentication error"}, 403

        city = body.get("city", "Lausanne")
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={OPENWEATHER_API_KEY}&lang=en"
        response = requests.get(url)
        forecast = response.json()

        return {"status": "success", "forecast": forecast}

    except Exception as e:
        return {"status": "failed", "message": str(e)}, 500

@app.route('/generate-tts', methods=['POST'])
def generate_tts():
    try:
        body = request.get_json(force=True)

        if not body or body.get("passwd") != HASH_PASSWD:
            return {"status": "failed", "message": "Authentication error"}, 403

        text = body.get("text")

        if not text:
            return jsonify({"error": "Missing 'text' in request"}), 400

        # Set up the client
        client = texttospeech.TextToSpeechClient()

        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )

        # Perform the TTS request
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )

        # Save to a temporary MP3 file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as out:
            out.write(response.audio_content)
            out.flush()
            return send_file(out.name, mimetype='audio/wav')

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)