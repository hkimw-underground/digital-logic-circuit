# 스마트 도어락 아키텍처 및 데이터 흐름

```markmap
# 2FA 스마트 도어락
## 하드웨어 (Arduino)
### 입력 장치
- MFRC522 (NFC)
- 4x4 매트릭스 키패드
### 출력 장치
- 릴레이 (도어 제어)
### 통신
- Serial (9600 bps)

## 서버 (Python/FastAPI)
### 핵심 엔진
- main.py (오케스트레이션)
- vision_ai.py (YOLOv8 + Face Recognition)
### 데이터베이스
- SQLite (bcrypt 해싱)
- access_logs 테이블
### 사용자 인터페이스
- FastAPI 대시보드
- 실시간 영상 스트리밍

## 보안 로직
### 1차 인증
- NFC UID 대조
- PIN 번호 일치 확인
### 2차 인증
- YOLO 생체 감지 (Liveness)
- 얼굴 특징값 비교
### 방어 기제
- 락다운 (연속 실패 시 차단)
- 안티 스푸핑 (화면 인식 차단)
```
