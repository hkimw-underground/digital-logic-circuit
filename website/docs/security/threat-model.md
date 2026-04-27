---
sidebar_position: 1
---

# 위협 모델 (Threat Model)

이 섹션에서는 2FA Smart Door Lock System에 대한 잠재적인 위협, 예상되는 영향, 구현된 완화 전략, 그리고 남아있는 잔여 위험에 대해 간략히 설명한다.

## 보안 매트릭스 (Security Matrix)

| 위협 행위자 / 행동 (Threat Actor / Action) | 영향 (Impact) | 완화 전략 (Mitigation Strategy) | 잔여 위험 (Remaining Risk) |
|---|---|---|---|
| **도난당한 NFC 카드를 가진 인가되지 않은 사용자** | 높음 (High). 시스템이 1차 인증을 시도한다. | 시스템은 긍정적인 2차 인증(얼굴 일치)을 요구한다. | 공격자가 사용자와 시각적으로 유사하거나(또는 고품질의 위조 메커니즘을 보유한 경우) 접근이 허용될 수 있다. |
| **PIN을 추측하는 인가되지 않은 사용자** | 높음 (High). | 2차 얼굴 일치 요구 사항으로 인해 무차별 대입 공격(Brute-force)이 방해받는다. 유효하지 않은 시도는 로깅된다. | 반복적인 사용으로 인한 키패드의 물리적 손상. |
| **제시 공격 (사진/화면 위조) (Presentation Attack / Photo/Screen Spoofing)** | 치명적 (Critical). 생체 인식 요소를 우회한다. | YOLOv8 모델 임계값(Thresholding) 설정으로 흐릿한 일치를 방지한다. | **높음 (High).** 표준 2D RGB 카메라는 깊이나 활성(Liveness)을 안정적으로 감지할 수 없다. 고해상도 태블릿 비디오가 시스템을 우회할 수 있다. |
| **시리얼 버스 변조 (Serial Bus Tampering)** | 치명적 (Critical). `UNLOCK` 명령을 주입한다. | 현재 소프트웨어에는 구현되지 않음. | **높음 (High).** 공격자가 Server와 Arduino 사이의 USB 케이블에 접근하면 일반 텍스트 시리얼 명령을 보낼 수 있다. |
| **물리적 릴레이 우회 (Physical Relay Bypass)** | 치명적 (Critical). 잠금장치를 직접 작동시킨다. | 물리적 외함(Physical enclosure) (가정됨). | **높음 (High).** 공격자가 릴레이 출력 단자를 직접 단락(Short)시키는 경우, 소프트웨어는 이를 감지하거나 방지할 수 없다. |
| **전원 차단 (Power Interruption)** | 보통 (Moderate). 서비스 거부(Denial of service). | Fail-secure 물리적 잠금 하드웨어 사용. | 기계적인 재정의(Override) 키가 제공되지 않는 한 정전 시 정당한 사용자가 들어갈 수 없다. |

## 설계 철학 (Design Philosophy)

이 시스템은 "Fail-Secure" 원칙을 고수한다. 소프트웨어 예외 발생, 하드웨어 누락(예: 카메라 연결 끊김) 또는 통신 시간 초과 시 기본적으로 거부 상태가 된다. 릴레이는 연속적이고 긍정적인 논리 경로가 성공적으로 완료되지 않는 한 비활성화된 상태를 유지한다.
