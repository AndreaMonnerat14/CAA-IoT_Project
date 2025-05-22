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
import lodepng  # handling png to binary (for lvgl)
import gc  # handling memory

wifiCfg.autoConnect(lcdShow=False)
wifiCfg.wlan_sta.active(True)
# wifiCfg.doConnect("iot-unil", "4u6uch4hpY9pJ2f9")

# LVGL init
lv.init()
scr = lv.obj()
scr.set_style_local_bg_color(scr.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x0d3853))

# Known WiFi Networks
networks = [
    ('YourNetwork', 'PW'),
    ('OtherNetwork', 'password123')
]


# Initial Connection with Local Label
def connect_to_known_networks(network_list):
    loading_label = lv.label(scr)
    loading_label.align(scr, lv.ALIGN.CENTER, -120, 0)
    loading_label.set_style_local_text_color(loading_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
    loading_label.set_style_local_text_font(loading_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
    loading_label.set_text("Connecting to WiFi...")

    lv.scr_load(scr)

    while True:
        for attempt in range(3):  # Retry scan
            available = wifiCfg.wlan_sta.scan()
            if available:
                break
            loading_label.set_text("Scanning WiFi...")
            lv.task_handler()
            time.sleep(2)

        if not available:
            loading_label.set_text("No networks found.")
            lv.task_handler()
            time.sleep(5)
            continue

        available_names = [net[0].decode('utf-8') for net in available]

        for ssid, password in network_list:
            if ssid in available_names:
                loading_label.set_text("Trying " + ssid + "...")
                lv.task_handler()
                wifiCfg.doConnect(ssid, password)

                for _ in range(15):
                    if wifiCfg.wlan_sta.isconnected():
                        ip = wifiCfg.wlan_sta.ifconfig()[0]
                        loading_label.set_text("Connected: " + ip)
                        lv.task_handler()
                        time.sleep(2)
                        loading_label.delete()
                        gc.collect()
                        return True
                    time.sleep(1)

        loading_label.set_text("Retrying in 5s...")
        lv.task_handler()
        time.sleep(5)


connect_to_known_networks(networks)

# Init LVGL screen and loading label

loading_label = lv.label(scr)
loading_label.align(scr, lv.ALIGN.CENTER, -100, 0)
loading_label.set_style_local_text_color(loading_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))
loading_label.set_style_local_text_font(loading_label.PART.MAIN, lv.STATE.DEFAULT, lv.font_montserrat_22)
loading_label.set_text("Data loading...")

# Error display area
error_textarea = lv.textarea(scr)
error_textarea.set_size(300, 100)
error_textarea.align(scr, lv.ALIGN.IN_BOTTOM_MID, 0, -10)
error_textarea.set_text("")  # start empty
error_textarea.set_cursor_hidden(True)  # hide cursor so it looks like a label
error_textarea.set_style_local_text_color(scr.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x000000))
error_textarea.set_hidden(True)  # hidden by default


# displaying errors
def display_error(msg):
    global img
    if msg:
        if img:
            img.set_hidden(True)
        error_textarea.set_text(msg)
        error_textarea.set_hidden(False)
        wait(2)
        error_textarea.set_hidden(True)
        if img:
            img.set_hidden(False)
    else:
        error_textarea.set_text("")
        error_textarea.set_hidden(True)


# Init sensors
try:
    env3 = unit.get(unit.ENV3, unit.PORTA)
    air = unit.get(unit.TVOC, unit.PORTC)
    pir = unit.get(unit.PIR, unit.PORTB)
except Exception as e:
    display_error("Sensor connection error, please check wires: " + str(e))
wait(1)

# password
passwd = ""
hash_bytes = hashlib.sha256(passwd.encode()).digest()
passwd = ubinascii.hexlify(hash_bytes).decode()

# Time
ntp = ntptime.client(host='cn.pool.ntp.org', timezone=2)

# location
ip_info_res = urequests.get("http://ip-api.com/json")
ip_info = ip_info_res.json()
lat = ip_info.get("lat", 46.4)
lon = ip_info.get("lon", 6.3)
city = ip_info.get("city", "Lausanne")

ip_info_res.close()
del ip_info, ip_info_res
gc.collect()

# Flask URL
flask_url = "https://caa-iot-project-1008838592938.europe-west6.run.app"


