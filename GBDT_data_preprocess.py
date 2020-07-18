import csv
import os
import argparse
from utils import *

# Multiprocessing
import itertools
from multiprocessing import Pool

parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-areas', help='areas')
args = parser.parse_args()

features = ['','PM2.5','O3','AMB_TEMP','CH4','CO','NMHC','NO','NO2','NOx','PM10','RAINFALL','RH','SO2','THC','WD_HR','WIND_DIREC','WIND_SPEED','WS_HR','DAY_OF_YEAR','HOUR','WEEKDAY','MONTH']

data_root_folder = "./EPA_Station_rawdata"
train_begin_year = 2015  # default value
train_end_year = 2018  # default value
test_begin_year = 2019  # default value
test_end_year = 2019  # default value
target_variable = "PM2.5"


def main(cfg):
    global data_root_folder
    data_root_folder = cfg['data_root_folder']

    global target_variable
    target_variable = cfg['variable']

    multiprcossing_number = cfg["multiprcossing_number"] if cfg and "multiprcossing_number" in cfg else 10

    if not args.areas and not cfg['areas']:
        areas = ["North", "South", "Central", "East", "Other"]
    elif args.areas:
        areas = args.areas.split(',')
    elif cfg['areas']:
        areas = cfg['areas']

    for area in areas:
        print('################ Processing area: ' + area + ' ################')
        if not args.s and not cfg['stations']:
            stations = os.listdir('/'.join([data_root_folder, area]))
        elif args.s:
            stations = args.s.split(',')
        elif cfg['stations']:
            stations = cfg['stations']

        # Make the Pool of workers
        pool = Pool(multiprcossing_number)
        pool.map(hour_multiprocess, itertools.product(stations, [area], range(1, 14)))


def hour_multiprocess(hour_input):
    global data_root_folder, target_variable

    station, area, hour = hour_input

    if '.' in station: return
    if station not in os.listdir('/'.join([data_root_folder, area])): return
    print('Converting station to GBDT format: ' + station + ' hour ' + str(hour))

    lstm_csv_path = '/'.join([data_root_folder, area, station, '2015_2018.csv'])
    gbdt_csv_path = '/'.join([data_root_folder, area, station, target_variable, str(hour)])
    lstm_to_gbdt_csv(lstm_csv_path, gbdt_csv_path, 'gbdt_2015_2018.csv', hour)

    lstm_csv_path = '/'.join([data_root_folder, area, station, '2019.csv'])
    gbdt_csv_path = '/'.join([data_root_folder, area, station, target_variable, str(hour)])
    lstm_to_gbdt_csv(lstm_csv_path, gbdt_csv_path, 'gbdt_2019.csv', hour)


def lstm_to_gbdt_csv(lstm_csv_path, gbdt_csv_path, gbdt_csv_name, hour_offset):
    global target_variable

    if not os.path.exists(gbdt_csv_path):
        os.makedirs(gbdt_csv_path)

    output_csv_path = '/'.join([gbdt_csv_path, gbdt_csv_name])

    output = open(output_csv_path, "w")
    wr = csv.writer(output)

    with open(lstm_csv_path, newline='') as f:
        reader = csv.reader(f)
        next(reader)

        row_48 = []

        for _ in range(48):
            row = next(reader)
            row_48.append(row)

        flag = True
        header = ['TIME', target_variable + '_TARGET']
        while row != None:
            row_48_t = list(map(list, zip(*row_48)))
            data_point = []
            try:
                row = next(reader)
                feature_index = features.index(target_variable)
                data_point.append(row[0])
                data_point.append(row[feature_index])
                for feature_ind in [1,2,4,5,6,7,8,9,10,13,14]:
                    for hour_back in range(1, 37):
                        if flag:
                            header.append(features[feature_ind] + '_T' + str(hour_back))
                        data_point.append(row_48[-hour_offset-hour_back+1][feature_ind])
                for feature_ind in [3,11,12,15,16,17,18]:
                    for hour_back in range(1, 13):
                        if flag:
                            header.append(features[feature_ind] + '_T' + str(hour_back))
                        data_point.append(row_48[-hour_offset-hour_back+1][feature_ind])
                for feature_ind in [1,2,4,5,6,7,8,9,10,13,14]:
                    for hour_avg in [3,6,12,24]:
                        if flag:
                            header.append(features[feature_ind] + '_AVG' + str(hour_avg))
                        if hour_offset == 1:
                            avg = round(sum([float(s) for s in row_48_t[feature_ind][-hour_avg:]])/hour_avg, 3)
                        else:
                            avg = round(sum([float(s) for s in row_48_t[feature_ind][-hour_avg-hour_offset+1:-hour_offset+1]])/hour_avg, 3)
                        data_point.append(avg)

                data_point.extend(row[-4:])
                if flag:
                    header.extend(['DAY_OF_YEAR','HOUR','WEEKDAY','MONTH'])
                    wr.writerow(header)
                    flag = False

                wr.writerow(data_point)

                row_48.append(row)
                row_48 = row_48[1:]

            except StopIteration:
                row = None

    output.close()


if __name__ == "__main__":
    cfg = read_config()
    main(cfg)
