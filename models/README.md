# 영상 모델 파일

실제 사용 전에 YOLO nano 모델 파일을 이 디렉터리에 둔다.

기본 경로:

```text
models/doorlock_yolov8n.pt
```

감지 이름은 환경변수로 조정할 수 있다.

- `DOORLOCK_YOLO_FACE_CLASSES`: 얼굴 감지 이름
- `DOORLOCK_YOLO_PHONE_CLASSES`: 출입을 차단할 휴대폰, 화면, 태블릿, 노트북, 모니터 이름
- `DOORLOCK_YOLO_OPEN_EYE_CLASSES`: 열린 눈 이름
- `DOORLOCK_YOLO_CLOSED_EYE_CLASSES`: 감긴 눈 이름

학습된 모델 파일은 용량이 크고 환경에 따라 달라지므로 저장소에 포함하지 않는다.
