from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from server import Server

PORT = 9999
W = 1000; H = 600


class SWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.server = Server(self)
        self.appear()
        return

    def appear(self):
        '''창을 띄움'''
        self.setWindowTitle('Server')

        # 서버 설정 부분
        server_box = QHBoxLayout()
        group_box = QGroupBox('Server setting')
        server_box.addWidget(group_box)

        box1 = QHBoxLayout()

        ip_label = QLabel('Server IP')
        self.server_ip = QLineEdit('127.0.0.1') # localhost
        box1.addWidget(ip_label)
        box1.addWidget(self.server_ip)

        port_label = QLabel('Port')
        self.port = QLineEdit(str(PORT))
        box1.addWidget(port_label)
        box1.addWidget(self.port)

        self.btn = QPushButton('Run Server')
        self.btn.setCheckable(True)
        self.btn.toggled.connect(self.toggle_btn)
        box1.addWidget(self.btn)

        group_box.setLayout(box1)

        # 접속자 정보
        client_box = QHBoxLayout()
        group_box = QGroupBox('Clients')
        group_box.setMaximumWidth(300)
        client_box.addWidget(group_box)

        box2 = QHBoxLayout()
        self.client_list = QTableWidget()
        self.client_list.setColumnCount(2)
        self.client_list.setHorizontalHeaderItem(0, QTableWidgetItem('Address'))
        self.client_list.setHorizontalHeaderItem(1, QTableWidgetItem('Name'))

        box2.addWidget(self.client_list)
        group_box.setLayout(box2)

        # 채팅창
        group_box = QGroupBox('Messages')
        box3 = QVBoxLayout()
        self.msg = QListWidget()
        box3.addWidget(self.msg)
        group_box.setLayout(box3)
        client_box.addWidget(group_box)

        # 전체 레이아웃
        box = QVBoxLayout()
        box.addLayout(server_box)
        box.addLayout(client_box)
        self.setLayout(box)
        self.resize(W, H)
        self.show()
        return

    def toggle_btn(self):
        '''접속 버튼과 연결'''
        server_ip = self.server_ip.text()
        port = int(self.port.text())
        if self.server.run(server_ip, port):
            self.btn.setEnabled(False)
        else:
            QMessageBox.warning(self, "QMessageBox", "다른 Server IP, Port를 입력해주세요.")
            self.btn.setEnabled(True)
        return

    def update_client(self, addr, name, connected):
        '''signal에 의해 client 목록을 바꿈'''
        if connected: # 새로운 client가 입장
            self.client_list.setRowCount(self.client_list.rowCount()+1)
            self.client_list.setItem(self.client_list.rowCount()-1, 0, QTableWidgetItem(addr))
            self.client_list.setItem(self.client_list.rowCount()-1, 1, QTableWidgetItem(name))
        else: # 퇴장
            r = self.client_list.rowCount()
            for i in range(r):
                a = self.client_list.item(i, 0).text()
                if a == addr:
                    self.client_list.removeRow(i)
                    break
        return

    def update_msg(self, msg):
        '''signal에 의해 채팅창을 업데이트'''
        self.msg.addItem(QListWidgetItem(msg))
        return

    # Override
    def closeEvent(self, event):
        '''창을 닫으면 실행'''
        self.server.terminate()
        return super().closeEvent(event)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SWindow()
    sys.exit(app.exec_())
