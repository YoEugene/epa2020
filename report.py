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
    global data_root_folder
    global train_begin_year
    global train_end_year
    global test_begin_year
    global test_end_year
    global target_variable
    global error_input_name
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


    df_o = pd.DataFrame(columns=['station','month','SMAPE_T1','SMAPE_T2','SMAPE_T3','SMAPE_T4','SMAPE_T5','SMAPE_T6','SMAPE_T7','SMAPE_T8','SMAPE_T9','SMAPE_T10','SMAPE_T11','SMAPE_T12','SMAPE_T13'])
    # df_o = pd.DataFrame(columns=['station','month','MAPE_T1','MAPE_T2','MAPE_T3','MAPE_T4','MAPE_T5','MAPE_T6','MAPE_T7','MAPE_T8','MAPE_T9','MAPE_T10','MAPE_T11','MAPE_T12','MAPE_T13'])
    # df_o = pd.DataFrame(columns=['station','month','MAE_T1','MAE_T2','MAE_T3','MAE_T4','MAE_T5','MAE_T6','MAE_T7','MAE_T8','MAE_T9','MAE_T10','MAE_T11','MAE_T12','MAE_T13'])

    for area in areas:
        print('################ Processing area: ' + area + ' ################')
        # Import CSV file into a dataframe
        error_input_path = './EPA_Station_MAE_hour_PM2.5/' + area + '_error_nearby_v2_24hour_20200709.csv'
        # error_input_path = '/'.join([data_root_folder, error_input_name])
        print(error_input_path)
        df = pd.read_csv(error_input_path)

        df['time'] = pd.to_datetime(df['time'])

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
                predict_values = df_by_station_mon.drop(['Unnamed: 0','station','time','variable'], axis=1).iloc[:, 13:26]
                true_values = df_by_station_mon.drop(['Unnamed: 0','station','time','variable'], axis=1).iloc[:, 26:39].values
                # print(a)
                # print(b)
                # print(a.subtract(b))
                # df_by_station_mon_error = list(abs(df_by_station_mon.drop(['Unnamed: 0','station','time','variable'], axis=1)).mean().round(3)[:13])  # MAE
                # df_by_station_mon_error = list(abs(predict_values.subtract(true_values)).divide(true_values).mean().round(5))   # MAPE
                df_by_station_mon_error = list(abs(predict_values.subtract(true_values)).divide(predict_values.add(true_values).divide(2)).mean().round(5))  # SMAPE
                # print(df_by_station_mon_error)
                df_length = len(df_o)
                df_o.loc[df_length] = [station, str(mon)] + df_by_station_mon_error
                # df_o = df_o.append(df_by_station_mon_error, ignore_index=True)
                # print('month ' + str(mon) + ' finished.')

    df_o.to_csv('./EPA_Station_MAPE_month_PM2.5/Central_mon_error_nearby_v2_24hour_20200709.csv')
    # df_o.to_csv('/'.join([data_root_folder, area + '_' + error_output_file]))


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)
