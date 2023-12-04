from typing import Any
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from multiprocessing import Queue, Process
from hashlib import sha256
from mafiaProtocol import mRequest, mResponse
import os, sys

executablePath = os.path.dirname(os.path.abspath(sys.executable))
scriptPath = os.path.dirname(__file__)
os.chdir(scriptPath)

loginuiForm = uic.loadUiType('./loginForm.ui')[0]
lobbyuiForm = uic.loadUiType('./lobbyForm.ui')[0]
roomuiForm = uic.loadUiType('./roomForm.ui')[0]


class WindowContoller(QThread):

    loginToogle = pyqtSignal(bool)
    loginFailToggle = pyqtSignal(str)

    lobbyToogle = pyqtSignal(bool)
    lobbyFailToggle = pyqtSignal(str)
    lobbyID = pyqtSignal(str)

    roomToogle = pyqtSignal(bool)
    roomID = pyqtSignal(tuple)
    setUserInfo = pyqtSignal(mResponse.NoticeResponse)
    updateUserInfo = pyqtSignal(mResponse.NoticeResponse)
    exitUserInfo = pyqtSignal(mResponse.NoticeResponse)
    updateChat = pyqtSignal(mResponse.ChatResponse)
    setRoomMaster = pyqtSignal(mResponse.NoticeResponse)
    setMyJob = pyqtSignal(mResponse.NoticeResponse)
    setTime = pyqtSignal(mResponse.NoticeResponse)
    changeUserStatus = pyqtSignal(mResponse.NoticeResponse)
    setAbilityTarget = pyqtSignal(mResponse.NoticeResponse)
    noticeVote = pyqtSignal(mResponse.NoticeResponse)
    gameEnd = pyqtSignal(mResponse.NoticeResponse)

    def __init__(self, controlQ, windows):
        super().__init__()
        self.controlQ = controlQ
        self.windows = windows

    def run(self):
        while True:
            flag = sum([window.isVisible() for window in self.windows])
            if not flag: break
            cmd = self.controlQ.get(timeout=None)
            if cmd[0] == 'show':
                param = cmd[1]
                if param[0] == 'login':
                    self.loginToogle.emit(param[1])
                elif param[0] == 'lobby':
                    self.lobbyToogle.emit(param[1])
                elif param[0] == 'room':
                    self.roomToogle.emit(param[1])

            elif cmd[0] == 'loginfail':
                param = cmd[1]
                self.loginFailToggle.emit(param[0])

            elif cmd[0] == 'lobbyfail':
                param = cmd[1]
                self.lobbyFailToggle.emit(param[0])

            elif cmd[0] == 'setid':
                param = cmd[1]
                self.lobbyID.emit(param[0])

            elif cmd[0] == 'setroomid':
                param = cmd[1]
                self.roomID.emit(param)

            elif cmd[0] == 'setuserinfo':
                param = cmd[1]
                self.setUserInfo.emit(param[0])

            elif cmd[0] == 'updateuserinfo':
                param = cmd[1]
                self.updateUserInfo.emit(param[0])

            elif cmd[0] == 'exituserinfo':
                param = cmd[1]
                self.exitUserInfo.emit(param[0])

            elif cmd[0] == 'updatechat':
                param = cmd[1]
                self.updateChat.emit(param[0])

            elif cmd[0] == 'setroommaster':
                param = cmd[1]
                self.setRoomMaster.emit(param[0])

            elif cmd[0] == 'setmyjob':
                param = cmd[1]
                self.setMyJob.emit(param[0])

            elif cmd[0] == 'settime':
                param = cmd[1]
                self.setTime.emit(param[0])

            elif cmd[0] == 'changeuserstatus':
                param = cmd[1]
                self.changeUserStatus.emit(param[0])

            elif cmd[0] == 'setabilitytarget':
                param = cmd[1]
                self.setAbilityTarget.emit(param[0])
            
            elif cmd[0] == 'noticevote':
                param = cmd[1]
                self.noticeVote.emit(param[0])
            
            elif cmd[0] == 'gameend':
                param = cmd[1]
                self.gameEnd.emit(param[0])

