import json
import os
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from ui.tab_radon import TabRadonMonitor
from ui.tab_daq import TabSiPMDAQ

class RENE_DaqMasterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Korean HK Group - Integrated DAQ & Environment Monitor")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #F1F5F9; color: #0F172A; font-family: 'Malgun Gothic';")

        affiliation = "N/A"
        operator = "N/A"
        config_path = os.path.join(os.getcwd(), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                affiliation = config.get("affiliation", affiliation)
                operator = config.get("operator", operator)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        header_layout = QHBoxLayout()
        lbl_info = QLabel(f"Affiliation: {affiliation}   |   Operator: {operator}")
        lbl_info.setFont(QFont("Malgun Gothic", 12, QFont.Weight.Bold))
        lbl_info.setStyleSheet("color: #475569; padding: 5px;")
        
        self.lbl_clock = QLabel()
        self.lbl_clock.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.lbl_clock.setStyleSheet("color: #2563EB; padding: 5px;")
        
        header_layout.addWidget(lbl_info)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_clock)
        
        main_layout.addLayout(header_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #F1F5F9; }
            QTabBar::tab { background: #E2E8F0; color: #475569; padding: 15px 30px; font-weight: bold; font-size: 16px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #2563EB; border-top: 4px solid #2563EB; }
        """)
        
        self.tab_radon = TabRadonMonitor()
        self.tab_sipm = TabSiPMDAQ()
        
        self.tabs.addTab(self.tab_radon, "RS-9A Radon Monitor")
        self.tabs.addTab(self.tab_sipm, "Optical Sensor Attenuation (Sim)")
        
        main_layout.addWidget(self.tabs)

    def update_clock(self):
        from datetime import datetime
        self.lbl_clock.setText(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))