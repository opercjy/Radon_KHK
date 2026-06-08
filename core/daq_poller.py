import time
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

class PMTDaqPoller(QThread):
    # 신호 포맷: (X_Array, Y_Array, 펄스파고(V), 펄스적분값(V*ns))
    wave_ready = pyqtSignal(object, object, float, float)

    def __init__(self):
        super().__init__()
        self.running = False

    def run(self):
        self.running = True
        x_time = np.linspace(0, 100, 500) # 100ns 윈도우, 500샘플링 (dt = 0.2ns)
        dt = 0.2
        
        while self.running:
            noise = np.random.normal(0, 0.02, len(x_time))
            amplitude = np.random.uniform(1.5, 3.0)
            center = np.random.uniform(40, 60)
            width = np.random.uniform(3, 8)
            
            y_volt = amplitude * np.exp(-((x_time - center)**2) / (2 * width**2)) + noise
            
            pulse_height = np.max(y_volt)
            pulse_integral = np.sum(y_volt) * dt # 적분 (Area)
            
            self.wave_ready.emit(x_time, y_volt, pulse_height, pulse_integral)
            time.sleep(0.1) # 10Hz 화면 갱신

    def stop(self):
        self.running = False
        self.quit()
        self.wait()