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
import openai
from zoneinfo import ZoneInfo
from collections import Counter

load_dotenv()

# You only need to uncomment the line below if you want to run your flask app locally.
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
#GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
HASH_PASSWD = os.environ.get("HASH_PASSWD")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

#default lat and lon
lat = 46.4
lon = 6.3

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

#get the right time and date
def get_local_datetime_info(timezone_str="Europe/Zurich"):
    now = datetime.now(ZoneInfo(timezone_str))
    return {
        "date": now.date().isoformat(),
        "time": now.time().strftime("%H:%M:%S"),
        "timestamp": now.isoformat()
    }

#get city from location (ip)
def get_city_nominatim(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
    headers = {"User-Agent": "MyIoTApp/1.0"}
    resp = requests.get(url, headers=headers).json()
    return resp.get("address", {}).get("city")

#call to openAI API
def generate_llm_alert(tag, base_text):
    prompt = (
        f"You are a friendly and funny assistant generating human-like weather and environment alerts for a m5stack weather station.\n"
        f"Here is an internal alert message: \"{base_text}\"\n"
        f"Please rewrite it to sound more natural, friendly, and possibly a bit humorous. Keep it short.\n"
        f"Don't mention you're an assistant or that this is an alert.\n"
        f"Example alerts include:\n"
        f"- 'Humidity rate is quite low, drink water and do sport!'\n"
        f"- 'Temperature is too high, get naked.'\n"
        f"- 'A storm is coming, take a blanket and make tea.'\n"
        f"Now rewrite the alert:\n"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You generate creative and friendly environmental alert messages."},
                {"role": "user", "content": prompt}
            ],
           #this parameter adds creativity to the model, if you increase it, you give the llm more freedom to generate a text
            temperature=1.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenAI error] {tag}: {e}")
        return base_text

#%%
@app.route('/send-to-bigquery', methods=['GET', 'POST'])
def send_to_bigquery():
    global lat, lon
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

            #Add location from lat and lon
            try:
                data["lat"] = data.get("lat", lat)
                data["lon"] = data.get("lon", lon)
                data["city"] = get_city_nominatim(data["lat"], data["lon"])
            except Exception as e:
                print(f"Unable to load city: {e}")

            # Enrich with outdoor weather from OpenWeatherMap
            try:
                city = data["city"] if "city" in data and data["city"] else "Lausanne"
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={OPENWEATHER_API_KEY}&lang=fr"
                response = requests.get(url)
                weather_json = response.json()
                data["outdoor_temp"] = weather_json["main"]["temp"]
                data["outdoor_humidity"] = weather_json["main"]["humidity"]
                data["outdoor_weather"] = weather_json["weather"][0]["main"]
            except Exception as e:
                print(f"[WARN] Failed to fetch outdoor weather: {e}")

            # Get column types to avoid mismatch
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
            try:
                query_job = client.query(insert_q)
                query_job.result()  # Will raise a GoogleCloudError if the query fails
            except Exception as e:
                print(f"[ERROR] BigQuery insert failed: {e}")
                return {"status": "failed", "message": "BigQuery insert failed", "details": str(e)}, 500

            return {"status": "success", "data": data}

        except Exception as e:
            return {"status": "failed", "message": str(e)}, 500

    return {"status": "failed", "message": "Method not allowed"}, 405


#External weather
@app.route('/get_outdoor_weather', methods=['POST'])
def get_outdoor_weather():
    try:
        # Parse the request body (assuming it's JSON)
        body = request.get_json(force=True)

        #Check password
        if not body or 'passwd' not in body:
            return {"status": "failed", "message": "Missing password"}, 400
        if body["passwd"] != HASH_PASSWD:
            return {"status": "failed", "message": "Incorrect password"}, 403

        #trying to retrieve location
        lat = float(body.get("lat", 46.4))  # Default latitude
        lon = float(body.get("lon", 6.3))   # Default longitude

    except Exception as e:
        return {"status": "failed", "message": f"Invalid request: {str(e)}"}, 400

    try:
        # Construct the weather API request URL
        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}&lang=en"
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


#Retrieving latest values for M5 UI
@app.route('/get-latest-values', methods=['GET', 'POST'])
def get_latest_values():
    if request.method == 'POST':
        body = request.get_json(force=True)

        #password check
        if not body or "passwd" not in body:
            return {"status": "failed", "message": "Missing password"}, 400
        if body["passwd"] != HASH_PASSWD:
            return {"status": "failed", "message": "Incorrect password"}, 403

        try:
            # Query to get per-day averages of indoor values for last 3 days with data
            q = """
            WITH last_dates AS (
                SELECT DISTINCT date
                FROM `assignment1-452312.Lab4_IoT_datasets.weather-records`
                WHERE date < CURRENT_DATE()
                ORDER BY date DESC
                LIMIT 3
            )
            SELECT
                FORMAT_DATE('%d.%m', date) AS date,
                ROUND(AVG(indoor_temp), 2) AS avg_indoor_temp,
                ROUND(AVG(indoor_humidity), 2) AS avg_indoor_humidity
            FROM `assignment1-452312.Lab4_IoT_datasets.weather-records`
            WHERE date IN (SELECT date FROM last_dates)
            GROUP BY date
            ORDER BY date DESC
            """

            df = client.query(q).to_dataframe()

            if df.empty:
                return {"status": "success", "message": "No data yet", "data": {}}

            data = df.to_dict(orient="records")
            return {"status": "success", "data": data}

        except Exception as e:
            return {"status": "failed", "message": str(e)}, 500

    return {"status": "failed", "message": "Method not allowed"}, 405

