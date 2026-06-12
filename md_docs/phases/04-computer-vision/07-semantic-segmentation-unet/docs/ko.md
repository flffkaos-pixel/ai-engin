# 시맨틱 분할 — U-Net

> 분류: "이 이미지는 고양이다." 분할: "이 픽셀들이 고양이다."

**유형:** 빌드  
**언어:** Python  
**시간:** ~90분

## 개념

- **U-Net**: 인코더-디코더 + 스킵 연결. 의료 영상에서 시작, 현재 모든 분할의 기본
- 인코더: 다운샘플링하며 특징 추출
- 디코더: 업샘플링하며 픽셀 단위 예측
- 스킵 연결: 인코더 특징을 디코더로 직접 전달 → 정밀한 경계

## 빌드하기

```python
class UNet(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.enc1 = self.conv_block(in_ch, 64)
        self.enc2 = self.conv_block(64, 128)
        self.bottleneck = self.conv_block(128, 256)
        self.up2 = nn.ConvTranspose2d(256, 128, 2, 2)
        self.dec2 = self.conv_block(256, 128)  # 128+128 from skip
        self.up1 = nn.ConvTranspose2d(128, 64, 2, 2)
        self.dec1 = self.conv_block(128, 64)
        self.final = nn.Conv2d(64, out_ch, 1)
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| IoU (Jaccard) | 예측과 실제 마스크의 겹침 비율 |
| Dice 점수 | 2*|교집합|/(|A|+|B|) — 분할 평가 |