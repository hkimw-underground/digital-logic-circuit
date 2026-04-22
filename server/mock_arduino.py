import time
import random

def simulate_arduino():
    print("--- Arduino Mock Simulator Started ---")
    print("Commands: 'n' for NFC tag, 'p' for Password, 'q' to quit")
    
    while True:
        cmd = input("Simulate Input (n/p/q): ").strip().lower()
        if cmd == 'n':
            uid = "".join(random.choices("0123456789ABCDEF", k=8))
            print(f"SENDING -> WAKEUP:NFC:{uid}")
            # 실제 장비에서는 이 값이 시리얼 포트로 전송된다.
        elif cmd == 'p':
            print("SENDING -> WAKEUP:PW:[REDACTED]")
        elif cmd == 'q':
            break
        else:
            print("Invalid input.")

if __name__ == "__main__":
    simulate_arduino()
