import os
import shutil
from utils import read_config

# Define each 空品區 belongs to which folder
area_relations = {
    '北部': 'North',
    '宜蘭': 'North',
    '竹苗': 'North',
    '中部': 'Central',
    '雲嘉南': 'South',
    '高屏': 'South',
}


def main(cfg):
    data_folder_prefix = cfg['data_root_folder']
    train_begin_year = cfg['train_begin_year']
    train_end_year = cfg['train_end_year']
    test_begin_year = cfg['test_begin_year']
    test_end_year = cfg['test_end_year']

    for year in list(range(train_begin_year, train_end_year+1)) + list(range(test_begin_year, test_end_year+1)):
        year_folder = str(year) + '_raw'
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
                                # 富貴角站 needs to be dealt with individual config due to its data start year is 2017
                                if "富貴角" in station_name: continue
                                file_path = '/'.join([data_folder_prefix, year_folder, area_folder, csv_file])
                                target_path = '/'.join([data_folder_prefix, position_path, station_name])
                                copy_file_to_path(file_path, target_path)


def copy_file_to_path(file_path, target_path):
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    shutil.copy(file_path, target_path)
    print('Copy file: ' + file_path + ' to path: ' + target_path)


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)
