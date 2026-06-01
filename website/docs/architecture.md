---
sidebar_position: 4
---

# 시스템 아키텍처 (System Architecture)

본 2FA 스마트 도어락 시스템은 하드웨어 제어, 백엔드 로직, 데이터 저장소 및 Vision AI 모듈이 유기적으로 결합된 구조로 설계되었다.

## 아키텍처 개요 (Architecture Overview)

전체 시스템은 크게 사용자 인터페이스를 담당하는 하드웨어 레이어, 인증 로직을 처리하는 백엔드 서버 레이어, 그리고 상태를 모니터링하는 웹 대시보드로 구성된다.

<div style={{ textAlign: 'center', margin: '2rem 0' }}>
  <svg width="800" height="400" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" style={{ border: '1px solid #e2e8f0', borderRadius: '8px', backgroundColor: '#f8fafc' }}>
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#1e3a8a" />
      </marker>
    </defs>

    {/* 하드웨어 레이어 */}
    <rect x="50" y="50" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="125" y="85" textAnchor="middle" fill="#0f172a" fontWeight="bold">하드웨어 입력</text>
    <text x="125" y="105" textAnchor="middle" fill="#334155" fontSize="12">NFC Reader &amp; Keypad</text>

    {/* Arduino */}
    <rect x="50" y="180" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="125" y="215" textAnchor="middle" fill="#0f172a" fontWeight="bold">마이크로컨트롤러</text>
    <text x="125" y="235" textAnchor="middle" fill="#334155" fontSize="12">Arduino (Serial)</text>

    {/* Lock */}
    <rect x="50" y="300" width="150" height="50" rx="8" fill="#ffffff" stroke="#e11d48" strokeWidth="2" />
    <text x="125" y="330" textAnchor="middle" fill="#0f172a" fontWeight="bold">서보 / 도어락</text>

    {/* 백엔드 레이어 */}
    <rect x="325" y="180" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="400" y="215" textAnchor="middle" fill="#0f172a" fontWeight="bold">백엔드 서버</text>
    <text x="400" y="235" textAnchor="middle" fill="#334155" fontSize="12">Python FastAPI</text>

    {/* Vision 레이어 */}
    <rect x="600" y="50" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="675" y="85" textAnchor="middle" fill="#0f172a" fontWeight="bold">Vision 모듈</text>
    <text x="675" y="105" textAnchor="middle" fill="#334155" fontSize="12">YOLOv8 / OpenCV</text>

    {/* DB 레이어 */}
    <rect x="600" y="180" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="675" y="215" textAnchor="middle" fill="#0f172a" fontWeight="bold">데이터베이스</text>
    <text x="675" y="235" textAnchor="middle" fill="#334155" fontSize="12">SQLite</text>

    {/* 웹 대시보드 */}
    <rect x="600" y="300" width="150" height="50" rx="8" fill="#ffffff" stroke="#059669" strokeWidth="2" />
    <text x="675" y="330" textAnchor="middle" fill="#0f172a" fontWeight="bold">웹 대시보드</text>

    {/* 연결선 */}
    <path d="M 125 130 L 125 180" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 125 260 L 125 300" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 200 220 L 325 220" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 325 200 L 200 200" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />

    <path d="M 400 180 L 400 90 L 600 90" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 475 220 L 600 220" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 400 260 L 400 325 L 600 325" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />

  </svg>
</div>

## 구성 요소별 역할 (Component Responsibilities)

