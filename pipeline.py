import airtw_xls_to_csv
import move_csv_to_area
import LSTM_data_preprocess
import GBDT_data_preprocess
import GBDT_add_nearby_data
import train
import predict
import report
from utils import read_config
import json
from pprint import pprint

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-config', help='config')
args = parser.parse_args()


def main(cfg):
    # # Step 1
    # airtw_xls_to_csv.main(cfg)

    # # Step 2
    # move_csv_to_area.main(cfg)

    # # Step 3
    # LSTM_data_preprocess.main(cfg)

    # # Step 4 - 1
    # GBDT_data_preprocess.main(cfg)

    # Step 4 - 2
    GBDT_add_nearby_data.main(cfg)

    # Step 5
    # train.main(cfg)

    # # Step 6
    # predict.main(cfg)

    # # Step 7
    # report.main(cfg)


if __name__ == '__main__':
    cfg = read_config()
    pprint(cfg)
    main(cfg)