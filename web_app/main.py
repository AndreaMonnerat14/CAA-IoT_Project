#%%
from flask import Flask, request
import os
from google.cloud import bigquery
import requests
from datetime import datetime
import pandas as pd

# You only need to uncomment the line below if you want to run your flask app locally.
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "assignment1-452312-d155b30eaf2d.json"
client = bigquery.Client(project="assignment1-452312")

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
        query_job = client.query(q)
        df = query_job.to_dataframe()
        # For exercise 2: Call the openweatherapi and add the resulting 
        # values to the `data` dictionary
        # data["outdoor_temp"] = ...
        # data["outdoor_humidity"] = ...
        # data["weather"] = ...
        # building the query
        q = """INSERT INTO `assignment1-452312.Lab4_IoT_datasets.weather_records` 
        """
        names = """"""
        values = """"""

        for k, v in data.items():
            names += f"""{k},"""
            if df.dtypes[k] == float:
                values += f"""{v},"""
            else:
                # string values in the query should be in single qutation!
                values += f"""'{v}',"""
        # remove the last comma
        names = names[:-1]
        values = values[:-1]
        q = q + f""" ({names})""" + f""" VALUES({values})"""
        query_job = client.query(q)
        return {"status": "sucess", "data": data}
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