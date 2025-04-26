import requests
data = {
    "passwd": "fce21e30cc9a328d8531fefc6f6dff8fb80fedced25b37fa6259ceec595e4057",
    "values": {
        "date": "2025-03-13", # example of the correct format: '2025-03-13'
        "time": "16:30:00", # example of the correct format: '16:30:00'
        "indoor_temp": 23, # random values for the indoor temperature and humidity
        "indoor_humidity": 67
    }
}

response = requests.post("http://127.0.0.1:8080/send-to-bigquery", json=data)

print(response.status_code, response.text)