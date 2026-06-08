import time
import pandas as pd
import serial.tools.list_ports
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QPushButton, QComboBox, QMessageBox, QFileDialog,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from core.rs9a_poller import RS9APoller

# ExcelPreviewDialog 클래스는 제시하신 원본과 동일하게 유지 (생략 없이 사용)
class ExcelPreviewDialog(QDialog):
    def __init__(self, data_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Previewing Excel Export")
        self.resize(700, 400)
        self.setStyleSheet("background-color: #F8FAFC; color: #0F172A; font-family: 'Malgun Gothic';")
        
        layout = QVBoxLayout(self)
        lbl_info = QLabel("Previewing last 50 entries.\nProceed to save?")
        lbl_info.setFont(QFont("Malgun Gothic", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_info)
        
        self.table = QTableWidget()
        if data_list:
            headers = list(data_list[0].keys())
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            preview_data = data_list[-50:]
            self.table.setRowCount(len(preview_data))
            for row_idx, row_data in enumerate(preview_data):
                for col_idx, key in enumerate(headers):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data[key])))
        
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save"); btn_save.setFixedSize(120, 40)
        btn_save.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; border-radius: 6px;")
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Cancel"); btn_cancel.setFixedSize(120, 40)
        btn_cancel.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; border-radius: 6px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

class TabRadonMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.log_data = [] 
        self.time_data = []
        self.radon_data = []
        self.upper_data = []
        self.lower_data = []
        self.init_ui()

    def init_ui(self):
        # UI 레이아웃 구성부는 제시하신 코드 원본과 동일하게 유지
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        ctrl_group = QGroupBox("RS-9A Control Panel")
        ctrl_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 18px; border: 1px solid #CBD5E1; border-radius: 8px; padding-top: 25px; background: #FFFFFF;}")
        ctrl_layout = QHBoxLayout(ctrl_group)
        
        self.combo_port = QComboBox()
        self.combo_port.setMinimumWidth(250)
        self.refresh_ports()

        self.btn_refresh = QPushButton("Scan"); self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_start = QPushButton("Start"); self.btn_start.clicked.connect(self.start_monitoring)
        self.btn_stop = QPushButton("Stop"); self.btn_stop.setEnabled(False); self.btn_stop.clicked.connect(self.stop_monitoring)
        self.btn_export = QPushButton("Export Excel"); self.btn_export.clicked.connect(self.export_to_excel)

        self.lbl_status = QLabel("Standby")
        self.lbl_current_val = QLabel("0.0 Bq/m³")
        self.lbl_current_val.setFont(QFont("Malgun Gothic", 24, QFont.Weight.Bold))
        self.lbl_current_val.setStyleSheet("color: #DC2626;")

        ctrl_layout.addWidget(self.combo_port); ctrl_layout.addWidget(self.btn_refresh)
        ctrl_layout.addWidget(self.btn_start); ctrl_layout.addWidget(self.btn_stop); ctrl_layout.addWidget(self.btn_export)
        ctrl_layout.addStretch()
        
        info_layout = QVBoxLayout()
        info_layout.addWidget(self.lbl_status, alignment=Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(self.lbl_current_val, alignment=Qt.AlignmentFlag.AlignRight)
        ctrl_layout.addLayout(info_layout)

        graph_group = QGroupBox("Real-time Trend (7-Day Log)")
        graph_group.setStyleSheet(ctrl_group.styleSheet())
        graph_layout = QVBoxLayout(graph_group)
        
        lbl_notice = QLabel("* Note: RS-9A applying 60-min moving average; polling port every 1 min for status.")
        lbl_notice.setStyleSheet("color: #F59E0B; font-weight: bold;")
        graph_layout.addWidget(lbl_notice)

        self.date_axis = pg.DateAxisItem(orientation='bottom')
        self.graph_widget = pg.PlotWidget(background='w', axisItems={'bottom': self.date_axis})
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.graph_widget.setLabel('left', 'Radon Concentration', units='Bq/m³', color='#0F172A')
        
        self.plot_curve = self.graph_widget.plot(pen=pg.mkPen('#2563EB', width=3), symbol='o', symbolBrush='#DC2626')
        
        self.upper_curve = pg.PlotDataItem(pen=pg.mkPen(color=(37, 99, 235, 0)))
        self.lower_curve = pg.PlotDataItem(pen=pg.mkPen(color=(37, 99, 235, 0)))
        self.graph_widget.addItem(self.upper_curve)
        self.graph_widget.addItem(self.lower_curve)
        
        self.error_band = pg.FillBetweenItem(self.lower_curve, self.upper_curve, brush=pg.mkBrush(37, 99, 235, 50)) 
        self.graph_widget.addItem(self.error_band)

        graph_layout.addWidget(self.graph_widget)

        layout.addWidget(ctrl_group, 1)
        layout.addWidget(graph_group, 5)

    def refresh_ports(self):
        self.combo_port.clear()
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.combo_port.addItem("No Device Found", None)
            return
        for p in ports:
            self.combo_port.addItem(f"{p.device} - {p.description}", p.device)

    def start_monitoring(self):
        port = self.combo_port.currentData()
        if not port: return
        self.poller = RS9APoller(port=port)
        self.poller.data_ready.connect(self.update_data)
        self.poller.start()
        self.btn_start.setEnabled(False); self.btn_stop.setEnabled(True)

    def stop_monitoring(self):
        if hasattr(self, 'poller'): self.poller.stop()
        self.btn_start.setEnabled(True); self.btn_stop.setEnabled(False)

    def update_data(self, status, val, rou, rtime):
        current_unix_time = time.time()
        log_timestamp = datetime.fromtimestamp(current_unix_time).strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. 초기화(READY) 상태 처리: 그래프는 멈추되 로그는 연속 기록하여 추적성 확보
        if status == "READY":
            self.lbl_status.setText(f"Initializing... ({rtime}m remaining)")
            self.lbl_current_val.setText("Awaiting Data")
            self.log_data.append({
                "Datetime": log_timestamp, 
                "Radon (Bq/m3)": 0.0, 
                "Uncert.": 0.0
            })
            return
        
        # 2. 정상 측정(NORMAL) 상태 처리
        self.lbl_status.setText(f"Acquiring (Updating in {rtime}m) | Uncert.(1-σ): ±{rou}")
        self.lbl_current_val.setText(f"{val:.1f} Bq/m³")
        
        # [핵심 교정] 동일 값일 때 기록을 건너뛰는 조건문 제거. 시간의 전진은 물리적 사실이므로 반드시 기록
        self.time_data.append(current_unix_time)
        self.radon_data.append(val)
        self.upper_data.append(val + rou)
        self.lower_data.append(val - rou)
        
        # 7일 분량(10080분) 초과 시 과거 데이터 삭제하여 메모리 누수 방지
        if len(self.time_data) > 10080:
            self.time_data.pop(0)
            self.radon_data.pop(0)
            self.upper_data.pop(0)
            self.lower_data.pop(0)
            
        self.plot_curve.setData(self.time_data, self.radon_data)
        self.upper_curve.setData(self.time_data, self.upper_data)
        self.lower_curve.setData(self.time_data, self.lower_data)
        
        self.log_data.append({
            "Datetime": log_timestamp, 
            "Radon (Bq/m3)": val, 
            "Uncert.": rou
        })

    def export_to_excel(self):
        if not self.log_data:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return

        dialog = ExcelPreviewDialog(self.log_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "HK_Group_Radon_Log.xlsx", "Excel Files (*.xlsx)")
            if file_path:
                pd.DataFrame(self.log_data).to_excel(file_path, index=False, engine='openpyxl')