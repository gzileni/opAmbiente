import requests
import logging
from datetime import datetime
import geopandas
import pandas as pd
import os

root = os.path.dirname(os.path.abspath(__file__))

geopandas.options.use_pygeos = False

# get request data
def geoRequest(url, params):
    try:
        url = url + '?comune=' + params["city"] + \
            '&giorni=' + str(params["days"]) + '&inquinante=' + params["pollution"]

        logging.info(str(datetime.now()) + ' - Get fata from ' + url)

        # ----------------------------------------------
        # request HTTP GET data
        r = requests.get(url, 
                         verify=False,
                         stream=True,
                         timeout=120,
                         headers={'Content-Type': 'application/json'})
        if (r.status_code == 200):
            r.raise_for_status()
            return r.json()
        else:
            msg = str(datetime.now()) + ' -  Status Code : ' + str(r.status_code) + ' from ' + url
            logging.warning(msg)
            r.raise_for_status()
            return None

    except requests.ReadTimeout:
        msg = str(datetime.now()) + ' -  Readtimeout from : ' + url
        logging.error(msg)
        print(msg)
        return None

# get stations
def load_stations(engine, crs):
    stations = geopandas.GeoDataFrame.from_postgis(
                sql="SELECT * FROM public.stations", 
                con=engine, 
                crs=crs)
    return stations

def _set_index(df):
    df['station'] = df['station'].str.upper()
    df['station'] = df['station'].str.strip()
    df['pollution'] = df['pollution'].str.upper()
    df['pollution'] = df['pollution'].str.strip()
    df.set_index(['station', 'pollution'])
    return df

# -------------------------------------
# get data and convert to geojson
def geoData(engine, crs, data):
    
    stations = load_stations(engine, crs)
    stations = _set_index(stations)
    
    if (data is not None):

        gd = geopandas.GeoDataFrame(data)
        gd = gd.rename(columns={
                        "Valore": "value", 
                        "Centralina": "station",
                        "Inquinante": "pollution", 
                        "Provincia": "prov", 
                        "Comune": "city", 
                        "Data": "ts"})
        
        del gd['city']
        del gd['prov']

        gd['ts'] = pd.to_datetime(
            gd['ts'], format="%d-%m-%Y",
            errors='ignore')
        gd['created_at'] = pd.to_datetime(
            datetime.now().isoformat(),
            errors='ignore')
        gd['value'] = pd.to_numeric(
            gd['value'], errors='coerce', downcast='float')
        gd['crs'] = crs
        gd['platform'] = 'Arpa Puglia'
        gd = _set_index(gd)

        gd = pd.merge(gd, stations, how='inner', right_on=['station', 'pollution'], left_on=['station', 'pollution'])
        gd.reset_index(inplace=True)
        gd = gd.set_geometry('geom')
        
        return gd

# get nearest station 
def nearest(engine, params):
    
    sql = "SELECT stations_values.station, stations_values.geom," + \
          "MIN(ST_Distance(ST_Transform(geom, " + str(params["crs"]) + "), 'SRID=" + str(params["crs"]) + ";POINT(" + params["lng"] + " " + params["lat"] + ")'::geometry)) as distances " + \
          "FROM public.stations_values " + \
          "WHERE UPPER(stations_values.pollution) = '" + params["pollution"].upper() + "' " + \
          "AND ts between '" + params["start"] + "' AND '" + params["end"] + "' " + \
          "GROUP BY stations_values.station, stations_values.geom " + \
          "ORDER BY geom <-> 'SRID=" + str(params["crs"]) + ";POINT(" + params["lng"] + " " + params["lat"] + ")'::geometry " + \
          "LIMIT 1"

    station = geopandas.GeoDataFrame.from_postgis(
              sql, con=engine, crs='EPSG:'+params["crs"])['station'][0]

    return station

# get pollutions
def getPollution(engine, station):
    sql = "SELECT stations_pollution.* " + \
          "FROM config.stations_pollution " + \
          "WHERE UPPER(config.stations_pollution.station) = '" + station.upper() + "'"
    station_values = pd.read_sql(sql, con=engine)
    print(station_values)

    return station_values

# get range data from stations
def getData(engine, params):
    sql = "SELECT * " + \
          "FROM public.stations_values " + \
          "WHERE stations_values.pollution = '" + params["pollution"] + "' " + \
          "AND ts between '" + params["start"] + "' and '" + params["end"] + "' " + \
          "AND UPPER(stations_values.station)='" + params["station"].upper() + "'"

    station_values = geopandas.GeoDataFrame.from_postgis(
        sql, con=engine, crs='EPSG:' + str(params["crs"]))

    return station_values
