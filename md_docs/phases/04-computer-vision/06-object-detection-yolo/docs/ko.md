# 객체 탐지 — YOLO

> 분류는 "무엇인가?" 묻습니다. 탐지는 "어디에 무엇이 있나?" 묻습니다.

**유형:** 빌드  
**언어:** Python  
**시간:** ~90분

## 개념

- YOLO: 이미지를 그리드로 분할, 각 셀이 경계 상자 + 클래스 예측
- **IoU (Intersection over Union)**: 예측 상자와 실제 상자의 겹침 비율. >0.5 = 올바른 탐지
- **mAP**: 평균 정밀도 — 탐지 벤치마크

## 주요 모델

| 모델 | 특징 |
|------|------|
| YOLOv5/v8 | 빠름, PyTorch 네이티브 |
| Faster R-CNN | 2단계 — 영역 제안 → 분류 |
| DETR | Transformer 기반 탐지 |

## 빌드하기

```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
results = model('image.jpg')
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| IoU | 겹침 비율 — 임계값 이상 = 탐지 성공 |
| NMS | 중복 상자 제거 — 가장 높은 신뢰도만 유지 |
| mAP@0.5 | IoU 0.5에서 평균 정밀도 |