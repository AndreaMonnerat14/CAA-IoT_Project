
# import the required packages in this walkthrough
import numpy as np
import pandas as pd
import requests
import time
from datetime import datetime
import os
import pandas as pd
import hashlib
from google.cloud import bigquery

# Google Collab
from google.colab import auth
auth.authenticate_user()
print("Authenticated")

# If you want to use your local jupyter notebook:
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path-to-service-account-key-json"

# Define the BigQuery client
client = bigquery.Client(project="assignment1-452312") # PROJECT_ID

q = """
SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather_records`
LIMIT 10
"""

query_job = client.query(q)
df = query_job.to_dataframe()
df

"""## 3.3 Insert new rows in the BigQuery table
For this application, we need to insert new rows in the BigQuery table in order to be able to keep track of the historical data. To do this we can use the SQL `INSERT` statement. See the documentation to know more about the syntax of this statement: https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#insert_statement

Note that if you do not specify any values for some of the columns, those columns will get a NULL value. Follow the following examples to better understand how does the `INSERT` statement works.
"""

# Insert some random values!
q = f"""
INSERT INTO `assignment1-452312.Lab4_IoT_datasets.weather_records`
(date, time, indoor_temp, indoor_humidity, outdoor_temp, outdoor_humidity, outdoor_weather)
VALUES('2025-03-12', '16:02:23', 23, 65, 0, 0, 'Sunny')
"""

query_job = client.query(q)

# Now we can query the database again and see the new row added to it!
q = f"""
SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather_records`
LIMIT 10
"""

query_job = client.query(q)
df = query_job.to_dataframe()
df

"""-------------

# 4. Creating a web service that receives data from the IoT device
Because of the limitations of the micropython, we are not able to install Google Cloud packages on the device and therefore we are not able to directly query the BigQuery table from the device. Therefore, we need to create a web service accesible via the Internet, so that we can send the data from the device to that web service. The job of the web service is to receive the data from the M5stack device and insert it in the BigQuery table.

The script `main.py` in the lab's folder will create a simple Flask application that can recieve data from the IoT device and insert it into your BigQuery database. pay attention to the following remarks about this flask app:

- A flask app in general can have multiple endpoint. In this part, we want to use the `/send-to-bigquery` endpoint. This endpoint will accept a post request from the IoT device that contains the indoor temperature values inside a json file. Then it builds a SQL query based on these values and sends this query to the BigQuery database. Please take a moment and look carefully how the SQL query is being made.
- It is important to make sure that only you, as the owner of the database, can call this endpoint and insert new rows inside the database! To do so, we need to make the calls to this endpoint __authenticated__. One way to do that is to set up a password which will be checked on the flask server. To avoid sending the password from the IoT device in plain text, we need to hash this password first and send it to the flask server. In the flask server, the correct hash string is already stored and each time a post request is made the received hash string (from the IoT device) will be checked against the stored hash string. In the `m5stack.py` script, see how we have set-up a password and converted it to a hash string. In the `main.py` script (flask app), see how the correctness of the hash string is checked for each post request. To know more about hash functions, check the [wikipedia page](https://en.wikipedia.org/wiki/Hash_function).
- In the `m5stack.py` script select a password for yourself (the `passwd` variable).
- In the `m5stack.py` script, observe that we send data to the flask app every 5 minutes.
- You need to store the hash of your password in the flask server. You can use the code cell below to hash your password. Copy the result to the `main.py` file (`YOUR_HASH_PASSWD` variable).
"""

h = hashlib.sha256(b"okmec") # change this to a password of choice!
h.hexdigest() # this is the hashed password: YOUR_HASH_PASSWD

"""To test the endpoint locally on your computer, you can dowonload the `main.py` file and run it on your computer.

In your terminal run `python main.py`.

You can use the following cell to test your endpoint locally.
"""

data = {
    "passwd": "fce21e30cc9a328d8531fefc6f6dff8fb80fedced25b37fa6259ceec595e4057",
    "values": {
        "date": "2025-03-13", # example of the correct format: '2025-03-13'
        "time": "16:30:00", # example of the correct format: '16:30:00'
        "indoor_temp": 23, # random values for the indoor temperature and humidity
        "indoor_humidity": 67
    }
}

