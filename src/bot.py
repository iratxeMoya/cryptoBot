import websocket, json, sys, configparser
import pandas as pd
from lib.model import generateModel, trainModel
from binance.enums import *
from binance import Client
from lib.data import *
from lib.model import *
from lib.log import logger
from lib.technicalAnalisys import *

config = configparser.ConfigParser()

RSI_PERIOD = 14
DIM_PERIOD = 14                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
RSI_OVERBOUGHT = config['CONSTRAINTS']['RSI_OVERBOUGHT']
RSI_OVERSOLD = config['CONSTRAINTS']['RSI_OVERSOLD']

closes = []
highs = []
lows = []
buying = []
selling = []

indicators = config['CONSTRAINTS']['indicators']
SEQ_LEN = 100
useSaved = config['DATA']['useSaved']
distance = 6 # Period of predictions based on PERIOD. If PERIOD is 4h, then distance = 6 means 24h

PAIR1 = 'near'
PAIR2 = 'usdt'
PERIOD = '4h'
API_KEY = config['BINANCE']['API_KEY']
SECRET_KEY = config['BINANCE']['SECRET_KEY']
SOCKET = "wss://stream.binance.com:9443/ws/{}{}@kline_{}".format(PAIR1, PAIR2, PERIOD)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               

model = None  
actions = []
saveActions = 'data/actions.json' 

#! DESPUES DE TESTEAR QUE EL BOT FUNCIONA CORRECTAMENTE:
# TODO: Eliminar toda variable dependiente al cliente
# TODO: Calcular SEQ_LEN en funcion de la cantidad de datos
# TODO: Eliminar el run de ws
    
def on_open(ws):
    
    global model, dates, datas, SEQ_LEN, scaler
    print('opened connection')
    
    client = Client(API_KEY, SECRET_KEY)
    
    crypto = client.get_all_tickers()
    crypto_df = pd.DataFrame(crypto)
    crypto_df.set_index('symbol', inplace=True)

    if PAIR1.upper() + PAIR2.upper() not in crypto_df.index:
        logger.error('Pair {}{} not listed in Binance'.format(PAIR1.upper(), PAIR2.upper()))
        sys.exit()

    logger.info('Fetching historical data for {}{}\n'.format(PAIR1.upper(), PAIR2.upper()))  
    hist_df = getData(PAIR1, PAIR2, PERIOD, client, useSaved)
    
    logger.info('Preprocessing data')
    X_train, y_train, X_test, y_test, dates, scaler = preprocessData(hist_df, SEQ_LEN)
    
    logger.info('Preparing some data for inference')
    datas = np.concatenate((y_train, y_test), axis=0)

    logger.info("GRU model generation")
    model = generateModel(X_train.shape[1], X_train.shape[2])
    
    logger.info('Training model')
    history = trainModel(model, X_train, y_train)

def on_close(ws):
    global model, actions
    
    del model
    if saveActions is not None and len(actions) > 0:
        with open(saveActions, 'w') as f:
            json.dump([ob.__dict__ for ob in actions], f)
            
    logger.info('closed connection')

def on_message(ws, message):
    global closes, highs, lows, buying, selling, model, datas, scaler
    
    json_message = json.loads(message)
    candle = json_message['k']

    if candle['x']:
        buying = []
        selling = []
        
        closes, highs, lows = addNewInfo(candle, closes, highs, lows)

        selling, buying = checkRSI(RSI_PERIOD, closes, buying, selling)
        selling, buying = checkDIM(DIM_PERIOD, closes, highs, lows, buying, selling)
          
        prediction = makePrediction(distance, model, SEQ_LEN, datas, candle, scaler)
        
        action = tradingAction(buying, selling, prediction, candle['c'])
        
        if action:
            actions.append(action)

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
# ws.close() for stopping connection
"""[Sending arguments to callbacks]

from functools import partial
ws = websock.WebSocketApp(uri, on_message=partial(on_message, someList=ref_to_Obj))

"""