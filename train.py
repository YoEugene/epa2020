import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
import pickle
import argparse
from utils import *

# Multiprocessing
import itertools
from multiprocessing import Pool

parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-areas', help='areas')
parser.add_argument('-verbose', help='verbose')
parser.add_argument('-o', help='output')
parser.add_argument('-target', help='target')
parser.add_argument('-gs', help='grid search')

args = parser.parse_args()

data_root_folder = "./EPA_Station_rawdata"
train_begin_year = 2015  # default value
train_end_year = 2018  # default value
test_begin_year = 2019  # default value
test_end_year = 2019  # default value
target_variable = "PM2.5"
grid_search = False

# Import relevant items
import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# import datetime as dt
# from datetime import datetime
# import math

param_grid = {
    "learning_rate": [0.01, 0.05, 0.1],
    # "min_samples_split": [0.01, 2],
    # "min_samples_leaf": [0.01, 1],
    "max_depth": [3,5],
    # "max_features":["sqrt", None],
    # "criterion": ["friedman_mse", "mae"],
    # "subsample": [0.6, 1.0],  # [0.5, 0.618, 0.8, 0.85, 0.9, 0.95, 1.0]
    "n_estimators": [50, 100, 150]
    # "n_estimators": [10, 20]
}

# parameters = {
#     'learning_rate': [0.1], 
#     'n_estimators': [256], 
#     'max_depth': [6,8,10], 
#     'max_features': [0.2,0.4], 
#     'verbose': [1], 
#     'random_state': [0]
# }


def main(cfg):
    global data_root_folder
    global target_variable
    global output_file
    global verbose
    global model_output_folder
    global grid_search
    data_root_folder = cfg['data_root_folder']
    train_begin_year = cfg['train_begin_year']
    train_end_year = cfg['train_end_year']
    test_begin_year = cfg['test_begin_year']
    test_end_year = cfg['test_end_year']
    target_variable = cfg['variable']
    grid_search = cfg['grid_search']
    model_output_folder = cfg['model_output_folder'] + target_variable

    multiprcossing_number = cfg["multiprcossing_number"] if cfg and "multiprcossing_number" in cfg else 10

    if not args.areas and not cfg['areas']:
        areas = ["North", "South", "Central", "East", "Other"]
    elif args.areas:
        areas = args.areas.split(',')
    elif cfg['areas']:
        areas = cfg['areas']

    if not args.verbose and not cfg['verbose']:
        verbose = 0
    elif args.verbose:
        verbose = int(args.verbose)
    elif cfg['verbose']:
        verbose = int(cfg['verbose'])

    if not args.gs and not cfg['grid_search']:
        grid_search = False
    elif args.gs:
        grid_search = args.gs == "True" or args.gs == "1"
    elif cfg['grid_search']:
        grid_search = cfg['grid_search']

    if not args.o and not cfg['model_output_name']:
        output_file = "model.pickle"
    elif args.o:
        output_file = args.o
    elif cfg['model_output_name']:
        output_file = cfg['model_output_name']

    for area in areas:
        print('################ Processing area: ' + area + ' ################')

        if not args.s and not cfg['stations']:
            stations = os.listdir('/'.join([data_root_folder, area]))
        elif args.s:
            stations = args.s.split(',')
        elif cfg['stations']:
            stations = cfg['stations']

        if not grid_search:
            # Make the Pool of workers
            pool = Pool(multiprcossing_number)
            pool.map(station_multiprocess, itertools.product(stations, [area], range(1, 14)))
        else:
            for station in stations:
                for hour in range(1, 14):
                    station_multiprocess((station, area, hour))


def station_multiprocess(station_input):
    global data_root_folder
    global target_variable
    global output_file
    global verbose
    global model_output_folder

    station, area, hour = station_input

    if '.' in station: return
    if station not in os.listdir('/'.join([data_root_folder, area])): return

    print('Variable: ' + target_variable + '. Start training on: ' + station + ' hour ' + str(hour))

    hour = str(hour)

    output_model_path = '/'.join([model_output_folder, hour])
    if not os.path.exists(output_model_path):
        os.makedirs(output_model_path)

    if (station + '_' + output_file) in os.listdir(output_model_path):
        print('Skip. Model with same name already existed. ' + station + ' hour ' + hour)
        return

    train_data_path = '/'.join([data_root_folder, area, station, target_variable, hour]) + '/gbdt_2015_2018_nearby.parquet'

    df = pd.read_parquet(train_data_path)
    X_train, y_train = df.drop([target_variable + '_TARGET','TIME'], axis=1), df[target_variable + '_TARGET']

    test_data_path = '/'.join([data_root_folder, area, station, target_variable, hour]) + '/gbdt_2019_nearby.parquet'

    df_test = pd.read_parquet(test_data_path)
    X_test, y_test = df_test.drop([target_variable + '_TARGET','TIME'], axis=1), df_test[target_variable + '_TARGET']

    if grid_search:
        # Simple Grid Search
        reg = GridSearchCV(GradientBoostingRegressor(random_state=42, verbose=verbose), param_grid=param_grid, cv=5, n_jobs=-1)

        reg.fit(X_train, y_train)
        print('>>> Best params: ': + str(reg.best_params_))
    else:
        # Normal Train
        # reg = GradientBoostingRegressor(learning_rate=0.05, n_estimators=200, max_depth=6, verbose=verbose, random_state=42)
        reg = GradientBoostingRegressor(random_state=42, verbose=verbose)
        reg.fit(X_train, y_train)

    with open(output_model_path + '/' + station + '_' + output_file, 'wb') as f:
        pickle.dump(reg, f)
        print('Model: ' + station + ' hour ' + hour + ' saved.')

    MAE = str(sum(abs(reg.predict(X_test) - y_test))/len(X_test))

    print(', '.join([station, hour, MAE]))


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)
