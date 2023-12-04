import ssl, json
from multiprocessing import Queue, Process, Manager
from mafiaProtocol import mRequest, mResponse
from socketHandler import clientSocketHandler
from hashlib import sha256
from socket import *

def recvViewer(recvQ):
    while True:
        if not recvQ.empty():
            recv = recvQ.get()
            recv = mResponse.fromdict(recv)
            if type(recv) != mResponse.CheckAlivenessResponse:
                print(recv, recv.dict())


if __name__ == '__main__':
    host = 'ldjmafia.kro.kr'
    port = 443

    sockHandler = clientSocketHandler(host, port, Manager())
    recvListener = Process(target=recvViewer, args=(sockHandler.recvs, ))
    sockHandler.start()
    recvListener.start()

    myid = input("로그인 ID: ")
    pw = input("로그인 PW: ")
    req = mRequest.LoginRequest(myid, sha256(pw.encode()).hexdigest())
    sockHandler.send(req.dict())

    while True:
        inp = input('방 생성 1 / 방 입장 2 / 채팅 3 : ')
        if inp == '1':
            req = mRequest.CreateRoomRequest(myid)
            sockHandler.send(req.dict())
        elif inp == '2':
            roomid = input('방 번호 입력 : ')
            req = mRequest.JoinRoomRequest(myid, roomid)
            sockHandler.send(req.dict())
        elif inp == '3':
            while True:
                chat = input("채팅 할 내용 입력 : ")
                req = mRequest.ChatRequest(myid, chat)
                sockHandler.send(req.dict())
            