from multiprocessing import Process, Queue
import pickle, numpy as np
from mafiaProtocol import mRequest, mResponse
from datetime import datetime, timedelta
from setproctitle import *
from collections import defaultdict
from random import randint
class GameManager:
    def __init__(self):
        self.roomid = -1
        self.playerid = {}
        self.maxPlayer = 8
        self.roommasterid = ""
        self.playerJob = {}
        self.whatPeriod = "투표"
        self.time = datetime.now()
        self.gameStatus = False
        self.mafiaTargeted = ""
        self.doctorTargeted = ""
        self.whoVotewho = {}
        self.JobSide = {'마피아':'마피아', '의사':'시민', '경찰':'시민', '시민':'시민', '유령':'유령'}
        self.firstJob = {}
        self.responseQueue = Queue()
        self.requestQueue = Queue()
        self._managerunner = None

    def start(self):
        self._managerunner = Process(target=self._manageRunner, args=(self.__dict__, ), name=f"GameManager-{self.roomid}")
        self._managerunner.start()
                                     

    def close(self):
        self.requestQueue.close()
        self._managerunner.terminate()
        self._managerunner.join()

    def dayTick(self):
        if self.whatPeriod == "밤":
            if datetime.now() - self.time > timedelta(seconds=30):
                self.whatPeriod = '낮'

                if self.mafiaTargeted != "":
                    if self.mafiaTargeted != self.doctorTargeted:
                        res = mResponse.NoticeResponse(200, f"{self.mafiaTargeted} 님이 죽었습니다.", self.mafiaTargeted, self.roomid, 'playerdead', self.playerid, mRequest.NullRequest())
                        self.playerJob[self.mafiaTargeted] = '유령'
                    else:
                        res = mResponse.NoticeResponse(200, f"{self.mafiaTargeted} 님이 의사의 치료로 살아났습니다.", self.mafiaTargeted, self.roomid, 'playerlive', self.playerid, mRequest.NullRequest())
                else:
                    res = mResponse.NoticeResponse(200, f"이번 밤에는 아무도 죽지 않았습니다.", "",self.roomid, 'playerdead', self.playerid, mRequest.NullRequest())
                self.responseQueue.put(res)
                        
                mafiaCnt = 0
                citizenCnt = 0 
                for tjob in list(self.playerJob.values()):
                    if tjob == '마피아':
                        mafiaCnt += 1
                    elif tjob != '유령':
                        citizenCnt += 1
                if mafiaCnt >= citizenCnt:
                    self.time = datetime.now() - timedelta(days=1)
                    self.gameStatus = False
                    res = mResponse.NoticeResponse(200, '게임 종료 [마피아 승]', self.firstJob, self.roommasterid, 'gameend', self.playerid, mRequest.NullRequest())

                elif mafiaCnt == 0:
                    self.time = datetime.now() - timedelta(days=1)
                    self.gameStatus = False
                    res = mResponse.NoticeResponse(200, '게임 종료 [시민 승]', self.firstJob, self.roommasterid, 'gameend', self.playerid, mRequest.NullRequest())
                else:
                    alivePlayers = {}
                    for tId, tJob in list(self.playerJob.items()):
                        if tJob != '유령':
                            alivePlayers[tId] = 1
                    self.time = datetime.now()
                    res = mResponse.NoticeResponse(200, '낮', alivePlayers, self.roomid, 'timenotice', self.playerid, mRequest.NullRequest())
                self.responseQueue.put(res)
        elif self.whatPeriod == '낮':
            if datetime.now() - self.time > timedelta(seconds=30):
                self.whatPeriod = '투표'
                self.time = datetime.now()
                self.whoVotewho = {}
                alivePlayers = {}
                for tId, tJob in list(self.playerJob.items()):
                    if tJob != '유령':
                        alivePlayers[tId] = 1
                res = mResponse.NoticeResponse(200, '투표', alivePlayers, self.roomid, 'timenotice', self.playerid, mRequest.NullRequest())
                self.responseQueue.put(res)
        elif self.whatPeriod == '투표':
            if datetime.now() - self.time > timedelta(seconds=30):
                self.whatPeriod = '밤'
                
                voteCnt = defaultdict(int)
                for i in self.whoVotewho.values():
                    voteCnt[i] += 1
                
                maxID, maxVote, maxCnt = "", 0, 0
                for tId, voteValue in voteCnt.items():
                    if voteValue > maxVote:
                        maxCnt = 1
                        maxID, maxVote = tId, voteValue
                    elif voteValue == maxVote:
                        maxCnt += 1

                if maxCnt == 1:
                    res = mResponse.NoticeResponse(200, f"{maxID} 님이 죽었습니다.", maxID, self.roomid, 'playerdead', self.playerid, mRequest.NullRequest())
                    self.playerJob[maxID] = '유령'
                    self.responseQueue.put(res)
                elif maxID != "":
                    res = mResponse.NoticeResponse(200, f"아무도 죽지 않았습니다.", "", self.roomid, 'playerdead', self.playerid, mRequest.NullRequest())
                    self.responseQueue.put(res)

                

                mafiaCnt = 0
                citizenCnt = 0 
                for tjob in list(self.playerJob.values()):
                    if tjob == '마피아':
                        mafiaCnt += 1
                    elif tjob != '유령':
                        citizenCnt += 1
                if mafiaCnt >= citizenCnt:
                    self.time = datetime.now() - timedelta(days=1)
                    self.gameStatus = False
                    res = mResponse.NoticeResponse(200, '게임 종료 [마피아 승]', self.firstJob, self.roommasterid, 'gameend', self.playerid, mRequest.NullRequest())

                elif mafiaCnt == 0:
                    self.time = datetime.now() - timedelta(days=1)
                    self.gameStatus = False
                    res = mResponse.NoticeResponse(200, '게임 종료 [시민 승]', self.firstJob, self.roommasterid, 'gameend', self.playerid, mRequest.NullRequest())
                else:
                    self.doctorTargeted = ""
                    self.mafiaTargeted = ""
                    alivePlayers = {}
                    for tId, tJob in list(self.playerJob.items()):
                        if tJob != '유령':
                            alivePlayers[tId] = 1
                    
                    self.time = datetime.now()
                    res = mResponse.NoticeResponse(200, '밤', alivePlayers, self.roomid, 'timenotice', self.playerid, mRequest.NullRequest())

                self.responseQueue.put(res)


    def _manageRunner(self, params):
        self.roomid = params['roomid']
        self.roommasterid = params['roommasterid']
        self.responseQueue = params['responseQueue']
        self.requestQueue = params['requestQueue']
        setproctitle(f"LDJMAFIA-GameManager-{self.roomid}")
        while True:
            if self.gameStatus:
                self.dayTick()
            if not self.requestQueue.empty():
                req = self.requestQueue.get()
                if type(req) == mRequest.CreateRoomRequest or type(req) == mRequest.JoinRoomRequest:
                    if len(self.playerid) >= self.maxPlayer:
                        res = mResponse.NoticeResponse(406, 'Room is FULL', req.id, self.roomid, 'roominfo', -1, req)
                        self.responseQueue.put(res)
                        continue
                    else:
                        res = mResponse.NoticeResponse(200, 'Room Players ID', req.id, self.roomid, 'roominfo', self.playerid.copy(), req)
                        self.responseQueue.put(res)
                        res = mResponse.NoticeResponse(200, 'Room Players ID', req.id, self.roomid, 'playerenter', self.playerid.copy(), req)
                        self.responseQueue.put(res)
                        res = mResponse.NoticeResponse(200, '', self.roommasterid, self.roomid, "newroommaster", {req.id:1}, req)
                        self.responseQueue.put(res)

                        self.playerid[req.id] = 1
                        self.playerJob[req.id] = '유령'

                elif type(req) == mRequest.AbilityTargetRequest:
                    if self.gameStatus:
                        if self.whatPeriod == '밤':
                            if self.playerJob[req.id] == '마피아':
                                self.mafiaTargeted = req.targetid
                                res = mResponse.NoticeResponse(200, '', self.mafiaTargeted, self.roomid, "mafiatarget", self.mafias, req)

                            elif self.playerJob[req.id] == '경찰':
                                isMafia = bool(self.playerJob[req.targetid] == '마피아')
                                res = mResponse.NoticeResponse(200, isMafia, req.targetid, self.roomid, "policetarget", self.police, req)

                            elif self.playerJob[req.id] == '의사':
                                self.doctorTargeted = req.targetid
                                res = mResponse.NoticeResponse(200, '', self.doctorTargeted, self.roomid, "doctortarget", self.doctor, req)
                        elif self.whatPeriod == '투표':
                            self.whoVotewho[req.id] = req.targetid
                            res = mResponse.NoticeResponse(200, 'You Voted.', self.whoVotewho[req.id], self.roomid, "vote", {req.id:1}, req)
                        self.responseQueue.put(res)

                elif type(req) == mRequest.ChatRequest:
                    if self.whatPeriod == "밤":
                        targetIDs = []
                        targetIDs.append(req.id)
                        jobtag = self.playerJob[req.id]
                        for tId in self.playerid.keys():
                            if tId == req.id: continue
                            if self.playerJob[req.id] == self.playerJob[tId] or self.playerJob[tId] == '유령':
                                targetIDs.append(tId)
                    else:
                        if self.playerJob[req.id] != '유령':
                            targetIDs = list(self.playerid.keys())
                            jobtag = '시민'
                        else:
                            targetIDs = []
                            targetIDs.append(req.id)
                            for tId in self.playerid.keys():
                                if tId == req.id: continue
                                if self.playerJob[tId] == '유령':
                                    targetIDs.append(tId)
                            jobtag = '유령'

                    res = mResponse.ChatResponse(req.id, self.roomid, req.chat, targetIDs, jobtag)
                    self.responseQueue.put(res)

                elif type(req) == mRequest.GameStartRequest:
                    if len(self.playerid) < 4:
                        res = mResponse.NoticeResponse(406, "방 인원이 4명 이상일 때 부터 시작할 수 있습니다.", req.id, self.roomid, 'roominfo', -1, req)
                    else:
                        self.time = datetime.now() - timedelta(days=1)
                        self.gameStatus = True

                        # initialize
                        self.mafiaTargeted = ""
                        self.doctorTargeted = ""
                        self.whatPeriod = '투표'
                        self.whoVotewho = {}

                        self.mafiaCount = 2 if len(self.playerid) >= 6 else 1
                        self.policeCount = 1
                        self.doctorCount = 1
                        
                        popRandomPlayers = list(self.playerid.keys())

                        self.mafias = {}
                        for _ in range(self.mafiaCount):
                            randI = randint(0, len(popRandomPlayers) - 1)
                            tId = popRandomPlayers[randI]
                            del popRandomPlayers[randI]
                            self.mafias[tId] = 1

                        self.police = {}
                        for _ in range(self.policeCount):
                            randI = randint(0, len(popRandomPlayers) - 1)
                            tId = popRandomPlayers[randI]
                            del popRandomPlayers[randI]
                            self.police[tId] = 1
                            
                        self.doctor = {}
                        for _ in range(self.doctorCount):
                            randI = randint(0, len(popRandomPlayers) - 1)
                            tId = popRandomPlayers[randI]
                            del popRandomPlayers[randI]
                            self.doctor[tId] = 1     


                        for tId in self.mafias.keys():
                            self.playerJob[tId] = '마피아'
                        res = mResponse.NoticeResponse(200, "마피아", "", self.roomid, 'jobnotice', self.mafias, req)
                        self.responseQueue.put(res)

                        for tId in self.police.keys():
                            self.playerJob[tId] = '경찰'
                            res = mResponse.NoticeResponse(200, "경찰", "", self.roomid, 'jobnotice', self.police, req)
                        self.responseQueue.put(res)

                        for tId in self.doctor.keys():
                            self.playerJob[tId] = '의사'
                            res = mResponse.NoticeResponse(200, "의사", "", self.roomid, 'jobnotice', self.doctor, req)
                        self.responseQueue.put(res)
                        
                        while popRandomPlayers:
                            tId = popRandomPlayers.pop()
                            self.playerJob[tId] = '시민'
                            res = mResponse.NoticeResponse(200, "시민", "", self.roomid, 'jobnotice', {tId:1}, req)
                            self.responseQueue.put(res)
                        
                        
                        self.firstJob = self.playerJob.copy()
                elif type(req) == mRequest.ExitRoomRequest:
                    try:
                        del self.playerid[req.id]
                        del self.playerJob[req.id]

                        if len(self.playerid) == 0:
                            res = mResponse.CloseRoomResponse(self.roomid)
                        else:
                            res = mResponse.NoticeResponse(200, '', req.id, self.roomid, 'playerexit', self.playerid.copy(), req)
                            
                            if self.roommasterid == req.id:
                                self.responseQueue.put(res)
                                self.roommasterid = set(self.playerid.keys()).pop()
                                res = mResponse.NoticeResponse(200, '', self.roommasterid, self.roomid, "newroommaster", self.playerid.copy(), req)
                                
                            
                        
                        self.responseQueue.put(res)
                    except KeyError: pass

