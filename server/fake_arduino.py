#!/usr/bin/env python3
"""
Fake Arduino Simulator for Full Software Testing
================================================

이 스크립트는 실제 Arduino / 브레드보드 없이도
Python 백엔드 + 웹 UI + 인증 로직 전체를 현실적으로 테스트할 수 있게 해준다.

사용법 (가장 추천):
1. 터미널 A에서 실행:
   python server/fake_arduino.py

2. 출력되는 장치 경로를 복사 (예: /dev/pts/12)
3. 터미널 B에서 서버 실행:
   DOORLOCK_VISION_MOCK=true DOORLOCK_YOLO_ENABLED=false \
   DOORLOCK_SERIAL_PORT=/dev/pts/12 \
   DOORLOCK_WEB_PORT=8080 \
   python server/main.py

이제 fake_arduino 메뉴에서 '1', '2' 등을 눌러서
가짜 NFC 태그, PIN 입력을 서버로 보낼 수 있다.

서버가 보내는 명령(OPEN_DOOR, AUTH_FAIL, LOCKDOWN)도 실시간으로 볼 수 있다.

이걸로 다음 상황들을 미리 예측하고 검증할 수 있다:
- 정상 2FA 성공 흐름
- 1차 인증 실패
- 2차(얼굴) 인증 실패
- Rate limit 동작
- 연속 실패 → LOCKDOWN 진입
- 잘못된 시리얼 데이터 수신 시 안정성
- Door open timer 시뮬레이션 등
"""

import os
import pty
import sys
import time
import threading
import select
import random
from datetime import datetime

# 색상 출력 (터미널 지원 시)
class C:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def ts():
    return datetime.now().strftime("%H:%M:%S")

def log_from_arduino(msg: str):
    print(f"{C.OKGREEN}[ARDUINO → SERVER {ts()}]{C.ENDC} {msg}")

def log_from_server(msg: str):
    print(f"{C.OKCYAN}[SERVER → ARDUINO {ts()}]{C.ENDC} {msg}")

def log_info(msg: str):
    print(f"{C.OKBLUE}[FAKE]{C.ENDC} {msg}")

def log_scenario(msg: str):
    print(f"{C.WARNING}[SCENARIO]{C.ENDC} {msg}")


