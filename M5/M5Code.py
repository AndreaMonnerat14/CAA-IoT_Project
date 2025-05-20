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
import _thread
import lodepng

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
pir = unit.get(unit.PIR, unit.PORTB)
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
city = ip_info.get("city")

# Flask URL
flask_url = "https://caa-iot-project-1008838592938.europe-west6.run.app"


def get_latest_values():
    global passwd, flask_url
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
    global passwd, flask_url
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

# Create screens
scr1 = lv.obj()
scr1.set_style_local_bg_color(scr1.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x0d3853))

scr = lv.obj()
scr.set_style_local_bg_color(scr.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x0d3853))

# Loading label
loading_label = lv.label(scr1)
loading_label.align(scr1, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 10)
loading_label.set_style_local_text_color(loading_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
loading_label.set_style_local_text_font(loading_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
loading_label.set_text("Data loading...")

# Load screen
lv.scr_load(scr1)

# Date/time label at top center
clock_label = lv.label(scr)
clock_label.set_text("")
clock_label.align(scr, lv.ALIGN.IN_TOP_MID, -20, 5)
clock_label.set_style_local_text_color(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))

# "In" label on center left
label_in = lv.label(scr)
label_in.set_text("In")
label_in.align(scr, lv.ALIGN.CENTER, -130, -80)  # Adjust -100 as needed for left centering
label_in.set_style_local_text_color(label_in.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xd3d0d0))
label_in.set_style_local_text_font(label_in.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
label_in.set_hidden(True)

# In table (2x2 grid layout manually created using labels)
temp_label = lv.label(scr)
temp_label.set_text("")
temp_label.align(label_in, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 10)
temp_label.set_style_local_text_color(temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
temp_label.set_style_local_text_font(temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)

hum_label = lv.label(scr)
hum_label.set_text("")
hum_label.align(temp_label, lv.ALIGN.OUT_RIGHT_TOP, 65, 0)
hum_label.set_style_local_text_color(hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
hum_label.set_style_local_text_font(hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)

tvoc_label = lv.label(scr)
tvoc_label.set_text("")
tvoc_label.align(temp_label, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 10)
tvoc_label.set_style_local_text_color(tvoc_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
tvoc_label.set_style_local_text_font(tvoc_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_18)

eco2_label = lv.label(scr)
eco2_label.set_text("")
eco2_label.align(tvoc_label, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 10)
eco2_label.set_style_local_text_color(eco2_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
eco2_label.set_style_local_text_font(eco2_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_18)

# "Out" label on center right
label_out = lv.label(scr)
label_out.set_text("Out")
label_out.align(scr, lv.ALIGN.CENTER, 20, -80)  # Adjust 100 as needed for right centering
label_out.set_style_local_text_color(label_out.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xd3d0d0))
label_out.set_style_local_text_font(label_out.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
label_out.set_hidden(True)

# Out table (1x2)
out_temp_label = lv.label(scr)
out_temp_label.set_text("")
out_temp_label.align(label_out, lv.ALIGN.OUT_BOTTOM_LEFT, 0, 10)
out_temp_label.set_style_local_text_color(out_temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))  # Cyan
out_temp_label.set_style_local_text_font(out_temp_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)

out_hum_label = lv.label(scr)
out_hum_label.set_text("")
out_hum_label.align(out_temp_label, lv.ALIGN.OUT_RIGHT_TOP, 65, 0)
out_hum_label.set_style_local_text_color(out_hum_label.PART.MAIN, lv.STATE.DEFAULT,
                                         lv.color_hex(0xf4f6f7))  # Light green
out_hum_label.set_style_local_text_font(out_hum_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
# Weather icon below out table, center-right
weather_icon = lv.img(scr)
weather_icon.set_size(64, 64)  # adjust size as needed
weather_icon.align(out_temp_label, lv.ALIGN.OUT_BOTTOM_LEFT, 20, 15)
weather_icon.set_hidden(True)

# Outdoor Weather Description Label
out_weather_label = lv.label(scr)
out_weather_label.set_style_local_text_color(out_weather_label.PART.MAIN, lv.STATE.DEFAULT,
                                             lv.color_hex(0xFFFFFF))  # White
out_weather_label.set_style_local_text_font(out_weather_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
out_weather_label.align(scr, lv.ALIGN.IN_TOP_MID, 0, 190)
out_weather_label.set_text("")

error_textarea = lv.textarea(scr)
error_textarea.set_size(300, 100)
error_textarea.align(scr, lv.ALIGN.IN_BOTTOM_MID, 0, -10)
error_textarea.set_text("")  # start empty
error_textarea.set_cursor_hidden(True)  # hide cursor so it looks like a label
error_textarea.set_style_local_text_color(scr.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x000000))
error_textarea.set_hidden(True)  # hidden by default

error_counter = 0
error_triggered = False


def display_error(msg):
    global error_triggered
    if msg:
        error_textarea.set_text(msg)
        error_textarea.set_hidden(False)
        wait(2)
        error_triggered = True
        error_textarea.set_hidden(True)
    else:
        error_textarea.set_text("")
        error_textarea.set_hidden(True)
        error_triggered = False


"""
#---- BTNs-----#
btn = lv.btn(scr)
btn.set_size(100, 50)
btn.align(scr, lv.ALIGN.IN_BOTTOM_RIGHT, -10, -10)

style_hist = lv.style_t()
style_hist.init()
style_hist.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x3260c8))
style_hist.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x233560))

style_back = lv.style_t()
style_back.init()
style_back.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x3260c8))
style_back.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x233560))

label = lv.label(btn)
label.set_text("Hist")
label.align(btn, lv.ALIGN.CENTER, 0, 0)

btn.add_style(btn.PART.MAIN, style_hist)
"""
state = False


def get_forecast():
    global passwd, flask_url, lat, lon, city
    headers = {'Content-Type': 'application/json'}
    payload = {"passwd": passwd, "lat": lat, "lon": lon, "city": city}

    try:
        response = urequests.post(str(flask_url + "/get-weather-forecast-3"), headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                return result
            else:
                error_label.set_text("Server error:" + result["message"])
        else:
            error_label.set_text("HTTP error:" + str(response.status_code))
    except Exception as e:
        error_label.set_text("Forecast fetch failed:")
    return {}


forecast = get_forecast()

# Track all label groups for cleanup
forecast_labels = []
history_labels = []
main_labels = [temp_label, hum_label, tvoc_label, eco2_label, clock_label, out_temp_label, out_hum_label, label_in,
               label_out]
state = "main"  # can be 'main', 'hist', or 'forecast'

# ----------- HIST BUTTON -----------
btn = lv.btn(scr)
btn.set_size(100, 50)
btn.align(scr, lv.ALIGN.IN_BOTTOM_RIGHT, -10, -10)

style_hist = lv.style_t()
style_hist.init()
style_hist.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x3260c8))
style_hist.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x233560))
style_hist.set_style_local_text_color(lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))

style_back = lv.style_t()
style_back.init()
style_back.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0xeeeeee))
style_back.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0xeeeeee))

