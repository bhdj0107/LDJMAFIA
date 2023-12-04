import ssl
from socket import *
import traceback

host = '192.168.35.3'
port = 5095

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('./cert/certificate.crt', './cert/private.key')

with socket(AF_INET, SOCK_STREAM) as sock:
    with context.wrap_socket(sock, server_side=True) as sSock:
        sSock.bind((host, port))
        sSock.listen()

        print('server listening..')
        while True:
            try:
                conn, addr = sSock.accept()
                data = conn.recv(1024).decode()
                print(data)
            except ssl.SSLError:
                print(traceback.format_exc())
