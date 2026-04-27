---
title: "시스템 설계"
sidebar_label: "전체 설계"
sidebar_position: 1
---

# 시스템 설계

이 시스템은 NFC 카드 또는 PIN 번호로 1차 인증을 하고, 웹캠과 YOLOv8 얼굴 인식으로 2차 인증을 합니다. 두 가지 인증을 모두 통과해야만 문이 열립니다.

## 시스템 블록 구성

```mermaid
flowchart TB
    subgraph HW["하드웨어 (Arduino)"]
        NFC["MFRC522 NFC 리더\n카드 UID 읽기"]
        KP["4x4 키패드\nPIN 번호 입력"]
        RLY["릴레이\n도어락 제어"]
    end

    subgraph SRV["서버 (Python)"]
        MAIN["main.py\n시리얼 수신 · 인증 조율"]
        DB["database.py\n사용자 DB · bcrypt 해싱"]
        VIS["vision_ai.py\nYOLO 얼굴 인식"]
        NTF["notifier.py\n보안 알림"]
        WEB["web_app.py\n관리자 웹 화면"]
    end

    CAM["USB 웹캠"]
    ADM["관리자 브라우저"]

    NFC -->|시리얼 9600 baud| MAIN
    KP  -->|시리얼 9600 baud| MAIN
    MAIN -->|OPEN_DOOR| RLY
    MAIN --> DB
    MAIN --> VIS
    MAIN --> NTF
    CAM --> VIS
    WEB --> DB
    ADM <-->|HTTP :8000| WEB
```

## 인증 흐름

```mermaid
sequenceDiagram
    participant U as 사용자
    participant A as Arduino
    participant S as 서버(main.py)
    participant D as DB(database.py)
    participant V as 얼굴인식(vision_ai.py)

    U->>A: NFC 카드 태그 또는 PIN 입력
    A->>S: WAKEUP:NFC:<UID> 또는 WAKEUP:PW:<PIN>

    S->>D: 1차 인증 (UID 또는 PIN 조회)
    alt 1차 인증 실패
        D-->>S: 불일치
        S->>A: (응답 없음, 잠금 유지)
    else 1차 인증 성공
        D-->>S: 사용자 정보 반환
        S->>V: 얼굴 인식 요청 (카메라 촬영)
        V->>V: YOLO 얼굴 검출 · 눈 깜빡임 확인 · 등록 얼굴 대조
        alt 2차 인증 실패
            V-->>S: 불일치 또는 이상 감지
            S->>A: (잠금 유지)
        else 2차 인증 성공
            V-->>S: 인증 통과
            S->>A: OPEN_DOOR
            A->>A: 릴레이 ON → 잠금 해제
            A->>S: DOOR_OPENED
            A->>S: DOOR_CLOSED (타이머 후 자동 잠금)
        end
    end
```

## 웹 등록 과정

관리자가 브라우저에서 신규 사용자를 등록하는 흐름입니다.

```mermaid
sequenceDiagram
    participant A as 관리자
    participant W as 웹서버(web_app.py)
    participant V as 얼굴인식(vision_ai.py)
    participant D as DB(database.py)

    A->>W: /register 페이지 접속
    W-->>A: 등록 양식 표시
    A->>W: 얼굴 촬영 요청 (/api/capture_face)
    W->>V: 카메라에서 얼굴 인코딩 추출
    V-->>W: 얼굴 데이터 반환
    W-->>A: 촬영 성공
    A->>W: 이름 · NFC UID · PIN 입력 후 제출
    W->>D: 사용자 정보 저장 (PIN은 bcrypt 해싱)
    D-->>W: 등록 완료
    W-->>A: 등록 성공 메시지
```

## 데이터베이스 구조

| 테이블 | 주요 필드 | 역할 |
|--------|-----------|------|
| `users` | `username`, `nfc_uid`, `password`, `face_encoding` | 사용자 식별 정보 및 얼굴 템플릿 저장 |
| `access_logs` | `timestamp`, `method`, `status`, `snapshot` | 출입 기록 및 침입 사진 저장 |

| 상태 값 | 의미 |
|---------|------|
| `1ST_AUTH_SUCCESS` | NFC 또는 PIN이 등록 사용자와 일치 |
| `FINAL_SUCCESS` | 얼굴 인식까지 통과, 문 열림 명령 전송 |
| `FINAL_FAIL` | 1차 인증은 통과했지만 얼굴 인식 실패 |
| `UNAUTHORIZED` | 1차 인증 단계에서 NFC 또는 PIN 불일치 |

## 시리얼 프로토콜

Arduino와 서버는 USB 시리얼(9600 baud)로 통신합니다.

| 방향 | 메시지 | 설명 |
|------|--------|------|
| Arduino → 서버 | `SYSTEM_READY` | 아두이노 부팅 완료 |
| Arduino → 서버 | `WAKEUP:NFC:<UID>` | NFC 카드 감지, UID 전달 |
| Arduino → 서버 | `WAKEUP:PW:<PIN>` | 키패드 PIN 전달 |
| 서버 → Arduino | `OPEN_DOOR` | 릴레이를 열도록 명령 |
| Arduino → 서버 | `DOOR_OPENED` | 릴레이가 열린 상태로 전환됨 |
| Arduino → 서버 | `DOOR_CLOSED` | 릴레이가 잠긴 상태로 복귀 |

## 보안 정책 요약

- **실패 시 거부**: 카메라, YOLO 모델, 얼굴 데이터 중 하나라도 없으면 문을 열지 않습니다.
- **요청 제한**: 인증 실패 후 3초간 추가 입력을 무시합니다.
- **잠금 모드**: 1시간 내 10회 이상 실패하면 입력을 5초씩 지연시킵니다.
- **눈 깜빡임 확인**: 사진 인쇄물이나 화면으로 속이는 것을 방지합니다.
- **PIN 해싱**: PIN은 bcrypt(단방향 암호화)로 변환하여 저장합니다.
