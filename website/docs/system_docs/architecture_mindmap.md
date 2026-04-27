---
title: "시스템 구조 한눈에 보기"
sidebar_label: "시스템 구조 한눈에 보기"
---

## 전체 구조 마인드맵

2FA 스마트 도어락은 **하드웨어(아두이노)**와 **소프트웨어(파이썬 서버)** 두 부분으로 이루어져 있습니다. 아래 마인드맵으로 전체 구성을 한눈에 확인합니다.

```mermaid
mindmap
  root((2FA 스마트 도어락))
    하드웨어
      입력 장치
        MFRC522
          NFC 카드 읽기
        4x4 키패드
          PIN 번호 입력
      출력 장치
        릴레이
          문 열림/잠금 제어
      통신
        시리얼 9600 bps
    서버
      핵심 엔진
        main.py
          전체 흐름 조율
        vision_ai.py
          YOLOv8 얼굴 인식
      데이터베이스
        SQLite
          사용자 정보 저장
        bcrypt 해싱
          비밀번호 암호화
      웹 인터페이스
        FastAPI 대시보드
          관리자 화면
        실시간 영상
          웹캠 스트리밍
    보안 로직
      1차 인증
        NFC UID 대조
        PIN 번호 확인
      2차 인증
        YOLO 생체 감지
        얼굴 특징값 비교
      방어 기제
        락다운
          연속 실패 시 입력 차단
        안티 스푸핑
          사진 및 화면 재생 차단
```

---

## 하드웨어-소프트웨어 연결 흐름도

아두이노와 파이썬 서버가 **시리얼 통신**으로 연결되어 함께 동작하는 방식을 나타냅니다.

```mermaid
flowchart LR
    subgraph HW["하드웨어 (아두이노)"]
        NFC["MFRC522\nNFC 리더"]
        KP["4x4 키패드\nPIN 입력"]
        RLY["릴레이\n잠금 장치"]
    end

    subgraph SW["소프트웨어 (파이썬 서버)"]
        MAIN["main.py\n이벤트 수신 및 조율"]
        DB["database.py\n사용자 정보 대조"]
        AI["vision_ai.py\n얼굴 인식 2차 인증"]
        WEB["web_app.py\n관리자 대시보드"]
    end

    NFC -- "WAKEUP:NFC:UID" --> MAIN
    KP  -- "WAKEUP:PW:PIN"  --> MAIN
    MAIN --> DB
    MAIN --> AI
    AI -- "인증 성공" --> MAIN
    MAIN -- "OPEN_DOOR" --> RLY
    WEB <--> MAIN
```

---

## 구성요소 한 줄 설명

| 구성요소 | 역할 |
|---|---|
| MFRC522 | NFC 카드의 고유 번호(UID)를 읽어 서버로 전달합니다. |
| 4x4 키패드 | 사용자가 PIN 번호를 누르면 서버로 전달합니다. |
| 릴레이 | 서버로부터 허가 신호를 받으면 잠금 장치 전원을 제어합니다. |
| main.py | 시리얼 통신을 감시하며 인증 흐름 전체를 조율합니다. |
| database.py | 사용자 정보와 출입 기록을 SQLite 데이터베이스로 관리합니다. |
| vision_ai.py | YOLOv8 모델로 화면 재생을 차단하고 등록된 얼굴을 확인합니다. |
| web_app.py | FastAPI 기반 관리자 웹 화면과 API 경로를 제공합니다. |
| notifier.py | 보안 이벤트 발생 시 관리자에게 실시간으로 알림을 보냅니다. |
