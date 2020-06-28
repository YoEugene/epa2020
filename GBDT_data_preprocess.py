import csv
import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-pos', help='position')
args = parser.parse_args()

features = ['','PM2.5','O3','AMB_TEMP','CH4','CO','NMHC','NO','NO2','NOx','PM10','RAINFALL','RH','SO2','THC','WD_HR','WIND_DIREC','WIND_SPEED','WS_HR','DAY_OF_YEAR','HOUR','WEEKDAY','MONTH']
data_folder_prefix = './data'

# features: 
# 1. PM2.5, SO2, O3, CO, NOx, PM10, THC, NO2, NO, NMHC, CH4: pre 1-30
# 2. RH, WIND_DIREC, WIND_SPEED, WS_HR, WD_HR, AMB_TEMP: pre 1-13
# 3. PM2.5, SO2, O3, CO, NOx, PM10, THC, NO2, NO, NMHC, CH4: avg_3hr, avg_6hr, avg_12hr
# 4. hour of day, day of year, month, weekday


def main():
    for station in args.s.split('  '):

        for position in [args.pos]:
        # for station in os.listdir('/'.join([data_folder_prefix, position])):
            if '.' in station: continue
            print(station)
            for hour in range(1, 14):  # build data for prediction hour_1 ~ hour_13
                lstm_csv_path = '/'.join([data_folder_prefix, position, station, '2015_2018.csv'])
                gbdt_csv_path = '/'.join([data_folder_prefix, position, station, str(hour)])
                lstm_to_gbdt_csv(lstm_csv_path, gbdt_csv_path, 'gbdt_2015_2018.csv', hour)

                lstm_csv_path = '/'.join([data_folder_prefix, position, station, '2019.csv'])
                gbdt_csv_path = '/'.join([data_folder_prefix, position, station, str(hour)])
                lstm_to_gbdt_csv(lstm_csv_path, gbdt_csv_path, 'gbdt_2019.csv', hour)

def lstm_to_gbdt_csv(lstm_csv_path, gbdt_csv_path, gbdt_csv_name, hour_offset):
    if not os.path.exists(gbdt_csv_path):
        os.makedirs(gbdt_csv_path)

    output = open('/'.join([gbdt_csv_path, gbdt_csv_name]), "w")
    wr = csv.writer(output)
    # wr.writerow(['PM25','SO2','O3','CO','NOx','PM10','RH','THC','WIND_DIREC','AMB_TEMP','NO2','NO','NMHC','WIND_SPEED','CH4','WS_HR','WD_HR','DAY_OF_YEAR','HOUR','WEEKDAY','MONTH'])

    with open(lstm_csv_path, newline='') as f:
        reader = csv.reader(f)
        next(reader)

        row_48 = []

        for _ in range(48):
            row = next(reader)
            row_48.append(row)

        flag = True
        header = ['TIME', 'PM2.5_TARGET']
        while row != None:
            row_48_t = list(map(list, zip(*row_48)))
            data_point = []
            try:
                row = next(reader)
                data_point.append(row[0])
                data_point.append(row[1])
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
                            avg = sum([float(s) for s in row_48_t[feature_ind][-hour_avg:]])/hour_avg
                        else:
                            avg = sum([float(s) for s in row_48_t[feature_ind][-hour_avg-hour_offset+1:-hour_offset+1]])/hour_avg
                        data_point.append(avg)
                # for feature_ind in [1,2,4,5,6,7,8,9,10,13,14]:
                #     for hour_back in range(2, 13):
                #         if flag:
                #             header.append(features[feature_ind] + '_DIVTSQR_T' + str(hour_back))
                #         divtsqr_value = float(row_48[-hour_offset-hour_back+1][feature_ind]) / (hour_back ** 2)
                #         # print(divtsqr_value)
                #         data_point.append(divtsqr_value)

                data_point.extend(row[-4:])
                if flag:
                    header.extend(['DAY_OF_YEAR','HOUR','WEEKDAY','MONTH'])
                    wr.writerow(header)
                    flag = False

                # print(data_point)

                wr.writerow(data_point)

                row_48.append(row)
                row_48 = row_48[1:]
                # break

            except StopIteration:
                row = None
                print('/'.join([gbdt_csv_path, gbdt_csv_name]) + ' done.')


if __name__ == "__main__":
    main()
