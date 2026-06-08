import sys
import os
from PyQt6.QtWidgets import QApplication

# Qt 디버그 메시지 숨김
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt6ct.debug=false"

from ui.main_window import RENE_DaqMasterApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RENE_DaqMasterApp()
    ex.show()
    sys.exit(app.exec())