# retrieve historical values (3 last recorded days)
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
                del response
                gc.collect()
                return avg_temp_by_day, avg_humidity_by_day
            else:
                display_error("Error from server: " + result["message"])
        else:
            display_error("HTTP Error: " + response.status_code)
        response.close()
        del response
        gc.collect()
    except Exception as e:
        print("Request failed:", e)

    return {}, {}  # Return empty dicts if something went wrong


# Current weather
def get_outdoor_weather():
    global passwd, flask_url
    data = {"passwd": passwd, "lat": lat, "lon": lon}
    response = urequests.post(str(flask_url + '/get_outdoor_weather'), json=data)
    if response.status_code == 200:
        result = response.json()
        if result["status"] == "success":
            response.close()
            del response
            gc.collect()
            return result
    else:
        response.close()
        del response
        gc.collect()
        return None


# tts_alerts - used to identify (too) high or low values
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

# Date/time label at top center
clock_label = lv.label(scr)
clock_label.set_text("")
clock_label.align(scr, lv.ALIGN.IN_TOP_MID, -20, 5)
clock_label.set_style_local_text_color(clock_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))

loc_label = lv.label(scr)
loc_label.set_text("")
loc_label.align(scr, lv.ALIGN.IN_TOP_LEFT, 0, 5)
loc_label.set_style_local_text_color(loc_label.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xf4f6f7))

# "In" label on center left
label_in = lv.label(scr)
label_in.set_text("In")
label_in.align(scr, lv.ALIGN.CENTER, -130, -80)  # Adjust -100 as needed for left centering
label_in.set_style_local_text_color(label_in.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xe6e6e6))
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
label_out.set_style_local_text_color(label_out.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0xe6e6e6))
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


# Reconnect to Wifi If Lost
def reconnect_if_lost():
    global networks

    if wifiCfg.wlan_sta.isconnected():
        return True

    wifiCfg.wlan_sta.active(True)
    time.sleep(1)

    display_error("WiFi lost. Reconnecting...")
    lv.scr_load(scr)

    while True:
        # Retry scan 3 times
        for attempt in range(3):
            available = wifiCfg.wlan_sta.scan()
            if available:
                break
            display_error("Scanning WiFi...")
            lv.task_handler()
            wait(2)

        if not available:
            display_error("No networks found.")
            lv.task_handler()
            wait(5)
            continue

        available_names = [net[0].decode('utf-8') for net in available]

        for ssid, password in networks:
            if ssid in available_names:
                display_error("Trying " + ssid + "...")
                lv.task_handler()
                wifiCfg.doConnect(ssid, password)

                for _ in range(15):
                    if wifiCfg.wlan_sta.isconnected():
                        ip = wifiCfg.wlan_sta.ifconfig()[0]
                        display_error("Reconnected: " + ip)
                        lv.task_handler()
                        wait(2)
                        gc.collect()
                        return True
                    time.sleep(1)

        display_error("Retrying in 5s...")
        lv.task_handler()
        wait(5)

    return False


# getting 3 days forecasts
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
                display_error("Server error:" + result["message"])
        else:
            display_error("HTTP error:" + str(response.status_code))
    except Exception as e:
        display_error("Forecast fetch failed:")
    return {}


forecast = get_forecast()

# Track all label groups for cleanup
forecast_labels = []
history_labels = []
main_labels = [temp_label, hum_label, tvoc_label, eco2_label, clock_label, out_temp_label, out_hum_label, label_in,
               label_out, loc_label]
state = "main"  # can be 'main', 'hist', or 'forecast'

# ----------- HIST BUTTON -----------
btn = lv.btn(scr)
btn.set_size(100, 50)
btn.align(scr, lv.ALIGN.IN_BOTTOM_RIGHT, -10, -10)

style_hist = lv.style_t()
style_hist.init()
style_hist.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x3260c8))
style_hist.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x233560))

style_back = lv.style_t()
style_back.init()
style_back.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))
style_back.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))

label = lv.label(btn)
label.set_text("History")
label.align(btn, lv.ALIGN.CENTER, 0, 0)

btn.add_style(btn.PART.MAIN, style_hist)
btn.set_hidden(True)

# ----------- FORECAST BUTTON -----------
btn_forecast = lv.btn(scr)
btn_forecast.set_size(100, 50)
btn_forecast.align(scr, lv.ALIGN.IN_BOTTOM_LEFT, 10, -10)

