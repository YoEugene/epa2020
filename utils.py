import os
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


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