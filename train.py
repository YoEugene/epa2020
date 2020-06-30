import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
import pickle
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-pos', help='position')
parser.add_argument('-verbose', help='verbose')
parser.add_argument('-o', help='output')
args = parser.parse_args()

verbose = args.verbose if args.verbose else 0

# Import relevant items
import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# import datetime as dt
# from datetime import datetime
# import math

output_file = args.o if args.o else 'model.pickle'
stations = os.listdir('/'.join([data_folder_prefix, position])) if not args.s else args.s.split('  ')

data_folder_prefix = './data'

# Import CSV file into a dataframe
for position in [args.pos]:
    print('===========' + position + '===========')
    for station in stations:
        if '.' in station: continue
        print('Start training on: ' + station)
        # try:
        # MAE_list = [position, station, 'PM2.5', '2019 (一整年)']
        for hour in range(1,14):
            files = os.listdir('/'.join([data_folder_prefix, position, station, str(hour)]))
            if output_file in files:
                print('Skip ' + str(hour))
                continue
            hour = str(hour)
            
            df = pd.read_csv('/'.join([data_folder_prefix, position, station, str(hour)]) + '/gbdt_2015_2018_nearby.csv')
            X_train, y_train = df.drop(['PM2.5_TARGET','TIME'], axis=1), df['PM2.5_TARGET']

            df_test = pd.read_csv('/'.join([data_folder_prefix, position, station, str(hour)]) + '/gbdt_2019_nearby.csv')
            X_test, y_test = df_test.drop(['PM2.5_TARGET','TIME'], axis=1), df_test['PM2.5_TARGET']

            reg = GradientBoostingRegressor(verbose=verbose, random_state=42)
            reg.fit(X_train, y_train)

            with open('/'.join([data_folder_prefix, position, station, str(hour), output_file]), 'wb') as f:
                pickle.dump(reg, f)
                print('hour ' + str(hour) + ' saved.')

            # MAE_list.append(str(sum(abs(reg.predict(X_test) - y_test))/len(X_test)))
            # print(MAE_list[-1])
        # print(','.join(MAE_list))
        # except Exception as e:
        #     print(repr(e))
        #     continue
