from m5stack import *
from m5stack_ui import *
from uiflow import *
import network
import time
import unit
import urequests
import hashlib
import ubinascii
import wifiCfg
import ntptime

"""
networks = [
    ('Redmi Note 7', 'local123'),
    ('MyHomeWiFi', 'mypassword'),
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

# password
passwd = "okmec"
hash_bytes = hashlib.sha256(passwd.encode()).digest()
passwd = ubinascii.hexlify(hash_bytes).decode()

# Time
ntp = ntptime.client(host='cn.pool.ntp.org', timezone=2)


# TTS function
def get_tts(text):
    url = "https://caa-iot-project-1008838592938.europe-west6.run.app/generate-tts"
    response = urequests.post(url, json={"text": text, "passwd": passwd})
    if response.status_code == 200:
        with open('tts.wav', 'wb') as f:
            f.write(response.content)
        response.close()
        return True
    else:
        print("TTS request failed:", response.text)
        return False


# Screen and sensors
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)
env3_0 = unit.get(unit.ENV3, unit.PORTA)
air_0 = unit.get(unit.TVOC, unit.PORTC)
wait(1)

# UI fixed labels
Temp = M5Label('Humidity:', x=19, y=101, color=0x000, font=FONT_MONT_18)
Humidity = M5Label('Temp:', x=19, y=142, color=0x000, font=FONT_MONT_18)
TVOC = M5Label('TVOC:', x=19, y=183, color=0x000, font=FONT_MONT_18)
ECO2 = M5Label('ECO2', x=19, y=220, color=0x000, font=FONT_MONT_18)

# Ui variable labels
Time = M5Label('...', x=90, y=15, color=0x000, font=FONT_MONT_18)
labelHumIn = M5Label('Temp:', x=19, y=142, color=0x000, font=FONT_MONT_18)
labelTempIn = M5Label('...', x=163, y=142, color=0x000, font=FONT_MONT_18)
label1 = M5Label('...', x=158, y=183, color=0x000, font=FONT_MONT_18)
label6 = M5Label('In', x=158, y=103, color=0x000, font=FONT_MONT_18)
label7 = M5Label('Out', x=234, y=103, color=0x000, font=FONT_MONT_18)
M5Label('TVOC:', x=19, y=220, color=0x000, font=FONT_MONT_18)
M5Label('eCO2:', x=19, y=260, color=0x000, font=FONT_MONT_18)
label_tvoc = M5Label('...', x=100, y=220, color=0x000, font=FONT_MONT_18)
label_eco2 = M5Label('...', x=100, y=260, color=0x000, font=FONT_MONT_18)
count = 0

while True:
    """
    count += 1
    if get_tts(str("It's been " + str(10*count) + "seconds")):
      speaker.playWAV("tts.wav", volume = 6)
    else:
      Time.set_text(ntp.formatDatetime('-', ':'))
      #speaker.playWAV("res/tts.wav", volume = 10)"""
    wait(10)

"""
# Mot de passe → hashé
passwd = "okmec"
hash_bytes = hashlib.sha256(passwd.encode()).digest()
passwd_hash = ubinascii.hexlify(hash_bytes).decode()
# Compteur de temps
temp_flag = 0
# URL Cloud Run
endpoint = "https://caa-iot-project-1008838592938.europe-west6.run.app/send-to-bigquery"
# Boucle principale
while True:
    try:
        # Lecture des capteurs
        temp = round(env3_0.temperature)
        hum = round(env3_0.humidity)
        tvoc = air_0.TVOC
        eco2 = air_0.eCO2
        # Affichage
        label0.set_text(str(temp) + "°C")
        label1.set_text(str(hum) + " %")
        label_tvoc.set_text(str(tvoc) + " ppb")
        label_eco2.set_text(str(eco2) + " ppm")
        # Alerte en cas de mauvaise qualité d'air
        if tvoc > 500:
            screen.set_screen_bg_color(0xff9999)  # rouge clair
        else:
            screen.set_screen_bg_color(0xd5d5d5)
        # Envoi toutes les 5 minutes (300 s)
        if temp_flag % 300:
            data = {
                "passwd": passwd_hash,
                "values": {
                    "indoor_temp": temp,
                    "indoor_humidity": hum,
                    "tvoc": tvoc,
                    "eco2": eco2
                }
            }
            res = urequests.post(endpoint, json=data)
            print("POST status:", res.status_code)
            res.close()
            temp_flag = 0
        temp_flag += 1
        wait(1)
    except Exception as e:
        print("Erreur M5Stack:", str(e))
    wait(5)
"""
"""import requests

ip_info = requests.get("http://ip-api.com/json").json()
lat = ip_info.get("lat")
lon = ip_info.get("lon")

def get_tts(text):
    url = "https://caa-iot-project-1008838592938.europe-west6.run.app/generate-tts"
    response = urequests.post(url, json={"text": text})
    if response.status_code == 200:
        with open('/flash/tts.mp3', 'wb') as f:
            f.write(response.content)
        response.close()
        return True
    else:
        print("TTS request failed:", response.text)
        return False

"""