# 잠재 Diffusion & Stable Diffusion

> 512×512 이미지의 픽셀 공간 diffusion은 계산적 전쟁 범죄이다. Rombach et al. (2022)은 이미지를 생성하기 위해 모든 786k 차원이 필요하지 않다는 것을 알아챘다 — 의미론적 구조를 포착하기에 충분하고 나머지를 위한 별도의 decoder가 필요하다. VAE의 잠재 공간에서 diffusion을 실행한다. 그 하나의 아이디어가 Stable Diffusion이다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 8 · 02 (VAE), Phase 8 · 06 (DDPM), Phase 7 · 09 (ViT)
**소요 시간:** ~75분

## 문제

512²에서 픽셀 공간 diffusion은 U-Net이 shape `[B, 3, 512, 512]`의 텐서에서 실행됨을 의미한다. 각 샘플링 단계는 500M-param U-Net에 대해 ~100 GFLOPS이다. 50단계는 이미지당 5 TFLOPS이다. 10억 개의 이미지로 교육하면 계산 청구서가 터무니없다.

이러한 FLOP의 대부분은 손실 VAE가 압축할 수 있는 고주파 텍스처를 net을 통해 푸시하는 데 소비된다 — 이는 perceptual하게 중요하지 않다. Rombach의 아이디어: VAE를 한 번 교육하고 (첫 번째 단계), 동결하고, diffusion을 entirely 4채널 64×64 잠재 공간 (두 번째 단계)에서 실행한다. 동일한 U-Net. 픽셀의 1/16. 품질 비교를 위해 ~64x 더 적은 FLOP.

이것이 Stable Diffusion 레시피이다. SD 1.x / 2.x는 `64×64×4` 잠재에서 860M U-Net을 사용하고, SDXL은 `128×128×4`에서 2.6B U-Net을 사용하고, SD3은 flow matching과 함께 U-Net을 Diffusion Transformer (DiT)로 교체했다. Flux.1-dev (Black Forest Labs, 2024)는 12B-param DiT-MMDiT를 제공한다. 모두 동일한 2단계 기질에서 실행된다.

## 개념

![잠재 diffusion: VAE 압축 + 잠재 공간에서 diffusion](../assets/latent-diffusion.svg)

**두 단계, separately 교육.**

1. **단계 1 — VAE.** Encoder `E(x) → z`, decoder `D(z) → x`. 목표 압축: 각 공간 축에서 8× 다운샘플 + 총 잠재 크기가 픽셀 수의 ~1/16이 되도록 채널 조정. 손실 = 재구성 (L1 + LPIPS perceptual) + KL (z가 정확히 가우시안이强制되지 않도록 작은 가중치; z에서 정확한 샘플링이 필요하지 않기 때문). often trained with an adversarial loss so decoded images are sharp.

2. **단계 2 — `z`에서 diffusion.** `z = E(x_real)`를 데이터로 처리. U-Net (또는 DiT)을 교육하여 `z_t`를 denoise한다. 추론 시: diffusion으로 `z_0`를 샘플링한 다음 `x = D(z_0)`.

**텍스트 조건.** 두 개의 추가 구성 요소. 동결된 텍스트 인코더 (SD 1.x의 경우 CLIP-L, SD 2/XL의 경우 CLIP-L+OpenCLIP-G, SD3 및 Flux의 경우 T5-XXL). 교차 attention 주입: 모든 U-Net 블록이 `[Q = 이미지 특징, K = V = 텍스트 토큰]`을 가져와서它们을 혼합한다. 토큰이 텍스트가 이미지에 영향을 미치는 유일한 방법이다.

**손실 함수는 Lesson 06과 동일하다.** 노이즈에 대한 동일한 DDPM / flow matching MSE. 데이터 도메인만 교환하면 된다.

## 아키텍처 변형