label_forecast = lv.label(btn_forecast)
label_forecast.set_text("Forecast")
label_forecast.align(btn_forecast, lv.ALIGN.CENTER, 0, 0)

btn_forecast.add_style(btn.PART.MAIN, style_hist)
btn_forecast.set_hidden(True)


# Displaying the 3 last recorded days
def show_history_data(temp_data, hum_data):
    col_x_offsets = [-90, 0, 90]
    global history_labels
    for lbl in history_labels:
        lbl.delete()
    history_labels = []

    days = list(temp_data.keys())
    days.sort()
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


# displaying the next 3 days' forecasts
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

            values = [day_str, min_temp + "°C", max_temp + "°C"]

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


forecast_state = False
forecast_icons = []
forecast_icon_positions = []
weather_img = None  # This will be the reusable lv.img object


# Preloading icons to avoid memory usage during loop
def preload_forecast_icons(forecast):
    global forecast_icons, forecast_icon_positions

    forecast_icons = []
    forecast_icon_positions = []

    try:
        summary = forecast.get("forecast_summary", {})
        dates = sorted(list(summary.keys()))
        max_days = min(3, len(dates))

        col_x_offsets = [-80, 10, 100]  # Same as in display_forecast
        y_icon = 10  # Adjust based on UI

        for i in range(max_days):
            day_info = summary[dates[i]]
            desc = day_info.get("description", "").lower()

            # Determine image path
            img_path = "res/"
            if "light" in desc:
                img_path += "light.png"
            elif "rain" in desc:
                img_path += "rain.png"
            elif "snow" in desc:
                img_path += "snow.png"
            elif "scattered" in desc:
                img_path += "scatter_clouds.png"
            elif "cloud" in desc:
                img_path += "clouds.png"
            elif "clear" in desc or "sun" in desc:
                img_path += "sun.png"
            else:
                img_path += "unknown.png"

            # Load binary image
            with open(img_path, 'rb') as f:
                img_data = f.read()

            img_dsc = lv.img_dsc_t()
            img_dsc.data = img_data
            img_dsc.data_size = len(img_data)

            forecast_icons.append(img_dsc)

            # Save absolute (x, y) position for this day
            forecast_icon_positions.append((col_x_offsets[i] + 30, y_icon))  # 160 is screen center X

    except Exception as e:
        display_error("Preload icon error: " + str(e))


# Displaying forecast icons depending on time to draw dynamics
def display_forecast_icon_for_day(t):
    global weather_img, forecast_icons, forecast_icon_positions, forecast_state

    try:
        if forecast_state:
            day_index = t % len(forecast_icons)

            # First time creation
            if weather_img is None:
                weather_img = lv.img(lv.scr_act())
                weather_img.set_zoom(70)

            weather_img.set_src(forecast_icons[day_index])

            # Use absolute position
            x, y = forecast_icon_positions[day_index]
            weather_img.set_pos(x, y)
            weather_img.set_hidden(False)
        else:
            if weather_img is not None:
                weather_img = None

    except Exception as e:
        display_error("Show icon err: " + str(e))


preload_forecast_icons(forecast)


# ---------- HIST BUTTON Action ----------
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


# ---------- FORECAST BUTTON Action ----------
def forecast_action(obj, event):
    global state, forecast, forecast_state
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
            forecast_state = True

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
            forecast_state = False
            if weather_img is not None:
                weather_img.set_hidden(True)


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
        del response
        gc.collect()
        return True
    else:
        display_error("TTS request failed:" + response.text)
        return False


# loading first values
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

wait(2)


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
        img.align(out_temp_label, lv.ALIGN.CENTER, 30, 55)

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
        if str(ntp.formatDatetime('-', ':')).startswith("2000") and t == 0:
            display_error("Cannot load local date:time")

    except Exception as e:
        display_error("Sensor read error:" + e)


# updating alert flags
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
        "Warm": outTemp > 20,
        "Cold": outTemp < 10
    }

    # Update the global alerts dictionary
    tts_alerts["alerts"] = alerts


# Send to bigquery
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
    result = res.json()
    if res.status_code != 200:
        display_error("Couldn't send data to the cloud")
    res.close()
    del res
    gc.collect()


