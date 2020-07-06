from datetime import datetime
import os
from collections import defaultdict
import csv
import argparse
from utils import read_config
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-areas', help='areas')
args = parser.parse_args()

features = ['','PM2.5','O3','AMB_TEMP','CH4','CO','NMHC','NO','NO2','NOx','PM10','RAINFALL','RH','SO2','THC','WD_HR','WIND_DIREC','WIND_SPEED','WS_HR']

data_root_folder = "./EPA_Station_rawdata"
train_begin_year = 2015  # default value
train_end_year = 2018  # default value
test_begin_year = 2019  # default value
test_end_year = 2019  # default value
target_variable = "PM2.5"


def main(cfg):
    global data_root_folder
    global train_begin_year
    global train_end_year
    global test_begin_year
    global test_end_year
    data_root_folder = cfg['data_root_folder']
    train_begin_year = cfg['train_begin_year']
    train_end_year = cfg['train_end_year']
    test_begin_year = cfg['test_begin_year']
    test_end_year = cfg['test_end_year']
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

        for station in stations:
            if '.' in station: continue
            if station not in os.listdir('/'.join([data_root_folder, area])): continue
            csv_files = os.listdir('/'.join([data_root_folder, area, station]))
            print('Converting station to LSTM format: ' + station)
            for year in list(range(train_begin_year, train_end_year+1)) + list(range(test_begin_year, test_end_year+1)):
                for csv_file in csv_files:
                    if str(int(year) - 1911) == csv_file[:3]:
                        raw_csv_path = '/'.join([data_root_folder, area, station, csv_file])
                        lstm_csv_path = '/'.join([data_root_folder, area, station, str(year) + '.csv'])
                        raw_csv_to_lstm_csv(raw_csv_path, lstm_csv_path, str(year), area, station)


def gen_day_empty(date_str, day_of_year, month):
    day, mon, year = [int(s) for s in date_str.split('.')]
    return {i: [date_str + ' ' + format(i, '02d') + ':00:00'] + [0 for xx in range(len(features)-1)] + [str((day_of_year) % 365), str(i), str(datetime(year, mon, day).weekday()), month] for i in range(1, 25)}


def raw_csv_to_lstm_csv(raw_csv, lstm_csv, year, area, station):
    # try:
    # TODO train test begin end year
    if year == '2019':
        output = open(lstm_csv, "w")
    else:
        lstm_csv = '/'.join([data_root_folder, area, station]) + '/' + str(train_begin_year) + '_' + str(train_end_year) + '.csv'
        if year == '2015':
            output = open(lstm_csv, "w")
        else:
            output = open(lstm_csv, "a")
    wr = csv.writer(output)
    if year == '2015' or year == '2019':
        wr.writerow(['Date Time','PM2.5','O3','AMB_TEMP','CH4','CO','NMHC','NO','NO2','NOx','PM10','RAINFALL','RH','SO2','THC','WD_HR','WIND_DIREC','WIND_SPEED','WS_HR','DAY_OF_YEAR','HOUR','WEEKDAY','MONTH'])

    day_ctr = 0
    d = gen_day_empty('01.01.' + year, 0, '1')
    with open(raw_csv, newline='') as f:
        # try:
        rows = csv.reader(f)
        cur_date = year + '/01/01'

        last_n_hours_rows = defaultdict(list)
        n_hours = 6  # hours

        for row in rows:
            if '測項' in row: continue  # pass first header row

            date_str = row[0]
            if cur_date != date_str:
                cur_date = date_str
                orig_day = str(day)
                # print(orig_day)
                year, mon, day = date_str.split('/')
                # print(day)
                if int(day) > 1 :
                    day_ctr += (int(day) - int(orig_day)) % 30 
                else:
                    day_ctr += 1
                for hr in range(1, 25):
                    wr.writerow(d[hr])
                d = gen_day_empty(day + '.' + mon + '.' + year, day_ctr, mon.lstrip('0'))
            year, mon, day = date_str.split('/')

            try:
                feature_ind = features.index(row[2])
            except ValueError:
                # print('feature ' + row[2] + ' not found.')
                pass
            else:
                if len(last_n_hours_rows[feature_ind]) < n_hours + 24:
                    extend_list = []
                    for s in row[3:]:
                        try:
                            extend_list.append(int(s))
                        except:
                            extend_list.append(round(sum(last_n_hours_rows[feature_ind])/len(last_n_hours_rows[feature_ind]), 3)) if len(last_n_hours_rows[feature_ind]) != 0 else extend_list.append(0)
                    last_n_hours_rows[feature_ind].extend(extend_list)
                else:
                    extend_list = []
                    for s in row[3:]:
                        try:
                            extend_list.append(int(s))
                        except:
                            extend_list.append(round(sum(last_n_hours_rows[feature_ind])/len(last_n_hours_rows[feature_ind]), 3))
                    last_n_hours_rows[feature_ind] = last_n_hours_rows[feature_ind][24:] + extend_list

                # print(len(last_n_hours_rows[feature_ind]))

                for hour in range(1, 25):
                    value = row[2+hour]
                    if value == 'NR':
                        d[hour][feature_ind] = 0
                    elif ('#' in value or '*' in value or 'x' in value or 'A' in value or value == ''):
                        try:
                            fill_value = round(sum(last_n_hours_rows[feature_ind][-(24-hour+1)-n_hours:-(24-hour+1)])/len(last_n_hours_rows[feature_ind][-(24-hour+1)-n_hours:-(24-hour+1)]), 3) if len(last_n_hours_rows[feature_ind][-(24-hour+1)-n_hours:-(24-hour+1)]) > 0 else 0
                            d[hour][feature_ind] = float(fill_value)
                        except Exception as e:
                            print(last_n_hours_rows[feature_ind])
                            print(repr(e))
                    elif (feature_ind == 15 or feature_ind == 16) and (value == '888' or value == '999'):
                        d[hour][feature_ind] = -1
                    else:
                        d[hour][feature_ind] = float(value)
        for hr in range(1, 25):
            wr.writerow(d[hr])

        output.close()

        # print('Convert ' + raw_csv + ' to ' + lstm_csv + ' done.')
    # except Exception as e:
    #     print(raw_csv)
    #     print(repr(e))
    #     return


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)