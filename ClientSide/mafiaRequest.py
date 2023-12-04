import json
import numpy as np
from abc import *

def createNonce():
    return int(np.random.randint(1000000000, 9999999999, dtype=np.int64))

class abcRequest(metaclass=ABCMeta):
    def __init__(self):
        self.nonce = -1
    
    @abstractmethod
    def dict(self):
        pass

class NullRequest(abcRequest):
    def __init__(self):
        self.id = ""
        self.nonce = -1
    
    def dict(self):
        return self.__dict__
    
class RegisterRequest(abcRequest):
    def __init__(self, id, pw):
        self.reqid = 1
        self.id = id
        self.pw = pw
        self.addr = ()
        self.nonce = createNonce()

    def dict(self):
        return self.__dict__

class LoginRequest(abcRequest):
    def __init__(self, id, pw):
        self.reqid = 2
        self.id = id
        self.pw = pw
        self.addr = ()
        self.nonce = createNonce()

    def dict(self):
        return self.__dict__

class CreateRoomRequest(abcRequest):
    def __init__(self, id):
        self.reqid = 3
        self.id = id
        self.nonce = createNonce()
    
    def dict(self):
        return self.__dict__
        
class JoinRoomRequest(abcRequest):
    def __init__(self, id, roomid):
        self.reqid = 4
        self.id = id
        self.roomid = roomid
        self.nonce = createNonce()
    
    def dict(self):
        return self.__dict__

class ChatRequest(abcRequest):
    def __init__(self, id, chat):
        self.reqid = 5
        self.id = id
        self.chat = chat
        self.nonce = createNonce()
    
    def dict(self):
        return self.__dict__
    
class AbilityTargetRequest(abcRequest):
    def __init__(self, id, targetid):
        self.reqid = 6
        self.id = id
        self.targetid = targetid
        self.nonce = createNonce()
    
    def dict(self):
        return self.__dict__
    
class ConnectionLostRequest(abcRequest):
    def __init__(self, addr):
        self.reqid = 7
        self.addr = addr
        self.nonce = createNonce()
    
    def dict(self):
        return self.__dict__
    
class ExitRoomRequest(abcRequest):
    def __init__(self, id):
        self.reqid = 8
        self.id = id
        self.nonce = createNonce()
    
    def dict(self):
        return self.__dict__
    
class CloseRoomRequest(abcRequest):
    def __init__(self, roomid):
        self.reqid = 9
        self.roomid = roomid
        self.nonce = createNonce()
    
    def dict(self):
        return self.__dict__
    
class GameStartRequest(abcRequest):
    def __init__(self, roomid, id):
        self.reqid = 10
        self.roomid = roomid
        self.id = id
        self.nonce = createNonce()
    
    def dict(self):
        return self.__dict__

def fromdict(req: dict) -> abcRequest: 
    reqid = req['reqid']

    if reqid == 1:
        a = RegisterRequest("", "")
    
    elif reqid == 2:
        a = LoginRequest("", "")
    
    elif reqid == 3:
        a = CreateRoomRequest("")
    
    elif reqid == 4:
        a = JoinRoomRequest("", 0)
    
    elif reqid == 5:
        a = ChatRequest("", "")
    
    elif reqid == 6:
        a = AbilityTargetRequest("", "")
        
    elif reqid == 7:
        a = ConnectionLostRequest("")
        
    elif reqid == 8:
        a = ExitRoomRequest("")
    
    elif reqid == 9:
        a = CloseRoomRequest("")
    
    elif reqid == 10:
        a = GameStartRequest("", "")

    for key in a.dict().keys():
        exec(f'a.{key} = req["{key}"]')
    return a