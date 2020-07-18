import os
import pandas as pd
from utils import read_config


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
            if '空品區' in area_folder or '監測站' in area_folder:
                print('################ Processing area: ' + area_folder + ' ################')
                for xls_file in os.listdir('/'.join([data_folder_prefix, year_folder, area_folder])):
                    if '.xls' == xls_file[-4:]:  # if filename end up with .xls
                        if xls_file.replace('xls', 'csv') in os.listdir('/'.join([data_folder_prefix, year_folder, area_folder])):
                            print('Skipped. Already converted to ' + xls_file.replace('xls', 'csv'))
                            continue
                        xls_filepath = '/'.join([data_folder_prefix, year_folder, area_folder, xls_file])
                        xls_to_csv(xls_filepath)


def xls_to_csv(filepath):
    try:
        read_file = pd.read_excel(filepath)
        read_file.to_csv(filepath.replace('xls', 'csv'), index=None, header=True)
        print('Convert ' + filepath + ' done.')
    except Exception as e:
        print('[Error] Converting ' + filepath + ' failed, reason: ' + repr(e))


if __name__ == '__main__':
    cfg = read_config()
    main(cfg)
