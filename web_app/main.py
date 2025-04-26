#%%
from flask import Flask, request
import os
from google.cloud import bigquery
import requests
from datetime import datetime
import pandas as pd

# You only need to uncomment the line below if you want to run your flask app locally.
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "assignment1-452312-d155b30eaf2d.json"
# Initialize BigQuery client
try:
    client = bigquery.Client(project="assignment1-452312")
except Exception as e:
    print(f"Error initializing BigQuery client: {e}")
    client = None

#%%

# For authentication

YOUR_HASH_PASSWD = "fce21e30cc9a328d8531fefc6f6dff8fb80fedced25b37fa6259ceec595e4057" # YOUR_HASH_PASSWD

app = Flask(__name__)

#%%
@app.route('/send-to-bigquery', methods=['GET', 'POST'])
def send_to_bigquery():
    if request.method == 'POST':
        if request.get_json(force=True)["passwd"] != YOUR_HASH_PASSWD:
            raise Exception("Incorrect Password!")
        data = request.get_json(force=True)["values"]

        # get the column names of the db
        q = """
        SELECT * FROM `assignment1-452312.Lab4_IoT_datasets.weather_records` LIMIT 10
        """
        try:
            query_job = client.query(q)
            df = query_job.to_dataframe()
        except Exception as e:
            return {"status": "failed", "message": f"BigQuery query failed: {e}"}

        # building the insert query
        q = """INSERT INTO `assignment1-452312.Lab4_IoT_datasets.weather_records` """
        names = ""
        values = ""

        for k, v in data.items():
            names += f"{k},"
            if df.dtypes[k] == float:
                values += f"{v},"
            else:
                values += f"'{v}',"

        # remove the last comma
        names = names[:-1]
        values = values[:-1]
        q = q + f" ({names}) VALUES({values})"

        try:
            query_job = client.query(q)
        except Exception as e:
            return {"status": "failed", "message": f"BigQuery insert failed: {e}"}

        return {"status": "success", "data": data}
    return {"status": "failed"}


#For exercise 3: Complete the following endpoint.
@app.route('/get_outdoor_weather', methods=['GET', 'POST'])
def get_outdoor_weather():
     if request.method == 'POST':
         if request.get_json(force=True)["passwd"] != YOUR_HASH_PASSWD:
             raise Exception("Incorrect Password!")
# get the latest outdoor temp values from the db


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)