class RoomWindow(QMainWindow, roomuiForm):
    def __init__(self, controller: WindowContoller, reqQ):
        super().__init__()
        self.setupUi(self)
        self.setMaximumSize(self.frameSize())
        self.setMinimumSize(self.frameSize())

        self.chattingPage.setReadOnly(True)
        self.requestQueue = reqQ

        self.btnStart.setEnabled(False)
        self.btnStart.clicked.connect(self.startGame)
        for i in range(1, 9):
            exec(f'self.user{i}.setEnabled(False)')
            eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/blank.png");')''')
        for i in range(1, 9):
            exec(f'self.user{i}.clicked.connect(self.clickMyAbility_{i})')
        self.id = ""

        self.abilTarget = "~~~~~"

        controller.roomToogle.connect(self.toggleShow)
        controller.roomID.connect(self.setRoomID) 
        controller.setUserInfo.connect(self.setUserInfo)
        controller.updateUserInfo.connect(self.updateUserInfo)
        controller.exitUserInfo.connect(self.exitUserInfo)
        controller.updateChat.connect(self.updateChat)
        controller.setRoomMaster.connect(self.setRoomMaster)
        controller.setMyJob.connect(self.setMyJob)
        controller.setTime.connect(self.setTime)
        controller.changeUserStatus.connect(self.changeUserStatus)
        controller.setAbilityTarget.connect(self.setAbilityTarget)
        controller.noticeVote.connect(self.noticeVote)
        controller.gameEnd.connect(self.gameEnd)

        self.inputChat.returnPressed.connect(self.sendChat)
        self.knowJob = {}

        for i in range(1, 9):
            exec(f'self.user{i}ID.setText("")')

    def setRoomID(self, params):
        id, roomid = params
        self.id = params[0]
        self.roomID.setText(params[1])

    def toggleShow(self, onoff):
        if onoff:
            self.show()
        else:
            self.close()

    def startGame(self):
        req = mRequest.GameStartRequest(self.roomID.text(), self.id)
        self.requestQueue.put(req)

    def setAbilityTarget(self, res: mResponse.NoticeResponse):
        if res.noticetype == 'mafiatarget':
            chat = f'[알림] {res.id} 님을 타겟으로 설정합니다.'

            prevSlot, tSlot = 0, 0
            for i in range(1, 9):
                if prevSlot and tSlot: break
                if eval(f'self.user{i}ID').text() == res.id:
                    tSlot = i
                if eval(f'self.user{i}ID').text() == self.abilTarget:
                    prevSlot = i
            
            if prevSlot:
                tJob = self.knowJob.get(self.abilTarget) if self.knowJob.get(self.abilTarget) else "시민"
                if self.job == '마피아':
                    eval(f'''self.user{prevSlot}.setStyleSheet('border-image:url("./images/{tJob}_blue.png");')''')
                else:
                    eval(f'''self.user{prevSlot}.setStyleSheet('border-image:url("./images/{tJob}.png");')''')
            if tSlot:
                tJob = self.knowJob.get(res.id) if self.knowJob.get(res.id) else "시민"
                eval(f'''self.user{tSlot}.setStyleSheet('border-image:url("./images/{tJob}_red.png");')''')

            self.abilTarget = res.id

        elif res.noticetype == 'policetarget':
            chat = f'[알림] {res.id} 님은 마피아가'
            append = '맞습니다' if res.desc else '아닙니다.'
            if res.desc:
                tSlot = 0
                for i in range(1, 9):
                    tSlot = i
                    if eval(f'self.user{tSlot}ID').text() == res.id: break

                self.knowJob[res.id] = '마피아'
                eval(f'''self.user{tSlot}.setStyleSheet('border-image:url("./images/마피아.png");')''')
            chat = chat + ' ' + append

        elif res.noticetype == 'doctortarget':
            chat = f'[알림] {res.id} 님을 치료대상으로 설정합니다.'

            prevSlot, tSlot = 0, 0
            for i in range(1, 9):
                if prevSlot and tSlot: break
                if eval(f'self.user{i}ID').text() == res.id:
                    tSlot = i
                if eval(f'self.user{i}ID').text() == self.abilTarget:
                    prevSlot = i
            
            if prevSlot:
                tJob = self.knowJob.get(self.abilTarget) if self.knowJob.get(self.abilTarget) else "시민"
                eval(f'''self.user{prevSlot}.setStyleSheet('border-image:url("./images/{tJob}_blue.png");')''')
            if tSlot:
                tJob = self.knowJob.get(res.id) if self.knowJob.get(res.id) else "시민"
                eval(f'''self.user{tSlot}.setStyleSheet('border-image:url("./images/{tJob}_red.png");')''')

            self.abilTarget = res.id
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">{chat}</span><br>')

    def gameEnd(self, res: mResponse.NoticeResponse):
        if res.roomid == self.id:
            self.btnStart.setEnabled(True)
        chat = f'[알림] {res.desc}'
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">{chat}</span><br>')

        
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">=====</span><br>')
        for id, job in res.id.items():
            chat = f'{id} : {job}'
            self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
            self.chattingPage.insertHtml(f'<span style=" color:#000000;">{chat}</span><br>')
        
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)    
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">=====</span><br>')
        for i in range(1, 9):
            eval(f'self.user{i}').setEnabled(False)
            if eval(f'self.user{i}ID').text() != "":
                eval(f'self.user{i}').setStyleSheet(f'border-image:url("./images/시민.png");')

    def noticeVote(self, res: mResponse.NoticeResponse):
        chat = f'[알림] 이번 투표에서 {res.id} 님을 투표합니다.'
        
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">{chat}</span><br>')
        prevSlot, tSlot = 0, 0
        for i in range(1, 9):
            if prevSlot and tSlot: break
            if eval(f'self.user{i}ID').text() == res.id:
                tSlot = i
            if eval(f'self.user{i}ID').text() == self.abilTarget:
                prevSlot = i
        
        if prevSlot:
            tJob = self.knowJob.get(self.abilTarget) if self.knowJob.get(self.abilTarget) else "시민"
            eval(f'''self.user{prevSlot}.setStyleSheet('border-image:url("./images/{tJob}_blue.png");')''')
        if tSlot:
            tJob = self.knowJob.get(res.id) if self.knowJob.get(res.id) else "시민"
            eval(f'''self.user{tSlot}.setStyleSheet('border-image:url("./images/{tJob}_red.png");')''')

        self.abilTarget = res.id
            
    def setUserInfo(self, NoticeResponse: mResponse.NoticeResponse):
        for i, username in enumerate(list(NoticeResponse.data.keys())):
            exec(f'self.user{i + 1}ID.setText("{username}")')
            eval(f'''self.user{i + 1}.setStyleSheet('border-image:url("./images/시민.png");')''')
        exec(f'self.user{len(NoticeResponse.data) + 1}ID.setText("{self.id}")')
        eval(f'''self.user{len(NoticeResponse.data) + 1}.setStyleSheet('border-image:url("./images/시민.png");')''')


    def updateUserInfo(self, NoticeResponse: mResponse.NoticeResponse):
        targetSlot = -1
        for i in range(1, 9):
            if eval(f'self.user{i}ID.text()') == '':
                targetSlot = i
                break
        exec(f'self.user{targetSlot}ID.setText("{NoticeResponse.id}")')
        eval(f'''self.user{targetSlot}.setStyleSheet('border-image:url("./images/시민.png");')''')
        chat = f'[알림] {NoticeResponse.id} 님 께서 입장하셨습니다.'
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">{chat}</span><br>')

    def exitUserInfo(self, NoticeResponse: mResponse.NoticeResponse):
        targetSlot = -1
        for i in range(1, 9):
            if eval(f'self.user{i}ID.text()') == NoticeResponse.id:
                targetSlot = i
                break
        exec(f'self.user{targetSlot}.setEnabled(False)')
        exec(f'self.user{targetSlot}ID.setText("")')
        eval(f'''self.user{targetSlot}.setStyleSheet('border-image:url("./images/blank.png");')''')

    def sendChat(self):
        chat = self.inputChat.text()
        self.inputChat.setText("")
        req = mRequest.ChatRequest(self.id, chat)
        self.requestQueue.put(req)

    def updateChat(self, res: mResponse.ChatResponse):
        assert type(self.chattingPage) == QTextEdit
        chat = res.chat
        color = '#ff0000' if res.messageType == '마피아' else '#000000'
        color = '#666666' if res.messageType == '유령' else color
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:{color};">[{res.id}] {chat}</span><br>')

    def setRoomMaster(self, res: mResponse.NoticeResponse):
        chat = f'[알림] {res.id} 님 께서 새로운 방장이 되었습니다.'
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">{chat}</span><br>')
        if res.id == self.id:
            self.btnStart.setEnabled(True)

    def setMyJob(self, res: mResponse.NoticeResponse):
        self.btnStart.setEnabled(False)
        self.job = res.desc
        self.knowJob = {}
        for id, job in res.data.items():
            self.knowJob[id] = self.job

            for i in range(1, 9):
                if eval(f'self.user{i}ID.text()') == id:
                    eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/{self.job}.png");')''')

        chat = f'[알림] {self.id} 님의 직업은 {res.desc} 입니다.'
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">{chat}</span><br>')

    def setTime(self, res: mResponse.NoticeResponse):
        if res.desc == '낮':
            chat = f'[알림] {res.desc} 이 되었습니다.'
            self.inputChat.setText("")
            self.inputChat.setEnabled(True)
            for i in range(1, 9):
                exec(f'self.user{i}.setEnabled(False)')
                tId = eval(f'self.user{i}ID').text()
                if tId != "":
                    tJob = self.knowJob.get(tId) if self.knowJob.get(tId) else '시민'
                    if tId in res.id.keys():
                        eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/{tJob}.png");')''')
                    else:
                        eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/{tJob}_disabled.png");')''')


        elif res.desc == '밤':
            chat = f'[알림] {res.desc} 이 되었습니다.'
            if self.job not in ('마피아', '유령'):
                self.inputChat.setText("")
                self.inputChat.setEnabled(False)
            if self.job in ('마피아', '경찰', '의사'):
                self.abilTarget = "~~~~~"
                alivePlayers = res.id
                for i in range(1, 9):
                    temp = eval(f'self.user{i}ID').text()
                    if temp in alivePlayers.keys():
                        exec(f'self.user{i}.setEnabled(True)')
                        tJob = self.knowJob.get(temp) if self.knowJob.get(temp) else '시민' 
                        eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/{tJob}_blue.png");')''')
            else:
                for i in range(1, 9):
                    if eval(f'self.user{i}').isEnabled(): 
                        temp = eval(f'self.user{i}ID').text()
                        exec(f'self.user{i}.setEnabled(False)')
                        tJob = self.knowJob.get(temp) if self.knowJob.get(temp) else '시민' 
                        eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/{tJob}.png");')''')

        else:
            chat = f'[알림] 투표 시간이 되었습니다.'
            self.abilTarget = '~~~~~'
            alivePlayers = res.id
            if self.job != '유령':
                for i in range(1, 9):
                    temp = eval(f'self.user{i}ID').text()
                    if temp in alivePlayers.keys():
                        exec(f'self.user{i}.setEnabled(True)')
                        tJob = self.knowJob.get(temp) if self.knowJob.get(temp) else '시민' 
                        eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/{tJob}_blue.png");')''')

        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">{chat}</span><br>')

    def changeUserStatus(self, res: mResponse.NoticeResponse):
        chat = res.desc
        self.chattingPage.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
        self.chattingPage.insertHtml(f'<span style=" color:#000000;">[알림] {chat}</span><br>')

        if res.noticetype == 'playerdead':
            for i in range(1, 9):
                if eval(f'self.user{i}ID').text() == res.id:
                    exec(f'self.user{i}.setEnabled(False)')
                    tJob = self.knowJob.get(res.id) if self.knowJob.get(res.id) else '시민'
                    eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/{tJob}_disabled.png");')''')
        
        if res.id == self.id and res.noticetype == 'playerdead':
            self.job = '유령'

    def clickMyAbility(self, tid):
        req = mRequest.AbilityTargetRequest(self.id, tid)
        self.requestQueue.put(req)

        if self.job == '경찰' and not self.inputChat.isEnabled():
            for i in range(1, 9):
                if eval(f'self.user{i}').isEnabled():
                    exec(f'self.user{i}.setEnabled(False)')
                    tId = eval(f'self.user{i}ID').text()
                    tJob = self.knowJob.get(tId) if self.knowJob.get(tId) else '시민'
                    eval(f'''self.user{i}.setStyleSheet('border-image:url("./images/{tJob}.png");')''')


    def clickMyAbility_1(self):
        tid = self.user1ID.text()
        self.clickMyAbility(tid)

    def clickMyAbility_2(self):
        tid = self.user2ID.text()
        self.clickMyAbility(tid)

    def clickMyAbility_3(self):
        tid = self.user3ID.text()
        self.clickMyAbility(tid)

    def clickMyAbility_4(self):
        tid = self.user4ID.text()
        self.clickMyAbility(tid)

    def clickMyAbility_5(self):
        tid = self.user5ID.text()
        self.clickMyAbility(tid)

    def clickMyAbility_6(self):
        tid = self.user6ID.text()
        self.clickMyAbility(tid)

    def clickMyAbility_7(self):
        tid = self.user7ID.text()
        self.clickMyAbility(tid)

    def clickMyAbility_8(self):
        tid = self.user8ID.text()
        self.clickMyAbility(tid)


