import ssl, os, sys
from mafiaUi import *
from socket import *
from socketHandler import clientSocketHandler
from multiprocessing import Manager, freeze_support, connection, Queue
from mafiaProtocol import mRequest, mResponse
host = 'ldjmafia.kro.kr'
port = 6666

executablePath = os.path.dirname(os.path.abspath(sys.executable))
scriptPath = os.path.dirname(__file__)
os.chdir(scriptPath)

environ = os.environ
environ["QT_DEVICE_PIXEL_RATIO"] = "0"
environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
environ["QT_SCREEN_SCALE_FACTORS"] = "1"
environ["QT_SCALE_FACTOR"] = "1"

def qWaiter(Q: Queue, signalPipe: connection.Connection):
    while True:
        try:
            signalPipe.send(Q.get(timeout=None))
        except EOFError: break
if __name__ == '__main__':
    freeze_support()
    rManager = Manager()
    sockHandler = clientSocketHandler(host, port, rManager)
    uiManager = UImanager()
    recvQPIPE, _recvQPIPE = connection.Pipe()
    reqQPIPE, _reqQPIPE = connection.Pipe()
    recvQWaiter = Process(target=qWaiter, args=(sockHandler.recvs, _recvQPIPE))
    reqQWaiter = Process(target=qWaiter, args=(uiManager._requestQueue, _reqQPIPE))

    recvQWaiter.start()
    reqQWaiter.start()

    uiManager.start()
    sockHandler.start()
    uiManager.setShow('login', True)
    
    userid = ""
    while True:
        if not uiManager.isalive(): break
        IOEnd = connection.wait([reqQPIPE, recvQPIPE], timeout=1)
        for IOE in IOEnd:
            if IOE == reqQPIPE:
                req = reqQPIPE.recv()
                sockHandler.send(req.dict())

            elif IOE == recvQPIPE:
                res = recvQPIPE.recv()
                res = mResponse.fromdict(res)
                if type(res) == mResponse.AuthResponse:
                    if res.code == 200:
                        uiManager.setID(res.id)
                        userid = res.id
                        uiManager.setShow('lobby', True)
                        uiManager.setShow('login', False)
                    else:
                        uiManager.loginFail(res.desc)

                elif type(res) == mResponse.RoomResponse:
                    if res.code == 200:
                        uiManager.setShow('room', True)
                        uiManager.setRoomID(userid, res.roomid)
                        uiManager.setShow('lobby', False)
                    else:
                        uiManager.lobbyFail(res.desc)

                elif type(res) == mResponse.NoticeResponse:
                    if res.code == 200:
                        if res.noticetype == 'roominfo':
                            uiManager.setUserInfo(res)
                        elif res.noticetype == 'playerenter':
                            uiManager.updateUserInfo(res)
                        elif res.noticetype == 'playerexit':
                            uiManager.exitUserInfo(res)
                        elif res.noticetype == 'newroommaster':
                            uiManager.setRoomMaster(res)
                        elif res.noticetype == 'jobnotice':
                            uiManager.setMyJob(res)
                        elif res.noticetype == 'timenotice':
                            uiManager.setTime(res)
                        elif res.noticetype in ('playerdead', 'playerlive'):
                            uiManager.changeUserStatus(res)
                        elif res.noticetype in ('mafiatarget', 'policetarget', 'doctortarget'):
                            uiManager.setAbilityTarget(res)
                        elif res.noticetype in ('vote'):
                            uiManager.noticeVote(res)
                        elif res.noticetype in ('gameend'):
                            uiManager.gameEnd(res)
                        pass
                    if res.code == 406:
                        uiManager.setShow('room', False)
                        uiManager.setShow('lobby', True)
                        uiManager.lobbyFail(res.desc)

                elif type(res) == mResponse.ChatResponse:
                    uiManager.updateChat(res)
    
    uiManager.stop()
    sockHandler.terminate()
    recvQWaiter.terminate()
    reqQWaiter.terminate()