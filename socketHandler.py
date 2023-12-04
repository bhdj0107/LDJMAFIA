from socket import *
import ssl, json, traceback
from multiprocessing import Process, Manager, connection
from mafiaProtocol import mRequest, mResponse
class serverSocketHandler:
    def __init__(self, host, port, cert, key, resourcemanager: Manager):
        self.host = host
        self.port = port
        self.cert = cert
        self.key = key

        self.addrs = resourcemanager.dict()

        self.connCnt = resourcemanager.Value('i', 0)
        self.recvs = resourcemanager.Queue()
        self._sends = resourcemanager.Queue()

        self._establisher = None

    def start(self):
        sockData = (self.host, self.port, self.cert, self.key)

        self._establisher = Process(target=self._connectionEstablisher, args=(sockData, self.recvs, self._sends, self.connCnt, self.addrs))
        self._establisher.start()

    def send(self, addr: tuple, response: dict):
        self._sends.put((addr, response))

    def broadcast(self, response: dict):
        for addr in list(self.addrs):
            self._sends.put((addr, response))

    def terminate(self):
        self._establisher.terminate()
        self._establisher.join()

    def _connectionEstablisher(self, sockData, recvs, sends, connCnt, addrs):
        host, port, cert, key = sockData
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, key)

        sock = ctx.wrap_socket(socket(AF_INET, SOCK_STREAM), server_side=True)
        sock.bind((host, port))
        sock.listen()
        sock.setblocking(False)

        connections = {}
        print("socket Handler is listening...\n================")
        while True:
            try:
                connCnt.set(len(connections))
                for addr, conn in list(connections.items()):
                    try:
                        res = mResponse.CheckAlivenessResponse()
                        res = json.dumps(res.dict()).encode()
                        conn.sendall(res)
                    except Exception as e:
                        del connections[addr]
                        del addrs[addr]
                        req = mRequest.ConnectionLostRequest(addr)
                        self.recvs.put((addr, req.dict()))


                ioEndSocks = connection.wait(connections.values(), timeout=0.0001)

                if not sends.empty():
                    try:
                        addr, send = sends.get()
                        if addr == -1: break
                        targetSock = connections.get(addr)
                        if targetSock:
                            if send.get('nonce'):
                                send = json.dumps(send).encode()
                                targetSock.sendall(send)
                    except UnicodeDecodeError: pass
                    except json.JSONDecodeError: pass
                    
                for ioEndSock in ioEndSocks:
                    try:
                        recv = ioEndSock.recv().decode()
                        recv = json.loads(recv)

                        # nonce 미포함 수신은 reject
                        if not recv.get('nonce'): continue

                        # 요청 address 와 recv 값을 tuple로 묶어 요청을 등록
                        recvs.put((ioEndSock.getpeername(), recv))

                    except UnicodeDecodeError: pass
                    except json.JSONDecodeError: pass

                serverSock = connection.wait([sock], timeout=0.0001)
                if serverSock:
                    try:
                        conn, addr = serverSock[0].accept()
                        connections[addr] = conn
                        addrs[addr] = 0
                    except ssl.SSLError: pass
            except ConnectionResetError: pass
class clientSocketHandler:
    def __init__(self, host, port, resourcemanager: Manager):
        self.host = host
        self.port = port

        self.recvs = resourcemanager.Queue()
        self._sends = resourcemanager.Queue()

        self._establisher = None

    def start(self):
        sockData = (self.host, self.port)

        self._establisher = Process(target=self._connectionEstablisher, args=(sockData, self.recvs, self._sends))
        self._establisher.start()

    def send(self, response: dict):
        self._sends.put(response)

    def terminate(self):
        self._establisher.terminate()
        self._establisher.join()

    def _connectionEstablisher(self, sockData, recvs, sends):
        host, port = sockData
        ctx = ssl.create_default_context()
        sock = ctx.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname=host)
        sock.connect((host, port))
        sock.setblocking(False)

        connections = {}
        print("socket Handler is listening...\n================")
        while True:

            if not sends.empty():
                try:
                    send = sends.get()
                    targetSock = sock
                    if targetSock:
                        if send.get('nonce'):
                            send = json.dumps(send).encode()
                            targetSock.sendall(send)
                except UnicodeDecodeError: pass
                except json.JSONDecodeError: pass
                
            serverSock = connection.wait([sock], timeout=0)
            if serverSock:
                try:
                    recv = serverSock[0].recv(2048).decode()
                    recvs.put(json.loads(recv))
                except ssl.SSLWantReadError: pass

if __name__ == '__main__':
    host = '192.168.35.3'
    port = 5095

    cert = './cert/certificate.crt'
    key = './cert/private.key'

    resourceManager = Manager()

    sockHandler = serverSocketHandler(host, port, cert, key, resourceManager)
    sockHandler.start()

    while True:
        if sockHandler.recvs:
            addr, req = sockHandler.recvs.pop()
            sockHandler.broadcast(req)
        print('Connection Counts : ', sockHandler.connCnt.get(), end='\r')