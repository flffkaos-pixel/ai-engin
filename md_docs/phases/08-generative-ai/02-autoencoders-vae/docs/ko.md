# Autoencoders & Variational Autoencoders (VAE)

> Plain autoencoder는 압축 후 재구성한다. 그것은 memorizes한다. 생성하지 않는다. 하나의 트릭을 추가한다 — code가 Gaussian처럼 보이도록 강제 — 그리고 sampler를 얻는다. 그 단일 트릭, `z = μ + σ·ε`의 reparameterization이 2026년에 사용하는 모든 latent-diffusion 및 flow-matching 이미지 모델의 입력에 VAE가 있는 이유이다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 3 · 02 (Backprop), Phase 3 · 07 (CNNs), Phase 8 · 01 (Taxonomy)
**소요 시간:** ~75분

## 문제

784픽셀 MNIST 숫자를 16숫자 코드로 압축한 다음 재구성한다. Plain autoencoder는 재구성 MSE를 완벽히 수행하지만 코드 공간은 울퉁불퉁한 엉망이다. 코드 공간에서 무작위 지점을 선택하고 decode하면 노이즈가 된다. 그것은 샘플러가 없다. 그것은 生成 模型으로 위장한 압축 모델이다.

실제로 원하는 것: (a) 코드 공간이 샘플링할 수 있는 깔끔하고 부드러운 분포이다 — 예를 들어 isotropic Gaussian `N(0, I)`, (b) 모든 샘플을 decoding하면 그럴듯한 숫자가 생성되고, (c) encoder와 decoder가 여전히 잘 압축한다. 세 가지 목표, 하나의 아키텍처, 하나의 손실.

Kingma의 2013 VAE는 encoder가 분포 `q(z|x) = N(μ(x), σ(x)²)`를 출력하도록 교육하고, KL 페널티를 통해 사후 분포를 사전 `N(0, I)`로 당기고, decoding하기 전에 `q(z|x)`에서 `z`를 샘플링하여解决这个问题한다. 추론 시: encoder를 드롭하고, `z ~ N(0, I)`를 샘플링하고, decode한다. KL 페널티가 코드 공간이 구조화되도록 강제한다.

2026년 VAE는 단독으로出货很少 — 원시 이미지 품질에서 diffusion이 능가했지만, 모든 latent-diffusion 모델 (SD 1/2/XL/3, Flux, AudioCraft)의 encoder이다. VAE를 학습하면 사용하는 모든 이미지 파이프라인의 보이지 않는 첫 번째 레이어를 학습한다.

## 개념

![Autoencoder vs VAE: reparameterization 트릭](../assets/vae.svg)

**Autoencoder.** `z = encoder(x)`, `x̂ = decoder(z)`, loss = `||x - x̂||²`. 코드 공간 unstructured.

**VAE encoder.** 두 벡터 출력: `μ(x)`와 `log σ²(x)`. 이것들은 `q(z|x) = N(μ, diag(σ²))`를 정의한다.

**Reparameterization 트릭.** `q(z|x)`에서 샘플링하는 것은 미분 가능하지 않다. 샘플을 `z = μ + σ·ε` where `ε ~ N(0, I)`로 다시 작성한다. 이제 `z`는 `(μ, σ)`의 결정론적 함수 plus non-parameter 노이즈이다 — gradient가 `μ`와 `σ`를 통해 흐른다.

**손실.** Evidence Lower BOund (ELBO), 두 항:

```
loss = reconstruction + β · KL[q(z|x) || N(0, I)]
     = ||x - x̂||²  + β · Σ_i ( σ_i² + μ_i² - log σ_i² - 1 ) / 2
```

재구성이 `x̂`를 `x`로 밀어붙인다. KL이 `q(z|x)`를 사전으로 밀어붙인다. 그들은 trade한다. 작은 β (<1) = 더 선명한 샘플, 코드 공간이 덜 Gaussian. 큰 β (>1) = 더 깨끗한 코드 공간, 더 blurry 샘플. β-VAE (Higgins 2017)가 이 노브를 유명하게 만들고 disentanglement 연구를 시작했다.

**샘플링.** 추론 시: `z ~ N(0, I)`를 그리고 decoder를 통과. 하나의 forward 통과 — diffusion 같은 반복적 샘플링 없음.

## 실습

`code/main.py`는 numpy나 torch 없이 tiny VAE를 구현한다. 입력은 8-D의 2성분 가우시안 mixture에서 drawn된 8차원 synthetic 데이터이다. Encoder와 decoder는 단일 은닉층 MLP이다. tanh activation, forward 통과, 손실,手書き backward 통과를 구현한다. Production이 아닌 — 교육.

