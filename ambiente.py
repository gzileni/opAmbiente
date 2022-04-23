import requests
import logging
from datetime import datetime
import geopandas
import pandas as pd
import os

from geoalchemy2 import Geometry

root = os.path.dirname(os.path.abspath(__file__))

geopandas.options.use_pygeos = False

def load_jobs(engine):
    # get engine postgresql
    df = pd.read_sql('SELECT * FROM config.view_jobs', engine)
    return df

# -------------------------------------
# update database
def updatePG(engine, gdf):
    gdf.to_postgis('stations_values',
                   engine,
                   schema='public',
                   if_exists="append",
                   dtype={'geom': Geometry(geometry_type='POINT', srid=4326)},
                   chunksize=10000)

# get request data
def geoRequest(url, city, days, pollution):
    try:
        url = url + '?comune=' + city + \
            '&giorni=' + str(days) + '&inquinante=' + pollution

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

# join nearest 
def nearest(engine, lat, lng, crs, pollution, start, end):
    
    sql = "SELECT stations_values.station, stations_values.geom," + \
          "MIN(ST_Distance(geom, 'SRID=4326;POINT(" + lng + " " + lat + ")'::geometry)) as distances " + \
          "FROM public.stations_values " + \
          "WHERE UPPER(stations_values.pollution) = '" + pollution.upper() + "'" + \
          "AND ts between '" + start + "' and '" + end + "'" + \
          "GROUP BY stations_values.station, stations_values.geom " + \
          "ORDER BY geom <-> 'SRID=4326;POINT(" + lng + " " + lat + ")'::geometry " + \
          "LIMIT 1"
    station = geopandas.GeoDataFrame.from_postgis(
        sql, con=engine, crs=crs)['station'][0]

    return station

#
def getPollution(engine, station):
    sql = "SELECT stations_pollution.* " + \
          "FROM config.stations_pollution " + \
          "WHERE UPPER(config.stations_pollution.station) = '" + station.upper() + "'"
    station_values = pd.read_sql(sql, con=engine)
    print(station_values)

    return station_values

#
def getData(engine, crs, start, end, pollution, station):
    sql = "SELECT * " + \
          "FROM public.stations_values " + \
          "WHERE stations_values.pollution = '" + pollution + "' " + \
          "AND ts between '" + start + "' and '" + end + "' " + \
          "AND UPPER(stations_values.station)='" + station.upper() + "'"

    station_values = geopandas.GeoDataFrame.from_postgis(
        sql, con=engine, crs=crs)

    return station_values

# 
def getDataHistory(engine, pollution, station):

    field = 'stations.'

    options = {'CO': 'co',
               'PM10': 'pm10',
               'PM2.5': 'pm2_5',
               'NO2': 'no2',
               'SO2': 'so2',
               'BENZENE': 'benzene',
               'O3': 'o3'
               }
    field += options[pollution]

    sql = "SELECT stations.ts, " + field + " as value " + \
          "FROM history.stations " + \
          "WHERE UPPER(stations.station)='" + station.upper() + "'"

    station_values = pd.read_sql(sql, con=engine)

    return station_values

