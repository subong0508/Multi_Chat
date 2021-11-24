from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from client import Client

PORT = 9999
W = 600; H = 200
W_D = 600; H_D = 800


class CDialog(QDialog):
    '''채팅창 객체, 연결 두절 인지를 위해 새롭게 상속'''

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        return

    # Override
    def closeEvent(self, event):
        self.parent.btn.setEnabled(True)
        # 비정상적으로 종료되었다면 (x 표시로 창 끔)
        if self.parent.reconn_signal:
            # 서버에게 연결두절 메시지 보내기
            msg = f"{self.parent.name.text()}님의 연결이 두절되었습니다."
            self.parent.client.send(msg, False) # 이름 정보 불필요
        return super().closeEvent(event)


class CWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.client = Client(self)
        # 재연결했을 때 데이터 복구를 위해 채팅을 미리 저장
        self.data = []
        # 재연결(비정상 종료) signal
        self.reconn_signal = True
        self.appear()
        return

    def __del__(self):
        '''소멸자'''
        self.client.terminate()
        return

    def appear(self):
        '''창을 띄움'''
        self.setWindowTitle('Client')

        labels = [QLabel('Server IP'), QLabel('Port'), QLabel('Name')]
        contents = [QLineEdit('127.0.0.1'), QLineEdit(str(PORT)), QLineEdit('익명')]

        # 서버 설정 부분
        self.server_ip, self.port, self.name = self.contents

        self.btn = QPushButton('Connect server', self)
        self.btn.clicked.connect(self.connect)

        text_box = QHBoxLayout()
        for l, c in zip(labels, contents):
            text_box.addWidget(l)
            text_box.addWidget(c)

        btn_box = QHBoxLayout()
        btn_box.addWidget(self.btn)

        # 전체 레이아웃
        vbox = QVBoxLayout()
        vbox.addLayout(text_box)
        vbox.addLayout(btn_box)
        self.setLayout(vbox)
        self.resize(W, H)
        self.show()
        return

    def connect(self):
        '''서버와 연결'''
        if not self.client.connected: # 새로운 client 소켓을 생성한다면
            server_ip, port = self.server_ip.text(), int(self.port.text())
            name = self.name.text()
            if self.client.connect(server_ip, port, name):
                # 채팅창 띄움
                self.open_dialog()
                self.btn.setEnabled(False)
            else:
                QMessageBox.warning(self, "QMessageBox", "접속에 실패했습니다.\n다시 시도해주세요.")
                self.btn.setEnabled(True)
        else: # 이미 연결된 소켓 존재 - 비정상적으로 종료되었다는 의미, 재연결 해야함
            self.reconnect()
        return

    def open_dialog(self):
        '''채팅창을 띄운다'''
        self.dialog = CDialog(self)

        # close
        self.btn_clear = QPushButton('Close')
        self.btn_clear.clicked.connect(self.close_dialog)

        # send
        self.send_msg = QTextEdit()
        self.send_msg.setMaximumHeight(100)
        self.send_btn = QPushButton('Send')
        self.send_btn.setEnabled(True)
        self.send_btn.clicked.connect(self.send)

        # receive
        self.receive_msg = QListWidget()

        # button box
        btn_box = QHBoxLayout()
        btn_box.setAlignment(Qt.AlignRight)
        btn_box.addWidget(self.btn_clear)

        # recv box
        recv_box = QVBoxLayout()
        recv_box.addWidget(self.receive_msg)

        # send box
        send_box = QHBoxLayout()
        send_box.addWidget(self.send_msg)
        send_box.addWidget(self.send_btn)

        box = QVBoxLayout()
        box.addLayout(btn_box)
        box.addLayout(recv_box)
        box.addLayout(send_box)

        # 채팅창 레이아웃
        self.dialog.setLayout(box)
        self.dialog.setWindowTitle('Chatting room')
        self.dialog.resize(W_D, H_D)
        self.dialog.show()
        return

    def send(self):
        '''서버로 메시지를 보냄'''
        msg = self.send_msg.toPlainText()
        if msg:
            self.client.send(msg)
            self.send_msg.clear()
        else: # 내용이 없다면 서버에서는 퇴장으로 인지하므로 보내면 안됨
            QMessageBox.warning(self, "QMessageBox", "내용을 입력해주세요.")
        return

    def update_msg(self, msg):
        '''메시지 받았을 때 업데이트'''
        self.data.append(msg)
        self.receive_msg.addItem(QListWidgetItem(msg))
        return

    def reconnect(self):
        '''재연결, 대화 복구'''
        self.open_dialog()
        # 서버에게 재연결 신호 보내기
        msg = f"{self.name.text()}님이 재연결되었습니다."
        self.client.send(msg, False)
        # 데이터 복구
        for msg in self.data:
            self.receive_msg.addItem(QListWidgetItem(msg))
        return

    def close_dialog(self):
        '''정상 종료 - 사용자가 Close 버튼으로 채팅창 닫음'''
        self.reconn_signal = False
        self.dialog.close()
        self.client.terminate()
        self.btn.setEnabled(True)
        return

    # Override
    def closeEvent(self, event):
        self.client.terminate()
        self.data.clear()
        return super().closeEvent(event)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = CWindow()
    sys.exit(app.exec_())