### Step 1: encoder forward

```python
def encode(x, enc):
    h = tanh(add(matmul(enc["W1"], x), enc["b1"]))
    mu = add(matmul(enc["W_mu"], h), enc["b_mu"])
    log_sigma2 = add(matmul(enc["W_sig"], h), enc["b_sig"])
    return mu, log_sigma2
```

`s` 대신 `log σ²`를 사용하여 네트워크 출력이 제약되지 않도록 (σ의 softplus는 함정 — gradient가 σ ≈ 0에서 죽음).

### Step 2: reparameterize and decode

```python
def reparameterize(mu, log_sigma2, rng):
    eps = [rng.gauss(0, 1) for _ in mu]
    sigma = [math.exp(0.5 * lv) for lv in log_sigma2]
    return [m + s * e for m, s, e in zip(mu, sigma, eps)]

def decode(z, dec):
    h = tanh(add(matmul(dec["W1"], z), dec["b1"]))
    return add(matmul(dec["W_out"], h), dec["b_out"])
```

### Step 3: the ELBO

```python
def elbo(x, x_hat, mu, log_sigma2, beta=1.0):
    recon = sum((a - b) ** 2 for a, b in zip(x, x_hat))
    kl = 0.5 * sum(math.exp(lv) + m * m - lv - 1 for m, lv in zip(mu, log_sigma2))
    return recon + beta * kl, recon, kl
```

두 분포가 모두 가우시안이기 때문에 정확한 폐쇄형 KL. 수치적으로 적분하지 마라. 2026년에도 사람들이 monte-carlo KL 추정을 사용하여 코드를出货한다 — 이유 없이 3x 느리다.

### Step 4: generate

```python
def sample(dec, z_dim, rng):
    z = [rng.gauss(0, 1) for _ in range(z_dim)]
    return decode(z, dec)
```

그것이 生成 模型이다. 다섯 줄.

## 함정

- **Posterior collapse.** KL 항이 `q(z|x) → N(0, I)`를 너무 강하게 밀어붙여서 `z`가 `x`에 대한 정보를 전달하지 못한다. 수정: β-annealing (β=0으로 시작, 1로 램프), free bits, 또는 비활성 차원에서 KL 건너뛰기.
- **Blurry 샘플.** 가우시안 decoder 우도가 L2 reconstruction를 의미하며 (평균용 Bayes 최선) — 그럴듯한 숫자 세트의 평균은 blurry 숫자이다. 수정: 이산 decoder (VQ-VAE, NVAE), 또는 VAE를 encoder로만 사용하고 잠재에 diffusion 쌓기 (이것이 Stable Diffusion이 하는 것이다).
- **β 너무 크고 너무 이르다.** Posterior collapse 참조. β≈0.01에서 시작하여 램프.
- **잠재 차원 너무 작다.** MNIST에는 16-D, ImageNet 256²에는 256-D, ImageNet 1024²에는 2048-D. Stable Diffusion의 VAE는 512×512×3 → 64×64×4 (공간 면에서 32x 다운샘플 factor, 채널에서 32x).

## 활용

2026 VAE 스택:

| 상황 | 선택 |
|------|------|
| Diffusion용 이미지-잠재 encoder | Stable Diffusion VAE (`sd-vae-ft-ema`) 또는 Flux VAE |
| 오디오 잠재 encoder | Encodec (Meta), SoundStream, 또는 DAC (Descript) |
| 비디오 잠재 | Sora의 시공간 패치, Latte VAE, WAN VAE |
| Disentangled 표현 학습 | β-VAE, FactorVAE, TCVAE |
| Transformer 모델링용 이산 잠재 | VQ-VAE, RVQ (ResidualVQ) |
| 생성을 위한 연속 잠재 | Plain VAE, 그런 다음 해당 잠재 공간에서 flow/diffusion 모델 조건 |

Latent-diffusion 모델은 encoder와 decoder 사이에 diffusion 모델이 있는 VAE이다. VAE가 조악한 압축을 하고, diffusion 모델이 무거운 작업을 한다. 비디오 (VAE + 비디오-diffusion DiT)와 오디오 (Encodec + MusicGen transformer)에 동일한 패턴.

## 결과물

`outputs/skill-vae-trainer.md`를 저장한다.

