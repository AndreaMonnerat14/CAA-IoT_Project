import requests
import random
from flask import request

url = 'https://caa-iot-project-1008838592938.europe-west6.run.app'

PASSWD = "fce21e30cc9a328d8531fefc6f6dff8fb80fedced25b37fa6259ceec595e4057"

data = {
    "passwd": "fce21e30cc9a328d8531fefc6f6dff8fb80fedced25b37fa6259ceec595e4057",
    "values": {
        "indoor_temp": random.randint(10, 20), # random values for the indoor temperature and humidity
        "indoor_humidity": random.randint(30, 80),
        "city": random.choices(["Villars-le-Comte", "Lausanne", "Rolle"])
    }
}
"""
response = requests.post(f"{url}/send-to-bigquery", json=data)
print(response.status_code, response.text)

response = requests.post(str(url + '/get_outdoor_weather'), json = data)
print(response.status_code, response.text)

res = requests.post(f"{url}/get-all-data", json=data)
print(res.status_code, res.text)

payload = {
    "passwd": PASSWD,
    "start_date": "2025-05-01",
    "end_date": "2025-05-12",
    "limit": 10
}

#response = requests.post(f'{url}/get-indoor-data', json=payload)

# Output the result
print("Status Code:", response.status_code)
print("Response JSON:", response.json())

payload = {
    "passwd": PASSWD,
    "text": "Hi Andrea! Comment tu te port espace the fasho?"
}

response = requests.post(f'{url}/generate-tts', json=payload)
if response.status_code == 200:
    with open("tts_output.wav", "wb") as f:
        f.write(response.content)
    print("✅ TTS audio saved as 'tts_output.mp3'")
else:
    print(f"❌ Error {response.status_code}: {response.text}")

def get_city_nominatim(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
    headers = {"User-Agent": "MyIoTApp/1.0"}
    resp = requests.get(url, headers=headers).json()
    return resp.get("address", {}).get("city")

print(get_city_nominatim(46.52, 6.63))
"""

data = { "passwd": PASSWD,
    "alerts": {"HumLow" : True,
       "HumHigh" : False,
       "TempLow": True,
       "TempHigh": False,
       "Air": True,
       "Storm": False,
       "Rain": True,
       "Sun": False,
       "Warm": False,
       "Cold": True}
}
response = requests.post(f"{url}/generate-tts-bis", json=data)
if response.status_code == 200:
    with open("tts_output.wav", "wb") as f:
        f.write(response.content)
    print("✅ TTS audio saved as 'tts_output.mp3'")
else:
    print(f"❌ Error {response.status_code}: {response.text}")
"""
data = {"passwd": PASSWD,
        "lat": 46.52,
        "lon": 6.63}
response = requests.post(str(url + '/get-weather-forecast-3'), json = data)
print(response.status_code, response.text)



response = requests.post(str(url + '/get-all-data'), json = data)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
"""