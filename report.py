# Import relevant items
import os
import pandas as pd
import numpy as np
import datetime as dt
from datetime import datetime
import math

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-pos', help='position')
parser.add_argument('-o', help='output')
args = parser.parse_args()

data_folder_prefix = './data'

def main(s, pos, o):
    # Import CSV file into a dataframe
    df = pd.read_csv('./data/全 70 測站誤差大表.csv')
    df['time'] = pd.to_datetime(df['time'])

    df_o = pd.DataFrame(columns=['station','month','MAE_T1','MAE_T2','MAE_T3','MAE_T4','MAE_T5','MAE_T6','MAE_T7','MAE_T8','MAE_T9','MAE_T10','MAE_T11','MAE_T12','MAE_T13'])

    for position in args.pos.split(','):
        if not args.s:
            stations = os.listdir('/'.join([data_folder_prefix, position]))
        else:
            stations = args.s.split('    ')
        for station in stations:
            if '.' in station: continue
            print('Start predicting on: ' + station)
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

    df_o.to_csv('/'.join([data_folder_prefix, args.o]))


if __name__ == '__main__':
    main(s, pos, o)