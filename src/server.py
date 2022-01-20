from simple_websocket_server import WebSocketServer, WebSocket
import websocket
from functools import partial
import json, os
import threading
from binanceConnection import *

connections = []

HOST = ''
PORT = int(os.environ["PORT"])

def runForever(connection, SOCKET):
    connection['ws'] = websocket.WebSocketApp(SOCKET, 
                        on_open=partial(on_open, connection=connection),
                        on_close=partial(on_close, connection = connection),
                        on_message=partial(on_message, connection = connection))
            
    connection['ws'].run_forever()

class CryptoBot(WebSocket):
    def handle(self):

        print(self.address, self.opcode, self.data, self.request, 'Message recived')
        message = json.loads(self.data)
        
        if message['action'] == 'createConection':
            
            if next((d for d in connections if d["client"] == self), None):
                self.send_message(json.dumps({'type': 'connection', 'message': 'Connection reopened'}))
            else:
                connection = message['content']
                connection['client'] = self
                connection['closes'], connection['highs'], connection['lows'], connection['buying'], connection['selling'], connection['actions'] = [], [], [], [], [], []
                connection['model'], connection['scaller'], connection['datas'], connection['SEQ_LEN'], connection['dates'] = None, None, None, None, None
                
                SOCKET = "wss://stream.binance.com:9443/ws/{}{}@kline_{}".format(connection['PAIR1'], connection['PAIR2'], connection['PERIOD'])
                th = threading.Thread(target=partial(runForever, connection = connection, SOCKET = SOCKET))
                th.start()
        
        if message['action'] == 'stopConnection':
            i = next((index for (index, d) in enumerate(connections) if d["client"] == self), None)
            connections.pop(i)
            connection['ws'].close()
        

    def connected(self):
        print(self.address, 'connected')
        

    def handle_close(self):
        print(self.address, 'disconnected')
        

print('conected')
server = WebSocketServer(HOST, PORT, CryptoBot)
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