# upadting colors wrt alerts
def update_variable_label_colors(temp, hum, tvoc, eco2, temp_label, hum_label, tvoc_label, eco2_label):
    def set_label_color(label, condition):
        color = lv.color_hex(0xe74c3c) if condition else lv.color_hex(0xf4f6f7)  # red if alert, light gray otherwise
        label.set_style_local_text_color(label.PART.MAIN, lv.STATE.DEFAULT, color)

    # Apply threshold conditions
    set_label_color(temp_label, temp > 26 or temp < 19)
    set_label_color(hum_label, hum > 60 or hum < 40)
    set_label_color(tvoc_label, tvoc > 500)
    set_label_color(eco2_label, eco2 > 1000)


# timers
forecast_t = 0
t = 0
tts_timer = 3597
gc.collect()

# Main loop
while True:
    # Check connection every 30 seconds (plus fréquent)
    if t % 30 == 0:
        reconnect_if_lost()

    # Init labels, btns, image at start
    try:
        if t == 0:
            loading_label.delete()
            btn.set_hidden(False)
            btn_forecast.set_hidden(False)
            lv.scr_load(scr)
            out_temp_label.set_text(str(outTemp) + "°C")
            out_hum_label.set_text(str(outHum) + "%")
            if city:
                loc_label.set_text(str(city))
            else:
                loc_label.set_text("Lat: " + str(lat) + " - Lon: " + str(lon))
            label_in.set_hidden(False)
            label_out.set_hidden(False)
            display_weather_image(outWeather)
    except Exception as e:
        display_error("Init error: " + str(e))

    # Updating labels/colors (local operations, no network)
    try:
        if reconnect_if_lost():
            update_labels()
            update_variable_label_colors(temp, hum, tvoc, eco2, temp_label, hum_label, tvoc_label, eco2_label)
        else:
            display_error("No WiFi - skipping update")
    except Exception as e:
        display_error("Update error: " + str(e))

    # Send data every 5 min (with network check)
    try:
        if t % 300 == 0:
            if reconnect_if_lost():  # Vérifier AVANT l'opération
                send_data()
                update_flags()
                gc.collect()
            else:
                display_error("No WiFi - skipping data send")
    except Exception as e:
        error_str = str(e).lower()
        if "network" in error_str or "connection" in error_str or "timeout" in error_str:
            display_error("Network error: " + str(e))
            print("Network error during send_data: " + str(e))
            # Retry once after 5 seconds
            time.sleep(5)
            if reconnect_if_lost():
                try:
                    send_data()
                    update_flags()
                    gc.collect()
                except:
                    display_error("Retry failed - will try next cycle")
        else:
            display_error("Send error: " + str(e))

    # Updates forecasts every hour (with network check)
    try:
        if t % 3600 == 0 and t != 0:
            if reconnect_if_lost():  # Vérifier AVANT l'opération
                forecast = get_forecast()
            else:
                display_error("No WiFi - skipping forecast update")
    except Exception as e:
        error_str = str(e).lower()
        if "network" in error_str or "connection" in error_str or "timeout" in error_str:
            display_error("Network error: " + str(e))
        else:
            display_error("Forecast error: " + str(e))

    # Displays forecast icons when in forecast screen (no network needed)
    try:
        if state == "forecast":
            display_forecast_icon_for_day(forecast_t)
    except Exception as e:
        display_error("Icon display error: " + str(e))

    # Send alerts if there is movement and if it's been at least an hour (with network check)
    try:
        if tts_timer > 3600 and pir.state:
            tts_timer = 0
            if reconnect_if_lost():  # Vérifier AVANT l'opération TTS
                if get_tts(tts_alerts):
                    try:
                        speaker.playWAV("tts.wav", volume=8)
                        wait(10)
                        gc.collect()
                    except Exception as e:
                        display_error("Playback error: " + str(e))
                else:
                    display_error("TTS generation failed")
            else:
                display_error("No WiFi - skipping TTS alert")
    except Exception as e:
        error_str = str(e).lower()
        if "network" in error_str or "connection" in error_str or "timeout" in error_str:
            display_error("TTS network error: " + str(e))
        else:
            display_error("TTS error: " + str(e))

    # Increments (always execute)
    t += 1
    tts_timer += 1
    forecast_t += 1

    # Debug info every 10 minutes
    if t % 600 == 0:
        print("Status - t: " + str(t) + ", WiFi: " + str(wifiCfg.wlan_sta.isconnected()) + ", Memory: " + str(
            gc.mem_free()))

    # Waiting time
    wait_ms(600)