| 모델 | 연도 | 백본 | 잠재 형태 | 텍스트 인코더 | 매개변수 |
|-------|------|----------|--------------|--------------|--------|
| SD 1.5 | 2022 | U-Net | 64×64×4 | CLIP-L (77 토큰) | 860M |
| SD 2.1 | 2022 | U-Net | 64×64×4 | OpenCLIP-H | 865M |
| SDXL | 2023 | U-Net + refiner | 128×128×4 | CLIP-L + OpenCLIP-G | 2.6B + 6.6B |
| SDXL-Turbo | 2023 | 증류됨 | 128×128×4 | same | 1-4 단계 샘플링 |
| SD3 | 2024 | MMDiT (multimodal DiT) | 128×128×16 | T5-XXL + CLIP-L + CLIP-G | 2B / 8B |
| Flux.1-dev | 2024 | MMDiT | 128×128×16 | T5-XXL + CLIP-L | 12B |
| Flux.1-schnell | 2024 | MMDiT 증류 | 128×128×16 | T5-XXL + CLIP-L | 12B, 1-4 단계 |

추세: U-Net을 DiT로 교체 (잠재 패치에 대한 transformer), 텍스트 인코더 스케일 (T5가 프롬프트 aderherence에서 CLIP 이김), 잠재 채널 증가 (4 → 16은 더 많은 디테일 헤드룸을 제공).

## 실습

`code/main.py`는 Lesson 06의 DDPM 위에 toy 1-D "VAE" (identity encoder + decoder, demonstration용; 실제 VAE는 conv net임)를 쌓고 classifier-free guidance로 클래스 조건을 추가한다. 원시 1-D 값에서 실행하든 인코딩된 값에서 실행하든 동일한 diffusion 손실이 작동함을 보여준다 — 핵심 통찰력.

### Step 1: encoder/decoder

```python
def encode(x):    return x * 0.5          # toy "compression" to smaller scale
def decode(z):    return z * 2.0
```

실제 VAE는 훈련된 가중치를 갖는다. 교육학을 위해 이 선형 맵은 diffusion이 원래 데이터 공간을 care하지 않고 `z`에서 운영됨을 보여주기에 충분하다.

### Step 2: `z`-공간에서 diffusion

Lesson 06의 동일한 DDPM. Net이 보는 데이터는 `z = E(x)`이다. `z_0`를 샘플링한 후 `D(z_0)`로 디코딩한다.

### Step 3: classifier-free guidance

교육 중 클래스 레이블을 10% 드롭 (null 토큰으로 교체). 추론 시 `ε_cond`와 `ε_uncond`를 모두 계산한 다음:

```python
eps_cfg = (1 + w) * eps_cond - w * eps_uncond
```

`w = 0` = 가이던스 없음 (전체 다양성), `w = 3` = 기본값, `w = 7+` = 포화 / over-sharp.

### Step 4: 텍스트 조건 (개념, 코드가 아님)

클래스 레이블을 frozen 텍스트 인코더 출력으로 교체. 텍스트 임베딩을 cross-attention을 통해 U-Net에 공급:

```python
h = h + CrossAttention(Q=h, K=text_embed, V=text_embed)
```

## 활용

2026년 production 이미지 파이프라인:

| 구성 | 크기 | 용도 |
|------|------|------|
| SDXL / SD3 / Flux base | 2-12B | 품질 기반 |
| ControlNet (_DEPTH, CANNY,POSE) | 70-360MB 각 | 공간 제어 |
| LoRA (스타일, 얼굴, 제품) | 20-200MB 각 | 개인화 |
| IP-Adapter | ~20MB | 레퍼런스 이미지 스타일 |

대부분의 production 파이프라인은 2-5개의 LoRA, 1-3개의 ControlNet, SDXL / SD3 / Flux base 위에 IP-Adapter를 Layer한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| 잠재 공간 | "압축된 공간" | VAE가 원본 데이터를 표현하는 낮은 차원 공간. |
| VAE | "첫 번째 단계" | 이미지를 잠재로 압축; diffusion은 잠재에서 실행. |
| 조건부 diffusion | "제어 생성" | 텍스트, 이미지 등으로 생성 제어. |
| Classifier-free guidance | "품질 다이버시티 트레이드오프" | 조건부/무조건 예측을混合하여 품질 향상. |
| Cross-attention | "텍스트-이미지 mixing" | U-Net에서 텍스트 임베딩이 이미지 특징에 영향을 미치는 방식. |

## 추가 자료

- [Rombach et al. (2022). High-Resolution Image Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752) — Stable Diffusion.
- [Podell et al. (2023). SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis](https://arxiv.org/abs/2307.01952) — SDXL.
- [Esser et al. (2024). Scaling Rectified Flow Transformers for High-Resolution Image Synthesis](https://arxiv.org/abs/2403.03206) — Flux.