class LobbyManager:
    def __init__(self):
        self._managerunner = None
        self.requestQueue = Queue()
        self.responseQueue = Queue()
        self.roomsReqQueue = {}

    def start(self):
        self._managerunner = Process(target=self._manageRunner, args=(self.__dict__, ))
        self._managerunner.start()

    def _manageRunner(self, params):
        self.requestQueue = params['requestQueue']
        self.responseQueue = params['responseQueue']
        self.roomsReqQueue = params['roomsReqQueue']
        maxPlayer = 8

        setproctitle(f"LDJMAFIA-LobbyManager")

        id2room = {}
        rooms = {}

        while True:
            if not self.requestQueue.empty():
                req = self.requestQueue.get()
                if type(req) == mRequest.CreateRoomRequest:

                    # 방 생성 제한 (최대치 도달)
                    if len(rooms) > 10000:
                        res = mResponse.RoomResponse(406, "Room Max. Can't Create Room.", "0", req)
                        self.responseQueue.put(res)
                        continue

                    # 방 생성 성공
                    while True:
                        newRoomid = f'{np.random.randint(1, 999999):006d}'
                        if newRoomid not in rooms: break

                    self.roomsReqQueue[newRoomid] = Queue()
                    rooms[newRoomid] = GameManager()
                    rooms[newRoomid].roomid = newRoomid
                    rooms[newRoomid].maxPlayer = maxPlayer
                    rooms[newRoomid].roommasterid = req.id
                    rooms[newRoomid].requestQueue = self.roomsReqQueue[newRoomid]
                    rooms[newRoomid].responseQueue = self.responseQueue
                    rooms[newRoomid].start()
                    rooms[newRoomid].requestQueue.put(req)
                    
                    id2room[req.id] = newRoomid
                    res = mResponse.RoomResponse(200, "Room Created", newRoomid, req)
                    self.responseQueue.put(res)

                elif type(req) == mRequest.JoinRoomRequest:
                    # 방 입장 성공
                    if req.roomid in rooms:
                        res = mResponse.RoomResponse(200, "Successfully Find Room.", req.roomid, req)
                        self.responseQueue.put(res)
                        id2room[req.id] = req.roomid
                        rooms[req.roomid].requestQueue.put(req)
                        continue
                    
                    # 방 입장 실패
                    res = mResponse.RoomResponse(404, "Can't Find Room.", req.roomid, req)
                    self.responseQueue.put(res)

                elif type(req) in (mRequest.ChatRequest, mRequest.GameStartRequest, mRequest.AbilityTargetRequest):
                    rooms[id2room[req.id]].requestQueue.put(req)

                elif type(req) == mRequest.ExitRoomRequest:
                    try:
                        rooms[id2room[req.id]].requestQueue.put(req)
                        del id2room[req.id]
                    except KeyError: pass
                elif type(req) == mRequest.CloseRoomRequest:
                    rooms[req.roomid].close()
                    del rooms[req.roomid]

