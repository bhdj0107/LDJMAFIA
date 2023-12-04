import json
import numpy as np
from abc import *
import mafiaRequest as mRequest
class abcResponse(metaclass=ABCMeta):
    def __init__(self):
        self.nonce = -1
        self.code = -1
        self.desc = ""

    @abstractmethod
    def dict(self):
        pass

class AuthResponse(abcResponse):
    def __init__(self, code, desc, nickname, fromReq: mRequest.RegisterRequest | mRequest.LoginRequest):
        self.resid = 1
        self.code = code
        self.desc = desc
        self.id = fromReq.id
        self.addr = fromReq.addr
        self.nickname = nickname
        self.nonce = fromReq.nonce
    
    def dict(self):
        return self.__dict__


class RoomResponse(abcResponse):
    def __init__(self, code, desc, roomid, fromReq: mRequest.CreateRoomRequest | mRequest.JoinRoomRequest):
        self.resid = 2
        self.code = code
        self.desc = desc
        if type(fromReq) == mRequest.CreateRoomRequest:
            self.roomid = roomid
        else:
            self.roomid = fromReq.roomid
        self.id = fromReq.id
        self.nonce = fromReq.nonce

    def dict(self):
        return self.__dict__
    
class NoticeResponse(abcResponse):
    def __init__(self, code, desc, id, roomid, noticetype, data, req: mRequest.abcRequest):
        self.resid = 3
        self.code = code
        self.desc = desc
        self.id = id
        self.noticetype = noticetype
        self.data = data
        self.roomid = roomid
        self.nonce = req.nonce
    def dict(self):
        return self.__dict__

class ChatResponse(abcResponse):
    def __init__(self, id, roomid, chat, targetIds, messageType):
        self.resid = 4
        self.id = id
        self.roomid = id
        self.chat = chat
        self.targetIds = targetIds
        self.messageType = messageType
        self.nonce = mRequest.createNonce()
    def dict(self):
        return self.__dict__

class CheckAlivenessResponse(abcResponse):
    def __init__(self):
        self.resid = 5
        self.nonce = mRequest.createNonce()
    def dict(self):
        return self.__dict__

class CloseRoomResponse(abcResponse):
    def __init__(self, roomid):
        self.resid = 6
        self.roomid = roomid
        self.nonce = mRequest.createNonce()
    def dict(self):
        return self.__dict__


def fromdict(res: dict) -> abcResponse:
    resid = res['resid']
    if resid == 1:
        a = AuthResponse("", "", "", mRequest.LoginRequest("", ""))

    elif resid == 2:
        a = RoomResponse(0, "", 0, mRequest.JoinRoomRequest("", ""))

    elif resid == 3:
        a = NoticeResponse(0, "", 0, "", "", "", mRequest.NullRequest())

    elif resid == 4:
        a = ChatResponse("", "", "", [], "")

    elif resid == 5:
        a = CheckAlivenessResponse()

    elif resid == 6:
        a = CloseRoomResponse("")

    for reskey in res.keys():
        exec(f'a.{reskey} = res["{reskey}"]')
    return a