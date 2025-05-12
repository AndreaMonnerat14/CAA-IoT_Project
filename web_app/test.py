import requests
data = {
    "passwd": "fce21e30cc9a328d8531fefc6f6dff8fb80fedced25b37fa6259ceec595e4057",
    "values": {
        "indoor_temp": 27, # random values for the indoor temperature and humidity
        "indoor_humidity": 67,
        "city": "Lausanne"
    }
}

response = requests.post("http://127.0.0.1:8080/send-to-bigquery", json=data)

print(response.status_code, response.text)

response = requests.post()
