import geopandas
import os
from shapely.geometry import Point

root = os.path.dirname(os.path.abspath(__file__))

geopandas.options.use_pygeos = False

# -------------------------------------
# get geocode locations
def geocode(crs, location):

    result = {}
    df = geopandas.tools.geocode(location).to_crs(crs=crs)
    if (df is not None):
        return df.to_json()
    
    return result

# -------------------------------------
# get reverse geocode from coordinates
def reverse(crs, latitude, longitude):

    result = {}
    df = geopandas.tools.reverse_geocode(
        [Point(latitude, longitude)]).to_crs(crs=crs)
    if (df is not None):
        result = df.to_json()
    
    return result

