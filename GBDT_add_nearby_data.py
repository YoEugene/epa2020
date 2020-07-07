import csv
import os
import argparse
from datetime import datetime, timedelta
from utils import *

# Multiprocessing
import itertools
from multiprocessing import Pool

parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-areas', help='areas')
parser.add_argument('-o', help='output_name')
parser.add_argument('-target', help='target_csv_name')
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

    if not args.areas and not cfg['areas']:
        areas = ["North", "South", "Central"]
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
        pool = Pool(72)
        pool.map(station_multiprocess, itertools.product(stations, [area], range(1, 14)))


def station_multiprocess(station_input):
    global data_root_folder

    station, area, hour = station_input

    if '.' in station: return
    if station not in os.listdir('/'.join([data_root_folder, area])): return

    print('Adding nearby station data into: ' + station)

    csv_path = '/'.join([data_root_folder, area])
    other_stations = []
    for station_tmp in os.listdir('/'.join([data_root_folder, area])):
        if '.' in station_tmp: continue
        if station_tmp != station: other_stations.append(station_tmp)

    # gbdt_add_nearby_stations_data(csv_path, station, other_stations, str(hour), args.target, args.o)
    gbdt_add_nearby_stations_data(csv_path, station, other_stations, str(hour), 'gbdt_2015_2018.csv', 'gbdt_2015_2018_nearby.csv')
    gbdt_add_nearby_stations_data(csv_path, station, other_stations, str(hour), 'gbdt_2019.csv', 'gbdt_2019_nearby.csv')


def gbdt_add_nearby_stations_data(csv_path, target_station, other_stations, hour, target_csv_name, output_csv_name):
    global target_variable

    output_csv_path = '/'.join([csv_path, target_station, target_variable, hour, output_csv_name])

    output = open(output_csv_path, "w+")
    wr = csv.writer(output)

    target_nearby_station_data_path = '/'.join([csv_path, target_station, target_variable, hour, target_csv_name])

    parquet_to_csv(target_nearby_station_data_path.replace('csv', 'parquet'))

    target_reader = csv.reader(open(target_nearby_station_data_path), newline='')
    other_stations_readers = []
    for ost in other_stations:
        other_stations_readers.append(csv.reader(open('/'.join([csv_path, ost, target_variable, hour, target_csv_name]), newline='')))

    row = next(target_reader)
    header = row
    for osr in other_stations_readers:
        osr_row = next(osr)

    for i in range(len(other_stations_readers)):
        header.extend([
                        target_variable + '_NEARBY' + str(i+1) + '_T1', 
                        target_variable + '_NEARBY' + str(i+1) + '_AVG3', 
                        target_variable + '_NEARBY' + str(i+1) + '_AVG6', 
                        target_variable + '_NEARBY' + str(i+1) + '_AVG12', 
                        target_variable + '_NEARBY' + str(i+1) + '_AVG24',
                    ])

    # print(len(header))

    wr.writerow(header)

    format = '%d.%m.%Y %H:%M:%S'

    date_continue = [True for i in range(len(other_stations_readers))]
    while row != None:
        try:
            row = next(target_reader)
            date_check_str = row[0]
            try:
                cur_datetime = datetime.strptime(date_check_str, format)
            except ValueError:
                date_check_str = date_check_str.replace(' 24:', ' 23:')
                cur_datetime = datetime.strptime(date_check_str, format)
                cur_datetime += timedelta(hours=1)
            # print(date_check_str)
            data_point = row
            # for osr in other_stations_readers:
            for i, osr in enumerate(other_stations_readers):
                # print(date_continue)
                try:
                    if date_continue[i] is True:
                        osr_row = next(osr)
                        try:
                            osr_row_time = datetime.strptime(osr_row[0], format)
                        except ValueError:
                            date_check_tmp = osr_row[0].replace(' 24:', ' 23:')
                            osr_row_time = datetime.strptime(date_check_tmp, format)
                            osr_row_time += timedelta(hours=1)
                    else:
                        osr_row = date_continue[i]
                        try:
                            osr_row_time = datetime.strptime(osr_row[0], format)
                        except ValueError:
                            # print('err: ' + osr_row[0])
                            date_check_tmp = osr_row[0].replace(' 24:', ' 23:')
                            osr_row_time = datetime.strptime(date_check_tmp, format)
                            osr_row_time += timedelta(hours=1)
                except StopIteration as e:
                    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    print(other_stations[i])
                    row = None
                    break

                # print(date_check_str)
                # print(osr_row[0])


                if cur_datetime == osr_row_time:
                    date_continue[i] = True
                    osr_five = osr_row[2:3] + osr_row[482:486]
                    data_point.extend(osr_five)
                elif cur_datetime > osr_row_time:
                    while cur_datetime > osr_row_time:
                        osr_row = next(osr)
                        try:
                            osr_row_time = datetime.strptime(osr_row[0], format)
                        except ValueError:
                            # print('err: ' + osr_row[0])
                            date_check_tmp = osr_row[0].replace(' 24:', ' 23:')
                            osr_row_time = datetime.strptime(date_check_tmp, format)
                            osr_row_time += timedelta(hours=1)
                    if cur_datetime == osr_row_time:
                        date_continue[i] = True
                        osr_five = osr_row[2:3] + osr_row[482:486]
                        data_point.extend(osr_five)
                    elif cur_datetime < osr_row_time:
                        date_continue[i] = osr_row[:]
                        data_point.extend([-1,-1,-1,-1,-1])
                elif cur_datetime < osr_row_time:
                    date_continue[i] = osr_row[:]
                    data_point.extend([-1,-1,-1,-1,-1])
                    # print('here')
            # print(len(data_point))

            wr.writerow(data_point)
        except StopIteration as e:
            row = None
        except Exception as e:
            print(repr(e))

    print(target_station + ' ' + hour + ' done.')
    output.close()

    csv_to_parquet(output_csv_path)
    os.remove(output_csv_path)
    os.remove(target_nearby_station_data_path)


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)