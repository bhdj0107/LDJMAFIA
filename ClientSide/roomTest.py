from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import sys
uiForm = uic.loadUiType('./roomForm.ui')[0]

class RoomWindow(QMainWindow, uiForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.chattingPage.setReadOnly(True)

        assert type(self.user1) == QPushButton
        self.user1.setEnabled(False)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RoomWindow()
    window.show()
    app.exec_()