class AuthenticateManager:
    def __init__(self, logintablePath):
        self.logintablePath = logintablePath
        self.requestQueue = Queue()
        self.responseQueue = Queue()
    
        self._managerunner = None

    def start(self):
        self._managerunner = Process(target=self._manageRunner, args=(self.__dict__, ))
        self._managerunner.start()
    
    def _manageRunner(self, params):
        logintablePath = params['logintablePath']
        self.requestQueue = params['requestQueue']
        self.responseQueue = params['responseQueue']
        setproctitle(f"LDJMAFIA-AuthenticateManager")

        with open(logintablePath, 'rb') as f:
            logintable = pickle.load(f)

        while True:
            if not self.requestQueue.empty():
                req = self.requestQueue.get()

                # 회원가입 요청
                if type(req) == mRequest.RegisterRequest:
                    if req.id in logintable:
                        res = mResponse.AuthResponse(401, "Already Registered", "", req)
                        self.responseQueue.put(res)
                        continue
                    else:
                        logintable[req.id] = req.pw
                        with open(logintablePath, 'wb') as f:
                            pickle.dump(logintable, f)
                        res = mResponse.AuthResponse(200, "Register Successful", req.id, req)
                        self.responseQueue.put(res)
                        continue

                # 로그인 요청
                elif type(req) == mRequest.LoginRequest:
                    if req.id in logintable:
                        if logintable[req.id] == req.pw:
                            res = mResponse.AuthResponse(200, "Login Successful", req.id, req)
                            self.responseQueue.put(res)
                            continue
                    res = mResponse.AuthResponse(401, "id/pw invalid", "", req)
                    self.responseQueue.put(res)

