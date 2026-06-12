# 이미지 기초 — 픽셀, 채널, 색 공간

> 이미지는 빛 샘플의 텐서입니다. 모든 비전 모델은 이 한 가지 사실에서 시작합니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Phase 3
**시간:** ~45분

## 개념

### 이미지 = 텐서

- **그레이스케일**: (H, W) 또는 (H, W, 1)
- **RGB**: (H, W, 3) — R, G, B 채널
- **RGBA**: (H, W, 4) — 투명도 추가
- **배치**: (B, C, H, W) PyTorch / (B, H, W, C) TensorFlow

### 색 공간

| 공간 | 채널 | 용도 |
|------|------|------|
| RGB | Red, Green, Blue | 기본값 — 디스플레이 |
| HSV | Hue, Sat, Value | 색상 기반 세분화 |
| Lab | Lightness, a*, b* | 지각적 균일 — 차이 측정 |
| YCbCr | Luma, Chroma | 비디오 압축 |

### 기본 연산

- 정규화: [0,255] → [0,1] 또는 평균 0, std 1
- 크기 조정, 자르기, 뒤집기, 회전
- 채널별 평균/std 계산

## 빌드하기

```python
from PIL import Image
img = np.array(Image.open('photo.jpg'))  # (H, W, 3)
normalized = img.astype(np.float32) / 255.0
mean = normalized.mean(axis=(0,1))  # 채널별 평균
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 채널 | 이미지의 한 색상 차원 |
| 정규화 | [0,255]→[0,1] — 모델 입력 준비 |
| PIL | Python Imaging Library — 이미지 I/O |