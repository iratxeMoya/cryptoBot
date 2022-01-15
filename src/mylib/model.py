import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras.layers import Dropout, Activation, Dense, GRU
from sklearn.preprocessing import MinMaxScaler

def generateModel(shape1:int, shape2:int, DROPOUT:float = 0.2) -> keras.Sequential:
    
    model = keras.Sequential()
    model.add(GRU(units=50, input_shape=(shape1, shape2),return_sequences=False))
    model.add(Activation('tanh'))
    model.add(Dropout(DROPOUT))
    model.add(Dense(1))
    model.add(Activation('relu'))
    
    model.compile(
        loss='mean_squared_error',
        optimizer='adam'
    )
    
    return model

def trainModel(model:keras.Sequential, X_train:np.array, y_train:np.array, EPOCHS:int = 10, BATCH_SIZE:int = 64) -> None:
    
    model.fit(
        X_train,
        y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        shuffle=False,
        validation_split=0.1
    )
    
def predictPeriod(period:int, model:keras.Sequential, SEQ_LEN:int, prediction_list:list) -> list:
    
    prediction_list = prediction_list[-SEQ_LEN + 1:]
    
    for _ in range(period):
        x = prediction_list[-SEQ_LEN + 1:]
        x = x.reshape((1, SEQ_LEN - 1, 1))
        out = model.predict(x)[0][0]
        prediction_list = np.append(prediction_list, out)
    prediction_list = prediction_list[SEQ_LEN - 1:]
        
    return prediction_list
    
def predict_dates(period:int, dates:np.array):
    
    dates = dates.reshape(dates.shape[0])
    last_date = dates[-1]
    prediction_dates = pd.date_range(last_date, periods=period).tolist()
    prediction_dates = [timestamp.to_pydatetime().date().strftime('%Y-%m-%d %H:%M:%S') for timestamp in prediction_dates]
    
    return prediction_dates

def makePrediction(period:int, model:keras.Sequential, SEQ_LEN:int, prediction_list:list, candle:dict, scaler:MinMaxScaler) -> list:
    
    newClose = np.array([[candle['c']]])
    newClose = scaler.transform(newClose)
    prediction_list = np.concatenate((prediction_list, newClose), axis = 0)
    
    predictions = predictPeriod(period, model, SEQ_LEN, prediction_list).tolist()
    
    return predictions, prediction_list
    
    
    
    