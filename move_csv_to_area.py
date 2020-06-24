import os
import shutil

data_folder_prefix = './data'
year_folders = [
    '2015(104)_HOUR_00_20160323',
    '2016(105)_HOUR_00_20170301',
    '2017(106)_HOUR_00_20180308',
    '2018(107)_HOUR_00_20190315',
    '2019(108)_HOUR_00_20200317',
]
area_relations = {
    '北部': 'North',
    '宜蘭': 'North',
    '竹苗': 'North',
    '中部': 'Central',
    '雲嘉南': 'South',
    '高屏': 'South',
}


def main():
    for year_folder in year_folders:
        print('============= Start on year: ' + year_folder + ' =============')
        for area_folder in os.listdir('/'.join([data_folder_prefix, year_folder])):
            if '空品區' in area_folder:
                print('################ Processing area: ' + area_folder + ' ################')
                for area in area_relations.keys():
                    if area in area_folder:
                        position_path = area_relations[area]
                        for csv_file in os.listdir('/'.join([data_folder_prefix, year_folder, area_folder])):
                            if '.csv' == csv_file[-4:]:  # if filename end up with .csv
                                station_name = csv_file[csv_file.index('年') + 1: csv_file.index('站') + 1]
                                file_path = '/'.join([data_folder_prefix, year_folder, area_folder, csv_file])
                                target_path = '/'.join([data_folder_prefix, position_path, station_name])
                                copy_file_to_path(file_path, target_path)


def copy_file_to_path(file_path, target_path):
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    shutil.copy(file_path, target_path)
    print('Copy file: ' + file_path + ' to path: ' + target_path)


if __name__ == '__main__':
    main()
