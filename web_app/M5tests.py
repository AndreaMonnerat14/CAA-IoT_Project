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

"""
#Wifi connection
networks = [
    ('Redmi Note 7', 'local123'),
    ('iot-unil', '4u6uch4hpY9pJ2f9'),
    ('OtherNetwork', 'password123')
]

wifi_status = M5Label("Connecting to WiFi...", x=20, y=20, color=0x000000, font=FONT_MONT_18)

def connect_to_known_networks():
    available = wifiCfg.wlan_sta.scan()
    available_names = [net[0].decode('utf-8') for net in available]

    for ssid, password in networks:
        if ssid in available_names:
            wifi_status.set_text("Trying " + str(ssid) + "...")
            wifiCfg.doConnect(ssid, password)
            for i in range(10):
                if wifiCfg.wlan_sta.isconnected():
                    ip = wifiCfg.wlan_sta.ifconfig()[0]
                    wifi_status.set_text("Connected: " + ip)
                    return True
                time.sleep(1)
    wifi_status.set_text("No known networks found.")
    return False

#--- At start --- #
if connect_to_known_networks():
  wifi_status.set_text("Connected !")
"""
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
temp_label.set_text("")

hum_label = lv.label(scr)
hum_label.set_style_local_text_color(hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x00FFFF))
hum_label.set_style_local_text_font(hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
hum_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 40)
hum_label.set_text("")

tvoc_label = lv.label(scr)
tvoc_label.set_style_local_text_color(tvoc_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFF00FF))
tvoc_label.set_style_local_text_font(tvoc_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
tvoc_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 70)
tvoc_label.set_text("")

eco2_label = lv.label(scr)
eco2_label.set_style_local_text_color(eco2_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFFFF00))
eco2_label.set_style_local_text_font(eco2_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
eco2_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 100)
eco2_label.set_text("")

clock_label = lv.label(scr)
clock_label.set_style_local_text_color(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))
clock_label.set_style_local_text_font(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_18)
clock_label.align(scr, lv.ALIGN.IN_TOP_RIGHT, -10, 10)
clock_label.set_text("")

# Outdoor Temperature Label
out_temp_label = lv.label(scr)
out_temp_label.set_style_local_text_color(out_temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x00FFFF))  # Cyan
out_temp_label.set_style_local_text_font(out_temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
out_temp_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 130)  # Slightly below eco2_label
out_temp_label.set_text("")

# Outdoor Humidity Label
out_hum_label = lv.label(scr)
out_hum_label.set_style_local_text_color(out_hum_label.PART.MAIN, lv.STATE.DEFAULT,
                                         lv.color_hex(0xADFF2F))  # Light green
out_hum_label.set_style_local_text_font(out_hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
out_hum_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 160)
out_hum_label.set_text("")

# Outdoor Weather Description Label
out_weather_label = lv.label(scr)
out_weather_label.set_style_local_text_color(out_weather_label.PART.MAIN, lv.STATE.DEFAULT,
                                             lv.color_hex(0xFFFFFF))  # White
out_weather_label.set_style_local_text_font(out_weather_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
out_weather_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 190)
out_weather_label.set_text("")

error_label = lv.label(scr)
error_label.set_style_local_text_color(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFF0000))
error_label.set_style_local_text_font(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_18)
error_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 120)
error_label.set_text("")

btn = lv.btn(scr)
btn.set_size(100, 50)
btn.align(scr, lv.ALIGN.IN_BOTTOM_RIGHT, -10, -10)

style_hist = lv.style_t()
style_hist.init()
style_hist.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x00AFFF))
style_hist.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x00AFFF))

style_back = lv.style_t()
style_back.init()
style_back.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))
style_back.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))

label = lv.label(btn)
label.set_text("Hist")
label.align(btn, lv.ALIGN.CENTER, 0, 0)

btn.add_style(btn.PART.MAIN, style_hist)
state = False


def get_forecast():
    headers = {'Content-Type': 'application/json'}
    payload = {"passwd": passwd, "lat": lat, "lon": lon}

    try:
        response = urequests.post(str(flask_url + "/get-weather-forecast"), headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                return result["forecast"]
            else:
                print("Server error:", result["message"])
        else:
            print("HTTP error:", response.status_code)
    except Exception as e:
        print("Forecast fetch failed:", e)
    return {}


forecast = get_forecast()

main_labels = [temp_label, hum_label, tvoc_label, eco2_label, clock_label, out_temp_label, out_hum_label]
history_labels = []


def show_history_data(temp_data, hum_data):
    col_x_offsets = [-90, 0, 90]  # X offsets for 3 columns

    # Clear any existing labels
    global history_labels
    for lbl in history_labels:
        lbl.delete()
    history_labels = []

    days = list(temp_data.keys())
    for i, day in enumerate(days):
        x = col_x_offsets[i]

        # Date label
        lbl_date = lv.label(scr)
        lbl_date.set_text(day)
        lbl_date.set_style_local_text_color(lbl_date.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))
        lbl_date.set_style_local_text_font(lbl_date.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_14)
        lbl_date.align(scr, lv.ALIGN.CENTER, x, -40)
        history_labels.append(lbl_date)

        # Avg Temp label
        lbl_temp = lv.label(scr)
        lbl_temp.set_text(str(temp_data[day]) + "°C")
        lbl_temp.set_style_local_text_color(lbl_temp.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFFA500))  # Orange
        lbl_temp.set_style_local_text_font(lbl_temp.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
        lbl_temp.align(scr, lv.ALIGN.CENTER, x, -10)
        history_labels.append(lbl_temp)

        # Avg Hum label
        lbl_hum = lv.label(scr)
        lbl_hum.set_text(str(hum_data[day]) + "%")
        lbl_hum.set_style_local_text_color(lbl_hum.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x00FF00))  # Green
        lbl_hum.set_style_local_text_font(lbl_hum.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
        lbl_hum.align(scr, lv.ALIGN.CENTER, x, 20)
        history_labels.append(lbl_hum)
    hist_title_lbl = lv.label(scr)
    hist_title_lbl.set_text("Last recorded days' averages")
    hist_title_lbl.set_style_local_text_color(lbl_date.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))
    hist_title_lbl.set_style_local_text_font(lbl_date.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_14)
    hist_title_lbl.align(scr, lv.ALIGN.CENTER, 0, -70)
    history_labels.append(hist_title_lbl)


