---
sidebar_position: 1
---

# 개발 방법론 (Development Methodology)

이 부록(Appendix)에서는 2FA 프로토타입 개발 과정에서 이루어진 엔지니어링 방법론과 반복적인 의사 결정 사항들을 자세히 설명한다.

## 반복적 개발 단계 (Iterative Development Phases)

이 프로젝트는 복잡성을 분리하기 위해 순차적인 단계로 실행되었다.

### 1단계: 하드웨어 추상화 (Phase 1: Hardware Abstraction)
초기 개발은 Arduino 펌웨어에만 독점적으로 집중했다. 목표는 MFRC522 SPI 통신 및 Matrix Keypad 폴링(Polling)을 간단하고 안정적인 시리얼 인터페이스로 추상화하는 것이었다. 이를 통해 Backend는 하드웨어 장비를 블랙박스(Black-box) I/O 스트림으로 취급할 수 있게 되었다.

### 2단계: 핵심 인증 로직 (Phase 2: Core Authentication Logic)
Python Backend는 테스트 주도 개발(TDD / Test-Driven Development) 원칙을 사용하여 개발되었다. 1차 인증 스레드(Thread)를 잠그지 않고 대시보드(Dashboard)의 동시 읽기 액세스를 제공하기 위해 WAL(Write-Ahead Logging) 모드의 SQLite를 선택했다.

### 3단계: 비전 통합 (Phase 3: Vision Integration)
표준 CPU/Edge 하드웨어에서 속도와 정확도의 균형을 맞추기 위해 얼굴 추출 용도로 YOLOv8을 통합했다. 초기 구현에서는 조명이 어두운 환경에서 오탐(False Positive)이 발생하는 문제가 있었으나, 엄격한 신뢰도 임계값(Confidence Threshold)을 구현하고 최소 경계 상자(Bounding-box) 크기를 강제함으로써 완화했다.

### 4단계: 시스템 통합 (Phase 4: System Integration)
마지막 단계에서는 Serial Manager를 Vision 파이프라인에 연결했다. 가장 큰 과제는 Vision 모듈이 CPU를 차단(Block)하는 동안 비동기 시리얼 시간 초과(Asynchronous Serial Timeouts)를 관리하는 것이었다. 이는 시리얼 리스너(Serial Listener)를 전용 백그라운드 스레드로 분리(Decoupling)하여 해결했다.
