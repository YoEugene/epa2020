# Import relevant items
import os
import pandas as pd
import numpy as np
import datetime as dt
from datetime import datetime
import math
from utils import read_config
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-areas', help='areas')
parser.add_argument('-i', help='input')
parser.add_argument('-o', help='output')
args = parser.parse_args()

data_root_folder = "./EPA_Station_rawdata"
train_begin_year = 2015  # default value
train_end_year = 2018  # default value
test_begin_year = 2019  # default value
test_end_year = 2019  # default value
target_variable = "PM2.5"
error_input_name = ""

def main(cfg):
    data_root_folder = cfg['data_root_folder']
    train_begin_year = cfg['train_begin_year']
    train_end_year = cfg['train_end_year']
    test_begin_year = cfg['test_begin_year']
    test_end_year = cfg['test_end_year']
    target_variable = cfg['variable']
    error_input_name = ""

    if not args.areas and not cfg['areas']:
        areas = ["North", "South", "Central"]
    elif args.areas:
        areas = args.areas.split(',')
    elif cfg['areas']:
        areas = cfg['areas']

    if not args.i and not cfg['error_input_name']:
        error_input_name = "error.csv"
    elif args.i:
        error_input_name = args.i
    elif cfg['error_input_name']:
        error_input_name = cfg['error_input_name']

    if not args.o and not cfg['error_output_name']:
        error_output_file = "error.csv"
    elif args.o:
        error_output_file = args.o
    elif cfg['error_output_name']:
        error_output_file = cfg['error_output_name']

    # Import CSV file into a dataframe
    error_input_path = '/'.join([data_root_folder, error_input_name])
    print(error_input_path)
    df = pd.read_csv(error_input_path)
    df['time'] = pd.to_datetime(df['time'])

    df_o = pd.DataFrame(columns=['station','month','MAE_T1','MAE_T2','MAE_T3','MAE_T4','MAE_T5','MAE_T6','MAE_T7','MAE_T8','MAE_T9','MAE_T10','MAE_T11','MAE_T12','MAE_T13'])

    for area in areas:
        print('################ Processing area: ' + area + ' ################')

        if not args.s and not cfg['stations']:
            stations = os.listdir('/'.join([data_root_folder, area]))
        elif args.s:
            stations = args.s.split(',')
        elif cfg['stations']:
            stations = cfg['stations']

        for station in stations:
            if '.' in station: continue
            if station not in os.listdir('/'.join([data_root_folder, area])): continue
            print('Start Reporting on: ' + station)
            for mon in range(1,13):
                df_by_station_mon = df[df['station'] == station]
                mon_mask = df_by_station_mon['time'].map(lambda x: x.month) == mon
                year_mask = df_by_station_mon['time'].map(lambda x: x.year) == 2019
                df_by_station_mon = df_by_station_mon[mon_mask & year_mask]
                df_by_station_mon_mae = list(abs(df_by_station_mon.drop(['Unnamed: 0','station','time','variable'], axis=1)).mean().round(3)[:13])
                # print(df_by_station_mon_mae)
                # to_append = [5, 6]
                df_length = len(df_o)
                df_o.loc[df_length] = [station, str(mon)] + df_by_station_mon_mae
                # df_o = df_o.append(df_by_station_mon_mae, ignore_index=True)
                print('month ' + str(mon) + ' finished.')

    df_o.to_csv('/'.join([data_root_folder, area + '_' + error_output_file]))


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)
