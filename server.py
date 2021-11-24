from socket import *
from threading import *

from PyQt5.QtCore import QObject, pyqtSignal

# socket buffer size
BUF_SIZE = 1024
# thread 관리용 mutex
mtx = Lock()


class Server(QObject):
    # client 목록 update에 관한 시그널: addr, msg, add/delete -> 서버 GUI 클라이언트 목록
    update_signal = pyqtSignal(str, str, bool)
    # client로부터 메시지 받는 시그널 -> 서버 GUI 채팅창
    recv_signal = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.server_socket = None
        # listen 모드
        self.connected = False
        # client 정보 저장
        self.clients = {}
        # client 연결(accept) 위한 스레드
        self.thread = None
        # client로부터 메시지 받는 스레드
        self.threads = {}
        # signal - 함수 연결
        self.update_signal.connect(self.parent.update_client)
        self.recv_signal.connect(self.parent.update_msg)
        return

    def __del__(self):
        '''소멸자'''
        self.terminate()
        return

    def terminate(self):
        '''모든 client 소켓, server 소켓 닫고 스레드 제거'''
        self.connected = False

        for client_socket, _ in self.clients.values():
            client_socket.close()
        self.clients.clear()

        if self.server_socket is not None:
            self.server_socket.close()

        self.threads.clear()
        return

    def run(self, server_ip, port):
        '''소켓을 생성하고 listen 모드 활성화 - 성공하면 True, 실패하면 False 리턴'''
        # IPv4, TCP socket 생성
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.server_socket.bind((server_ip, port))
            self.connected = True
            self.thread = Thread(target=self.listen, args=(self.server_socket, ))
            self.thread.daemon = True # 메인 스레드 종료되면 종료
            self.thread.start()
        except Exception as e:
            print("Server) Error in socket binding:", e)
            return False
        return True

    def listen(self, server_socket):
        '''client의 접속을 대기'''
        server_socket.listen()
        while self.connected:
            try:
                client_socket, addr = server_socket.accept()
                # addr: (ip, port)
                addr = addr[0] + ':' + str(addr[1])
                name = client_socket.recv(BUF_SIZE).decode()
                # 다른 스레드들의 접근 막음
                mtx.acquire()
                self.clients[addr] = client_socket, name
                self.update_signal.emit(addr, name, True) # client 접속
                # client로부터 메시지를 받기 위한 스레드 생성
                t = Thread(target=self.receive, args=(client_socket, addr, name))
                t.daemon = True # 메인 스레드 종료되면 종료
                self.threads[addr] = t
                mtx.release()
                t.start()
            except Exception as e:
                print("Server) Error in accepting:", e)
                break

        self.terminate()
        return

    def receive(self, client_socket, addr, name):
        '''client 소켓이 접속하면 메시지를 받기 시작'''
        # 입장 메시지
        msg = f">> {name}님이 입장하셨습니다."
        self.send(msg)
        self.recv_signal.emit(msg)
        
        while True:
            try:
                buffer = client_socket.recv(BUF_SIZE)
                msg = buffer.decode()
                if msg:
                    msg = f">> {msg}"
                    self.send(msg)
                    self.recv_signal.emit(msg)
                else:
                    # 퇴장
                    break
            except Exception as e:
                print("Server) Error in receiving messages:", e)
                break

        self.remove_client(client_socket, addr, name)
        return

    def send(self, msg):
        '''client로부터 온 메시지를 모든 client에게 echo'''
        for client_socket, _ in self.clients.values():
            try:
                client_socket.send(msg.encode())
            except Exception as e:
                print("Server) Error in sending messages:", e)
                continue
        return

    def remove_client(self, client_socket, addr, name):
        '''client를 제거'''
        client_socket.close()

        # clients 목록에서 제거
        mtx.acquire()
        del self.clients[addr]
        mtx.release()

        # 퇴장메시지
        self.update_signal.emit(addr, name, False)
        msg = f">> {name}님이 퇴장하셨습니다."
        self.send(msg)
        self.recv_signal.emit(msg)

        # 스레드 제거
        del self.threads[addr]
        return
