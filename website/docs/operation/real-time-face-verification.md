# 실시간 얼굴 인증 (Blink + ArcFace) 구현 현황

## 개요
이 문서는 2025년 4월 기준으로 동작하는 **실시간 blink 감지 + 512-dim ArcFace** 2차 인증 파이프라인의 최종 상태를 정리한 것이다.

- 1차 인증: NFC / PIN (Arduino)
- 2차 인증: ESP32-CAM 실시간 프레임 → MediaPipe FaceMesh (blink) + ArcFace ONNX (얼굴 일치)

## 핵심 수정 사항 (문제 해결 이력)

### 1. protobuf 필드명 오류 (가장 치명적)
```python
# 잘못된 코드 (AttributeError 발생 → 조용히 무시됨)
lm = results.multi_face_landmarks[0].landmarks

# 수정 후
lm = results.multi_face_landmarks[0].landmark
```
- 이 한 줄 때문에 `landmark_frames=22`가 나와도 EAR/ArcFace 코드가 전혀 실행되지 않았다.
- `except Exception: pass`에 완전히 삼켜져 로그조차 남지 않음.

### 2. MediaPipe FaceMesh 설정 (저화질 ESP32-CAM 대응)
```python
mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,           # tracking 대신 매 프레임 재검출
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)
```
- `static_image_mode=False`에서는 CIF 해상도에서 tracking이 즉시 끊겼음.

### 3. Blink 감지 로직 강화
- EAR 임계값: close 0.22 / open 0.26
- 연속 프레임 조건: `consecutive_below >= 1`
- 10초 타임아웃 내에 blink 1회 + sim ≥ 0.55 만족 시 즉시 통과

### 4. ArcFace 유사도 임계값
- 0.60 → **0.55**로 완화 (단일 인코딩 + 실제 조명 환경 고려)

### 5. Lockdown 실패 카운트 초기화
성공적으로 문이 열리면 (`OPEN_DOOR` 전송 시점) `recent_failure_count = 0`으로 초기화.

## 현재 동작 흐름 (성공 사례)

```
NFC 태그 인식
→ [AUTH] 김현우 verified via NFC. Running face check...
→ [SERVER -> ARDUINO] 1ST_SUCCESS
→ Real-time face verification started...
→ Face detected by MediaPipe.
→ EAR=0.27x (blink=False)
→ ArcFace sim=0.89x (best=0.895)
→ Blink detected!
→ ArcFace sim=0.905 (best=0.895)
→ SUCCESS (blink + ArcFace sim=0.905)
→ [AUTH] Face check passed. Opening door for 김현우.
→ [SERVER -> ARDUINO] OPEN_DOOR
→ recent_failure_count = 0 (초기화)
```

## 사용된 모델 및 환경

- **ArcFace**: `yolo_vulkan_test/models/arcface.onnx` (512-dim)
- **MediaPipe**: 0.10.14 (FaceMesh, refine_landmarks=True)
- **ESP32-CAM**: FRAMESIZE_CIF @ 921600 baud
- **Python**: 3.12 + ONNX Runtime (CPU)

## 알려진 한계

- ESP32-CAM CIF 해상도에서는 MediaPipe가 얼굴을 잡는 프레임 수가 제한적이다.
- 조명 변화가 심하거나 얼굴이 너무 작으면 blink 감지가 늦어질 수 있음.
- 단일 인코딩만 등록된 상태이므로, 등록 당시와 다른 조명/각도에서는 sim이 낮게 나올 수 있음.

## 다음에 수정이 필요할 때 확인할 파일

- `server/vision_ai.py` — `verify_face_liveness_arcface()` 함수
- `server/main.py` — `handle_wakeup()` 내 성공/실패 처리
- `server/database.py` — `password` 컬럼 (PIN 해시 저장)

---

**검증 일시**: 2025-04 (실제 하드웨어에서 NFC → 문 열림까지 전체 흐름 확인 완료)
**작성자**: hwkim
