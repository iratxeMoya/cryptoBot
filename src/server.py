from simple_websocket_server import WebSocketServer, WebSocket
import websocket
from functools import partial
import json
from .bot import *

clients = []
connections = []

class CryptoBot(WebSocket):
    def handle(self):

        print(self.address, self.opcode, self.data, self.request, 'Message recived')
        message = json.loads(self.data)
        
        if message['action'] == 'createConection':
            
            connection = message['content']
            connection['client'] = self
            connection['closes'], connection['highs'], connection['lows'], connection['buying'], connection['selling'] = [], [], [], [], []
            connection['model'], connection['scaller'], connection['datas'], connection['SEQ_LEN'] = None, None, None, None
            
            SOCKET = "wss://stream.binance.com:9443/ws/{}{}@kline_{}".format(connection['PAIR1'], connection['PAIR2'], connection['PERIOD'])
            connection['ws'] = websocket.WebSocketApp(SOCKET, 
                                                      on_open=partial(on_open, connection=connection),
                                                      on_close=partial(on_close, connection = connection),
                                                      on_message=partial(on_message, connection = connection))
            
            connection['ws'].run_forever()
        
        if message['action'] == 'stopConnection':
            connection = next((d for d in connections if d["client"] == self), None)
            connection['ws'].close()
        

    def connected(self):
        print(self.address, 'connected')
        clients.append(self)
        

    def handle_close(self):
        print(self.address, 'disconnected')


server = WebSocketServer('', 8000, CryptoBot)
server.serve_forever()

"""[Client side]
+ Connect
+ Send message (EN STRING!): 
    ++ {'action': 'createConnection','content': 
        {'PAIR1', 'PAIR2', 'PERIOD', 'API_KEY', 'SECRET_KEY', 'distance', 'RSI_PERIOD', 'DIM_PERIOD'}}
+ Listen
+ Send message (EN STRING!):
    ++ {'action': 'stopConnection'} -> Disconnect
"""