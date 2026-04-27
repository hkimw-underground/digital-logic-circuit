---
sidebar_position: 2
---

# AI 지원 워크플로우 (AI-Assisted Workflow)

이 실험적 프로토타입의 개발 수명 주기(Development Lifecycle) 동안 대규모 언어 모델(LLM / Large Language Models)이 엔지니어링 보조 도구로 활용되었다. 이 문서는 AI 도구가 표준 개발 워크플로우에 어떻게 통합되었는지 간략히 설명한다.

## AI 지원의 적용 (Applications of AI Assistance)

1. **빠른 프로토타이핑 / 보일러플레이트 생성 (Rapid Prototyping / Boilerplate Generation):**
   FastAPI 웹 서버 라우팅 및 React/Docusaurus 프론트엔드 구성을 위한 표준 보일러플레이트(Boilerplate) 코드를 생성하는 데 AI 모델이 사용되었다. 이를 통해 초기 설정 속도를 높였다.

2. **하드웨어 인터페이스 지침 (Hardware Interfacing Guidance):**
   LLM은 C++ MFRC522 SPI 라이브러리 및 Keypad 매트릭스 스캐닝을 위한 참조 구현(Reference Implementation)을 제공했으며, 이후 프로토타입의 특정 핀 아웃(Pinout)에 맞게 다듬어지고 적용되었다.

3. **문서 구조화 (Documentation Structuring):**
   원시 엔지니어링 노트(Raw engineering notes)를 구조화된 마크다운 문서로 포맷팅하고, 아키텍처에 대한 자연어 설명을 기반으로 다이어그램 구문을 생성하는 데 AI 도구가 지원되었다.

## 워크플로우 통합 가이드라인 (Workflow Integration Guidelines)

코드 품질과 보안을 유지하기 위해 다음 가이드라인을 엄격하게 준수했다.
- **제로 트러스트 검토 (Zero-Trust Review):** AI가 생성한 모든 코드는 수동 코드 리뷰(Manual code review) 및 로컬 단위 테스트(Local unit testing)를 거쳤다.
- **아키텍처 권한 (Architectural Authority):** 핵심 아키텍처 결정(예: 동기식 vs 비동기식 처리, 데이터베이스 스키마 설계)은 인간 엔지니어가 내렸으며, AI는 오직 구현 실행을 위해서만 엄격하게 사용되었다.
- **보안 원시 요소 (Security Primitives):** 암호화 작업(예: `bcrypt`를 통한 PIN 해싱)은 AI의 제안에만 의존하지 않고 업계 모범 사례를 기반으로 수동으로 검증되었다.
