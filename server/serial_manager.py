import serial
import time

class SerialManager:
    def __init__(self, port=None, baudrate=9600, mock=True):
        self.mock = mock
        if not mock and port:
            self.ser = serial.Serial(port, baudrate, timeout=1)
        else:
            self.ser = None
            print("Running in MOCK serial mode.")

    def read_line(self):
        if self.mock:
            # 테스트 모드에서는 실제 시리얼 입력을 읽지 않는다.
            return None 
        if self.ser and self.ser.in_waiting > 0:
            return self.ser.readline().decode('utf-8').strip()
        return None

    def send_command(self, command):
        print(f"SENDING TO ARDUINO -> {command}")
        if not self.mock and self.ser:
            self.ser.write((command + '\n').encode('utf-8'))

    def simulate_incoming(self, data):
        """테스트에서 Arduino 입력을 흉내 낸다."""
        return data
