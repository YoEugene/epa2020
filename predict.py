import os
import pickle
import argparse
import pandas as pd
import datetime as dt
from utils import read_config
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-areas', help='areas')
parser.add_argument('-o', help='output')
parser.add_argument('-m', help='model')

args = parser.parse_args()

data_root_folder = "./EPA_Station_rawdata"
train_begin_year = 2015  # default value
train_end_year = 2018  # default value
test_begin_year = 2019  # default value
test_end_year = 2019  # default value
target_variable = "PM2.5"


def datetime_transform(date_str):
    if date_str[11:13] != '24':
        return pd.to_datetime(date_str, format='%d.%m.%Y %H:%M:%S')

    date_str = date_str[:11] + '00' + date_str[13:]
    return pd.to_datetime(date_str, format='%d.%m.%Y %H:%M:%S') + dt.timedelta(days=1)


def main(cfg):
    data_root_folder = cfg['data_root_folder']
    train_begin_year = cfg['train_begin_year']
    train_end_year = cfg['train_end_year']
    test_begin_year = cfg['test_begin_year']
    test_end_year = cfg['test_end_year']
    target_variable = cfg['variable']

    if not args.areas and not cfg['areas']:
        areas = ["North", "South", "Central"]
    elif args.areas:
        areas = args.areas.split(',')
    elif cfg['areas']:
        areas = cfg['areas']

    if not args.o and not cfg['predict_output_name']:
        output_file = "error.csv"
    elif args.o:
        output_file = args.o
    elif cfg['predict_output_name']:
        output_file = cfg['predict_output_name']

    if not args.m and not cfg['model_output_name']:
        model_name = "model.pickle"
    elif args.m:
        model_name = args.m
    elif cfg['model_output_name']:
        model_name = cfg['model_output_name']

    header_flag = True
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
            print('Start predicting on: ' + station)
            df = pd.DataFrame(columns=[
                'station','time','variable',
                'Error_T+1','Error_T+2','Error_T+3','Error_T+4','Error_T+5','Error_T+6','Error_T+7','Error_T+8','Error_T+9','Error_T+10','Error_T+11','Error_T+12','Error_T+13',
                'pred_T+1','pred_T+2','pred_T+3','pred_T+4','pred_T+5','pred_T+6','pred_T+7','pred_T+8','pred_T+9','pred_T+10','pred_T+11','pred_T+12','pred_T+13',
                'true_T+1','true_T+2','true_T+3','true_T+4','true_T+5','true_T+6','true_T+7','true_T+8','true_T+9','true_T+10','true_T+11','true_T+12','true_T+13'
            ])
            num_of_cases = [0] * 13
            for hour in range(1, 14):
                files = os.listdir('/'.join([data_root_folder, area, station, target_variable, str(hour)]))
                if model_name in files:
                    with open('/'.join([data_root_folder, area, station, target_variable, str(hour), model_name]), 'rb') as model:
                        reg = pickle.load(model)
                        df_true = pd.read_csv('/'.join([data_root_folder, area, station, target_variable, str(hour)]) + '/gbdt_2019_nearby.csv')
                        X_true, y_true = df_true.drop([target_variable + '_TARGET','TIME'], axis=1), df_true[target_variable + '_TARGET']
                        y_pred = pd.Series(reg.predict(X_true))
                        y_pred = y_pred.round(2)
                        y_error = (y_pred - y_true).round(2)
                        num_of_cases[hour-1] = len(y_true)
                        df['true_T+' + str(hour)] = y_true.shift(-hour)
                        df['pred_T+' + str(hour)] = y_pred.shift(-hour)
                        df['Error_T+' + str(hour)] = y_error.shift(-hour)
                        print('hour ' + str(hour) + ' finished.')
                else:
                    print("model name: " + model_name + ' not found for station: ' + station)
                    continue
            if not all(n == num_of_cases[0] for n in num_of_cases):
                print('Error!')
                print(num_of_cases)
            df['station'] = station
            df['time'] = df_true['TIME'].apply(datetime_transform)
            df['variable'] = target_variable
            if header_flag:
                df.to_csv('/'.join([data_root_folder, area + '_' + output_file]))
                header_flag = False
            else:
                df.to_csv('/'.join([data_root_folder, area + '_' + output_file]), mode = 'a', header = False)


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)
