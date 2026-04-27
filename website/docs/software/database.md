---
sidebar_position: 2
---

# 데이터베이스 스키마 (Database Schema)

이 시스템은 로컬 및 제로 네트워크 종속성(Zero-network-dependency) 작동을 보장하기 위해 내장형 SQLite 데이터베이스(`database.py`)를 사용한다. 데이터베이스는 인증 루프가 로그를 기록하는 동안 웹 대시보드(Web Dashboard)에서 동시 읽기(Concurrent Reads)를 지원하기 위해 WAL(Write-Ahead Logging) 모드로 작동한다.

## 테이블 (Tables)

### 1. `users`

등록된 사용자의 자격 증명을 저장한다.

| 열 (Column) | 타입 (Type) | 제약 조건 (Constraints) | 설명 (Description) |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | 고유한 내부 식별자(Identifier). |
| `name` | TEXT | NOT NULL | 표시 이름(Display name). |
| `nfc_uid` | TEXT | UNIQUE | 정규화된(Normalized) NFC 카드 UID. |
| `pin_hash` | TEXT | | Bcrypt로 해시 처리된 PIN 코드 (선택 사항). |
| `face_encoding` | BLOB | | 사용자의 얼굴에 대한 직렬화된(Serialized) 벡터 배열. |

### 2. `access_logs`

모든 시스템 활동에 대한 변경 불가능한(Immutable) 감사 추적(Audit Trail)을 제공한다.

| 열 (Column) | 타입 (Type) | 제약 조건 (Constraints) | 설명 (Description) |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | 고유한 로그 항목 ID. |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 이벤트 발생 시간. |
| `nfc_uid` | TEXT | | 제시된 UID (있는 경우). |
| `status` | TEXT | NOT NULL | 예: `SUCCESS`, `FAILURE_AUTH1`, `FAILURE_AUTH2`. |
| `reason` | TEXT | | 상세한 실패 컨텍스트 (예: "Face Mismatch"). |
