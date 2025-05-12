import requests
from flask import request

url = 'https://caa-iot-project-1008838592938.europe-west6.run.app'

PASSWD = "fce21e30cc9a328d8531fefc6f6dff8fb80fedced25b37fa6259ceec595e4057"

data = {
    "passwd": "fce21e30cc9a328d8531fefc6f6dff8fb80fedced25b37fa6259ceec595e4057",
    "values": {
        "indoor_temp": 27, # random values for the indoor temperature and humidity
        "indoor_humidity": 67,
        "city": "Lausanne"
    }
}

#response = requests.post("http://127.0.0.1:8080/send-to-bigquery", json=data)



response = requests.post(str(url + '/get_outdoor_weather'), json = data)
print(response.status_code, response.text)

res = requests.post(f"{url}/get-all-data", json=data)
print(res.status_code, res.text)

payload = {
    "passwd": PASSWD,
    "start_date": "2025-05-01",
    "end_date": "2025-05-04",
    "limit": 10
}

response = requests.post(f'{url}/get-indoor-data', json=payload)

# Output the result
print("Status Code:", response.status_code)
print("Response JSON:", response.json())