label = lv.label(btn)
label.set_text("History")
label.align(btn, lv.ALIGN.CENTER, 0, 0)

btn.add_style(btn.PART.MAIN, style_hist)

# ----------- FORECAST BUTTON -----------
btn_forecast = lv.btn(scr)
btn_forecast.set_size(100, 50)
btn_forecast.align(scr, lv.ALIGN.IN_BOTTOM_LEFT, 10, -10)

label_forecast = lv.label(btn_forecast)
label_forecast.set_text("Forecast")
label_forecast.align(btn_forecast, lv.ALIGN.CENTER, 0, 0)

btn_forecast.add_style(btn.PART.MAIN, style_hist)


def show_history_data(temp_data, hum_data):
    col_x_offsets = [-90, 0, 90]
    global history_labels
    for lbl in history_labels:
        lbl.delete()
    history_labels = []

    days = list(temp_data.keys())
    for i, day in enumerate(days):
        x = col_x_offsets[i]

        lbl_date = lv.label(scr)
        lbl_date.set_text(day)
        lbl_date.set_style_local_text_color(lbl_date.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
        lbl_date.set_style_local_text_font(lbl_date.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_14)
        lbl_date.align(scr, lv.ALIGN.CENTER, x, -40)
        history_labels.append(lbl_date)

        lbl_temp = lv.label(scr)
        lbl_temp.set_text(str(round(temp_data[day])) + "°C")
        lbl_temp.set_style_local_text_color(lbl_temp.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
        lbl_temp.set_style_local_text_font(lbl_temp.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
        lbl_temp.align(scr, lv.ALIGN.CENTER, x, -10)
        history_labels.append(lbl_temp)

        lbl_hum = lv.label(scr)
        lbl_hum.set_text(str(round(hum_data[day])) + "%")
        lbl_hum.set_style_local_text_color(lbl_hum.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
        lbl_hum.set_style_local_text_font(lbl_hum.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
        lbl_hum.align(scr, lv.ALIGN.CENTER, x, 20)
        history_labels.append(lbl_hum)

    hist_title_lbl = lv.label(scr)
    hist_title_lbl.set_text("Last recorded days' averages")
    hist_title_lbl.set_style_local_text_color(hist_title_lbl.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
    hist_title_lbl.set_style_local_text_font(hist_title_lbl.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_14)
    hist_title_lbl.align(scr, lv.ALIGN.CENTER, 0, -70)
    history_labels.append(hist_title_lbl)


def display_forecast(forecast):
    global forecast_labels
    try:
        # Step 1: Clear old labels
        try:
            for label in forecast_labels:
                label.delete()
            forecast_labels = []
        except Exception as e:
            display_error("Error clearing labels: " + str(e))
            return

        # Step 2: Extract forecast summary
        try:
            if "forecast_summary" not in forecast:
                display_error("Missing 'forecast_summary' in forecast")
                return
            summary = forecast["forecast_summary"]
            if not summary:
                display_error("Forecast summary is empty")
                return
        except Exception as e:
            display_error("Error extracting summary: " + str(e))
            return

        # Step 3: Display forecast in 3 columns
        col_x_offsets = [-80, 10, 100]
        dates = list(summary.keys())
        if not dates:
            display_error("No dates found in forecast summary")
            return

        dates.sort()
        max_days = min(3, len(dates))

        # Column titles
        titles = ["", "Min", "Max", ""]
        for i, title in enumerate(titles):
            lbl = lv.label(scr)
            lbl.set_text(title)
            lbl.set_style_local_text_color(lbl.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
            lbl.set_style_local_text_font(lbl.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_14)
            lbl.align(scr, lv.ALIGN.CENTER, -130, -90 + i * 30)
            forecast_labels.append(lbl)

        for i in range(max_days):
            x = col_x_offsets[i]
            date = dates[i]
            day_info = summary.get(date, {})

            # Date formatting
            if len(date) >= 10:
                day_str = date[8:10] + "." + date[5:7]
            else:
                day_str = date

            min_temp = str(round(day_info.get("min", "?")))
            max_temp = str(round(day_info.get("max", "?")))
            desc = day_info.get("description", "No data")

            values = [day_str, min_temp + "°C", max_temp + "°C", desc]

            for j, val in enumerate(values):
                try:
                    lbl = lv.label(scr)
                    lbl.set_text(str(val))
                    lbl.set_style_local_text_color(lbl.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
                    lbl.set_style_local_text_font(lbl.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_18)
                    lbl.align(scr, lv.ALIGN.CENTER, x, -90 + j * 30)
                    forecast_labels.append(lbl)
                except Exception as le:
                    display_error("Label error (col " + str(i) + " row " + str(j) + "): " + str(le))

    except Exception as e:
        display_error("Unhandled error: " + str(e))


# ---------- HIST BUTTON ----------
def action(obj, event):
    global state, img
    if event == lv.EVENT.CLICKED:
        if state == "main":
            # switch to history
            for lbl in main_labels:
                lbl.set_hidden(True)
            btn.set_hidden(False)
            btn_forecast.set_hidden(True)
            img.set_hidden(True)
            label.set_text("Back")
            btn.add_style(btn.PART.MAIN, style_back)
            show_history_data(temp_hist_data, humidity_hist_data)
            state = "hist"

        elif state == "hist":
            # switch back to main
            for lbl in main_labels:
                lbl.set_hidden(False)
            for lbl in history_labels:
                lbl.delete()
            history_labels.clear()
            label.set_text("History")
            btn.add_style(btn.PART.MAIN, style_hist)
            btn_forecast.set_hidden(False)
            img.set_hidden(False)
            state = "main"


btn.set_event_cb(action)


# ---------- FORECAST BUTTON ----------
def forecast_action(obj, event):
    global state, forecast
    if event == lv.EVENT.CLICKED:
        if state == "main":
            # switch to forecast
            for lbl in main_labels:
                lbl.set_hidden(True)
            btn_forecast.set_hidden(False)
            btn.set_hidden(True)
            img.set_hidden(True)
            label_forecast.set_text("Back")
            btn_forecast.add_style(btn_forecast.PART.MAIN, style_back)
            display_forecast(forecast)
            state = "forecast"

        elif state == "forecast":
            # return to main
            for lbl in main_labels:
                lbl.set_hidden(False)
            for lbl in forecast_labels:
                lbl.delete()
            forecast_labels.clear()
            label_forecast.set_text("Forecast")
            btn_forecast.add_style(btn_forecast.PART.MAIN, style_hist)
            btn.set_hidden(False)
            img.set_hidden(False)
            state = "main"


btn_forecast.set_event_cb(forecast_action)


# TTS function
def get_tts(text):
    global flask_url
    url = str(flask_url + "/generate-tts-bis")
    response = urequests.post(url, json=text)
    if response.status_code == 200:
        with open('tts.wav', 'wb') as f:
            f.write(response.content)
        response.close()
        return True
    else:
        display_error("TTS request failed:" + response.text)
        return False


# Load screen
# lv.scr_load(scr)

temp = env3.temperature
hum = env3.humidity
tvoc = air.TVOC
eco2 = air.eCO2
outData = get_outdoor_weather()
outTemp = outData.get("outdoor_temp", "...")
outWeather = outData.get("weather_description")
outHum = outData.get("outdoor_humidity")
if outTemp:
    outTemp = round(outTemp)
else:
    outTemp = ""

wait(3)

t = 0
tts_timer = 3595


def display_weather_image(outWeather):
    try:
        # Clear any existing image if needed (optional)
        global img
        if "img" in globals() and img:
            img.delete()

        # Lowercase and check for weather type
        w = str(outWeather).strip().lower()

        # Default image path
        img_path = "res/"

        if "light" in w:
            img_path += "light.png"
        elif "rain" in w:
            img_path += "rain.png"
        elif "snow" in w:
            img_path += "snow.png"
        elif "scattered" in w:
            img_path += "scatter_clouds.png"
        elif "cloud" in w:
            img_path += "clouds.png"
        elif "clear" in w or "sun" in w:
            img_path += "sun.png"
        else:
            return

        # rain/scat
        with open(img_path, 'rb') as f:
            img_data = f.read()

        # Decode the PNG
        img_dsc = lv.img_dsc_t()
        img_dsc.data = img_data
        img_dsc.data_size = len(img_data)

        # Create image object
        img = lv.img(lv.scr_act())
        img.set_src(img_dsc)

        # Set size (scale)
        img.set_zoom(70)
        img.align(out_temp_label, lv.ALIGN.CENTER, 30, 60)

    except Exception as e:
        display_error("Img load err: " + str(e))


def display_weather_image_forecast(outWeather):
    try:
        # Clear any existing image if needed (optional)
        global weather_img
        if "weather_img" in globals() and weather_img:
            weather_img.delete()
        display_error(outWeather)
        # Lowercase and check for weather type
        w = str(outWeather).strip().lower()
        display_error(w)
        # Default image path
        img_path = "res/"

        if "light" in w:
            img_path += "light.png"
        elif "rain" in w:
            img_path += "rain.png"
        elif "snow" in w:
            img_path += "snow.png"
        elif "scattered" in w:
            img_path += "scatter_clouds.png"
        elif "cloud" in w:
            img_path += "clouds.png"
        elif "clear" in w or "sun" in w:
            img_path += "sun.png"
        else:
            return

        # rain/scat
        with open(img_path, 'rb') as f:
            img_data = f.read()

        # Decode the PNG
        img_dsc = lv.img_dsc_t()
        img_dsc.data = img_data
        img_dsc.data_size = len(img_data)

        # Create image object
        img = lv.img(lv.scr_act())
        img.set_src(img_dsc)

        # Set size (scale)
        img.set_zoom(70)
        img.align(out_temp_label, lv.ALIGN.CENTER, 30, 60)

    except Exception as e:
        display_error("Img load err: " + str(e))


# Update function
def update_labels():
    global temp, hum, tvoc, eco2, temp_label, hum_label, tvoc_label, eco2_label, clock_label, outTemp, outHum, t, outWeather
    try:
        temp = round(env3.temperature)
        hum = round(env3.humidity)
        tvoc = round(air.TVOC)
        eco2 = round(air.eCO2)
        # updates outdoor values every half hour
        if t % 1800 == 0 & t != 0:
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
            display_weather_image(outWeather)

        temp_label.set_text(str(temp) + "°C")
        hum_label.set_text(str(hum) + "%")
        tvoc_label.set_text(str(tvoc) + "ppb")
        eco2_label.set_text(str(eco2) + "ppm")
        clock_label.set_text(str(ntp.formatDatetime('-', ':')))


    except Exception as e:
        error_label.set_text("ERROR: Cannot update values.")
        print("Sensor read error:", e)


def update_flags():
    global tts_alerts, temp, hum, tvoc, eco2, outTemp, outHum, t, outWeather

    # Ensure outWeather is a string and lowercase
    weather = str(outWeather).lower()

    # Create a new dictionary of alerts
    alerts = {
        "TempHigh": temp > 26,
        "TempLow": temp < 19,
        "HumHigh": hum > 60,
        "HumLow": hum < 40,
        "Air": tvoc > 500 or eco2 > 1000,
        "Storm": "storm" in weather,
        "Rain": "rain" in weather,
        "Sun": "sun" in weather,
        "Warm": outTemp > 14,
        "Cold": outTemp < 10
    }

    # Update the global alerts dictionary
    tts_alerts["alerts"] = alerts


def send_data():
    global passwd, flask_url, temp, hum, tvoc, eco2, lat, lon, city
    data = {
        "passwd": passwd,
        "values": {
            "indoor_temp": temp,
            "indoor_humidity": hum,
            "tvoc": tvoc,
            "eco2": eco2,
            "lat": lat,
            "lon": lon,
            "city": city
        }
    }
    res = urequests.post(str(flask_url + "/send-to-bigquery"), json=data)
    if res.status_code != 200:
        display_error("Couldn't send data to the cloud")
    res.close()


def send_alert():
    global passwd, flask_url, tts_alerts, tts_timer, pir
    if tts_timer > 3600 and pir.state:
        tts_timer = 0
        if get_tts(tts_alerts):
            speaker.playWAV("tts.wav", volume=8)
        else:
            display_error("Couldn't load alerts")


def play_ding():
    try:
        # Optional: List flash to confirm file exists
        if "ding.wav" not in os.listdir("/res"):
            display_error("ding.wav not found")
            return

        speaker.stop()  # Always stop any current playback first
        speaker.playWAV("tts.wav", volume=8)  # Avoid wait=False for now
    except Exception as e:
        display_error("Audio play error: " + str(e))


# Main loop
while True:
    if str(ntp.formatDatetime('-', ':'))[:3] == "2000":
        ntp = ntptime.client(host='cn.pool.ntp.org', timezone=2)

    if t == 0:
        loading_label.delete()
        lv.scr_load(scr)
        out_temp_label.set_text(str(outTemp) + "°C")
        out_hum_label.set_text(str(outHum) + "%")
        label_in.set_hidden(False)
        label_out.set_hidden(False)
        display_weather_image(outWeather)

    update_labels()
    if t % 300 == 0:
        # send data
        send_data()
        # update flags
        update_flags()

    # updates forecasts every hour
    if t % 3600 == 0 & t != 0:
        forecast = get_forecast()

    if error_triggered:
        error_counter += 1
        if error_counter == 5:
            error_triggered = False
            error_counter = 0
            display_error()
    """
    if tts_timer >3600 and pir.state:
      tts_timer = 0
      if get_tts(tts_alerts):
        display_error("Successful")
        #speaker.stop()
        try:
          #_thread.start_new_thread(play_ding, ())
          speaker.playWAV("tts.wav", volume=8)
        except:
          speaker.stop()
          display_error("Not working")
      else:
        display_error("Couldn't load alerts")"""
    # send_alert()
    t += 1
    tts_timer += 1
    wait_ms(600)