Skill은: 데이터 세트 프로필 + 잠재 차원 목표 + downstream 사용 (재구성, 샘플링, 또는 latent-diffusion 입력)을 가져와서: 아키텍처 선택 (plain/β/VQ/RVQ), β 스케줄, 잠재 차원, decoder 우도 (가우시안 vs 범주형), 평가 계획 (recon MSE, 차원당 KL, `q(z|x)`와 `N(0, I)` 사이의 Fréchet 거리)을 출력한다.

## 연습 문제

1. **쉬움.** `code/main.py`의 `β`를 `0.01`, `0.1`, `1.0`, `5.0`로 변경한다. 최종 재구성 MSE와 KL을 기록한다. 어떤 β가 합성 데이터에 대해 Pareto 최선인가?
2. **보통.** 가우시안 decoder 우도를 Bernoulli 우도 (cross-entropy 손실)로 교체한다. 동일한 합성 데이터의 이진화 버전에서 샘플 품질을 비교한다.
3. **어려움.** `code/main.py`를 mini VQ-VAE로 확장: 연속 `z`를 K=32 항목의 codebook에서 最近傍 조회로 교체. Reconstruction MSE를 비교하고 얼마나 많은 codebook 항목이 사용되는지 보고한다 (codebook collapse는 실제 문제임).

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Autoencoder | 인코더-디코더 네트워크 | `x → z → x̂`, MSE 학습. 生成 模型이 아님. |
| VAE | 샘플러가 있는 AE | Encoder가 분포를 출력하고, KL 페널티가 코드 공간을 형성. |
| ELBO | Evidence lower bound | `log p(x) ≥ recon - KL[q(z\|x) \|\| p(z)]`; `q = p(z\|x)`일 때 긴밀. |
| Reparameterization | `z = μ + σ·ε` | 확률 노드를 결정론적 + 순수 노이즈로 다시 작성. 샘플링을 통해 backprop을 가능하게 함. |
| Prior | `p(z)` | 잠재에 대한 목표 분포, typically `N(0, I)`. |
| Posterior collapse | "KL 항이 이김" | Encoder가 `x`를 무시하고 사전을 출력; decoder가 환각해야 함. |
| β-VAE | 조정 가능한 KL 가중치 | `loss = recon + β·KL`. 더 높은 β = 더 disentangled하지만 더 blurry. |
| VQ-VAE | 이산 잠재 | 연속 `z`를 最近傍 codebook 벡터로 교체; transformer 모델링을 가능하게 함. |

## Production note: VAE는 diffusion 서버에서 가장 빠른 경로이다

Stable Diffusion / Flux / SD3 파이프라인에서 VAE는 요청당 두 번 호출된다 — 한 번은 인코딩 (img2img / 인페인팅을 하는 경우)하고 한 번은 디코딩. 1024²에서 decoder 통과는 종종 전체 파이프라인에서 가장 큰 활성화 메모리 피크이다 — `128×128×16` 잠재를 다시 `1024×1024×3`으로 업샘플링하기 때문이다. 두 가지 실제 결과:

- **디코드를 슬라이스하거나 타일링.** `diffusers`는 `pipe.vae.enable_slicing()`과 `pipe.vae.enable_tiling()`을 노출한다. Tiling은 작은 seam 아티팩트를 `O(H·W)` 대신 `O(tile²)` 메모리와 trade한다. 소비자 GPU에서 1024²+에 필수.
- **bf16 decoder, 최종 리사이즈용 fp32 수치.** SD 1.x VAE는 fp32로 출시되었고 1024²에서 fp16으로 캐스트될 때 *조용히 NaN을 생성*한다. SDXL은 `madebyollin/sdxl-vae-fp16-fix`를 제공한다 — 항상 fp16-fix 변형을 선호하거나 bf16을 사용한다.

## 추가 자료

- [Kingma & Welling (2013). Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114) — VAE 논문.
- [Higgins et al. (2017). β-VAE: Learning Basic Visual Concepts with a Constrained Variational Framework](https://openreview.net/forum?id=Sy2fzU9gl) — disentangled β-VAE.
- [van den Oord et al. (2017). Neural Discrete Representation Learning](https://arxiv.org/abs/1711.00937) — VQ-VAE.
- [Vahdat & Kautz (2021). NVAE: A Deep Hierarchical Variational Autoencoder](https://arxiv.org/abs/2007.03898) — 최첨단 이미지 VAE.
- [Rombach et al. (2022). High-Resolution Image Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752) — Stable Diffusion; encoder로서의 VAE.
- [Défossez et al. (2022). High Fidelity Neural Audio Compression](https://arxiv.org/abs/2210.13438) — 오디오 VAE 표준.