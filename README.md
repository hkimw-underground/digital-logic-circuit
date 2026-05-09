# 2FA 스마트 도어락: 지능형 이중 인증 시스템
### Sahmyook University 디지털 논리 회로 캡스톤 디자인 프로젝트

본 프로젝트는 NFC/PIN 기반의 1차 인증과 YOLOv8 얼굴 인식 기반의 2차 인증을 결합한 스마트 도어락 실험 모델이다. 보안의 3요소인 소유(NFC 카드), 지식(PIN 번호), 존재(얼굴 정보)를 계층적으로 결합하여 높은 보안 수준을 유지하도록 설계되었다.

[![Docusaurus](https://img.shields.io/badge/Documentation-GitHub_Pages-blue)](https://school-project-hwkim-dev.github.io/digital-logic-circuit/)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Web_GUI-009688)
![Arduino](https://img.shields.io/badge/Arduino-Hardware-00979D)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57)

## 📖 기술 문서 (Documentation)
상세한 시스템 설계, 하드웨어 명세 및 검증 결과는 [프로젝트 웹사이트](https://school-project-hwkim-dev.github.io/digital-logic-circuit/)에서 확인할 수 있다.

* **[서론 (Introduction)](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/intro)**: 프로젝트 배경 및 핵심 목표
* **[시스템 구조 (Architecture)](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/architecture)**: 전체 시스템 아키텍처 및 데이터 흐름
* **[하드웨어 구현 (Hardware)](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/hardware/hardware-overview)**: 부품 명세 및 회로 연결도
* **[보안 위협 분석 (Security)](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/security/threat-model)**: STRIDE 프레임워크 기반 보안 분석
* **[검증 및 테스트 (Validation)](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/validation/test-plan)**: 통합 테스트 시나리오 및 결과

## ⚙️ 핵심 설계 원칙
* **Multi-Factor Authentication**: NFC/PIN 인증과 얼굴 인식을 순차적으로 결합하여 보안성 강화
* **Fail-Secure**: 시스템 장애, 전원 차단, 모델 로드 실패 등 비정상 상태 발생 시 잠금 상태를 유지하여 물리적 보안 보장
* **실시간 가시성**: FastAPI 기반의 통합 대시보드를 통해 실시간 로그 및 카메라 피드 제공

> **인증 로직 요약:**
> `최종 승인 = (NFC/PIN 일치) && (생체 감지 통과) && (등록 얼굴 일치)`

## 🚀 시작하기 (Quick Start)

본 시스템은 Arduino와 Python 서버 간의 시리얼 통신을 통해 제어된다.

```bash
# 가상환경 구축 및 의존성 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 서버 실행 (하드웨어 미연결 시 Mock 모드 활용 가능)
python3 server/main.py
```

## ⚖️ 라이선스
이 프로젝트는 [MIT License](./LICENSE)에 따라 배포된다.