class LobbyWindow(QMainWindow, lobbyuiForm):
    def __init__(self, controller, reqQ):
        super().__init__()
        self.setupUi(self)
        self.setMaximumSize(self.frameSize())
        self.setMinimumSize(self.frameSize())
        
        self.requestQueue = reqQ

        controller.lobbyToogle.connect(self.toggleShow)
        controller.lobbyFailToggle.connect(self.lobbyFailed)
        controller.lobbyID.connect(self.setID)
        self.btnCreateRoom.clicked.connect(self.createRoom)
        self.btnJoinRoom.clicked.connect(self.JoinRoom)

    def setID(self, id):
        self.id = id

    def toggleShow(self, onoff):
        if onoff:
            self.show()
        else:
            self.close()

    def lobbyFailed(self, param):
        self.btnCreateRoom.setEnabled(True)
        self.btnJoinRoom.setEnabled(True)
        self.statusBar.showMessage(param)

    def createRoom(self):
        self.btnCreateRoom.setEnabled(False)
        self.btnJoinRoom.setEnabled(False)
        req = mRequest.CreateRoomRequest(self.id)
        self.requestQueue.put(req)

    def JoinRoom(self):
        self.btnCreateRoom.setEnabled(False)
        self.btnJoinRoom.setEnabled(False)
        roomid = self.inputRoomID.text()
        req = mRequest.JoinRoomRequest(self.id, roomid)
        self.requestQueue.put(req)


