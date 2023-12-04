from socket import socket
from multiprocessing import Process, Manager
import ssl, json
from socket import *
def isClosed(socket: socket):
    return bool(1 >= len(str(socket).split('raddr=')))


# class sockHandler:
#     def __init__(self):
#         self.host = ""
#         self.port = ""

#         self.resourceManager = Manager()

#         self.requests = self.resourceManager.Queue()
#         self.responses = self.resourceManager.dict()

#         self.connections = self.resourceManager.dict()
#         self.controller = self.resourceManager.Queue()

#         self.runner = Process()

#     def __socketListener(self, host, port):
#         ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#         ctx.load_cert_chain('./cert/certificate.crt', './cert/private.key')
#         sock = ctx.wrap_socket(socket(AF_INET, SOCK_STREAM), server_side=True)
#         sock.bind((host, port))
#         sock.listen()
#         while True:

#             # control Listener
#             if not self.controller.empty():
#                 op, param = self.controller.get()
#                 if op == 'stop':
#                     break


#             # recv/send datas
#             try:
#                 res = sock.recv().decode()
#                 res = json.loads(res)
#                 self.responses[res['nonce']] = res['response']
#             except ssl.SSL_ERROR_WANT_READ: pass

#             if not self.requests.empty():
#                 nonce, target, req = self.requests.get()

#                 reqbody = {}
#                 reqbody['nonce'] = nonce
#                 reqbody['request'] = req

#                 reqbody = json.dumps(reqbody)
#                 reqbody = reqbody.encode('utf-8')

#                 self.connections[target].sendall(reqbody)

#     def 


# if __name__ == '__main__':
#     a = sockHandler()