class FakeArduino:
    def __init__(self):
        self.master, self.slave = pty.openpty()
        self.slave_name = os.ttyname(self.slave)
        self.running = True
        self.last_sent = ""

        # 서버가 보내는 명령을 읽는 스레드
        self.reader_thread = threading.Thread(target=self._read_from_server, daemon=True)
        self.reader_thread.start()

    def _read_from_server(self):
        """서버가 보내는 명령을 계속 읽어서 화면에 표시"""
        while self.running:
            try:
                r, _, _ = select.select([self.master], [], [], 0.2)
                if r:
                    data = os.read(self.master, 1024)
                    if data:
                        text = data.decode('utf-8', errors='ignore').strip()
                        if text:
                            for line in text.splitlines():
                                line = line.strip()
                                if line:
                                    log_from_server(line)
                                    # 간단한 자동 응답 시뮬레이션 (실제 펌웨어 흉내)
                                    self._simulate_firmware_response(line)
            except OSError:
                break
            except Exception as e:
                log_info(f"Read error: {e}")
                time.sleep(0.5)

    def _simulate_firmware_response(self, cmd: str):
        """서버가 보낸 명령에 대해 실제 아두이노 펌웨어가 어떻게 반응할지 흉내"""
        cmd = cmd.strip().upper()
        if cmd == "OPEN_DOOR":
            # 실제로는 서보를 돌리고 3초 후 DOOR_CLOSED 보냄
            time.sleep(0.4)
            self.send("DOOR_OPENED")
            log_info("펌웨어: 서보 회전 → 문 열림 (3초 후 자동 잠김 시뮬레이션)")
            # 3초 후 자동으로 문 닫힘 피드백
            threading.Timer(2.8, lambda: self.send("DOOR_CLOSED")).start()

        elif cmd == "PING":
            self.send("PONG:DOORLOCK_ARDUINO")

        elif cmd == "STATUS":
            self.send("STATUS:LOCKED")

        elif cmd == "AUTH_FAIL":
            log_info("펌웨어: 부저 FAIL 음 + LED 4회 점멸")

        elif cmd == "LOCKDOWN":
            log_info("펌웨어: 비상 잠금 모드 진입 (부저 5회 + LED 빠른 점멸)")

    def send(self, line: str):
        """서버로 데이터 전송 (실제 시리얼 쓰기와 동일)"""
        try:
            os.write(self.master, (line + "\n").encode('utf-8'))
            log_from_arduino(line)
            self.last_sent = line
        except OSError as e:
            log_info(f"전송 실패: {e}")

    def send_nfc(self, uid: str = None):
        if uid is None:
            uid = "".join(random.choices("0123456789ABCDEF", k=8))
        self.send(f"WAKEUP:NFC:{uid}")

    def send_pin(self, pin: str = None):
        if pin is None:
            pin = "".join(random.choices("0123456789", k=random.randint(4, 8)))
        self.send(f"WAKEUP:PW:{pin}")

    def send_garbage(self):
        garbage = random.choice([
            "GARBAGE_DATA_123",
            "WAKEUP:NFC:ZZZZ",           # 잘못된 hex
            "WAKEUP:PW:ABC",             # PIN이 숫자가 아님
            "WAKEUP:FACE:12345678",      # 지원하지 않는 타입
            "",                          # 빈 줄
            "SYSTEM_READY",              # 중복 부팅 메시지
        ])
        self.send(garbage)

    def print_menu(self):
        print("\n" + "="*60)
        print(f"{C.BOLD}Fake Arduino Control Menu (포트: {self.slave_name}){C.ENDC}")
        print("="*60)
        print("  1) 정상 NFC 태그 전송          (랜덤 UID)")
        print("  2) 정상 PIN 입력               (랜덤 4~8자리)")
        print("  3) 등록되지 않은 NFC (실패)")
        print("  4) 잘못된 PIN (실패)")
        print("  5) 🔥 연속 실패 12회 폭주 (LOCKDOWN 유발)")
        print("  6) Rate limit 테스트 (빠른 반복 입력)")
        print("  7) 쓰레기 데이터 / 오염된 프레임 전송")
        print("  8) SYSTEM_READY 재전송")
        print("  9) 문 열림/닫힘 수동 피드백 (DOOR_OPENED/CLOSED)")
        print("  s) 현재 상태 요약")
        print("  q) 종료")
        print("-"*60)
        print("번호나 명령을 입력하고 Enter: ", end="", flush=True)

    def run_interactive(self):
        print(f"\n{C.OKGREEN}=== Fake Arduino Simulator Started ==={C.ENDC}")
        print(f"이 장치를 서버에 연결하세요:")
        print(f"  {C.BOLD}DOORLOCK_SERIAL_PORT={self.slave_name}{C.ENDC}")
        print()
        log_info("이 창에서 1~9, s, q 등을 입력하면 서버로 신호가 갑니다.")
        log_info("서버가 보내는 명령(OPEN_DOOR 등)도 여기서 실시간으로 보입니다.\n")

        try:
            while self.running:
                self.print_menu()
                choice = input().strip().lower()

                if choice == '1':
                    self.send_nfc()
                elif choice == '2':
                    self.send_pin()
                elif choice == '3':
                    self.send_nfc("DEADBEEF")   # 거의 등록되지 않을 확률
                elif choice == '4':
                    self.send_pin("00000000")
                elif choice == '5':
                    self._run_lockdown_flood()
                elif choice == '6':
                    self._run_rate_limit_test()
                elif choice == '7':
                    self.send_garbage()
                elif choice == '8':
                    self.send("SYSTEM_READY")
                elif choice == '9':
                    self.send("DOOR_OPENED")
                    time.sleep(1.5)
                    self.send("DOOR_CLOSED")
                elif choice == 's':
                    self._print_status()
                elif choice in ('q', 'quit', 'exit'):
                    print("종료합니다...")
                    break
                else:
                    print("알 수 없는 명령입니다.")

                time.sleep(0.15)
        except KeyboardInterrupt:
            print("\nCtrl+C 감지. 종료.")
        finally:
            self.running = False

    def _run_lockdown_flood(self):
        log_scenario("=== LOCKDOWN 유발 시나리오 시작 (12회 연속 실패) ===")
        for i in range(1, 13):
            uid = f"BAD{i:02d}"
            self.send(f"WAKEUP:NFC:{uid}")
            time.sleep(0.25)   # 실제 사람이 빠르게 시도하는 속도
        log_scenario("12회 입력 완료. 서버가 LOCKDOWN을 보내는지 확인하세요.")
        log_info("웹 UI 상단에 빨간 경고 배너가 떠야 하고, 최근 로그에 여러 UNAUTHORIZED가 보여야 합니다.")

    def _run_rate_limit_test(self):
        log_scenario("=== Rate Limit 테스트 (3초 내 재시도) ===")
        self.send_nfc("RATETEST1")
        time.sleep(0.3)
        self.send_nfc("RATETEST2")   # 너무 빠름 → 서버가 무시해야 함
        log_info("서버 로그에 '[DENIED] Rate limited' 메시지가 나와야 정상입니다.")

    def _print_status(self):
        print(f"\n현재 가상 포트: {self.slave_name}")
        print(f"마지막으로 보낸 신호: {self.last_sent or '(없음)'}")
        print("서버 프로세스가 이 포트에 연결되어 있는지 확인하세요.\n")


