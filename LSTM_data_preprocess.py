from datetime import datetime
import os
from collections import defaultdict
import csv
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-y', help='years')
parser.add_argument('-s', help='stations')
parser.add_argument('-pos', help='position')
args = parser.parse_args()

data_folder_prefix = './data'
year_folders = [
    '2015(104)_HOUR_00_20160323',
    '2016(105)_HOUR_00_20170301',
    '2017(106)_HOUR_00_20180308',
    '2018(107)_HOUR_00_20190315',
    '2019(108)_HOUR_00_20200317',
]
# means = [0, 17.5, 23, 24.4, 1.9, 0.64, 0.2, 10.35, 23.84, 34.18, 38.30, 0.226, 75.75, 2.91, 2.11, 164.24, 164.68, 1.92, 1.4386]
features = ['','PM2.5','O3','AMB_TEMP','CH4','CO','NMHC','NO','NO2','NOx','PM10','RAINFALL','RH','SO2','THC','WD_HR','WIND_DIREC','WIND_SPEED','WS_HR']


def main():
    for position in args.pos.split(','):
        if not args.s:
            for station in os.listdir('/'.join([data_folder_prefix, position])):
                if '.' in station: continue
                csv_files = os.listdir('/'.join([data_folder_prefix, position, station]))
                print(station)
                for year in args.y.split(','):
                    for csv_file in csv_files:
                        if year == csv_file[:3]:
                            raw_csv_path = '/'.join([data_folder_prefix, position, station, csv_file])
                            lstm_csv_path = '/'.join([data_folder_prefix, position, station, str(int(year)+1911) + '.csv'])
                            raw_csv_to_lstm_csv(raw_csv_path, lstm_csv_path, str(int(year)+1911), position, station)
        else:
            for station in args.s.split(','):
                if '.' in station: continue
                csv_files = os.listdir('/'.join([data_folder_prefix, position, station]))
                print(station)
                for year in args.y.split(','):
                    for csv_file in csv_files:
                        if year == csv_file[:3]:
                            raw_csv_path = '/'.join([data_folder_prefix, position, station, csv_file])
                            lstm_csv_path = '/'.join([data_folder_prefix, position, station, str(int(year)+1911) + '.csv'])
                            raw_csv_to_lstm_csv(raw_csv_path, lstm_csv_path, str(int(year)+1911), position, station)
            


def gen_day_empty(date_str, day_of_year, month):
    day, mon, year = [int(s) for s in date_str.split('.')]
    return {i: [date_str + ' ' + format(i, '02d') + ':00:00'] + [0 for xx in range(len(features)-1)] + [str((day_of_year) % 365), str(i), str(datetime(year, mon, day).weekday()), month] for i in range(1, 25)}


def raw_csv_to_lstm_csv(raw_csv, lstm_csv, year, position, station):
    # try:
    if year == '2019':
        output = open(lstm_csv, "w")
    else:
        lstm_csv = '/'.join([data_folder_prefix, position, station]) + '/2015_2018.csv'
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
        n_hours = 72  # 3 days

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
    main()