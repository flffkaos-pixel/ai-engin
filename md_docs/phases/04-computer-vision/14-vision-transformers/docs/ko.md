# 비전 트랜스포머 (ViT)

> CNN 없는 이미지 이해. 이미지를 패치로 나누고, Transformer처럼 처리합니다.

**유형:** 빌드  
**언어:** Python  
**시간:** ~75분

## 개념

- 이미지 → 겹치지 않는 패치 → 선형 임베딩 → Transformer
- CNN의 귀납적 편향 제거, 순수 attention으로 학습
- 더 많은 데이터에서 CNN 능가

## CNN vs ViT

| 특성 | CNN | ViT |
|------|-----|-----|
| 지역성 | 내장 (커널) | 학습 필요 |
| 데이터 효율 | 적은 데이터 OK | 많은 데이터 필요 |
| 확장성 | 제한적 | 뛰어남 |

## 빌드하기

```python
class ViT(nn.Module):
    def __init__(self, patch_size=16, dim=768, depth=12):
        self.patch_embed = nn.Conv2d(3, dim, patch_size, patch_size)
        self.cls_token = nn.Parameter(torch.randn(1,1,dim))
        self.pos_embed = nn.Parameter(torch.randn(1, 197, dim))
        self.transformer = nn.TransformerEncoder(...)
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| 패치 | 이미지의 작은 사각형 — Transformer의 "토큰" |
| CLS 토큰 | 분류용 특수 토큰 |