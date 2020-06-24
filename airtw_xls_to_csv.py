import os
import pandas as pd

data_folder_prefix = './data'
year_folders = [
    '2015(104)_HOUR_00_20160323',
    '2016(105)_HOUR_00_20170301',
    '2017(106)_HOUR_00_20180308',
    '2018(107)_HOUR_00_20190315',
    '2019(108)_HOUR_00_20200317',
]


def xls_to_csv(filepath):
    try:
        read_file = pd.read_excel(filepath)
        read_file.to_csv(filepath.replace('xls', 'csv'), index=None, header=True)
        print('Convert ' + filepath + ' done.')
    except Exception as e:
        print('[Error] Converting ' + filepath + ' failed, reason: ' + repr(e))


def main():
    for year_folder in year_folders:
        print('============= Start on year: ' + year_folder + ' =============')
        for area_folder in os.listdir('/'.join([data_folder_prefix, year_folder])):
            if '空品區' in area_folder:
                print('################ Processing area: ' + area_folder + ' ################')
                for xls_file in os.listdir('/'.join([data_folder_prefix, year_folder, area_folder])):
                    if '.xls' == xls_file[-4:]:  # if filename end up with .xls
                        xls_filepath = '/'.join([data_folder_prefix, year_folder, area_folder, xls_file])
                        xls_to_csv(xls_filepath)


if __name__ == '__main__':
    main()
