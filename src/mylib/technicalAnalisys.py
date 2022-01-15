import numpy as np
import talib, json
from tensorflow import keras
from .log import logger
from .classes import Action
from typing import Tuple

def computeDIM(closes:list, highs:list, lows:list):
    
    np_closes = np.array(closes)
    np_highs = np.array(highs)
    np_lows = np.array(lows)
    
    dim = {}
    dim['di+'] = talib.PLUS_DI(np_highs, np_lows, np_closes, timeperiod = 14)
    dim['di-'] = talib.MINUS_DI(np_highs, np_lows, np_closes, timeperiod = 14)
    return dim

def checkRSI(RSI_PERIOD:int, closes:list, buying:list, selling:list, RSI_OVERBOUGHT:int, RSI_OVERSOLD:int) -> Tuple[list, list]:
    
    if len(closes) > RSI_PERIOD:
        np_closes = np.array(closes)
        rsi = talib.RSI(np_closes, RSI_PERIOD)
        last_rsi = rsi[-1]

        if last_rsi > RSI_OVERBOUGHT:
            selling.append(True)
            logger.warning('RSI selling achived')
        
        if last_rsi < RSI_OVERSOLD:
            buying.append(True)
            logger.warning('RSI buying achived')
            
    return selling, buying

def checkDIM(DIM_PERIOD:int, closes:list, highs:list, lows:list, buying:list, selling:list) -> Tuple[list, list]:
    
    if len(closes) > DIM_PERIOD:
        dim = computeDIM(closes, highs, lows)
        
        if dim['di+'] - dim['di-'] > 0:
            buying.append(True)
            logger.warning('DIM buying achived')
        
        elif dim['di+'] - dim['di-'] < 0:
            selling.append(True)
            logger.warning('DIM selling achived')
    
    return selling, buying

def addNewInfo(candle:dict, closes:list, highs:list, lows:list) -> Tuple[list, list, list]:
    
    closes.append(float(candle['c']))
    highs.append(float(candle['h']))
    lows.append(float(candle['l']))
    
    return closes, highs, lows

def tradingAction(buying:list, selling:list, prediction:list, actualPrice:float, indicators:int = 2):
    
    action = None
    
    if prediction[-1] > actualPrice:
        if sum(buying) > 0 and sum(buying) > sum(selling) and indicators - sum(buying) < indicators / 2:
            logger.warning('BUY')
            action = Action('Buy')
    else:
        if sum(selling) > 0 and sum(buying) < sum(selling) and indicators - sum(selling) < indicators / 2:
            logger.warning('SELL')
            action = Action('Sell')
    
    return action