import websocket, json, sys, configparser
import pandas as pd
from .lib.model import generateModel, trainModel
from binance.enums import *
from binance import Client
from lib.data import *
from lib.model import *
from lib.log import logger
from lib.technicalAnalisys import *
from lib.classes import ActionEncoder

config = configparser.ConfigParser()
config.read('config.ini')

RSI_PERIOD = 14
DIM_PERIOD = 14                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
RSI_OVERBOUGHT = int(config['CONSTRAINTS']['RSI_OVERBOUGHT'])
RSI_OVERSOLD = int(config['CONSTRAINTS']['RSI_OVERSOLD'])

closes = []
highs = []
lows = []
buying = []
selling = []

indicators = int(config['CONSTRAINTS']['indicators'])
SEQ_LEN = 200
useSaved = bool(config['DATA']['useSaved'])
distance = 6 # Period of predictions based on PERIOD. If PERIOD is 4h, then distance = 6 means 24h

PAIR1 = 'near'
PAIR2 = 'usdt'
PERIOD = '5m'
API_KEY = config['BINANCE']['API_KEY']
SECRET_KEY = config['BINANCE']['SECRET_KEY']
SOCKET = "wss://stream.binance.com:9443/ws/{}{}@kline_{}".format(PAIR1, PAIR2, PERIOD)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               

model = None  
actions = []
saveActions = 'src/data/actions.json' 

#! DESPUES DE TESTEAR QUE EL BOT FUNCIONA CORRECTAMENTE:
# TODO: Eliminar toda variable dependiente al cliente
# TODO: Calcular SEQ_LEN en funcion de la cantidad de datos
# TODO: Eliminar el run de ws
    
def on_open(ws, connection):
    
    print('opened connection')
    connection['client'].send_message(json.dumps({'type': 'connection', 'message': 'Connection opened'}))
    
    client = Client(connection['API_KEY'], connection['SECRET_KEY'])
    
    crypto = client.get_all_tickers()
    crypto_df = pd.DataFrame(crypto)
    crypto_df.set_index('symbol', inplace=True)

    if PAIR1.upper() + PAIR2.upper() not in crypto_df.index:
        logger.error('Pair {}{} not listed in Binance'.format(PAIR1.upper(), PAIR2.upper()))
        sys.exit()

    logger.info('Fetching historical data for {}{}\n'.format(PAIR1.upper(), PAIR2.upper()))  
    hist_df = getData(PAIR1, PAIR2, PERIOD, client, useSaved)
    hist_df = hist_df if len(hist_df) < 5000 else hist_df[-5000:] # Get las 5000 data
    
    logger.info('Preprocessing data')
    X_train, y_train, X_test, y_test, connection['dates'], connection['scaler'] = preprocessData(hist_df, SEQ_LEN)
    
    logger.info('Preparing some data for inference')
    datas = np.concatenate((y_train, y_test), axis=0)

    logger.info("GRU model generation")
    connection['model'] = generateModel(X_train.shape[1], X_train.shape[2])
    
    logger.info('Training model')
    history = trainModel(connection['model'], X_train, y_train)
    connection['client'].send_message(json.dumps({'type': 'debug', 'message': 'model trained'}))

def on_close(ws, connection):
    
    del connection['model']
    if len(actions) > 0:
        actionsEncoded = []
        for a in connection['actions']:
            actionsEncoded.append(json.dumps({'user': a.user, 'date': a.date, 'action': a.action}))
                
        connection['actions'] = json.dumps(actionsEncoded)
            
    logger.info('closed connection')
    connection['client'].send_message(json.dumps({'type': 'connection', 'message': 'connection closed'}))

def on_message(ws, message, connection):
    
    json_message = json.loads(message)
    candle = json_message['k']

    if candle['x']:
        connection['buying'] = []
        connection['selling'] = []
        
        connection['closes'], connection['highs'], connection['lows'] = addNewInfo(candle, connection['closes'], connection['highs'], connection['lows'])

        connection['selling'], connection['buying'] = checkRSI(connection['RSI_PERIOD'], connection['closes'], connection['buying'], connection['selling'], RSI_OVERBOUGHT, RSI_OVERSOLD)
        connection['selling'], connection['buying'] = checkDIM(connection['DIM_PERIOD'], connection['closes'], connection['highs'], connection['lows'], connection['buying'], connection['selling'])
          
        prediction, connection['datas'] = makePrediction(connection['distance'], connection['model'], connection['SEQ_LEN'], connection['datas'], candle, connection['scaler'])
        
        action = tradingAction(connection['buying'], connection['selling'], connection['scaler'].inverse_transform(np.array(prediction).reshape(-1, 1)).reshape(connection['distance']).tolist(), float(candle['c']))
        
        if action:
            connection['actions'].append(action)
            connection['client'].send_message(json.dumps({'type': 'action', 'message': action.action}))

