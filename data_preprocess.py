import csv
from time import sleep

years = ['2018', '2019', '2020']
subfolder_prefix = 'aqx_p_13_'
months = 12
days = 31

cols = ['SiteId', 'SiteName', 'ItemId', 'ItemName', 'ItemEngName', 'ItemUnit', 'MonitorDate', \
            'MonitorValue00', 'MonitorValue01', 'MonitorValue02', 'MonitorValue03', 'MonitorValue04', 'MonitorValue05', \
            'MonitorValue06', 'MonitorValue07', 'MonitorValue08', 'MonitorValue09', 'MonitorValue10', 'MonitorValue11', \
            'MonitorValue12', 'MonitorValue13', 'MonitorValue14', 'MonitorValue15', 'MonitorValue16', 'MonitorValue17', \
            'MonitorValue18', 'MonitorValue19', 'MonitorValue20', 'MonitorValue21', 'MonitorValue22', 'MonitorValue23']

features = ['','O3','RAINFALL','WD_HR','NO','AMB_TEMP','WIND_SPEED','THC','NO2','RH','WS_HR','CH4','NMHC','WIND_DIREC','PM2.5','PM10','CO','NOx','SO2']

def gen_day_empty(date_str):
    return {i: [date_str + ' ' + format(i, '02d') + ':00:00'] + [0 for xx in range(len(features)-1)] for i in range(1, 25)}

output = open("lstm_data.csv", "w")
wr = csv.writer(output)
wr.writerow(['Date Time','O3','RAINFALL','WD_HR','NO','AMB_TEMP','WIND_SPEED','THC','NO2','RH','WS_HR','CH4','NMHC','WIND_DIREC','PM2.5','PM10','CO','NOx','SO2'])

day_counter = 0
for year in years:
    for mon in range(1, months + 1):
        mon = '0' + str(mon) if mon < 10 else str(mon)
        for day in range(1, days + 1):
            day = '0' + str(day) if day < 10 else str(day)
            d = gen_day_empty(day + '.' + mon + '.' + year)
            try:
                file_path = 'data/' + year + '/' + subfolder_prefix + year + '-' + mon + '/' + subfolder_prefix + year + '-' + mon + '-' + day + '.csv'
                with open(file_path, newline='') as f:
                    # print(file_path)
                    rows = csv.reader(f)
                    for row in rows:
                        if row[1] == '中山':
                            feature_ind = features.index(row[4])
                            for hour in range(1, 25):
                                try:
                                    d[hour][feature_ind] = float(row[6+hour]) if row[6+hour] not in {'x', ''} else 0
                                except Exception as e:
                                    print(row[6+hour])
                                    print(repr(e))
                for hr in range(1, 25):
                    wr.writerow(d[hr])
            except Exception as e:
                # print(repr(e))
                pass

output.close()

# print(features)