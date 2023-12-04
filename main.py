from multiprocessing import Manager, Queue
from socketHandler import serverSocketHandler
from mafiaProtocol import mRequest, mResponse
from mafiaManagers import *
from setproctitle import *


class LDJMafiaServer:
    def __init__(self, host, port, cert, key):
        self.id2addr = {}
        tTitle = getproctitle()
        setproctitle("LDJMAFIA-viaProcess-Resource-Manager")
        self.resourceM = Manager()
        setproctitle(tTitle)

        self.socketHandler = serverSocketHandler(host, port, cert, key, self.resourceM)
        self.authManager = AuthenticateManager('./logintable')

        self.lobbyManager = LobbyManager()
        self.mainResponseQueue = Queue()

        self.authManager.responseQueue = self.mainResponseQueue
        self.lobbyManager.responseQueue = self.mainResponseQueue

    def start(self):
        self.socketHandler.start()
        self.authManager.start()
        self.lobbyManager.start()

        while True:
            if not self.socketHandler.recvs.empty():
                addr, req = self.socketHandler.recvs.get()
                req = mRequest.fromdict(req)
                print(req, req.dict())
                if type(req) == mRequest.RegisterRequest:
                    req.addr = addr
                    self.authManager.requestQueue.put(req)

                if type(req) == mRequest.LoginRequest:
                    if not self.id2addr.get(req.id):
                        req.addr = addr
                        self.authManager.requestQueue.put(req)
                    else:
                        res = mResponse.AuthResponse(401, 'Already Logged in User', req.id, req)
                        res.addr = addr
                        self.socketHandler.send(res.addr, res.dict())

                elif type(req) in (mRequest.CreateRoomRequest, mRequest.JoinRoomRequest, mRequest.ChatRequest, mRequest.GameStartRequest, mRequest.AbilityTargetRequest):
                    self.id2addr[req.id] = addr
                    self.id2addr[addr] = req.id
                    self.lobbyManager.requestQueue.put(req)
                
                elif type(req) == mRequest.ConnectionLostRequest:
                    try:
                        del_id = self.id2addr[req.addr]
                        del self.id2addr[req.addr]
                        del self.id2addr[del_id]
                        exitReq = mRequest.ExitRoomRequest(del_id)
                        self.lobbyManager.requestQueue.put(exitReq)
                    except KeyError: pass


            if not self.mainResponseQueue.empty():
                res = self.mainResponseQueue.get()
                print(res, res.dict())
                if type(res) == mResponse.NoticeResponse:
                    if res.noticetype == 'roominfo':
                        self.socketHandler.send(self.id2addr[res.id], res.dict())
                    elif res.noticetype in ('playerenter', 'playerexit', 'newroommaster', 'jobnotice', 'timenotice', 'playerdead', 'playerlive', 'vote', 'policetarget', 'mafiatarget', 'doctortarget', 'gameend'):
                        for playerid in res.data.keys():
                            self.socketHandler.send(self.id2addr[playerid], res.dict())
                    
                elif type(res) == mResponse.ChatResponse:
                    for tId in res.targetIds:
                        self.socketHandler.send(self.id2addr[tId], res.dict())
                elif type(res) == mResponse.CloseRoomResponse:
                    req = mRequest.CloseRoomRequest(res.roomid)
                    self.lobbyManager.requestQueue.put(req)
                elif type(res) == mResponse.AuthResponse:
                    if res.code == 200:
                        self.id2addr[res.id] = res.addr
                        self.id2addr[res.addr] = res.id
                    self.socketHandler.send(res.addr, res.dict())
                else:
                    self.socketHandler.send(self.id2addr[res.id], res.dict())


if __name__ == '__main__':
    host = '192.168.35.3'
    port = 5095
    cert = './cert/certificate.crt'
    key = './cert/private.key'
    
    setproctitle(f"LDJMAFIA")
    server = LDJMafiaServer(host, port, cert, key)
    server.start()
    