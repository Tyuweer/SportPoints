import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import PredictorWindow
from PyQt5.QtGui import QIcon

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.ico'))
    window = PredictorWindow()
    window.show()
    sys.exit(app.exec_())   