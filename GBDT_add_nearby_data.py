import csv
import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-pos', help='position')
parser.add_argument('-o', help='output_name')
parser.add_argument('-target', help='target_csv_name')
args = parser.parse_args()

features = ['','PM2.5','O3','AMB_TEMP','CH4','CO','NMHC','NO','NO2','NOx','PM10','RAINFALL','RH','SO2','THC','WD_HR','WIND_DIREC','WIND_SPEED','WS_HR','DAY_OF_YEAR','HOUR','WEEKDAY','MONTH']
data_folder_prefix = './data'


def main():
    for hour in range(1, 25):
        for station in args.s.split('  '):
            if '.' in station: continue
            position = args.pos
            other_stations = []
            for station_tmp in os.listdir('/'.join([data_folder_prefix, position])):
                if '.' in station_tmp: continue
                if station_tmp != station: other_stations.append(station_tmp)

            csv_path = '/'.join([data_folder_prefix, position])

            print(csv_path, station, other_stations, str(hour), args.target)
            gbdt_add_nearby_stations_data(csv_path, station, other_stations, str(hour), args.target)
            return


def gbdt_add_nearby_stations_data(csv_path, target_station, other_stations, hour, target_csv_name):
    output = open('/'.join([csv_path, target_station, hour, args.o]), "w+")
    wr = csv.writer(output)

    target_reader = csv.reader(open('/'.join([csv_path, target_station, hour, target_csv_name]), newline=''))
    other_stations_readers = []
    for ost in other_stations:
        other_stations_readers.append(csv.reader(open('/'.join([csv_path, ost, hour, target_csv_name]), newline='')))

    row = next(target_reader)
    header = row
    for osr in other_stations_readers:
        osr_row = next(osr)

    for i in range(len(other_stations_readers)):
        header.extend(['PM2.5_NEARBY' + str(i+1) + '_T1', 'PM2.5_NEARBY' + str(i+1) + '_AVG3', 'PM2.5_NEARBY' + str(i+1) + '_AVG6', 'PM2.5_NEARBY' + str(i+1) + '_AVG12', 'PM2.5_NEARBY' + str(i+1) + '_AVG24'])

    wr.writerow(header)

    while row != None:
        try:
            row = next(target_reader)
            date_check_str = row[0]
            print(date_check_str)
            data_point = row
            # for osr in other_stations_readers:
            date_continue = [True for i in range(len(other_stations_readers))]
            for i, osr in enumerate(other_stations_readers):
                try:
                    if date_continue[i] is True:
                        osr_row = next(osr)
                    else:
                        osr_row = date_continue[i]
                except StopIteration as e:
                    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    print(other_stations[i])
                    row = None
                    break

                if osr_row[0] == date_check_str:
                    date_continue[i] = True
                    osr_five = osr_row[2:3] + osr_row[482:486]
                    data_point.extend(osr_five)
                else:
                    date_continue[i] = osr_row[:]
                    data_point.extend([-1,-1,-1,-1,-1])

            wr.writerow(data_point)
        except StopIteration as e:
            row = None
        except Exception as e:
            print(repr(e))

    print(target_station + ' ' + hour + ' done.')

if __name__ == '__main__':
    main()