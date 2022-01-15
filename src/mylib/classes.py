import getpass, json
from json import JSONEncoder
from datetime import datetime

class Action:
    def __init__(self, action:str):
        self.action = action
        self.date = datetime.today().strftime('%d %b %Y, %H:%M')
        self.user = getpass.getuser()
        
        
# subclass JSONEncoder
class ActionEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__