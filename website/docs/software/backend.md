---
sidebar_position: 1
---

# 백엔드 아키텍처 (Backend Architecture)

백엔드(Backend)는 시스템의 권한 있는 의사 결정(Authoritative Decision-making) 및 제어의 중심 역할을 한다. Arduino로부터 수신된 센서 데이터를 처리하고, Vision AI 모듈을 통해 2차 인증을 수행하며, 모든 이벤트를 데이터베이스에 기록하고 관리자에게 알림을 전송한다.

## 핵심 모듈 (Core Modules)

1. **`main.py` (Orchestration Logic):**
   - 시스템의 전체 워크플로우를 조율한다.
   - 시리얼 통신, 데이터베이스, Vision AI, 알림 시스템을 통합하여 인증 로직을 실행한다.
   - 백그라운드 태스크로 데이터베이스 백업을 관리한다.
2. **`web_app.py` (FastAPI Server):**
   - FastAPI 기반의 웹 인터페이스 및 REST API를 제공한다.
   - 사용자 등록, 로그 조회, 실시간 모니터링(Video Feed) 기능을 담당한다.
3. **`serial_manager.py` (Serial Communication):**
   - Arduino와의 비동기 시리얼 통신을 처리한다.
   - NFC UID 및 PIN 데이터를 파싱하여 코어 로직에 전달하고, 서버의 제어 명령(Unlock)을 하드웨어로 송신한다.
4. **`vision_ai.py` (Vision Module):**
   - YOLOv8 및 OpenCV를 활용하여 얼굴 인식 파이프라인을 관리한다.
   - 실시간 프레임 캡처, 얼굴 임베딩 추출 및 코사인 유사도(Cosine Similarity) 기반 매칭을 수행한다.
5. **`notifier.py` (Discord Integration):**
   - Discord Webhook을 통해 실시간 보안 알림을 전송한다.
   - 인증 실패 시 캡처된 스냅샷(Snapshot)을 포함하여 관리자에게 즉시 보고한다.
6. **`config.py` (Centralized Configuration):**
   - 포트 설정, 타임아웃, 보안 임계값(Failure Limits) 등 시스템의 전역 설정을 중앙 집중식으로 관리한다.

## API 엔드포인트 (API Endpoints)

| 엔드포인트 (Endpoint) | 메서드 | 목적 (Purpose) |
|---|---|---|
| `/` | GET | 시스템 상태 및 실시간 로그를 확인하는 대시보드 메인 페이지. |
| `/api/logs` | GET | 최신 접근 로그 및 연속 인증 실패 경고 상태를 반환한다. |
| `/api/logs/{id}/snapshot` | GET | 특정 로그 항목에 저장된 인증 실패 시점의 사진을 반환한다. |
| `/api/register` | POST | 새로운 사용자의 NFC UID, PIN, 얼굴 정보를 등록한다. |
| `/api/capture_face` | POST | 사용자 등록을 위해 카메라에서 현재 얼굴 임베딩을 캡처한다. |
| `/api/users` | GET/DELETE | 등록된 사용자 목록을 조회하거나 특정 사용자를 삭제한다. |
| `/video_feed` | GET | 실시간 카메라 스트리밍 데이터를 제공한다. |

## 보안 및 신뢰성 기능 (Security & Reliability)

- **2단계 인증 (2FA):** 1차(NFC/PIN)와 2차(Face Recognition) 인증을 결합하여 보안 수준을 강화한다.
- **실시간 알림 (Instant Alerts):** 비인가 접근 시도나 2차 인증 실패 시 즉시 관리자의 Discord로 스냅샷을 포함한 알림을 발송한다.
- **속도 제한 및 잠금 (Rate Limiting):** 연속적인 인증 실패 시 일정 시간 동안 입력을 차단하여 브루트 포스(Brute-force) 공격을 방지한다.
- **자동 백업 (Automated Backup):** 설정된 간격마다 SQLite 데이터베이스 백업을 생성하여 데이터 유실에 대비한다.
- **Fail-safe 설계:** 시스템 오류나 미확인 상태에서는 항상 '잠금' 상태를 유지하도록 구현되어 있다.
