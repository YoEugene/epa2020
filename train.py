import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
import pickle
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-pos', help='position')
args = parser.parse_args()

# Import relevant items
import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# import datetime as dt
# from datetime import datetime
# import math

data_folder_prefix = './data'

finished_stations = []

# Import CSV file into a dataframe
for position in [args.pos]:
    print('===========' + position + '===========')
    # for station in reversed(os.listdir('/'.join([data_folder_prefix, position]))):
    for station in args.s.split('    '):
        if station in finished_stations: continue
        print('Start training on: ' + station)
        # try:
        MAE_list = [position, station, 'PM2.5', '2019 (一整年)']
        for hour in range(1,14):
            hour = str(hour)
            
            df = pd.read_csv('/'.join([data_folder_prefix, position, station, str(hour)]) + '/gbdt_2015_2018_nearby.csv')
            X_train, y_train = df.drop(['PM2.5_TARGET','TIME'], axis=1), df['PM2.5_TARGET']

            df_test = pd.read_csv('/'.join([data_folder_prefix, position, station, str(hour)]) + '/gbdt_2019_nearby.csv')
            X_test, y_test = df_test.drop(['PM2.5_TARGET','TIME'], axis=1), df_test['PM2.5_TARGET']

            reg = GradientBoostingRegressor(verbose=1, random_state=42)
            reg.fit(X_train, y_train)

            with open('/'.join([data_folder_prefix, position, station, str(hour), 'model.pickle']), 'wb') as f:
                pickle.dump(reg, f)
                print('hour ' + str(hour) + ' saved.')

            MAE_list.append(str(sum(abs(reg.predict(X_test) - y_test))/len(X_test)))
            print(MAE_list[-1])
        print(','.join(MAE_list))
        # except Exception as e:
        #     print(repr(e))
        #     continue