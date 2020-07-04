import airtw_xls_to_csv
import move_csv_to_area
import LSTM_data_preprocess
import GBDT_data_preprocess
import GBDT_add_nearby_data
import train
import predict
import report

import json

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-config', help='config')
args = parser.parse_args()


def main(cfg):
    # Step 1
    airtw_xls_to_csv.main(cfg['train_begin_year'], cfg['train_begin_year'], cfg['train_begin_year'], cfg['train_begin_year'])

    # Step 2
    move_csv_to_area.main(cfg['train_begin_year'], cfg['train_begin_year'], cfg['train_begin_year'], cfg['train_begin_year'])

    # Step 3
    LSTM_data_preprocess.main(cfg['train_begin_year'], cfg['train_begin_year'], cfg['train_begin_year'], cfg['train_begin_year'], cfg['station'], cfg['area'])

    # Step 4 - 1
    GBDT_data_preprocess.main()

    # Step 4 - 2
    GBDT_add_nearby_data.main()

    # Step 5
    train.main()

    # Step 6
    predict.main()

    # Step 7
    report.main()



def read_config():
    config_path = "./config.json" if not args.config else args.config
    with open('./config.json') as json_file:
        cfg = json.load(json_file)
    return cfg

if __name__ == '__main__':
    cfg = read_config()
    print(cfg)
    main(cfg)