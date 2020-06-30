## 資料前處理檔案列表
> 1. airtw_xls_to_csv.py: 將 AirTW 資料由 raw xls 轉為 raw csv，放置於原資料夾內
> 2. move_csv_to_area.py: 將轉好的 csv 檔案，移至對應 North/Central/South 的資料夾內
> 3. LSTM_data_preprocess.py: 將 raw csv 檔轉為 lstm 可吃的 csv 檔案格式 (時間序列)
> 4. GBDT_data_preprocess.py: 將 lstm csv 檔轉為 gbdt 可吃的 csv 檔案格式 (多個feature)

**使用說明**

### 1. airtw_xls_to_csv.py

```
python3 airtw_xls_to_csv.py
```
- 注意，airtw_xls_to_csv.py 需與 data 資料夾在同個資料夾內，並將 airtw 資料夾放在 data 資料夾內

### 2. move_csv_to_area.py

```
python3 move_csv_to_area.py
```
- move_csv_to_area.py 需與 data 資料夾在同個資料夾內，並且以執行完成步驟 1.

### 3. LSTM_data_preprocess.py

```
python3 LSTM_data_preprocess.py -y 104,105,106,107  # 將 2015~2018 壓成一包 lstm 資料 (訓練集)
python3 LSTM_data_preprocess.py -y 108  # 將 2019 獨立壓成一包 lstm 資料 (測試集)
```
- LSTM_data_preprocess.py 需與 data 資料夾在同個資料夾內，並且以執行完成步驟 1. 2.
- -y 為年份參數，用逗號分隔，同一個指令執行的年份會被壓在一起製成一份 lstm csv 檔案

### 4. GBDT_data_preprocess.py

```
python3 GBDT_add_nearby_data.py -s '中山站  汐止站  湖口站  苗栗站  萬華站  觀音站  頭份站' -pos North
```
- GBDT_add_nearby_data.py 需與 data 資料夾在同個資料夾內，並且以執行完成步驟 1. 2. 3.
- -s 為測站參數，用兩個空格分隔，同一個指令執行的測站會獨立被製成各自的 gbdt 訓練集
- -pos 為地區參數，可接受 North, South, Central，與 -s 測站必須相符