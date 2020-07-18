import os
import pickle
import argparse
import pandas as pd
from datetime import datetime, timedelta
from utils import *
import warnings
import aqi
warnings.simplefilter("ignore", UserWarning)
parser = argparse.ArgumentParser()
parser.add_argument('-s', help='stations')
parser.add_argument('-t', help='datetime')
parser.add_argument('-v', help='variable')

args = parser.parse_args()

data_root_folder = "./EPA_Station_rawdata"
train_begin_year = 2015  # default value
train_end_year = 2018  # default value
test_begin_year = 2019  # default value
test_end_year = 2019  # default value

# python3 predict_online -s 竹山站 -t '2019-07-12 06:00:00' -v PM2.5

def datetime_transform(date_str):
    if date_str[11:13] != '24':
        return pd.to_datetime(date_str, format='%Y-%m-%d %H:%M:%S')

    date_str = date_str[:11] + '00' + date_str[13:]
    return pd.to_datetime(date_str, format='%Y-%m-%d %H:%M:%S') + timedelta(days=1)


def read_station_date_df(station):
    global target_date, target_date_prev_1
    target_df = pd.read_csv('./data/aqi_daily_hourly/' + target_date + '/aqi_daily_hourly_' + target_date + '.csv')
    target_df_prev_1 = pd.read_csv('./data/aqi_daily_hourly/' + target_date_prev_1 + '/aqi_daily_hourly_' + target_date_prev_1 + '.csv')

    df = pd.concat([target_df_prev_1, target_df])
    df = df[df['Station'] == station]
    df['Date Time'] = df['Date Time'].apply(datetime_transform)

    return df


def main(cfg):
    global target_date, target_date_prev_1
    target_time = datetime.strptime(args.t, '%Y-%m-%d %H:%M:%S')
    target_date = str(target_time.date())
    target_date_prev_1 = str((target_time + timedelta(days=-1)).date())

    target_df = read_station_date_df(args.s)
    other_dfs = {}

    # other_stations = sorted(get_nearby_stations(args.s, 80))
    # other_stations = os.listdir('/'.join([data_root_folder, 'Central']))
    other_stations = ['大里站', '線西站', '埔里站', '忠明站', '彰化站', '竹山站', '西屯站', '南投站', '豐原站', '二林站', '沙鹿站']
    other_stations.remove(args.s)

    # print(other_stations)

    for o_station in other_stations:
        other_dfs[o_station] = read_station_date_df(o_station)

    data = []

    for feat in ['PM2.5','O3','CH4','CO','NMHC','NO','NO2','NOx','PM10','SO2','THC']:
        for i in range(1, 37):
            t = target_time + timedelta(hours=-i)
            val = target_df[target_df['Date Time'] == t][feat].values[0]
            try:
                val = int(val)
            except:
                val = 0
            data.append(val)
    for feat in ['AMB_TEMP','RAINFALL','RH','WD_HR','WIND_DIREC','WIND_SPEED','WS_HR']:
        for i in range(1, 13):
            t = target_time + timedelta(hours=-i)
            val = target_df[target_df['Date Time'] == t][feat].values[0]
            try:
                val = int(val)
            except:
                val = 0
            data.append(val)
    for feat in ['PM2.5','O3','CH4','CO','NMHC','NO','NO2','NOx','PM10','SO2','THC']:
        for hour_avg in [3,6,12,24]:
            summ = 0
            ctr = 0
            for i in range(hour_avg):
                t = target_time + timedelta(hours=-i-1)
                val = target_df[target_df['Date Time'] == t][feat].values[0]
                # print(val)
                try:
                    val = int(val)
                    summ += val
                    ctr += 1
                except:
                    pass
            data.append(summ / ctr)

    # 'DAY_OF_YEAR','HOUR','WEEKDAY','MONTH'
    day_of_year = target_time.timetuple().tm_yday - 1
    weekday = target_time.weekday()
    month = target_time.month


    os_data = []
    for ost in other_stations:
        feat = 'PM2.5'
        val = other_dfs[ost][other_dfs[ost]['Date Time'] == t][feat].values[0]
        os_data.append(val)
        for hour_avg in [3,6,12,24]:
            summ = 0
            ctr = 0
            for i in range(hour_avg):
                t = target_time + timedelta(hours=-i-1)
                val = other_dfs[ost][other_dfs[ost]['Date Time'] == t][feat].values[0]
                try:
                    val = int(val)
                    summ += val
                    ctr += 1
                except:
                    pass
            os_data.append(summ / ctr)


    if args.v != 'AQI':
        predict_model_folder = './EPA_Station_PredictModel_' + args.v
        predict_model_name = args.s + '_model_nearby_24hour_20200708.pickle'

        for hour in range(1, 14):
            with open('/'.join([predict_model_folder, str(hour), predict_model_name]), 'rb') as model:
                reg = pickle.load(model)
                pred = reg.predict([data + [day_of_year, hour, weekday, month] + os_data])[0]

            print('T' + str(hour) + ' ' + args.v + ' predict: ' + str(pred))
    else:
        o3_begin_mask = target_df['Date Time'].map(lambda x: x) <= target_time
        o3_end_mask = target_df['Date Time'].map(lambda x: x) >= target_time + timedelta(hours=-7)
        o3_8hr = list(target_df[o3_begin_mask & o3_end_mask]['O3'])
        # print(o3_8hr)
        for hour in range(1, 14):
            polluts = {}
            for v in ['PM2.5', 'PM10', 'NO2', 'O3']:
                predict_model_folder = './EPA_Station_PredictModel_' + v
                predict_model_name = args.s + '_model_nearby_24hour_20200708.pickle'

                with open('/'.join([predict_model_folder, str(hour), predict_model_name]), 'rb') as model:
                    reg = pickle.load(model)
                    pred = reg.predict([data + [day_of_year, hour, weekday, month] + os_data])

                polluts[v] = pred[0]
            o3_8hr = o3_8hr[1:] + [polluts['O3']]
            polluts['O3_8H'] = sum(o3_8hr) / len(o3_8hr)

            myaqi = aqi.to_aqi([
                (aqi.POLLUTANT_PM25, polluts['PM2.5']),
                (aqi.POLLUTANT_PM10, polluts['PM10']),
                (aqi.POLLUTANT_O3_8H, polluts['O3_8H'] / 1000),
                (aqi.POLLUTANT_NO2_1H, polluts['NO2'])
            ])

            print('T' + str(hour) + ' AQI predict: ' + str(myaqi))





if __name__ == '__main__':
    cfg = read_config()
    main(cfg)
