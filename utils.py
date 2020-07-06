import json


def read_config():
    config_path = "./config.json"
    with open('./config.json') as json_file:
        cfg = json.load(json_file)
    return cfg
