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

    multiprcossing_number = cfg["multiprcossing_number"] if cfg and "multiprcossing_number" in cfg else 10

    global nearby_km_range
    nearby_km_range = cfg['nearby_km_range']

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
        pool.map(station_multiprocess, itertools.product(stations, [area], range(1, 14)))

        print('################ Cleaning area csv files: ' + area + ' ################')

        if not args.s and not cfg['stations']:
            stations = os.listdir('/'.join([data_root_folder, area]))
        elif args.s:
            stations = args.s.split(',')
        elif cfg['stations']:
            stations = cfg['stations']

        for station in stations:
            if '.' in station: continue
            if station not in os.listdir('/'.join([data_root_folder, area])): continue
            for hour in range(1, 14):
                files = os.listdir('/'.join([data_root_folder, area, station, target_variable, str(hour)]))
                for f in files:
                    if '.csv' in f and 'nearby' in f:
                        os.remove('/'.join([data_root_folder, area, station, target_variable, str(hour), f]))
            print("Station cleaned: " + station)


def station_multiprocess(station_input):
    global data_root_folder, nearby_km_range

    station, area, hour = station_input

    if '.' in station: return
    if station not in os.listdir('/'.join([data_root_folder, area])): return

    print('Adding nearby station data into model: ' + station + " hour " + str(hour))

    other_stations = get_nearby_stations(station, cfg['nearby_km_range'])
    other_stations.extend(['富貴角站', '馬公站', '馬祖站', '金門站'])
    other_stations = sorted(list(set(other_stations)))

    # print('with nearby stations: ' + str(other_stations))

    gbdt_add_nearby_stations_data(area, station, other_stations, str(hour), 'gbdt_2015_2018.csv', 'gbdt_2015_2018_nearby_' + str(nearby_km_range) + 'km.csv')
    gbdt_add_nearby_stations_data(area, station, other_stations, str(hour), 'gbdt_2019.csv', 'gbdt_2019_nearby_' + str(nearby_km_range) + 'km.csv')


