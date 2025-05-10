"""
Code pour m5stack ui flow, si tu veux le faire fonctionenr sur pycharm il faut le modifier, demandes à chat oklm le s
"""
from m5stack import *
from m5stack_ui import *
from uiflow import *
import network
import time
import unit
import urequests
import hashlib
import wifiCfg

"""
wifiCfg.doConnect('zpo-28857', 'u60y-r3tl-rzfn-qrgq')

wifi_status = M5Label("Connexion...", x=20, y=20, color=0x000000, font=FONT_MONT_18)

timeout = 10
while not wifiCfg.wlan_sta.isconnected() and timeout > 0:
    wifi_status.set_text("Connexion WiFi...")
    wait(1)
    timeout -= 1

if wifiCfg.wlan_sta.isconnected():
    ip = wifiCfg.wlan_sta.ifconfig()[0]
    wifi_status.set_text("Connecté : " + ip)
else:
    wifi_status.set_text("Erreur WiFi")
"""
# Écran et capteur
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)
env3_0 = unit.get(unit.ENV3, unit.PORTA)
TVOC = unit.get(unit.TVOC, unit.PORTC)

# UI labels
Temp = M5Label('Temp:', x=19, y=101, color=0x000, font=FONT_MONT_22)
Humidity = M5Label('Humidity:', x=19, y=142, color=0x000, font=FONT_MONT_22)
Air_Quality = M5Label('Air Quality:', x=19, y=183, color=0x000, font=FONT_MONT_22)
labelTempIn = M5Label('...', x=163, y=101, color=0x000, font=FONT_MONT_22)
labelHumIn = M5Label('...', x=163, y=142, color=0x000, font=FONT_MONT_22)
labelAirIn = M5Label('...', x=163, y=183, color=0x000, font=FONT_MONT_22)
label6 = M5Label('In', x=158, y=60, color=0x000, font=FONT_MONT_18)
label7 = M5Label('Out', x=234, y=60, color=0x000, font=FONT_MONT_18)


#Hashing password and turning into hex (hex_digest not supported)
passwd = "okmec"
passwd_hash = hashlib.sha256(passwd.encode())
passwd_hash = passwd_hash.digest()
passwd_hash = ''.join('{:02x}'.format(b) for b in passwd_hash)


# Compteur de temps
temp_flag = 0

# URL Cloud Run
endpoint = "https://caa-iot-project-1008838592938.europe-west6.run.app/send-to-bigquery"

outdoor_endpoint = "https://caa-iot-project-1008838592938.europe-west6.run.app/get_outdoor_weather"

# Boucle principale
while True:
    try:
        # Affichage
        temp = round(env3_0.temperature)
        hum = round(env3_0.humidity)
        air = round(TVOC.eco2)
        tvoc = round(TVOC.tvoc)

        labelTempIn.set_text(str(temp) + "°C")
        labelHumIn.set_text(str(hum) + " %")
        labelAirIn.set_text(str(air) + " ppm")
        if tvoc > 500:
            screen.set_screen_bg_color(0xff9999)  # rouge clair
        else:
            screen.set_screen_bg_color(0xd5d5d5)

        # Envoi toutes les 5 minutes (300 s)
        if temp_flag >= 300:
            data = {
                "passwd": passwd_hash,
                "values": {
                    "indoor_temp": temp,
                    "indoor_humidity": hum,
                    "indoor_eco2" : air,
                    "indoor_tvoc" : TVOC
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