#retrieve all data
@app.route('/get-all-data', methods=['POST'])
def get_all_data():
    body = request.get_json(force=True)
    #password check
    if not body or body.get("passwd") != HASH_PASSWD:
        return {"status": "failed", "message": "Authentication error"}, 403
    try:
        query = "SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather-records` ORDER BY timestamp DESC"
        query_job = client.query(query)
        query_job.result()
        df = query_job.to_dataframe()
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

        city = body.get("city", None)
        if "lat" in body and "lon" in body:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={body.get('lat')}&lon={body.get('lon')}&units=metric&appid={OPENWEATHER_API_KEY}&lang=en"
        elif city:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={OPENWEATHER_API_KEY}&lang=en"
        else:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q=Lausanne&units=metric&appid={OPENWEATHER_API_KEY}&lang=en"

        response = requests.get(url)
        forecast = response.json()

        return {"status": "success", "forecast": forecast}

    except Exception as e:
        return {"status": "failed", "message": str(e)}, 500

#special endpoint for M5 UI
@app.route('/get-weather-forecast-3', methods=['POST'])
def get_weather_forecast_3():
    global lat, lon
    try:
        body = request.get_json(force=True)
        if not body or body.get("passwd") != HASH_PASSWD:
            return jsonify({"status": "failed", "message": "Authentication error"}), 403

        city = body.get("city", None)
        lat = float(body.get("lat", lat))
        lon = float(body.get("lon", lon))

        if lat is not None and lon is not None:
            url = "https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&units=metric&appid={}&lang=en".format(
                lat, lon, OPENWEATHER_API_KEY)
        elif city:
            url = "https://api.openweathermap.org/data/2.5/forecast?q={}&units=metric&appid={}&lang=en".format(
                city, OPENWEATHER_API_KEY)
        else:
            # Default to Lausanne
            url = "https://api.openweathermap.org/data/2.5/forecast?q=Lausanne&units=metric&appid={}&lang=en".format(
                OPENWEATHER_API_KEY)

        response = requests.get(url)
        response.raise_for_status()
        forecast = response.json()

        if "list" not in forecast:
            return jsonify({"status": "failed", "message": "Invalid forecast data"}), 500

        # Process forecast to next 3 days summary (excluding today)
        forecast_list = forecast["list"]
        days = {}
        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if not dt_txt:
                continue
            date_str = dt_txt.split()[0]
            days.setdefault(date_str, []).append(entry)

        today = datetime.today().date()

        sorted_dates = sorted(d for d in days.keys() if datetime.strptime(d, "%Y-%m-%d").date() > today)
        next_dates = sorted_dates[:3]

        #Creating a special JSON format to avoid overloading M5stack with data
        result = {}
        for date in next_dates:
            entries = days[date]
            temps = [e["main"]["temp"] for e in entries if "main" in e and "temp" in e["main"]]
            descriptions = [e["weather"][0]["description"] for e in entries if "weather" in e and len(e["weather"]) > 0]

            min_temp = min(temps) if temps else None
            max_temp = max(temps) if temps else None
            common_desc = Counter(descriptions).most_common(1)[0][0] if descriptions else "No data"

            result[date] = {
                "min": min_temp,
                "max": max_temp,
                "description": common_desc
            }

        return jsonify({"status": "success", "forecast_summary": result})

    except Exception as e:
        return jsonify({"status": "failed", "message": str(e)}), 500

#Generating text-to-speech including the openAI API variations
@app.route('/generate-tts-bis', methods=['POST'])
def generate_tts_bis():
    try:
        body = request.get_json(force=True)

        if not body or body.get("passwd") != HASH_PASSWD:
            return {"status": "failed", "message": "Authentication error"}, 403

        #alerts is JSON (e.g. with tempHigh:True) identifying problematic variables (temp too high for instance)
        body = body.get("alerts")
        possible_alerts = {"HumLow" : "Humidity rate is quite low, drink water and do sport!",
                           "HumHigh" : "Humidity rate is too high, open a window!",
                           "TempLow": "Temperature is too low, get a jacket!",
                           "TempHigh": "Temperature is too high, get naked.",
                           "Air": "Air quality is rather bad, open a window!",
                           "Storm": "A storm is coming, take a blanket and make tea.",
                           "Rain": "It's raining, take an umbrella if you're going out!",
                           "Sun": "You live in a beautiful sunny world, take sunglasses and have a cocktail!",
                           "Warm": "It's quite warm outside, don't plan skying.",
                           "Cold": "It's cold outside, wear warm clothes."}

        #Adding variations to our base alerts
        text = ""
        for tag, base_text in possible_alerts.items():
            if body.get(tag):
                variation = generate_llm_alert(tag, base_text)
                text += f"{variation} "

        if not text.strip():
            return jsonify({"error": "No alert triggered"}), 200

        # Set up the google tts client
        client = texttospeech.TextToSpeechClient()

        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-F",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=8000,
            speaking_rate=0.85,
            effects_profile_id=["telephony-class-application"]  # Optimized for 8kHz
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