class LoginWindow(QMainWindow, loginuiForm):
    def __init__(self, controller, reqQ):
        super().__init__()
        self.setupUi(self)
        self.setMaximumSize(self.frameSize())
        self.setMinimumSize(self.frameSize())

        controller.loginToogle.connect(self.toggleShow)
        controller.loginFailToggle.connect(self.loginFailed)

        self.btnLogin.clicked.connect(self.LoginClicked)
        self.btnLogin.setShortcut("Enter")
        self.btnLogin.setShortcut("Return")
        self.btnRegister.clicked.connect(self.RegisterClicked)


        self.requestQueue = reqQ

    def LoginClicked(self):
        self.btnLogin.setEnabled(False)
        self.btnRegister.setEnabled(False)
        self.statusBar().showMessage('로그인 중...')
        pw = sha256(self.inputPW.text().encode()).hexdigest()
        req = mRequest.LoginRequest(self.inputID.text(), pw)
        self.requestQueue.put(req)

    def RegisterClicked(self):
        self.btnLogin.setEnabled(False)
        self.btnRegister.setEnabled(False)
        self.statusBar().showMessage('로그인 중...')
        pw = sha256(self.inputPW.text().encode()).hexdigest()
        req = mRequest.RegisterRequest(self.inputID.text(), pw)
        self.requestQueue.put(req)

    def loginFailed(self, param):
        self.btnLogin.setEnabled(True)
        self.btnRegister.setEnabled(True)
        self.statusBar().showMessage(param)


    def toggleShow(self, onoff):
        if onoff:
            self.show()
        else:
            self.close()


