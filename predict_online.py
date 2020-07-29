import os
import pickle
import argparse
import pandas as pd
from datetime import datetime, timedelta
from utils import *
import warnings
import requests
import aqi
import math
from pprint import pprint
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

# def datetime_transform(date_str):
#     if date_str[11:13] != '24':
#         return pd.to_datetime(date_str, format='%Y-%m-%d %H:%M:%S')

#     date_str = date_str[:11] + '00' + date_str[13:]
#     return pd.to_datetime(date_str, format='%Y-%m-%d %H:%M:%S') + timedelta(days=1)


def read_station_date_df(station):
    global target_date, target_date_prev_1, target_date_prev_2, target_date_next

    if 'table:國家標準站_每日_小時值,day:' + target_date + '.parquet' not in os.listdir('./tmp'):
        url = 'gs://cameo_aqi/data/table:國家標準站_每日_小時值/table:國家標準站_每日_小時值,day:' + target_date + '.parquet'
        os.system('gsutil cp ' + url + ' ./tmp')
    if 'table:國家標準站_每日_小時值,day:' + target_date_prev_1 + '.parquet' not in os.listdir('./tmp'):
        url = 'gs://cameo_aqi/data/table:國家標準站_每日_小時值/table:國家標準站_每日_小時值,day:' + target_date_prev_1 + '.parquet'
        os.system('gsutil cp ' + url + ' ./tmp')
    if 'table:國家標準站_每日_小時值,day:' + target_date_prev_2 + '.parquet' not in os.listdir('./tmp'):
        url = 'gs://cameo_aqi/data/table:國家標準站_每日_小時值/table:國家標準站_每日_小時值,day:' + target_date_prev_2 + '.parquet'
        os.system('gsutil cp ' + url + ' ./tmp')
    if target_date_next is not None:
        if 'table:國家標準站_每日_小時值,day:' + target_date_next + '.parquet' not in os.listdir('./tmp'):
            url = 'gs://cameo_aqi/data/table:國家標準站_每日_小時值/table:國家標準站_每日_小時值,day:' + target_date_next + '.parquet'
            os.system('gsutil cp ' + url + ' ./tmp')

    target_df = pd.read_parquet('./tmp/table:國家標準站_每日_小時值,day:' + target_date + '.parquet')
    target_df_prev_1 = pd.read_parquet('./tmp/table:國家標準站_每日_小時值,day:' + target_date_prev_1 + '.parquet')
    target_df_prev_2 = pd.read_parquet('./tmp/table:國家標準站_每日_小時值,day:' + target_date_prev_2 + '.parquet')
    if target_date_next is not None:
        target_df_next = pd.read_parquet('./tmp/table:國家標準站_每日_小時值,day:' + target_date_next + '.parquet')

    df = pd.concat([target_df_prev_2, target_df_prev_1, target_df, target_df_next]) if target_date_next else pd.concat([target_df_prev_2, target_df_prev_1, target_df])
    deviceId = get_devideId_by_station(station)
    print(station, deviceId)

    return df[df['deviceId'] == deviceId]


