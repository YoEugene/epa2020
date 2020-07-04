import os
import pandas as pd


def xls_to_csv(filepath):
    try:
        read_file = pd.read_excel(filepath)
        read_file.to_csv(filepath.replace('xls', 'csv'), index=None, header=True)
        print('Convert ' + filepath + ' done.')
    except Exception as e:
        print('[Error] Converting ' + filepath + ' failed, reason: ' + repr(e))


def main(train_begin_year=2015, train_end_year=2018, test_begin_year=2019, test_end_year=2019):
    data_folder_prefix = './data'

    for year in list(range(train_begin_year, train_end_year+1)) + list(range(test_begin_year, test_end_year+1)):
        year_folder = str(year) + '_raw'
        print('============= Start on year: ' + year_folder + ' =============')
        for area_folder in os.listdir('/'.join([data_folder_prefix, year_folder])):
            if '空品區' in area_folder:
                print('################ Processing area: ' + area_folder + ' ################')
                for xls_file in os.listdir('/'.join([data_folder_prefix, year_folder, area_folder])):
                    if '.xls' == xls_file[-4:]:  # if filename end up with .xls
                        xls_filepath = '/'.join([data_folder_prefix, year_folder, area_folder, xls_file])
                        xls_to_csv(xls_filepath)


if __name__ == '__main__':
    train_begin_year, train_end_year, test_begin_year, test_end_year = 2015, 2018, 2019, 2019
    main(train_begin_year, train_end_year, test_begin_year, test_end_year)
