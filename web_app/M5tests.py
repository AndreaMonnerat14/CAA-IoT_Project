from m5stack import *
from uiflow import *
import unit
import lvgl as lv
import time
import network
import urequests
import hashlib
import ubinascii
import wifiCfg
import ntptime
import ujson

# Init screen
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x000000)

# Init LVGL
lv.init()

# Init sensors
env3 = unit.get(unit.ENV3, unit.PORTA)
air = unit.get(unit.TVOC, unit.PORTC)
wait(1)

# password
passwd = "okmec"
hash_bytes = hashlib.sha256(passwd.encode()).digest()
passwd = ubinascii.hexlify(hash_bytes).decode()

# Time
ntp = ntptime.client(host='cn.pool.ntp.org', timezone=2)

# location
ip_info = urequests.get("http://ip-api.com/json").json()
lat = ip_info.get("lat")
lon = ip_info.get("lon")

# Flask URL
flask_url = "https://caa-iot-project-1008838592938.europe-west6.run.app"


# TTS function
def get_tts(text):
    url = str(flask_url + "/generate-tts")
    response = urequests.post(url, json=text)
    if response.status_code == 200:
        with open('tts.wav', 'wb') as f:
            f.write(response.content)
        response.close()
        return True
    else:
        print("TTS request failed:", response.text)
        return False


def get_latest_values():
    headers = {'Content-Type': 'application/json'}
    payload = {"passwd": passwd}

    try:
        response = urequests.post(str(flask_url + "/get-latest-values"), headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                data = result["data"]

                # Initialize dictionaries to hold results
                avg_temp_by_day = {}
                avg_humidity_by_day = {}

                for entry in data:
                    day = entry["date"]
                    avg_temp_by_day[day] = float(entry["avg_indoor_temp"])
                    avg_humidity_by_day[day] = float(entry["avg_indoor_humidity"])

                response.close()
                return avg_temp_by_day, avg_humidity_by_day
            else:
                print("Error from server:", result["message"])
        else:
            print("HTTP Error:", response.status_code)
        response.close()
    except Exception as e:
        print("Request failed:", e)

    return {}, {}  # Return empty dicts if something went wrong


def get_outdoor_weather():
    data = {"passwd": passwd}
    response = urequests.post(str(flask_url + '/get_outdoor_weather'), json=data)
    if response.status_code == 200:
        result = response.json()
        if result["status"] == "success":
            response.close()
            return result
    else:
        response.close()
        return None


# tts_alerts
tts_alerts = {"passwd": passwd,
              "alerts": {"HumLow": False,
                         "HumHigh": False,
                         "TempLow": False,
                         "TempHigh": False,
                         "Air": False,
                         "Storm": False,
                         "Rain": False,
                         "Sun": False,
                         "Warm": False,
                         "Cold": False}}

# retrieving latest data (3 last recorded days averages)
temp_hist_data, humidity_hist_data = get_latest_values()

# Create screen
scr = lv.obj()
scr.set_style_local_bg_color(scr.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x000000))

# Create labels
temp_label = lv.label(scr)
temp_label.set_style_local_text_color(temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x00FF00))
temp_label.set_style_local_text_font(temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
temp_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 10)
temp_label.set_text("coucou")

hum_label = lv.label(scr)
hum_label.set_style_local_text_color(hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x00FFFF))
hum_label.set_style_local_text_font(hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
hum_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 40)

tvoc_label = lv.label(scr)
tvoc_label.set_style_local_text_color(tvoc_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFF00FF))
tvoc_label.set_style_local_text_font(tvoc_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
tvoc_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 70)

eco2_label = lv.label(scr)
eco2_label.set_style_local_text_color(eco2_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFFFF00))
eco2_label.set_style_local_text_font(eco2_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
eco2_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 100)

clock_label = lv.label(scr)
clock_label.set_style_local_text_color(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))
clock_label.set_style_local_text_font(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_18)
clock_label.align(scr, lv.ALIGN.IN_TOP_RIGHT, -10, 10)

# Outdoor Temperature Label
out_temp_label = lv.label(scr)
out_temp_label.set_style_local_text_color(out_temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x00FFFF))  # Cyan
out_temp_label.set_style_local_text_font(out_temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
out_temp_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 130)  # Slightly below eco2_label

# Outdoor Humidity Label
out_hum_label = lv.label(scr)
out_hum_label.set_style_local_text_color(out_hum_label.PART.MAIN, lv.STATE.DEFAULT,
                                         lv.color_hex(0xADFF2F))  # Light green
out_hum_label.set_style_local_text_font(out_hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
out_hum_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 160)

# Outdoor Weather Description Label
out_weather_label = lv.label(scr)
out_weather_label.set_style_local_text_color(out_weather_label.PART.MAIN, lv.STATE.DEFAULT,
                                             lv.color_hex(0xFFFFFF))  # White
out_weather_label.set_style_local_text_font(out_weather_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
out_weather_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 190)

error_label = lv.label(scr)
error_label.set_style_local_text_color(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFF0000))
error_label.set_style_local_text_font(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_18)
error_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 120)
error_label.set_text("")

# Load screen
lv.scr_load(scr)

temp = env3.temperature
hum = env3.humidity
tvoc = air.TVOC
eco2 = air.eCO2
outData = get_outdoor_weather()
outTemp = outData.get("outdoor_temp", "...")
outWeather = outData.get("weather_description")
outHum = outData.get("outdoor_humidity")

temp_label.set_text(str(temp) + "°C")
hum_label.set_text(str(hum) + "%")
tvoc_label.set_text(str(tvoc))
eco2_label.set_text(str(eco2))
clock_label.set_text(str(ntp.formatDatetime('-', ':')))

t = 0
tts_timer = 3600


# Update function
def update_labels():
    global temp, hum, tvoc, eco2, temp_label, hum_label, tvoc_label, eco2_lobal, clock_label, t
    try:
        temp = round(env3.temperature)
        hum = round(env3.humidity)
        tvoc = round(air.TVOC)
        eco2 = round(air.eCO2)
        if t % 1800 == 0:
            outData = get_outdoor_weather()
            outTemp = outData.get("outdoor_temp", "...")
            outWeather = outData.get("weather_description")
            outHum = outData.get("outdoor_humidity")

        temp_label.set_text(str(temp) + "°C")
        hum_label.set_text(str(hum) + "%")
        tvoc_label.set_text(str(tvoc))
        eco2_label.set_text(str(eco2))
        clock_label.set_text(str(ntp.formatDatetime('-', ':')))
        out_temp_label.set_text(str(outTemp) + "°C")
        out_hum_label.set_text(str(outHum) + "%")

    except Exception as e:
        error_label.set_text("ERROR")
        print("Sensor read error:", e)


while True:
    if t % 300 == 0:
        data = {
            "passwd": passwd,
            "values": {
                "indoor_temp": temp,
                "indoor_humidity": hum,
                "tvoc": tvoc,
                "eco2": eco2,
                "lat": lat,
                "lon": lon
            }
        }
        res = urequests.post(str(flask_url + "/send-to-bigquery"), json=data)
        print("POST status:", res.status_code)
        res.close()
        """
        #movement and tts
        if get_movement_sensor & tts_timer >3600:
            if get_tts(tts_alerts):
                speaker.playWAV("tts.wav", volume=6)
        """
    update_labels()
    t += 1
    wait(1)