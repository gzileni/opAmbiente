from flask import Flask, request, json
from geocode import geocode, reverse
from functions import geoData, geoRequest, nearest, getData, getPollution
from ambiente import updatePG, load_jobs

from sqlalchemy import *
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import *

from werkzeug.exceptions import HTTPException

import datetime
import time
# import json
# ----------------------------
# Info:
# https://medium.com/@robertbracco1/how-to-write-a-telegram-bot-to-send-messages-with-python-bcdf45d0a580
import telegram_send

app = Flask(__name__)
f = open('./opAmbiente.json')
 
# returns JSON object as
# a dictionary
config = json.load(f)

# -------------------------------------
# get engine database
def getEngine():
    url = "postgresql://" + config["USERNAME_PG"] + ":" + config["PASSWORD_PG"] + "@" + \
          config["POSTGRESQL"] + ":" + \
          str(config["PORT"]) + "/" + config["DATABASE"]
    engine = create_engine(url)
    return engine

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

# ----------------------------------------------------------------
# HTTP GET /geocode
@app.route('/ambiente/geocode/<string:location>/<int:crs>', methods=['GET'])
def get_geocode(location, crs):
    return geocode(crs, location)

# ----------------------------------------------------------------
# HTTP GET /reverse
@app.route('/ambiente/reverse/<float:latitude>/<float:longitude>/<int:crs>', methods=['GET'])
def get_reverse(latitude, longitude, crs):
    return reverse(crs, latitude, longitude)

# ----------------------------------------------------------------
# HTTP POST /map
@app.route('/ambiente/map', methods=['POST'])
def ambiente():
    result = {}
    
    params = {
        "crs": request.form['crs'],
        "city": request.form['city'],
        "days": request.form['days'],
        "pollution": request.form['pollution']
    }

    engine = getEngine()
    data = geoRequest(config['SERVER'],
                      params)
    if (data is not None):
        gdf = geoData(engine, params["crs"], data)
        if (gdf is not None):
            # convert timestamp to serialize json
            gdf['ts'] = gdf['ts'].astype(str)
            gdf['created_at'] = gdf['created_at'].astype(str)
            result = gdf.to_json()

    return result

# ----------------------------------------------------------------
# HTTP GET /near
@app.route('/ambiente/near', methods=['POST'])
def nearest_station():

    params = {
        "lat": request.form['lat'],
        "lng": request.form["lng"],
        "pollution": request.form['pollution'],
        "start": request.form['start'],
        "end": request.form['end'],
        "crs": request.form['crs']
    }

    engine = getEngine()
    # nearest join with data
    station = nearest(engine, params)
    return {
        "station": station 
    }

# ----------------------------------------------------------------
# HTTP GET /data
@app.route('/ambiente/data', methods=['POST'])
def data_nearest():

    params = {
        "station": request.form['station'],
        "pollution": request.form['pollution'],
        "start": request.form['start'],
        "end": request.form['end'],
        "crs": request.form['crs']
    }

    engine = getEngine()
    # nearest join with data
    data = getData(engine, params)
    data['ts'] = data['ts'].astype(str)
    data['created_at'] = data['ts'].astype(str)
    return data.to_json()

# ----------------------------------------------------------------
# HTTP GET /pollution
@app.route('/ambiente/pollution/<string:station>', methods=['GET'])
def pollution(station):

    engine = getEngine()
    # nearest join with data
    data = getPollution(engine, station)
    return data.to_json(orient='records')

# ----------------------------------------------------------------
# HTTP POST /job
@app.route('/ambiente/job', methods=['POST'])
def job():

    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        body = request.json
        days = body['days']

        engine = getEngine()
        jobs = load_jobs(engine)
        jobs_cities = []
        jobs_cities_nodata = []
        last_station = ''
        last_station_nodata = ''
        result = {
            "updated": "",
            "noData": ""
        }

        for row in jobs.iterrows():
            
            params = {
                "city": row[1]['city'],
                "station": row[1]['station'],
                "pollution": row[1]['pollution'],
                "days": str(days)
            }

            data = geoRequest(config['SERVER'], params)
            if (data is not None):
                gdf = geoData(engine, config["CRS"], data)
                if (gdf is not None):
                    msg = str(datetime.datetime.now()) + \
                          '- Nuovi dati di inquinamento per ' + \
                          params["station"] + \
                          ' per la centralina (' + params["station"] + ') e inquinante ' + \
                          params["pollution"] + ' rilevati dall\'ARPA Puglia'
                    print(gdf.head(5))
                    updatePG(engine, gdf, params["pollution"], 'arpa')

                if (params["station"] != last_station):
                    jobs_cities.append(params["station"])
                    last_station = params["station"]
            else:
                if (params["station"] != last_station_nodata):
                    jobs_cities_nodata.append(params["station"])
                    last_station_nodata = params["station"]

                msg = str(datetime.datetime.now()) + \
                    ' - Nessun dato per ' + params["station"] + \
                    ' con inquinante ' + params["pollution"] + \
                    ' negli ultimi ' + str(params["days"]) + ' giorni.'
                print(msg)
            time.sleep(3)

        if (len(jobs_cities) > 0):
            msg = str(datetime.datetime.now()) + \
                  ' - Nuovi dati di inquinamento per le centraline \n' + \
                  str(jobs_cities) + \
                  '\nrilevati dall\'ARPA Puglia negli ultimi ' + \
                  str(params["days"]) + ' giorni.'
            telegram_send.send(messages=[msg])
            result['updated'] = msg

        if (len(jobs_cities_nodata) > 0):
            msg = str(datetime.datetime.now()) + ' - Nessun dato di inquinamento per le centraline \n' + str(jobs_cities_nodata) + \
                '\nrilevati dall\'ARPA Puglia negli ultimi ' + \
                str(days) + ' giorni'
            telegram_send.send(messages=[msg])
            result['noData'] = msg

        return result
    else:
        return 'Content-Type not supported!'