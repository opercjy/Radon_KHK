import time
import serial
from PyQt6.QtCore import QThread, pyqtSignal

class RS9APoller(QThread):
    # Signal format: (Status, Value, Uncertainty, Remaining Time)
    data_ready = pyqtSignal(str, float, float, int)
    error_signal = pyqtSignal(str)

    def __init__(self, port, baudrate=19200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.serial_conn = None

    def run(self):
        self.running = True
        try:
            # 1. 실제 장비 연결 및 안정화 대기
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2) 
            
            # 2. 하드웨어 단위를 Bq/m3로 강제 설정 명령 전송
            self.serial_conn.write(b"UNIT 1\r\n") 
            time.sleep(0.5)
            
        except Exception as e:
            self.error_signal.emit(f"Failing port connection: {e}")
            self.running = False
            return

        while self.running:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    # [핵심 교정] 60초 대기 중 누적된 노이즈 및 이전 데이터를 쿼리 전송 직전에 폐기
                    self.serial_conn.reset_input_buffer() 
                    
                    # 3. 데이터 요청 쿼리 전송
                    self.serial_conn.write(b"VALUE?\r\n")
                    time.sleep(0.5) 
                    
                    # 4. 수신된 실제 데이터 읽기
                    if self.serial_conn.in_waiting:
                        raw_data = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if raw_data:
                            self.parse_rs9a_data(raw_data)
                            
            except Exception as e:
                self.error_signal.emit(f"Experiencing communication error: {e}")
            
            # 포트 폴링은 1분(60초) 간격으로 수행
            for _ in range(60): 
                if not self.running: break
                time.sleep(1.0)

    def parse_rs9a_data(self, raw_str):
        try:
            # RS-9A의 불규칙한 콜론(:) 포맷을 공백으로 치환하여 안정적인 인덱싱 확보
            clean_str = raw_str.replace(":", " ")
            parts = clean_str.split()
            if len(parts) < 2: return
            
            status = parts[1] # READY, NORMAL, ERR1, ERR2
            
            if status in ["ERR1", "ERR2"]:
                self.error_signal.emit(f"Detecting sensor error: {status}")
                return
                
            if status == "READY":
                rtime_idx = parts.index("rTime") + 1
                rtime = int(parts[rtime_idx])
                self.data_ready.emit(status, 0.0, 0.0, rtime)
                
            elif status == "NORMAL":
                val_idx = parts.index("VALUE") + 1
                rou_idx = parts.index("ROU") + 1
                rtime_idx = parts.index("rTime") + 1
                
                val = float(parts[val_idx])
                rou = float(parts[rou_idx])
                rtime = int(parts[rtime_idx])
                
                self.data_ready.emit(status, val, rou, rtime)
                
        except Exception:
            # 예상치 못한 응답 포맷은 무시하고 다음 주기에 재시도
            pass

    def stop(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.quit()
        self.wait()