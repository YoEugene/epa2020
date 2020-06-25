import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV

# Import relevant items
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import datetime as dt
from datetime import datetime
import math

data_folder_prefix = './data'

finished_stations = ['竹山站']

# Import CSV file into a dataframe
for position in ['South']:
    print('===========' + position + '===========')
    for station in reversed(os.listdir('/'.join([data_folder_prefix, position]))):
        if station in finished_stations: continue
        # print('Start training on: ' + station)
        try:
            MAE_list = [position, station, 'PM2.5', '2019 (一整年)']
            for hour in range(1,14):
                hour = str(hour)
                
                df = pd.read_csv('/'.join([data_folder_prefix, position, station, str(hour)]) + '/gbdt_2015_2018.csv')
                df.drop(['PM2.5_TARGET'], axis=1)
                X_train, y_train = df.drop(['PM2.5_TARGET'], axis=1), df['PM2.5_TARGET']

                df_test = pd.read_csv('/'.join([data_folder_prefix, position, station, str(hour)]) + '/gbdt_2019.csv')
                X_test, y_test = df_test.drop(['PM2.5_TARGET'], axis=1), df_test['PM2.5_TARGET']

                reg = GradientBoostingRegressor(random_state=42)
                reg.fit(X_train, y_train)

                MAE_list.append(str(sum(abs(reg.predict(X_test) - y_test))/len(X_test)))
            print(','.join(MAE_list))
        except Exception as e:
            print(repr(e))
            continue