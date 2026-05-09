# 2FA 스마트 도어락: 지능형 이중 인증 시스템

SYU - Sahmyook University 디지털 논리 회로 실습 캡스톤디자인

이 저장소의 주요 문서들은 모두 [GitHub Pages](https://school-project-hwkim-dev.github.io/digital-logic-circuit/)를 통해 제공됩니다.
상세한 시스템 문서, 문제 해결, 배포 가이드 등은 웹사이트를 참고해주세요.

(기본적인 정보 및 퀵스타트는 동일하게 제공됩니다.)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Web_GUI-009688)
![YOLO](https://img.shields.io/badge/YOLO-Vision_AI-yellow)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57)

NFC/PIN 1차 인증과 YOLOv8 기반 얼굴 인식 2차 인증을 결합한 고성능 스마트 도어락 시스템입니다. 본 프로젝트는 보안의 세 가지 요소 중 '소유(NFC)', '지식(PIN)', '존재(얼굴)'를 결합하여 빈틈없는 보안 환경을 구축하는 것을 목표로 합니다.

```text
최종 승인 = (인증 수단 일치) + (생체 감지 통과) + (등록 얼굴 일치)
```

> **보안 철학:** 모든 인증 단계는 'Fail-Safe' 원칙을 따릅니다. 인공지능 모델 미로드, 카메라 연결 오류 등 시스템의 불완전한 상태가 감지되면 출입을 즉시 차단하여 잠금 상태를 유지합니다.

## 개발 및 문서 관리
* [문서 홈](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/intro)
* [초보자 정복 가이드](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/system_docs/EASY_GUIDE)
* [시스템 설계 상세](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/system_docs/system_design)
* [하드웨어 배선 및 사양](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/system_docs/hardware_spec)
* [보안 취약점 분석](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/SECURITY_ANALYSIS)
* [문제 해결 가이드](https://school-project-hwkim-dev.github.io/digital-logic-circuit/docs/TROUBLESHOOTING)
* [AI 협업 가이드 (Jules)](docs/jules-workflow.md)

## Getting Started (실행 방법)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 server/main.py
```
