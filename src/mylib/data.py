import pandas as pd
import math
import os.path
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from dateutil import parser
from binance import Client
from mylib.log import logger
from typing import Tuple

binsizes = {"1m": 1, "5m": 5, "1h": 60, "4h": 240, "1d": 1440}

def minutes_of_new_data(symbol, kline_size, data, binance_client):
    
    if len(data) > 0:  
        old = parser.parse(data["timestamp"].iloc[-1])
    else: 
        old = datetime.strptime('1 Jan 2017', '%d %b %Y')
        
    new = pd.to_datetime(binance_client.get_klines(symbol=symbol, interval=kline_size)[-1][0], unit='ms')

    return old, new

def get_all_binance(symbol, kline_size, binance_client, save = False):
    
    filename = '%s-%s-data.csv' % (symbol, kline_size)
    
    if os.path.isfile(filename): 
        data_df = pd.read_csv(filename)
    else: 
        data_df = pd.DataFrame()
        
    oldest_point, newest_point = minutes_of_new_data(symbol, kline_size, data_df, binance_client)
    delta_min = (newest_point - oldest_point).total_seconds()/60
    available_data = math.ceil(delta_min/binsizes[kline_size])
        
    klines = binance_client.get_historical_klines(symbol, kline_size, oldest_point.strftime("%d %b %Y %H:%M:%S"), newest_point.strftime("%d %b %Y %H:%M:%S"))
    data = pd.DataFrame(klines, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    
    if len(data_df) > 0:
        temp_df = pd.DataFrame(data)
        data_df = data_df.append(temp_df)
    else: 
        data_df = data
        
    if save: 
        data_df.to_csv(filename)
        
    return data_df

def to_sequences(data, seq_len):
        d = []

        for index in range(len(data) - seq_len):
            d.append(data[index: index + seq_len])

        return np.array(d)

def preprocess(data_raw:np.array, seq_len:int, train_split:float) -> Tuple[np.array, np.array, np.array, np.array]:

    data = to_sequences(data_raw, seq_len)

    num_train = int(train_split * data.shape[0])

    X_train = data[:num_train, :-1, :]
    y_train = data[:num_train, -1, :]

    X_test = data[num_train:, :-1, :]
    y_test = data[num_train:, -1, :]

    return X_train, y_train, X_test, y_test

def getData(PAIR1:str, PAIR2:str, PERIOD:str, client:Client, useSaved:bool = False) -> pd.DataFrame:
    
    if os.path.exists('%s-%s-data.csv' % (PAIR1.upper() + PAIR2.upper(), PERIOD)) and useSaved:
        hist_df = pd.read_csv('%s-%s-data.csv' % (PAIR1.upper() + PAIR2.upper(), PERIOD))
        hist_df.drop(hist_df.columns[0], axis=1, inplace=True)
    else:
        if os.path.exists('%s-%s-data.csv' % (PAIR1.upper() + PAIR2.upper(), PERIOD)):
            os.remove('%s-%s-data.csv' % (PAIR1.upper() + PAIR2.upper(), PERIOD))
        historical = get_all_binance(PAIR1.upper() + PAIR2.upper(), PERIOD, client, True)
        hist_df = pd.DataFrame(historical)

    return hist_df

def preprocessData(hist_df:pd.DataFrame, SEQ_LEN:int = 100) -> Tuple[np.array, np.array, np.array, np.array, np.array]:
    
    hist_df.columns = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 'Number of Trades', 'TB Base Volume', 'TB Quote Volume', 'Ignore']

    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote Asset Volume', 'TB Base Volume', 'TB Quote Volume']
    hist_df[numeric_columns] = hist_df[numeric_columns].apply(pd.to_numeric, axis=1)

    hist_df.sort_values('Open Time')

    scaler = MinMaxScaler()

    dates = hist_df['Open Time'].values.reshape(-1, 1)
    close_price = hist_df.Close.values.reshape(-1, 1)
    scaled_close = scaler.fit_transform(close_price)
    scaled_close = scaled_close[~np.isnan(scaled_close)]
    scaled_close = scaled_close.reshape(-1, 1)

    X_train, y_train, X_test, y_test = preprocess(scaled_close, SEQ_LEN, train_split = 0.95)
    
    return X_train, y_train, X_test, y_test, dates, scaler