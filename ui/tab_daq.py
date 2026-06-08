from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from core.daq_poller import PMTDaqPoller

class TabSiPMDAQ(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.poller = PMTDaqPoller()
        self.poller.wave_ready.connect(self.update_wave)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        ctrl_group = QGroupBox("Optical Sensor (PMT/SiPM) Control")
        ctrl_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 18px; border: 1px solid #CBD5E1; border-radius: 8px; padding-top: 25px; background: #FFFFFF;}")
        ctrl_layout = QHBoxLayout(ctrl_group)
        
        self.btn_start = QPushButton("Start Sim Pulse")
        self.btn_start.setFixedSize(160, 40)
        self.btn_start.setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold; border-radius: 6px;")
        self.btn_start.clicked.connect(self.toggle_daq)
        
        self.lbl_height = QLabel("Amplitude: 0.00 V")
        self.lbl_integral = QLabel("Integral: 0.00 V·ns")
        font_c = QFont("Consolas", 18, QFont.Weight.Bold)
        self.lbl_height.setFont(font_c); self.lbl_height.setStyleSheet("color: #DC2626;")
        self.lbl_integral.setFont(font_c); self.lbl_integral.setStyleSheet("color: #2563EB;")
        
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.lbl_height)
        ctrl_layout.addSpacing(25)
        ctrl_layout.addWidget(self.lbl_integral)

        graph_group = QGroupBox("Real-time Waveform (Oscilloscope)")
        graph_group.setStyleSheet(ctrl_group.styleSheet())
        graph_layout = QVBoxLayout(graph_group)

        self.graph_widget = pg.PlotWidget(background='#0F172A') 
        self.graph_widget.showGrid(x=True, y=True, alpha=0.5)
        self.graph_widget.setLabel('left', 'Voltage', units='V', color='#FFFFFF')
        self.graph_widget.setLabel('bottom', 'Time', units='ns', color='#FFFFFF')
        self.plot_curve = self.graph_widget.plot(pen=pg.mkPen('#10B981', width=2)) 
        
        graph_layout.addWidget(self.graph_widget)
        layout.addWidget(ctrl_group, 1)
        layout.addWidget(graph_group, 5)

    def toggle_daq(self):
        if not self.poller.running:
            self.poller.start()
            self.btn_start.setText("Stop")
            self.btn_start.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; border-radius: 6px;")
        else:
            self.poller.stop()
            self.btn_start.setText("Start Sim Pulse")
            self.btn_start.setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold; border-radius: 6px;")

    def update_wave(self, x_data, y_data, height, integral):
        self.plot_curve.setData(x_data, y_data)
        self.lbl_height.setText(f"Amplitude: {height:.2f} V")
        self.lbl_integral.setText(f"Integral: {integral:.2f} V·ns")