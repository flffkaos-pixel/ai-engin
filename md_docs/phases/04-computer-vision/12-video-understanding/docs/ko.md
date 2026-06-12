# 비디오 이해

> 비디오 = 이미지 시퀀스 + 시간. 같은 CNN에 시간 차원 추가.

**유형:** 빌드  
**언어:** Python  
**시간:** ~75분

## 개념

- **3D CNN**: (T, H, W, C) → 3D 커널이 시공간 패턴 학습
- **Two-Stream**: RGB (공간) + Optical Flow (시간)
- **Transformer 기반**: ViViT, TimeSformer — 공간+시간 attention

## 작업

| 작업 | 설명 |
|------|------|
| 행동 인식 | 사람이 무엇을 하는가? |
| 시간적 행동 탐지 | 언제 무엇을 하는가? |
| 비디오 캡션 | 비디오 → 텍스트 설명 |

## 빌드하기

```python
class VideoCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv3d = nn.Conv3d(3, 64, kernel_size=(3,7,7), padding=(1,3,3))
        self.pool = nn.AdaptiveAvgPool3d((1,1,1))
        self.fc = nn.Linear(64, num_classes)
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Optical Flow | 픽셀 움직임 — 명시적 시간 정보 |
| 3D Conv | 시공간 패턴 — 움직임 감지 |