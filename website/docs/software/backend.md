---
sidebar_position: 1
---

# 백엔드 아키텍처 (Backend Architecture)

백엔드(Backend)는 시스템의 권한 있는 의사 결정(Authoritative Decision-making) 컴포넌트 역할을 한다. Arduino에서 들어오는 데이터를 처리하고, Vision 모듈과 통신하며, 데이터베이스를 유지 관리한다.

## 핵심 모듈 (Core Modules)

1. **`main.py` / `app.py`:**
   - FastAPI 웹 애플리케이션을 초기화한다.
   - 웹 대시보드(Web Dashboard) 및 외부 통합을 위한 API 라우팅을 관리한다.
2. **`serial_manager.py`:**
   - Arduino와의 비동기 시리얼 통신(Asynchronous Serial Communication)을 처리한다.
   - 들어오는 UID/PIN 문자열을 구문 분석(Parsing)하여 검증 로직으로 전달한다.
   - 물리적 하드웨어가 없는 CI/CD 환경을 위해 `mock` 모드를 제공한다.
3. **`vision_ai.py`:**
   - YOLOv8 및 OpenCV 파이프라인을 관리한다.
   - 연결된 카메라에서 프레임을 캡처한다.
   - 얼굴 임베딩(Facial Embeddings)을 추출하고 등록된 프로필과 코사인 유사도 매칭(Cosine Similarity Matching)을 수행한다.
4. **`validation.py`:**
   - 2단계 인증 로직을 조율(Orchestration)한다.
   - UID 형식의 일관성을 보장한다.

## API 엔드포인트 (웹 인터페이스) (API Endpoints / Web Interface)

| 엔드포인트 (Endpoint) | 메서드 (Method) | 목적 (Purpose) |
|---|---|---|
| `/api/logs` | GET | 페이지네이션(Paginated)된 접근 로그 목록을 검색한다. |
| `/api/status` | GET | 시스템 상태 측정 항목(DB 연결, Vision 모듈 상태)을 검색한다. |
| `/api/register` | POST | NFC UID 및 초기 얼굴 스캔을 사용하여 새로운 사용자를 등록한다. |

*참고: 관리자 엔드포인트는 별도의 네트워크 수준 인증이 필요하며, 이는 이 하드웨어 프로토타입 문서의 범위를 벗어난다.*