def display_forecast(forecast):
    forecast_labels = []
    try:
        days = {}
        for entry in forecast["list"]:
            dt_txt = entry["dt_txt"]
            date = dt_txt.split()[0]
            if date not in days:
                days[date] = []
            days[date].append(entry)

        selected_days = list(days.keys())[:3]

        for i, day in enumerate(selected_days):
            entries = days[day]
            temps = [e["main"]["temp"] for e in entries]
            conditions = [e["weather"][0]["description"] for e in entries]

            avg_temp = round(sum(temps) / len(temps), 1)
            common_weather = max(set(conditions), key=conditions.count)

            label = lv.label(scr)
            label.set_style_local_text_color(label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x00FFAA))
            label.set_style_local_text_font(label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_20)
            label.set_text(str(day[8:]) + "." + str(day[5:7]) + ":" + str(avg_temp) + "°C  " + str(common_weather))
            label.align(scr, lv.ALIGN.IN_TOP_LEFT, 10 + i * 100, 180)
            forecast_labels.append(label)
    except Exception as e:
        print("Display forecast error:", e)
    return forecast_labels


# Button toggle action
def action(obj, event):
    global state, history_labels, main_labels
    if event == lv.EVENT.CLICKED:
        if not state:
            # Switch to historical view
            for lbl in main_labels:
                lbl.set_hidden(True)
            btn.add_style(btn.PART.MAIN, style_back)
            label.set_text("Back")
            show_history_data(temp_hist_data, humidity_hist_data)
        else:
            # Back to main view
            for lbl in main_labels:
                lbl.set_hidden(False)
            for lbl in history_labels:
                lbl.delete()
            history_labels.clear()
            btn.add_style(btn.PART.MAIN, style_hist)
            label.set_text("Hist")
        state = not state


btn.set_event_cb(action)

btn_forecast = lv.btn(scr)
btn_forecast.set_size(100, 50)
btn_forecast.align(scr, lv.ALIGN.IN_BOTTOM_LEFT, 10, -10)
label_forecast = lv.label(btn_forecast)
label_forecast.set_text("Forecast")
label_forecast.align(btn_forecast, lv.ALIGN.CENTER, 0, 0)

forecast_state = False
forecast_labels = []


def forecast_action(obj, event):
    global forecast_state, forecast_labels, forecast
    if event == lv.EVENT.CLICKED:
        if not forecast_state:
            forecast_labels = display_forecast(forecast)
            label_forecast.set_text("Back")
        else:
            for label in forecast_labels:
                label.delete()
            forecast_labels = []
            label_forecast.set_text("Forecast")
        forecast_state = not forecast_state


btn_forecast.set_event_cb(forecast_action)

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
tts_timer = 3400


# Update function
def update_labels():
    global temp, hum, tvoc, eco2, temp_label, hum_label, tvoc_label, eco2_label, clock_label, outTemp, outHum, t
    try:
        temp = round(env3.temperature)
        hum = round(env3.humidity)
        tvoc = round(air.TVOC)
        eco2 = round(air.eCO2)
        if t % 1800 == 0:
            outData = get_outdoor_weather()
            outTemp = outData.get("outdoor_temp", None)
            if outTemp:
                outTemp = round(outTemp)
            else:
                outTemp = ""
            outWeather = outData.get("weather_description", "")
            outHum = outData.get("outdoor_humidity", "")
            out_temp_label.set_text(str(outTemp) + "°C")
            out_hum_label.set_text(str(outHum) + "%")

        temp_label.set_text(str(temp) + "°C")
        hum_label.set_text(str(hum) + "%")
        tvoc_label.set_text(str(tvoc))
        eco2_label.set_text(str(eco2))
        clock_label.set_text(str(ntp.formatDatetime('-', ':')))


    except Exception as e:
        error_label.set_text("ERROR: Cannot update values.")
        print("Sensor read error:", e)


"""
def update_flags():
  global tts_alerts, temp, hum, tvoc, eco2,outTemp, outHum, t
  if temp
"""

# Main loop
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
        tts_timer = 0
            if get_tts(tts_alerts):
                speaker.playWAV("tts.wav", volume=6)
        """
    if t % 3600 == 0 & t != 0:
        forecast = get_forecast()
    update_labels()
    t += 1
    tts_timer += 1
    wait(1)