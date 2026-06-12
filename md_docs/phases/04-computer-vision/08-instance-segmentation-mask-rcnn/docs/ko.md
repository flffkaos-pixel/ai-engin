# 인스턴스 분할 — Mask R-CNN

> 시맨틱: "모든 사람." 인스턴스: "사람1, 사람2, 사람3."

**유형:** 빌드  
**언어:** Python  
**시간:** ~90분

## 개념

- Faster R-CNN에 마스크 분기 추가 → 경계 상자 + 픽셀 마스크
- **RoIAlign**: RoIPool의 양자화 오류 수정 → 정확한 픽셀 정렬
- 각 탐지된 객체에 대해 바이너리 마스크 예측

## 주요 모델

| 모델 | 특징 |
|------|------|
| Mask R-CNN | 2단계 — 영역 제안 → 마스크 |
| YOLOv8-seg | 1단계 — 실시간 |
| SAM (Meta) | 프롬프트 기반 — 제로샷 분할 |

## 빌드하기

```python
import torchvision
model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=True)
model.eval()
predictions = model([image_tensor])
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| 인스턴스 | 개별 객체 식별 — 같은 클래스 다른 인스턴스 |
| RoIAlign | 정밀한 특징 정렬 — 양자화 없는 보간 |