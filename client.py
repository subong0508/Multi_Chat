from socket import *
from threading import *

from PyQt5.QtCore import pyqtSignal, QObject

BUF_SIZE = 1024


class CSignal(QObject):
    # 서버로부터 메시지 받는 시그널 -> 채팅창
    recv_signal = pyqtSignal(str)


class Client(object):
    def __init__(self, parent):
        self.parent = parent
        self.client_socket = None
        # client 이름
        self.name = None
        # 서버로부터 메시지를 받기 위한 스레드
        self.thread = None
        # 서버로부터 메시지 받는 시그널 -> 채팅창에 띄움
        self.recv = CSignal()
        self.recv.recv_signal.connect(self.parent.update_msg)
        # 서버와 연결되었는지?
        self.connected = False
        return

    def __del__(self):
        '''소멸자'''
        self.terminate()
        return

    def terminate(self):
        '''서버와의 연결을 종료'''
        self.connected = False
        if self.client_socket is not None:
            self.client_socket.close()
        return

    def connect(self, server_ip, port, name):
        '''서버와 연결하고 대기 상태로 전환'''
        self.name = name
        # IPv4, TCP socket
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.client_socket.connect((server_ip, port))
            self.connected = True
            self.thread = Thread(target=self.receive, args=(self.client_socket, ))
            self.thread.daemon = True # 메인 스레드 종료되면 종료
            self.thread.start()
            self.client_socket.send(name.encode()) # 입장 메시지를 위해 이름을 보냄
        except Exception as e:
            print("Client) Error in connecting...:", e)
            return False
        return True

    def receive(self, client_socket):
        '''메시지를 받기 위한 대기 상태에 진입'''
        while self.connected:
            try:
                buffer = client_socket.recv(BUF_SIZE)
                msg = buffer.decode()
                if msg:
                    self.recv.recv_signal.emit(msg)
            except Exception as e:
                print("Client) Error in receiving message...:", e)
                break

        self.terminate()
        return

    def send(self, msg, include_name=True):
        '''서버에 메시지를 보내줌'''
        if include_name: # 일반 메시지
            msg = f"[{self.name}]: {msg}"
        if self.connected:
            try:
                self.client_socket.send(msg.encode())
            except Exception as e:
                print("Client) error sending message...:", e)
        return
        