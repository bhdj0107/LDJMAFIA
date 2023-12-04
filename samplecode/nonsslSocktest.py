import ssl, os
from socket import *
import traceback, select
from multiprocessing import Process, Queue, connection
host = '192.168.35.3'
port = 5095

os.chdir('../')
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('./cert/certificate.crt', './cert/private.key')
sock = context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_side=True)

sock.bind((host, port))
sock.listen()



print('server listening..')
sessions = []


def socketPrinter(conn, addr):
    while True:
        data = conn.recv(1024).decode()
        if data == '종료': break
        print(addr, ' said ', data)


sockHolder = [sock]

while True:
    targets = connection.wait(sockHolder)
    for target in targets:
        if target == sock:
            conn, addr = sock.accept()
            print(addr, "new sock connected.")
            print()
            sockHolder.append(conn)
        else:
            flag = bool(1 < len(str(target).split('raddr=')))
            if flag:
                data = target.recv(1024).decode('utf-8')
                print(str(target).split('raddr=')[-1][:-1], 'said', data)
                print()
            else:
                for i in range(len(sockHolder)):
                    if sockHolder[i] == target:
                        print(i, 'deleted')
                        print()
                        del sockHolder[i]
                        break

    print(sockHolder)
    print(targets)
    print('--------------')