class UImanager:
    def __init__(self):
        self._controlQueue = Queue()
        self._requestQueue = Queue()

        self.showableWindowNames = ('login', 'lobby', 'room')
        self._managerProcess = None

        self.id = None

    def start(self):
        self._managerProcess = Process(target=self._manageRunner, args=(self.__dict__, ))
        self._managerProcess.start()

    def stop(self):
        self._managerProcess.terminate()

    def isalive(self):
        return self._managerProcess.is_alive()

    def setRoomID(self, id, roomid):
        self._controlQueue.put(('setroomid', (id, roomid)))

    def setShow(self, targetWindow, onoff: bool):
        if targetWindow in self.showableWindowNames:
            self._controlQueue.put(('show', (targetWindow, onoff)))

    def loginFail(self, method: str):
        self._controlQueue.put(('loginfail', (method, )))

    def lobbyFail(self, method: str):
        self._controlQueue.put(('lobbyfail', (method, )))

    def setID(self, id):
        self._controlQueue.put(('setid', (id, )))

    def setUserInfo(self, res):
        self._controlQueue.put(('setuserinfo', (res, )))

    def updateUserInfo(self, res):
        self._controlQueue.put(('updateuserinfo', (res, )))

    def exitUserInfo(self, res):
        self._controlQueue.put(('exituserinfo', (res, )))

    def updateChat(self, res):
        self._controlQueue.put(('updatechat', (res, )))

    def setRoomMaster(self, res):
        self._controlQueue.put(('setroommaster', (res, )))
    
    def setMyJob(self, res):
        self._controlQueue.put(('setmyjob', (res, )))
    
    def setTime(self, res):
        self._controlQueue.put(('settime', (res, )))
    
    def changeUserStatus(self, res):
        self._controlQueue.put(('changeuserstatus', (res, )))

    def setAbilityTarget(self, res):
        self._controlQueue.put(('setabilitytarget', (res,)))

    def noticeVote(self, res):
        self._controlQueue.put(('noticevote', (res,)))

    def gameEnd(self, res):
        self._controlQueue.put(('gameend', (res,)))


    def _manageRunner(self, params):
        self._controlQueue = params['_controlQueue']
        self._requestQueue = params['_requestQueue']
        self.qapp = QApplication([])

        self.qapp.setAttribute(Qt.AA_EnableHighDpiScaling)
        self.windowController = WindowContoller(self._controlQueue, [])

        self.loginWindow = LoginWindow(self.windowController, self._requestQueue)
        self.lobbyWindow = LobbyWindow(self.windowController, self._requestQueue)
        self.roomWindow = RoomWindow(self.windowController, self._requestQueue)

        windows = [self.loginWindow, self.lobbyWindow, self.roomWindow]
        self.windowController.windows = windows
        self.loginWindow.show()
        self.windowController.start()
        self.qapp.exec_()