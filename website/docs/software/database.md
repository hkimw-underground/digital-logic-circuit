---
sidebar_position: 2
---

# 데이터베이스 설계 (Database Design)

이 시스템은 네트워크 의존성 없는 독립적인 작동과 데이터 무결성을 보장하기 위해 내장형 SQLite 데이터베이스를 사용한다. 캡스톤 프로젝트의 특성상 별도의 데이터베이스 서버 없이도 로컬 환경에서 안정적인 인증 로그 기록과 사용자 관리가 가능하도록 설계되었다.

## 데이터베이스 구성 및 설정

시스템 안정성과 동시성 제어를 위해 다음과 같은 기술적 설정을 적용한다.

- **WAL (Write-Ahead Logging) 모드**: 인증 루프가 로그를 기록하는 동안 웹 대시보드에서 지연 없이 데이터를 읽을 수 있도록 동시 읽기/쓰기 성능을 최적화한다.
- **Foreign Key 제약 조건**: `access_logs`와 `users` 테이블 간의 참조 무결성을 유지한다.
- **Busy Timeout**: 다중 스레드 환경에서 데이터베이스 잠금 경합 시 최대 20초까지 대기하여 오류 발생을 최소화한다.

## 테이블 정의

### 1. `users` (사용자 정보)

등록된 사용자의 식별 정보와 인증 자격 증명을 저장한다.

| 컬럼명 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | 시스템 내부 고유 식별자 (Auto-increment) |
| `username` | TEXT | NOT NULL | 사용자 표시 이름 및 고유 식별자 |
| `nfc_uid` | TEXT | UNIQUE | 정규화된 NFC 카드 UID |
| `password` | TEXT | | Bcrypt로 해시 처리된 PIN/비밀번호 |
| `face_encoding` | BLOB | | 사용자의 얼굴 특징점 벡터 배열 (Serialized) |

### 2. `access_logs` (출입 및 인증 로그)

모든 인증 시도와 시스템 활동에 대한 감사 추적(Audit Trail) 정보를 저장한다.

| 컬럼명 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | 로그 항목 고유 식별자 |
| `user_id` | INTEGER | FOREIGN KEY | `users.id` 참조 (탈퇴 시 NULL 유지) |
| `timestamp` | DATETIME | | 이벤트 발생 시각 (ISO 8601 형식) |
| `method` | TEXT | | 인증 수단 (NFC, PIN, FACE 등) |
| `status` | TEXT | NOT NULL | 인증 결과 상태 (SUCCESS, FAIL 등) |
| `snapshot` | BLOB | | 인증 실패 또는 보안 이벤트 발생 시 촬영된 사진 |

## 인덱스 (Indexes)

조회 성능 향상을 위해 주요 검색 필드에 인덱스를 생성한다.

- `idx_access_logs_user_id`: 특정 사용자의 출입 기록 조회 최적화
- `idx_access_logs_timestamp`: 시간 범위 기반 로그 검색 최적화
- `idx_access_logs_status_id`: 인증 상태별 로그 필터링 성능 향상

## 데이터 보안 및 보호

- **비밀번호 해싱**: 사용자 PIN 및 비밀번호는 `bcrypt` 알고리즘을 사용하여 솔팅(Salting) 및 해싱 후 저장된다. 평문 비밀번호는 절대 저장되지 않는다.
- **파일 권한 관리**: 데이터베이스 파일(`.db`) 및 로그 파일(`.db-wal`, `.db-shm`)은 시스템 소유자만 접근할 수 있도록 `0o600` (Owner Read/Write) 권한으로 강제 설정된다.
- **백업 전략**: 시스템은 데이터 유실 방지를 위해 정기적인 데이터베이스 백업 기능을 지원하며, 백업 파일 역시 동일한 보안 권한을 상속받는다.