def main(cfg):
    global station, target_date, target_date_prev_1, target_date_prev_2, target_date_next
    station = args.s
    target_time = datetime.strptime(args.t, '%Y-%m-%d %H:%M:%S')
    target_date = str(target_time.date())
    target_date_prev_1 = str((target_time + timedelta(days=-1)).date())
    target_date_prev_2 = str((target_time + timedelta(days=-2)).date())
    target_date_next = str((target_time + timedelta(days=1)).date())
    if target_time + timedelta(hours=14) > datetime.utcnow() + timedelta(hours=8):
        target_date_next = None

    other_stations = get_nearby_stations(station, cfg['nearby_km_range'])
    other_stations.extend(['富貴角站', '馬公站', '馬祖站', '金門站'])
    if station in other_stations: other_stations.remove(station)
    other_stations = sorted(list(set(other_stations)))
    print('相關測站：')
    print(', '.join(other_stations))
    print('\n============= 擷取相關測站資料中 =============\n')

    target_df = read_station_date_df(station)
    other_dfs = {}

    for o_station in other_stations:
        # print('nearby: ' + o_station)
        other_dfs[o_station] = read_station_date_df(o_station)

    data = []

    for feat in ['pm2_5', 'o3', 'ch4', 'co', 'nmhc', 'no', 'no2', 'nox', 'pm10', 'so2', 'thc']:
        for i in range(1, 37):
            t = target_time + timedelta(hours=-i)
            try:
                val = target_df[target_df['time'] == t][feat].values[0]
                val = int(val)
            except Exception:
                val = 0
            data.append(val)
    for feat in ['amb_temp', 'rainfall', 'rh', 'wd_hr', 'wind_direct', 'wind_speed', 'ws_hr']:
        for i in range(1, 13):
            t = target_time + timedelta(hours=-i)
            try:
                val = target_df[target_df['time'] == t][feat].values[0]
                val = int(val)
            except Exception:
                val = 0
            data.append(val)
    for feat in ['pm2_5', 'o3', 'ch4', 'co', 'nmhc', 'no', 'no2', 'nox', 'pm10', 'so2', 'thc']:
        for hour_avg in [3,6,12,24]:
            summ = 0
            ctr = 0
            for i in range(hour_avg):
                t = target_time + timedelta(hours=-i-1)
                try:
                    val = target_df[target_df['time'] == t][feat].values[0]
                    val = int(val)
                    summ += val
                    ctr += 1
                except Exception:
                    pass
            if ctr > 0:
                data.append(summ / ctr)
            else:
                data.append(0)

    # 'DAY_OF_YEAR','HOUR','WEEKDAY','MONTH'
    day_of_year = target_time.timetuple().tm_yday - 1
    weekday = target_time.weekday()
    month = target_time.month

    os_data = []
    for ost in other_stations:
        for feat in ['pm2_5', 'pm10', 'no2', 'o3', 'co']:
            print(ost, feat, target_time)
            val = other_dfs[ost][other_dfs[ost]['time'] == target_time][feat].values[0]
            # print(val)
            # print(type(val))
            try:
                tmp = int(other_dfs[ost][other_dfs[ost]['time'] == target_time][feat].values[0])
                if math.isnan(tmp):
                    tmp = 0
                os_data.append(tmp)
            except Exception:
                os_data.append(0)

            try:
                tmp = int(other_dfs[ost][other_dfs[ost]['time'] == target_time + timedelta(hours=-2)][feat].values[0])
                if math.isnan(tmp):
                    tmp = 0
                os_data.append(tmp)
            except Exception:
                os_data.append(0)

            try:
                tmp = int(other_dfs[ost][other_dfs[ost]['time'] == target_time + timedelta(hours=-5)][feat].values[0])
                if math.isnan(tmp):
                    tmp = 0
                os_data.append(tmp)
            except Exception:
                os_data.append(0)

            try:
                tmp = int(other_dfs[ost][other_dfs[ost]['time'] == target_time + timedelta(hours=-11)][feat].values[0])
                if math.isnan(tmp):
                    tmp = 0
                os_data.append(tmp)
            except Exception:
                os_data.append(0)

            try:
                tmp = int(other_dfs[ost][other_dfs[ost]['time'] == target_time + timedelta(hours=-23)][feat].values[0])
                if math.isnan(tmp):
                    tmp = 0
                os_data.append(tmp)
            except Exception:
                os_data.append(0)

            for hour_avg in [3,6,12,24]:
                summ = 0
                ctr = 0.01
                for i in range(hour_avg):
                    t = target_time + timedelta(hours=-i-1)
                    try:
                        val = other_dfs[ost][other_dfs[ost]['time'] == t][feat].values[0]
                        val = int(val)
                        summ += val
                        ctr += 1
                    except Exception as e:
                        pass
                if ctr > 0:
                    os_data.append(summ / ctr)
                else:
                    os_data.append(0)

    # print(data + [day_of_year, 1, weekday, month] + os_data)
    print('\n================= 進行預測 =================\n')
    print('target_time: ' + str(target_time) + '\n')

    if args.v != 'AQI':
        predict_model_folder = './EPA_Station_PredictModel_' + args.v
        predict_model_name = station + '_model_nearby_80km_24hour_20200718.pickle'

        preds = []
        for hour in range(1, 14):
            with open('/'.join([predict_model_folder, str(hour), predict_model_name]), 'rb') as model:
                reg = pickle.load(model)
                t = target_time + timedelta(hours=hour)
                predict_point = data + [t.year, t.hour + 1, t.weekday(), t.month] + os_data
                # print(predict_point)
                pred = reg.predict([predict_point])[0]

                preds.append(round(pred, 2))

        print(station + ' ' + args.v + ' T1 ~ T13 預測值: ')
        print(preds)
        print()

        if target_date_next is not None:
            real_data = []

            for i in range(1, 14):
                try:
                    real_data.append(round(target_df[target_df['time'] == target_time + timedelta(hours=i)][args.v.lower().replace('.', '_')].values[0], 2))
                except:
                    real_data.append(-1)

            print(station + ' ' + args.v + ' T1 ~ T13 實際值: ')
            print(real_data)
            print()

            print(station + ' ' + args.v + ' T1 ~ T13 誤差值: ')
            print([round(a - b, 2) for a, b in zip(preds, real_data)])
    else:
        o3_begin_mask = target_df['time'].map(lambda x: x) <= target_time
        o3_end_mask = target_df['time'].map(lambda x: x) >= target_time + timedelta(hours=-7)
        o3_8hr = list(target_df[o3_begin_mask & o3_end_mask]['o3'])
        # print(o3_8hr)
        myaqis = []
        for hour in range(1, 14):
            polluts = {}
            for v in ['PM2.5', 'PM10', 'NO2', 'O3']:
                predict_model_folder = './EPA_Station_PredictModel_' + v
                predict_model_name = station + '_model_nearby_80km_24hour_20200718.pickle'

                with open('/'.join([predict_model_folder, str(hour), predict_model_name]), 'rb') as model:
                    reg = pickle.load(model)
                    t = target_time + timedelta(hours=hour)
                    predict_point = data + [t.year, t.hour + 1, t.weekday(), t.month] + os_data
                    pred = reg.predict([predict_point])

                polluts[v] = pred[0]
            o3_8hr = o3_8hr[1:] + [polluts['O3']]
            polluts['O3_8H'] = sum(o3_8hr) / len(o3_8hr)

            myaqi = aqi.to_aqi([
                (aqi.POLLUTANT_PM25, polluts['PM2.5']),
                (aqi.POLLUTANT_PM10, polluts['PM10']),
                (aqi.POLLUTANT_O3_8H, polluts['O3_8H'] / 1000),
                (aqi.POLLUTANT_NO2_1H, polluts['NO2'])
            ])

            myaqis.append(float(myaqi))

        print(station + ' AQI T1 ~ T13 預測值: ')
        pprint(myaqis)
        print()

        if target_date_next is not None:
            real_data = []

            for i in range(1, 14):
                try:
                    real_data.append(target_df[target_df['time'] == target_time + timedelta(hours=i)]['aqi'].values[0])
                except:
                    real_data.append(-1)

            print(station + ' AQI T1 ~ T13 實際值: ')
            pprint(real_data)
            print()

            print(station + ' AQI T1 ~ T13 誤差值: ')
            pprint([a - b for a, b in zip(myaqis, real_data)])

    # files = os.listdir('./tmp')
    # for f in files:
    #     if '.parquet' in f:
    #         os.remove('./tmp/' + f)



if __name__ == '__main__':
    cfg = read_config()
    main(cfg)
