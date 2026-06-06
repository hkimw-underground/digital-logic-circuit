# YOLO + Vulkan Experiment (Isolated)

목표: Ryzen 4500U + Vulkan 환경에서 YOLOv8s 이상 모델을 ONNX Runtime + Vulkan EP로 돌리는 완전한 파이프라인 구축 및 검증.

## 폴더 구조
- `requirements.txt`
- `download_model.py` — YOLOv8s.pt 다운로드
- `export_onnx.py` — ONNX 변환 (Vulkan-friendly)
- `infer_vulkan.py` — Vulkan EP 강제 사용 + 검증 + 벤치마크
- `README.md`

## 최종 시스템 (Liveness + 512-dim Embedding)

### 1. Liveness 테스트
```bash
python video_liveness.py --video face_samples/face_sample_01.mp4 --imgsz 384
```

### 2. Embedding 업그레이드 (512차원 ArcFace ONNX)
```bash
# 1. ArcFace ONNX 모델 다운로드
python download_arcface_onnx.py

# 2. 등록 (이미지 → 512-dim embedding)
python arcface_enroll.py --image my_face.jpg --model models/arcface.onnx --output enrolled.npy

# 3. 인증 (liveness + 512-dim ArcFace)
python arcface_verify.py --video my_video.mp4 --enrolled enrolled.npy \
    --yolo-model models/yolov8m.pt --arcface-model models/arcface.onnx
```

- Liveness: MediaPipe EAR (blink detection)
- Embedding: ArcFace ONNX (512-dim, cosine similarity)
- 최대 4초 처리 시간 (liveness 중심)
```

## Vulkan EP 사용 확인 방법

`infer_vulkan.py` 실행 시 아래 로그가 나오면 성공:

```
Available providers: ['VulkanExecutionProvider', 'CPUExecutionProvider']
Using VulkanExecutionProvider
Inference time: XXX ms
```

Vulkan이 없으면 자동으로 CPU로 fallback되며 경고 출력.

## 주의사항

- 4500U Vega iGPU에서 Vulkan EP가 실제로 활성화되는지 확인 필요
- ONNX Runtime 1.17+ 에서 Vulkan EP 지원이 개선됨
- 모델은 YOLOv8s 기준 (v8n보다 3~4배 무거움)
