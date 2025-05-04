from m5stack import *
from m5stack_ui import *
from uiflow import *

import time
import unit
import urequests
import hashlib

# --- Connexion Wi-Fi ---
ssid = 'TON_SSID'
password = 'TON_MDP'
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(ssid, password)

# Affichage Wi-Fi (optionnel)
wifi_status = M5TextBox(20, 20, "Connexion...", lcd.FONT_DejaVu18, 0x000000)
timeout = 10
while not sta_if.isconnected() and timeout > 0:
    wifi_status.set_text("Connexion WiFi...")
    time.sleep(1)
    timeout -= 1

if sta_if.isconnected():
    wifi_status.set_text("Connecté : " + sta_if.ifconfig()[0])
else:
    wifi_status.set_text("Erreur WiFi")

# Écran et capteur
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)
env3_0 = unit.get(unit.ENV3, unit.PORTA)

# UI labels
Temp = M5Label('Temp:', x=19, y=142, color=0x000, font=FONT_MONT_22)
Humidity = M5Label('Humidity:', x=19, y=183, color=0x000, font=FONT_MONT_22)
label0 = M5Label('...', x=163, y=142, color=0x000, font=FONT_MONT_22)
label1 = M5Label('...', x=158, y=183, color=0x000, font=FONT_MONT_22)
label6 = M5Label('In', x=158, y=103, color=0x000, font=FONT_MONT_18)
label7 = M5Label('Out', x=234, y=103, color=0x000, font=FONT_MONT_18)

# Mot de passe → hashé
passwd = "okmec"
passwd_hash = hashlib.sha256(passwd.encode()).hexdigest()

# Compteur de temps
temp_flag = 0

# URL Cloud Run
endpoint = "https://caa-iot-project-1008838592938.europe-west6.run.app/send-to-bigquery"

# Boucle principale
while True:
    try:
        # Affichage
        temp = round(env3_0.temperature)
        hum = round(env3_0.humidity)

        label0.set_text(str(temp) + "°C")
        label1.set_text(str(hum) + " %")

        # Envoi toutes les 5 minutes (300 s)
        if temp_flag >= 300:
            data = {
                "passwd": passwd_hash,
                "values": {
                    "indoor_temp": temp,
                    "indoor_humidity": hum
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
