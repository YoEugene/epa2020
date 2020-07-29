import os
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from geopy import distance
import aqi
# from math import sin, cos, sqrt, atan2, radians

def read_config():
    config_path = "./config.json"
    with open('./config.json') as json_file:
        cfg = json.load(json_file)
    return cfg


def csv_to_parquet(str_csv_path_filename):
    df = pd.read_csv(str_csv_path_filename)
    table = pa.Table.from_pandas(df)
    pq.write_table(table,"{}.parquet".format(str_csv_path_filename[:-4]), compression="gzip")


def parquet_to_csv(str_parquet_path_filename):
    df = pd.read_parquet(str_parquet_path_filename, engine="pyarrow")
    df.to_csv("{}.csv".format(str_parquet_path_filename[:-8]), index=False)


def calc_distance(lon1, lat1, lon2, lat2):
    # approximate radius of earth in km
    coords_1 = (lat1, lon1)
    coords_2 = (lat2, lon2)
    return distance.distance(coords_1, coords_2).km


def get_nearby_stations(target_station, dist):
    target_station = target_station.replace('站', '')
    with open('./stations_geo_data.json') as f:
        data = json.load(f)
    stations = []
    for station in data:
        if station in target_station: continue
        d = calc_distance(
            data[target_station]['longitude'], 
            data[target_station]['latitude'], 
            data[station]['longitude'], 
            data[station]['latitude']
        )
        if d <= dist: stations.append(station + '站')

    return stations


def get_devideId_by_station(station):
    with open('./station_deviceId.json') as f:
        data = json.load(f)

    return data[station]
