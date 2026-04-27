---
sidebar_position: 2
---

# 한계점 (Limitations)

2FA Smart Door Lock System의 현재 구현은 실험적인 프로토타입이다. 다중 하드웨어 센서와 컴퓨터 비전 로직의 통합을 성공적으로 시연했지만, 실제 프로덕션 환경(Production Environment)에서 사용하기에는 여러 가지 한계가 존재한다.

### 1. 시리얼 링크의 암호화 보안 (Cryptographic Security of Serial Links)
Backend 서버와 마이크로컨트롤러 간의 통신은 USB 시리얼을 통해 일반 텍스트(Plaintext)로 전송된다. 케이블에 물리적으로 접근할 수 있는 공격자는 `UNLOCK` 문자열을 손쉽게 주입하여 모든 소프트웨어 인증을 우회할 수 있다. 실제 프로덕션 시스템은 암호화된 데이터 버스(예: OSDP 프로토콜)를 필요로 한다.

### 2. 생체 인식 위조 방지 (Biometric Anti-Spoofing)
Vision 모듈은 표준 2D 웹캠을 사용한다. 따라서 고해상도 사진이나 비디오 재생을 이용한 제시 공격(Presentation Attack)에 취약하다. 상업용 시스템은 깊이 센서(Depth Sensor / 예: 스테레오 카메라, 적외선 구조광)를 활용하여 이를 완화한다.

### 3. 릴레이 격리 및 물리적 보안 (Relay Isolation and Physical Security)
프로토타입은 릴레이의 물리적 격리를 강제하지 않는다. 릴레이 모듈이 노출되면 출력 단자를 수동으로 연결하여 잠금장치를 작동시킬 수 있다. 중요 스위칭 하드웨어는 견고한 외함(Enclosure)에 넣고 보안 구역(Secure-side) 내부에 장착해야 한다.

### 4. 제한된 사용자 관리 (Limited User Administration)
현재 사용자 등록은 직접적인 Backend API 호출이나 기본적인 웹 엔드포인트를 통해 처리된다. 시스템에는 대량 등록(Bulk Enrollment), 역할 기반 접근 제어(Role-based Access Control), 또는 예약된 접근 정책(Scheduled Access Policies)을 위한 포괄적인 계정 및 접근 관리(IAM / Identity and Access Management) 인터페이스가 부족하다.

### 5. 단일 노드 아키텍처 (Single Node Architecture)
SQLite 데이터베이스 및 Vision 처리는 단일 로컬 노드에서 발생한다. 중앙 집중식 서버와의 동기화가 없으므로 여러 문에 배포할 경우 완전히 독립된 사일로(Silo)로 작동하게 된다.
