import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
import pickle
import argparse
from tscv import GapWalkForward
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-pos', help='position')
parser.add_argument('-verbose', help='verbose')
parser.add_argument('-o', help='output')
parser.add_argument('-target', help='target')
args = parser.parse_args()

verbose = args.verbose if args.verbose is not None else 0

# Import relevant items
import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# import datetime as dt
# from datetime import datetime
# import math
data_folder_prefix = './data'

parameters = {
    "learning_rate": [0.05, 0.1],
    # "min_samples_split": [0.01, 2],
    # "min_samples_leaf": [0.01, 1],
    "max_depth":[3,5],
    "max_features":["sqrt", None],
    # "criterion": ["friedman_mse", "mae"],
    # "subsample":[1.0],  # [0.5, 0.618, 0.8, 0.85, 0.9, 0.95, 1.0]
    "n_estimators":[30, 50, 100]
}

# parameters = {
#     'learning_rate': [0.1], 
#     'n_estimators': [256], 
#     'max_depth': [6,8,10], 
#     'max_features': [0.2,0.4], 
#     'verbose': [1], 
#     'random_state': [0]
# }


def main(position=None):
    if not position: position = args.pos
    output_file = args.o if args.o else 'model.pickle'
    stations = os.listdir('/'.join([data_folder_prefix, position])) if not args.s else args.s.split('  ')
    # Import CSV file into a dataframe
    for position in [args.pos]:
        print('===========' + position + '===========')
        for station in stations:
            if '.' in station: continue
            print('Start training on: ' + station)
            # try:
            MAE_list = [position, station, 'PM2.5', '2019 (一整年)']
            for hour in range(1,14):
                files = os.listdir('/'.join([data_folder_prefix, position, station, str(hour)]))

                # # Skip hour if model is saved
                # if output_file in files:
                    # print('Skip ' + str(hour))
                    # continue

                hour = str(hour)

                df = pd.read_csv('/'.join([data_folder_prefix, position, station, str(hour)]) + '/gbdt_2015_2018_nearby.csv')
                X_train, y_train = df.drop(['PM2.5_TARGET','TIME'], axis=1), df['PM2.5_TARGET']

                df_test = pd.read_csv('/'.join([data_folder_prefix, position, station, str(hour)]) + '/gbdt_2019_nearby.csv')
                X_test, y_test = df_test.drop(['PM2.5_TARGET','TIME'], axis=1), df_test['PM2.5_TARGET']

                # # Normal Train
                # reg = GradientBoostingRegressor(verbose=verbose, random_state=42)
                # reg.fit(X_train, y_train)

                # Grid Search for Time series
                cv = GapWalkForward(n_splits=5, test_size=1)

                gbr = GradientBoostingRegressor(random_state=42)
                reg = GridSearchCV(gbr, param_grid=parameters, cv=cv, n_jobs=-1)
                reg.fit(X_train, y_train)
                print(reg.best_estimator_)
                print(reg.best_params_)
                print(reg.best_score_)

                with open('/'.join([data_folder_prefix, position, station, str(hour), output_file]), 'wb') as f:
                    pickle.dump(reg, f)
                    print('hour ' + str(hour) + ' saved.')

                MAE_list.append(str(sum(abs(reg.predict(X_test) - y_test))/len(X_test)))
                print(MAE_list[-1])
            print(','.join(MAE_list))
            # except Exception as e:
            #     print(repr(e))
            #     continue


if __name__ == '__main__':
    # main(position)
    main()