response = requests.post("http://0.0.0.0:8080/send-to-bigquery", json=data)

print(response.status_code, response.text)

"""If the above cells do not work for you, you can try sending a request directly from your git bash terminal Use the send_requests.sh file to do so

If you have replaced the place holders with the correct string/values, then after running the above cell you should see the new row being added to your db. If you are running this locally, make sure that the key you are using has the correct the right credentials to write in BigQuery! (IAM & Admin < IAM < select the key you are using < BigQuery Admin)
"""

q = """
SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather_records`
LIMIT 10
"""

query_job = client.query(q)
df = query_job.to_dataframe()
df

"""-------------

# 5. Deploying the Flask app in Google Cloud

To deploy the Flask app in the Gcloud Cloud Run, you have to follow the following steps:
1. Download the following files from the course repository and push them to your private repository.
    - `main.py`
    - `requirements.txt`
    - `Dockerfile`
2. Navigate to Cloud Run in your Google Cloud console and open a cloud shell terminal.
3. In the terminal navigate to the directory corresponding to your git repository and do `git pull`
4. Follow the instructions in lab 1 to build the docker image and push it to the container registry.
5. Follow the instrucitons in lab 1 to deploy the created image in the container registry to Cloud Run.

After completing the above steps successfully, you would get a URL for Flask web service. Try to insert some artificial data to the BigQuery db using the URL. You can use the code below.
"""

data = {
    "passwd": "YOUR_HASH_PASSWD",
    "values": {
        "date": "<some_random_date>", # example of the correct format: '2025-03-13'
        "time": "<some_random_time>", # example of the correct format: '16:30:00'
        "indoor_temp": 23, # random values for the indoor temperature and humidity
        "indoor_humidity": 67
    }
}

requests.post("<URL_FROM_CLOUDRUN>/send-to-bigquery", json=data)

"""Check if the data has been inserted correctly to the db."""

q = """
SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather_records`
LIMIT 10
"""

query_job = client.query(q)
df = query_job.to_dataframe()
df

"""-------------

# 6. Updating the `m5stack.py` with the URL of the deployed web service

Finally, you have to update the `m5stack.py` file with the URL of the web service you just deployed. After doing so, program the Core2 device with the new script. In the first iteration of the loop, the values of the ENV-III measurements will be sent to the server. So you sould be able to see the values added to the db almost immediately (You can check it by running a query!). After that, you should be able to see new values added to the server every 5 minutes!

-------------

# 7. Your Turn

1. Right now we are only inserting the measurements of the ENV-III sensor, temperature and humidity, to the db every 5 minutes. However, it is impossible to keep track of the historical data without keeping track of the actual time they were recorded. Therefore, we need to also send the time of the measurements from the Core2 device to the server. Try to do that! (Hint: check the `rtctime` package: https://docs.m5stack.com/en/uiflow/blockly/hardwares/rtc)

2. In the Flask server, augment the `/send-to-bigquery` endpoint such that for each post request it gets the weather information from the openweather api and insert the corresponding values in the `outdoor_weather`, `outdoor_humidity`, and `outdoor_weather` columns of the db. For the `outdoor_weather` column, use the value corresponding to the key `description` from the json file you get from the openweather api.

3. Create a new endpoint `/get_outdoor_weather` in the Flask app that accepts post requests and sends back the outdoor humidity and temperature values it gets from the latest entry in the db. In order to make sure that only you can read the records in your database, verify the password in this post request. Try to use this endpoint in the Core2 device so that you can show the outdoor weather info on the device.
    3.1. __bonus__: Can you also show the current date and time on the device?
    

After doing the 2nd and 3rd exercises, you can expect ot have this information on your Core2 device:

<img src="https://drive.usercontent.google.com/download?id=1fFtimdTCoP0GsL561hISafFbFe9fFeaP" width="500">
"""

# Help to call the openweather api

API_key = "YOUR_API_KEY"

city = "Lausanne"

url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_key}&units=metric'

response = requests.get(url)

temp = round(response.json()['main']['temp'])
humidity = round(response.json()['main']['humidity'])
weather = response.json()['weather'][0]['description']

print(f"temp: {temp}, humidity: {humidity}, weather: {weather}")