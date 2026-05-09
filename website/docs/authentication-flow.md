---
sidebar_position: 5
---

# 인증 흐름 (Authentication Flow)

본 시스템의 2단계 인증(2FA) 프로세스는 두 개의 독립적인 검증 단계를 순차적으로 완료해야 한다. 파이프라인의 어느 지점에서든 검증에 실패하면 즉시 프로세스가 중단되고, 실패 시도가 기록되며, 릴레이(Relay)는 잠금 상태를 유지한다.

## 검증 파이프라인 (Verification Pipeline)

<div style={{ textAlign: 'center', margin: '2rem 0' }}>
  <svg width="800" height="450" viewBox="0 0 800 450" xmlns="http://www.w3.org/2000/svg" style={{ border: '1px solid #e2e8f0', borderRadius: '8px', backgroundColor: '#f8fafc' }}>
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#1e3a8a" />
      </marker>
      <marker id="arrow-red" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#e11d48" />
      </marker>
      <marker id="arrow-green" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#059669" />
      </marker>
    </defs>

    <rect x="50" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="100" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">사용자</text>

    <rect x="200" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="250" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">Arduino</text>

    <rect x="350" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="400" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">Backend</text>

    <rect x="500" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="550" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">Vision AI</text>

    <rect x="650" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="700" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">Database</text>

    <line x1="100" y1="60" x2="100" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />
    <line x1="250" y1="60" x2="250" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />
    <line x1="400" y1="60" x2="400" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />
    <line x1="550" y1="60" x2="550" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />
    <line x1="700" y1="60" x2="700" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />

    <line x1="100" y1="90" x2="245" y2="90" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="175" y="80" textAnchor="middle" fill="#334155" fontSize="12">1. NFC 태그 또는 PIN 입력</text>

    <line x1="250" y1="110" x2="395" y2="110" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="325" y="100" textAnchor="middle" fill="#334155" fontSize="12">2. Serial 데이터 전송</text>

    <line x1="400" y1="130" x2="695" y2="130" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="550" y="120" textAnchor="middle" fill="#334155" fontSize="12">3. 인증 정보 조회 (Query)</text>

    <line x1="700" y1="150" x2="405" y2="150" stroke="#1e3a8a" strokeWidth="2" strokeDasharray="2" markerEnd="url(#arrow)" />
    <text x="550" y="145" textAnchor="middle" fill="#334155" fontSize="12">4. 1차 인증 성공 (UID/Hash 일치)</text>

    <line x1="400" y1="180" x2="545" y2="180" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="475" y="170" textAnchor="middle" fill="#334155" fontSize="12">5. 얼굴 인식 요청</text>

    <line x1="550" y1="200" x2="105" y2="200" stroke="#1e3a8a" strokeWidth="2" strokeDasharray="2" markerEnd="url(#arrow)" />
    <text x="325" y="195" textAnchor="middle" fill="#334155" fontSize="12">6. 카메라 프레임 캡처</text>

    <line x1="550" y1="230" x2="405" y2="230" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="475" y="225" textAnchor="middle" fill="#334155" fontSize="12">7. 대조 결과 반환</text>

    <rect x="90" y="250" width="620" height="70" fill="#ecfdf5" stroke="#059669" strokeWidth="1" />
    <text x="95" y="265" fill="#059669" fontWeight="bold" fontSize="12">일치 시 (Match Success)</text>

    <line x1="400" y1="280" x2="695" y2="280" stroke="#059669" strokeWidth="2" markerEnd="url(#arrow-green)" />
    <text x="550" y="275" textAnchor="middle" fill="#059669" fontSize="12">8a. 성공 로그 기록 (EVENT_SUCCESS)</text>

    <line x1="400" y1="305" x2="255" y2="305" stroke="#059669" strokeWidth="2" markerEnd="url(#arrow-green)" />
    <text x="325" y="300" textAnchor="middle" fill="#059669" fontSize="12">9a. 잠금 해제 명령 전송 (UNLOCK)</text>

    <rect x="90" y="330" width="620" height="70" fill="#fff1f2" stroke="#e11d48" strokeWidth="1" />
    <text x="95" y="345" fill="#e11d48" fontWeight="bold" fontSize="12">불일치 시 (Match Failed)</text>

    <line x1="400" y1="360" x2="695" y2="360" stroke="#e11d48" strokeWidth="2" markerEnd="url(#arrow-red)" />
    <text x="550" y="355" textAnchor="middle" fill="#e11d48" fontSize="12">8b. 2차 인증 실패 기록 (FAILURE_AUTH2)</text>

    <line x1="400" y1="385" x2="255" y2="385" stroke="#e11d48" strokeWidth="2" markerEnd="url(#arrow-red)" />
    <text x="325" y="380" textAnchor="middle" fill="#e11d48" fontSize="12">9b. 거부 명령 전송 (DENY)</text>

  </svg>
</div>

## 예외 처리 정책 (Failure Handling Policies)

본 시스템은 **Fail-Secure**(장애 시 보안 유지) 원칙에 따라 설계되었다.

1. **NFC / PIN 인증 실패:**
   - NFC UID가 등록되지 않았거나 PIN 해시가 일치하지 않는 경우, 시스템은 `PRIMARY_AUTH_FAILED` 이벤트를 기록한다. 이 단계에서 실패하면 Vision AI 모듈은 호출되지 않는다.
2. **얼굴 인식(Face Verification) 실패:**
   - 유효한 1차 인증 수단이 제공되었더라도 카메라가 얼굴을 감지하지 못하거나, 여러 얼굴이 감지되어 인증 대상이 모호한 경우, 또는 감지된 얼굴이 해당 UID의 등록된 프로필과 일치하지 않는 경우 시스템은 `SECONDARY_AUTH_FAILED` 이벤트를 기록한다.
3. **하드웨어 및 타임아웃 오류:**
   - Backend와 Arduino 간의 연결이 끊어지거나 Vision 모듈에서 타임아웃이 발생하는 경우, Backend는 예외를 처리하고 `SYSTEM_ERROR`를 기록한다. Arduino는 잠금 해제를 위해 Backend로부터 명시적인 승인 명령을 받아야 하며, 별도의 명령이 없으면 릴레이는 잠긴 상태를 유지한다.