def gbdt_add_nearby_stations_data(area, target_station, other_stations, hour, target_csv_name, output_csv_name):
    global data_root_folder
    global target_variable

    output_csv_path = '/'.join([data_root_folder, area, target_station, target_variable, hour, output_csv_name])

    # if os.path.exists(output_csv_path):
    #     print('Nearby data already added. Passed. ' + output_csv_path)
    #     return

    output = open(output_csv_path, "w+")
    wr = csv.writer(output)

    target_station_csv_path = '/'.join([data_root_folder, area, target_station, target_variable, hour, target_csv_name])

    target_reader = csv.reader(open(target_station_csv_path, newline=''))
    other_stations_readers = []
    for ost in other_stations:
        os_reader = None
        for area in ["North", "South", "Central", "East", "Other"]:
            try:
                os_reader = csv.reader(open('/'.join([data_root_folder, area, ost, target_variable, hour, target_csv_name]), newline=''))
                break
            except:
                pass
        if os_reader is not None:
            other_stations_readers.append(os_reader)

    row = next(target_reader)
    header = row
    for osr in other_stations_readers:
        osr_row = next(osr)

    for i in range(len(other_stations_readers)):
        related_variables = ['PM2.5', 'PM10', 'NO2', 'O3', 'CO']
        for variable in related_variables:
            header.extend([
                            variable + '_NEARBY' + str(i+1) + '_T1', 
                            variable + '_NEARBY' + str(i+1) + '_T3', 
                            variable + '_NEARBY' + str(i+1) + '_T6', 
                            variable + '_NEARBY' + str(i+1) + '_T12', 
                            variable + '_NEARBY' + str(i+1) + '_T24', 
                            variable + '_NEARBY' + str(i+1) + '_AVG3', 
                            variable + '_NEARBY' + str(i+1) + '_AVG6', 
                            variable + '_NEARBY' + str(i+1) + '_AVG12', 
                            variable + '_NEARBY' + str(i+1) + '_AVG24',
                        ])

    wr.writerow(header)

    date_format = '%d.%m.%Y %H:%M:%S'

    date_continue = [True for i in range(len(other_stations_readers))]
    while row != None:
        try:
            row = next(target_reader)
            date_check_str = row[0]
            try:
                cur_datetime = datetime.strptime(date_check_str, date_format)
            except ValueError:
                date_check_str = date_check_str.replace(' 24:', ' 23:')
                cur_datetime = datetime.strptime(date_check_str, date_format)
                cur_datetime += timedelta(hours=1)
            data_point = row
            for i, osr in enumerate(other_stations_readers):
                try:
                    if date_continue[i] is True:
                        osr_row = next(osr)
                        try:
                            osr_row_time = datetime.strptime(osr_row[0], date_format)
                        except ValueError:
                            date_check_tmp = osr_row[0].replace(' 24:', ' 23:')
                            osr_row_time = datetime.strptime(date_check_tmp, date_format)
                            osr_row_time += timedelta(hours=1)
                    else:
                        osr_row = date_continue[i]
                        try:
                            osr_row_time = datetime.strptime(osr_row[0], date_format)
                        except ValueError:
                            date_check_tmp = osr_row[0].replace(' 24:', ' 23:')
                            osr_row_time = datetime.strptime(date_check_tmp, date_format)
                            osr_row_time += timedelta(hours=1)
                except StopIteration as e:
                    print(other_stations[i])
                    row = None
                    break

                if cur_datetime == osr_row_time:
                    date_continue[i] = True
                    osr_extended_data = osr_row[2:3] + osr_row[4:5] + osr_row[7:8] + osr_row[13:14] + osr_row[25:26] + osr_row[482:486] + \
                                        osr_row[1+36*8+1:1+36*8+2] + osr_row[1+36*8+3:1+36*8+4] + osr_row[1+36*8+6:1+36*8+7] + osr_row[1+36*8+12:1+36*8+13] + osr_row[1+36*8+24:1+36*8+25] + osr_row[481+4*8+1:481+4*8+5] + \
                                        osr_row[1+36*6+1:1+36*6+2] + osr_row[1+36*6+3:1+36*6+4] + osr_row[1+36*6+6:1+36*6+7] + osr_row[1+36*6+12:1+36*6+13] + osr_row[1+36*6+24:1+36*6+25] + osr_row[481+4*6+1:481+4*6+5] + \
                                        osr_row[1+36*1+1:1+36*1+2] + osr_row[1+36*1+3:1+36*1+4] + osr_row[1+36*1+6:1+36*1+7] + osr_row[1+36*1+12:1+36*1+13] + osr_row[1+36*1+24:1+36*1+25] + osr_row[481+4*1+1:481+4*1+5] + \
                                        osr_row[1+36*3+1:1+36*3+2] + osr_row[1+36*3+3:1+36*3+4] + osr_row[1+36*3+6:1+36*3+7] + osr_row[1+36*3+12:1+36*3+13] + osr_row[1+36*3+24:1+36*3+25] + osr_row[481+4*3+1:481+4*3+5] + \
                                        osr_row[1+36*4+1:1+36*4+2] + osr_row[1+36*4+3:1+36*4+4] + osr_row[1+36*4+6:1+36*4+7] + osr_row[1+36*4+12:1+36*4+13] + osr_row[1+36*4+24:1+36*4+25] + osr_row[481+4*4+1:481+4*4+5] + \
                                        osr_row[1+36*5+1:1+36*5+2] + osr_row[1+36*5+3:1+36*5+4] + osr_row[1+36*5+6:1+36*5+7] + osr_row[1+36*5+12:1+36*5+13] + osr_row[1+36*5+24:1+36*5+25] + osr_row[481+4*5+1:481+4*5+5] + \
                                        osr_row[1+36*7+1:1+36*7+2] + osr_row[1+36*7+3:1+36*7+4] + osr_row[1+36*7+6:1+36*7+7] + osr_row[1+36*7+12:1+36*7+13] + osr_row[1+36*7+24:1+36*7+25] + osr_row[481+4*7+1:481+4*7+5]

                    data_point.extend(osr_extended_data)
                elif cur_datetime > osr_row_time:
                    while cur_datetime > osr_row_time:
                        osr_row = next(osr)
                        try:
                            osr_row_time = datetime.strptime(osr_row[0], date_format)
                        except ValueError:
                            # print('err: ' + osr_row[0])
                            date_check_tmp = osr_row[0].replace(' 24:', ' 23:')
                            osr_row_time = datetime.strptime(date_check_tmp, date_format)
                            osr_row_time += timedelta(hours=1)
                    if cur_datetime == osr_row_time:
                        date_continue[i] = True
                        osr_extended_data = osr_row[2:3] + osr_row[4:5] + osr_row[7:8] + osr_row[13:14] + osr_row[25:26] + osr_row[482:486] + \
                                        osr_row[1+36*8+1:1+36*8+2] + osr_row[1+36*8+3:1+36*8+4] + osr_row[1+36*8+6:1+36*8+7] + osr_row[1+36*8+12:1+36*8+13] + osr_row[1+36*8+24:1+36*8+25] + osr_row[481+4*8+1:481+4*8+5] + \
                                        osr_row[1+36*6+1:1+36*6+2] + osr_row[1+36*6+3:1+36*6+4] + osr_row[1+36*6+6:1+36*6+7] + osr_row[1+36*6+12:1+36*6+13] + osr_row[1+36*6+24:1+36*6+25] + osr_row[481+4*6+1:481+4*6+5] + \
                                        osr_row[1+36*1+1:1+36*1+2] + osr_row[1+36*1+3:1+36*1+4] + osr_row[1+36*1+6:1+36*1+7] + osr_row[1+36*1+12:1+36*1+13] + osr_row[1+36*1+24:1+36*1+25] + osr_row[481+4*1+1:481+4*1+5] + \
                                        osr_row[1+36*3+1:1+36*3+2] + osr_row[1+36*3+3:1+36*3+4] + osr_row[1+36*3+6:1+36*3+7] + osr_row[1+36*3+12:1+36*3+13] + osr_row[1+36*3+24:1+36*3+25] + osr_row[481+4*3+1:481+4*3+5] + \
                                        osr_row[1+36*4+1:1+36*4+2] + osr_row[1+36*4+3:1+36*4+4] + osr_row[1+36*4+6:1+36*4+7] + osr_row[1+36*4+12:1+36*4+13] + osr_row[1+36*4+24:1+36*4+25] + osr_row[481+4*4+1:481+4*4+5] + \
                                        osr_row[1+36*5+1:1+36*5+2] + osr_row[1+36*5+3:1+36*5+4] + osr_row[1+36*5+6:1+36*5+7] + osr_row[1+36*5+12:1+36*5+13] + osr_row[1+36*5+24:1+36*5+25] + osr_row[481+4*5+1:481+4*5+5] + \
                                        osr_row[1+36*7+1:1+36*7+2] + osr_row[1+36*7+3:1+36*7+4] + osr_row[1+36*7+6:1+36*7+7] + osr_row[1+36*7+12:1+36*7+13] + osr_row[1+36*7+24:1+36*7+25] + osr_row[481+4*7+1:481+4*7+5]

                        data_point.extend(osr_extended_data)
                    elif cur_datetime < osr_row_time:
                        date_continue[i] = osr_row[:]
                        data_point.extend([-1]*(len(related_variables)*9))
                elif cur_datetime < osr_row_time:
                    date_continue[i] = osr_row[:]
                    data_point.extend([-1]*(len(related_variables)*9))

            wr.writerow(data_point)
        except StopIteration as e:
            row = None
        except Exception as e:
            print(repr(e))

    output.close()
    csv_to_parquet(output_csv_path)


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)