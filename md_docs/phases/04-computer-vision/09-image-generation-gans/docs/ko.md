# 이미지 생성 — GAN

> 생성자와 판별자의 적대적 게임. 하나는 가짜를 만들고, 하나는 진짜와 구별합니다.

**유형:** 빌드  
**언어:** Python  
**시간:** ~90분

## 개념

- **생성자 G**: 랜덤 노이즈 → 가짜 이미지
- **판별자 D**: 진짜/가짜 분류
- **미니맥스 게임**: G는 D를 속이려 하고, D는 구별하려 함
- 문제: 모드 붕괴, 불안정한 훈련

## 주요 발전

| 모델 | 혁신 |
|------|------|
| DCGAN | CNN 기반 — 안정적 훈련 |
| WGAN | Wasserstein 거리 — 안정적 수렴 |
| StyleGAN | 스타일 기반 생성 — 고품질 얼굴 |
| CycleGAN | 쌍 없는 이미지-이미지 변환 |

## 빌드하기

```python
class Generator(nn.Module):
    def __init__(self, latent_dim=100):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 256), nn.ReLU(),
            nn.Linear(256, 512), nn.ReLU(),
            nn.Linear(512, 784), nn.Tanh()
        )
    def forward(self, z):
        return self.net(z).view(-1, 1, 28, 28)
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| 잠재 공간 | 노이즈 벡터 — 생성자의 입력 |
| 모드 붕괴 | G가 한 종류만 생성 — 다양성 상실 |