def run_automated_scenario(name: str, fake: FakeArduino):
    """자동 시나리오 실행 (CI나 빠른 재현용)"""
    print(f"\n{C.BOLD}=== Automated Scenario: {name} ==={C.ENDC}\n")

    if name == "lockdown":
        log_scenario("12회 연속 실패로 LOCKDOWN 유발")
        for i in range(1, 13):
            fake.send(f"WAKEUP:NFC:BAD{i:02d}")
            time.sleep(0.18)
        log_info("시나리오 종료. 서버 로그와 웹 UI를 확인하세요.")

    elif name == "rate_limit":
        log_scenario("Rate limit 검증")
        fake.send_nfc("FAST01")
        time.sleep(0.4)
        fake.send_nfc("FAST02")
        log_info("두 번째 입력이 무시되었는지 확인")

    elif name == "full_success":
        log_scenario("정상 2FA 성공 흐름 (등록된 UID 필요)")
        print("주의: 이 UID가 실제로 DB에 등록되어 있어야 FINAL_SUCCESS가 나옵니다.")
        fake.send("WAKEUP:NFC:DEMO1234")
        time.sleep(4)   # 얼굴 확인 시간 대기

    elif name == "garbage":
        log_scenario("오염된 시리얼 데이터 처리 테스트")
        for _ in range(5):
            fake.send_garbage()
            time.sleep(0.3)

    else:
        print(f"알 수 없는 시나리오: {name}")
        print("사용 가능한 시나리오: lockdown, rate_limit, full_success, garbage")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fake Arduino Simulator for SW-only testing")
    parser.add_argument("--scenario", choices=["lockdown", "rate_limit", "full_success", "garbage"],
                        help="자동으로 특정 상황 재현")
    parser.add_argument("--port-only", action="store_true",
                        help="포트만 출력하고 바로 종료 (다른 스크립트에서 사용)")
    args = parser.parse_args()

    fake = FakeArduino()

    if args.port_only:
        print(fake.slave_name)
        sys.exit(0)

    if args.scenario:
        # 자동 모드: 바로 시나리오 실행 후 종료
        run_automated_scenario(args.scenario, fake)
        time.sleep(1.5)
        fake.running = False
        return

    # 기본: 대화형 메뉴
    fake.run_interactive()


if __name__ == "__main__":
    main()