| 모듈 | 역할 및 책임 | 주요 기술 |
|---|---|---|
| **마이크로컨트롤러** | NFC 및 키패드 하드웨어 상태를 폴링(Polling)하고, 원시 입력을 Serial 통신으로 백엔드에 전달한다. 서버의 명령에 따라 서보와 부저를 제어한다. | Arduino UNO R4 WiFi, C++ |
| **백엔드 API** | 전체 인증 흐름을 제어한다. 1차 인증(NFC/PIN) 확인 후 Vision 모듈을 호출하며, 최종 승인 시 Arduino에 잠금 해제 명령을 전송한다. | Python, FastAPI, PySerial |
| **Vision 모듈** | 카메라로부터 프레임을 캡처하여 얼굴을 탐지하고, 등록된 사용자 프로필과 비교하여 2차 인증을 수행한다. YOLOv8 모델을 사용하여 실시간 추론을 수행한다. | OpenCV, YOLOv8 |
| **데이터베이스** | 사용자 자격 증명(해싱된 PIN, NFC UID) 및 수정 불가능한(Immutable) 출입 로그를 안전하게 저장한다. | SQLite |
| **웹 프런트엔드** | 시스템의 현재 상태, 인증 결과 요약 및 실시간 헬스 체크 지표를 시각화하여 제공한다. | React, Docusaurus |

## 데이터 및 제어 흐름 (Data vs Control Flow)

**데이터 흐름 (Data Flow):**
1. **입력 데이터**: 하드웨어에서 발생한 원시 데이터(UID, 키 입력)가 Arduino를 거쳐 백엔드로 전달된다.
2. **이미지 처리**: 백엔드는 1차 인증 성공 시 Vision 모듈을 활성화한다. Vision 모듈은 서버 내부에서 카메라 프레임을 처리하며, YOLOv8을 통해 얼굴의 특징점을 추출하고 저장된 데이터와 대조한다.
3. **결과 기록**: 인증의 모든 성공 및 실패 결과는 SQLite 데이터베이스에 로그 형태로 영구 저장된다.

**제어 흐름 (Control Flow):**
1. **중앙 집중식 의사결정**: Arduino는 독자적인 출입 결정 권한이 없으며, 모든 결정은 백엔드 서버에서 수행된다.
2. **명령 하사**: 모든 인증 단계가 통과된 경우에만 백엔드에서 `OPEN_DOOR` Serial 명령을 Arduino에 전송한다.
3. **하드웨어 실행**: Arduino는 수신된 명령에 따라 SG-90 서보를 열림 각도로 이동시킨다. 이는 소프트웨어 장애 시에도 잠금 상태를 유지하는 Fail-Secure 설계를 보장한다.

## 데이터 흐름도 (Data Flow Diagram)

<div style={{ textAlign: 'center', margin: '2rem 0' }}>
  <svg width="700" height="200" viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" style={{ border: '1px solid #e2e8f0', borderRadius: '8px', backgroundColor: '#f8fafc' }}>
    <defs>
      <marker id="df-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#1e3a8a" />
      </marker>
    </defs>

    <rect x="50" y="80" width="100" height="40" rx="8" fill="#e2e8f0" stroke="#1e3a8a" strokeWidth="1" />
    <text x="100" y="105" textAnchor="middle" fill="#0f172a" fontSize="12">하드웨어</text>

    <rect x="300" y="80" width="100" height="40" rx="8" fill="#1e3a8a" />
    <text x="350" y="105" textAnchor="middle" fill="#ffffff" fontSize="12">FastAPI 백엔드</text>

    <rect x="550" y="80" width="100" height="40" rx="8" fill="#e2e8f0" stroke="#1e3a8a" strokeWidth="1" />
    <text x="600" y="105" textAnchor="middle" fill="#0f172a" fontSize="12">SQLite 로그</text>

    {/* 순방향 흐름 */}
    <path d="M 150 90 L 300 90" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#df-arrow)" />
    <text x="225" y="80" textAnchor="middle" fill="#334155" fontSize="10">UID/PIN 입력</text>

    {/* 역방향 흐름 */}
    <path d="M 300 110 L 150 110" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#df-arrow)" />
    <text x="225" y="125" textAnchor="middle" fill="#334155" fontSize="10">OPEN_DOOR 명령</text>

    {/* 로그 흐름 */}
    <path d="M 400 100 L 550 100" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#df-arrow)" />
    <text x="475" y="90" textAnchor="middle" fill="#334155" fontSize="10">로그 영구 저장</text>
  </svg>
</div>
