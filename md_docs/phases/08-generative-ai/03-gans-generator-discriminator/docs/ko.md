# GANs — Generator vs Discriminator

> Goodfellow의 2014년 트릭은 밀도를 완전히 건너뛰는 것이었다. 두 개의 네트워크. 하나는 가짜를 만든다. 하나는 그것을 잡는다. 그들이 구분할 수 없을 때까지 싸운다. 그것은 작동해서는 안 된다. Often it doesn't. 작동할 때, 샘플은狭い 도메인에 대한 문헌에서 여전히 가장 선명하다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 3 · 02 (Backprop), Phase 3 · 08 (Optimizers), Phase 8 · 02 (VAE)
**소요 시간:** ~75분

## 문제

VAE는 MSE decoder 손실이 *평균* 이미지에 대해 Bayes 최적이고 — 많은 그럴듯한 숫자의 평균은 blurry 숫자이기 때문에 blurry 샘플을 생성한다. *그럴ausibility*를 rewarding하는 손실을 원한다 — 어떤 단일 대상에 대한 픽셀 단위 근접성이 아닌. 그럴ausibility에 대한 closed-form이 없다. 그것을 학습해야 한다.

Goodfellow의 아이디어: 실제 이미지와 가짜를 구분하도록 classifier `D(x)`를 교육한다. `D`를 속이도록 generator `G(z)`를 교육한다. `G`에 대한 손실 신호는 현재 `D`가 실제처럼 보이게 하는 것으로 간주하는 것이다. 이 신호는 `G`가 개선됨에 따라 업데이트되고, 움직이는 대상을 chase한다. 두 네트워크가 모두 수렴하면 `G`는 `log p(x)`를 전혀 작성하지 않고 데이터 분포를 학습했다.

이것은 적대적 교육이다. 수학은 minimax 게임이다:

```
min_G max_D  E_real[log D(x)] + E_fake[log(1 - D(G(z))]
```

2026년 GAN은 더 이상 SOTA 생성기가 아니다 (diffusion과 flow matching이 그 왕관을 가져갔다). 하지만 StyleGAN 2/3는 여전히 가장 선명한 얼굴 모델이며, GAN 판별기는 diffusion 교육에서 *perceptual losses*로 사용되며, 적대적 교육은 빠른 1단계 증류 (SDXL-Turbo, SD3-Turbo, LCM)를 powering하여 실시간 diffusion을出货할 수 있게 한다.

## 개념

![GAN 교육: generator와 discriminator가 minimax에서](../assets/gan.svg)

**Generator `G(z).** 노이즈 벡터 `z ~ N(0, I)`를 샘플 `x̂`로 매핑. 디코더 형태의 네트워크 (dense 또는 transposed conv).

**Discriminator `D(x).** 샘플을 스칼라 확률 (또는 점수)로 매핑. Real → 1, fake → 0.

**손실.** 두 개의 교대 업데이트:

- **교육 `D`:** `loss_D = -[ log D(x) + log(1 - D(G(z))) ]`. Real=1, fake=0에서 이진 교차 엔트로피.
- **교육 `G`:** `loss_G = -log D(G(z))`. 이것이 Goodfellow가 사용한 *비포화* 형태이다 (원래 `log(1 - D(G(z)))`는 `D`가 confident일 때 포화되고 gradient를 죽인다).

**교육 루프.** `D` 한 단계, `G` 한 단계. 반복.

**작동하는 이유.** `G`가 `p_data`와 완벽하게 일치하면 `D`는 우연보다 잘 할 수 없고 0.5 everywhere에서 출력한다; `G`는 더 이상 gradient를 얻지 못한다. 균형.

**깨지는 이유.** Mode collapse (`G`가 `D`가 분류할 수 없고 영구히 만드는 하나의 모드를 찾는다), vanishing gradient (`D`가 너무 빨리 학습하고 `log D`가 포화), 교육 불안정 (학습률, 배치 크기, 무엇이든).

## 변형을 작동시킨 GAN

| 연도 | 혁신 | 수정 |
|------|------------|-----|
| 2015 | DCGAN | Conv/deconv, batch norm, LeakyReLU — 첫 번째 안정적인 아키텍처. |
| 2017 | WGAN, WGAN-GP | BCE를 Wasserstein 거리 + gradient 페널티로 교체. vanishing gradient를 수정. |
| 2017 | Spectral normalization | 판별기의 Lipschitz 경계를 제한. 2026년 판별기에서 여전히 사용. |
| 2018 | Progressive GAN | 저해상도 먼저 교육, 레이어 추가. 첫 메가픽셀 결과. |
| 2019 | StyleGAN / StyleGAN2 | 매핑 네트워크 + adaptive instance norm. 고정 도메인 포토리얼리즘에 대한 최첨단. |
| 2021 | StyleGAN3 | Alias-free, translation-equivariant — 2026년에도 얼굴 금 표전. |
| 2022 | StyleGAN-XL | 조건부, 클래스 인식, 더 큰 규모. |
| 2024 | R3GAN | 더 강력한 정규화로 재브랜딩; 트릭 없이 1024²에서 작동. |

## 실습

`code/main.py`는 1-D 데이터 (두 개의 가우시안 mixture)에서 tiny GAN을 교육한다. Generator와 discriminator는 단일 은닉층 MLP이다. 손으로 forward, backward, minimax 루프를 구현한다. 목표는 두 가지 주요 실패 양식 (mode collapse + vanishing gradient)을 발생하는 것을 보는 것이다.

### Step 1: 비포화 손실

Vanilla Goodfellow 손실 `log(1 - D(G(z)))`는 `D`가 높은 신뢰도로 G의 가짜를 가짜로 분류할 때 0으로 간다. 그 시점에서 G의 gradient는基本上零이다 — G는 개선할 수 없다. 비포화 형태 `-log D(G(z))`는 반대漸近線: `D`가 confident일 때爆炸하여 G에 강한 신호를 제공한다.

```python
def g_loss(d_fake):
    # maximize log D(G(z))  <=>  minimize -log D(G(z))
    return -sum(math.log(max(p, 1e-8)) for p in d_fake) / len(d_fake)
```

### Step 2: generator 단계당 한 discriminator 단계

```python
for step in range(steps):
    # train D
    real_batch = sample_real(batch_size)
    fake_batch = [G(z) for z in sample_noise(batch_size)]
    update_D(real_batch, fake_batch)

    # train G
    fake_batch = [G(z) for z in sample_noise(batch_size)]  # fresh fakes
    update_G(fake_batch)
```

G에 대한 신선한 가짜, 그렇지 않으면 gradient가 오래되었다.

### Step 3: mode collapse 감시

```python
if step % 200 == 0:
    samples = [G(z) for z in sample_noise(500)]
    mode_a = sum(1 for s in samples if s < 0)
    mode_b = 500 - mode_a
    if min(mode_a, mode_b) < 50:
        print("  [!] mode collapse: one mode is starved")
```

표준 증상: 두 실제 모드 중 하나가 생성되는 것을 멈춘다. 판별기가 그것을 가짜로 보지 않기 때문에 수정이 그것을 멈춘다.

## 함정

- **판별기가 너무 강함.** D의 학습률을 2-5x 감소시키거나 인스턴스/레이어 노이즈를 추가한다. D가 >95% 정확도에 도달하면 G는 죽는다.
- **생성기가 모드를 memorizes.** D 입력에 노이즈를 추가하고, minibatch 판별기 레이어를 사용하거나 WGAN-GP로 전환한다.
- **배치 norm이 통계를 leaking.** Real 배치 + 가짜 배치가 동일한 BN 레이어를 통해 흐르면 통계가 섞인다. 대신 인스턴스 norm 또는 spectral norm을 사용한다.
- **Inception 점수 gaming.** FID와 IS는 샘플 수가 적을 때 noisy하다. 평가에서 ≥10k 샘플을 사용한다.
- **조건부 작업의 원샷 샘플링은 거짓말이다.** 여전히 사용 가능한 출력을 얻으려면 CFG 척도, 자르기 트릭, 재샘플링이 필요하다.

## 활용

2026년 GAN 스택:

| 상황 | 선택 |
|-----------|------|
| 포토리얼 인물 얼굴, 고정 포즈 | StyleGAN3 (가장 선명하고 가장 작음) |
| 애니 / 양식화된 얼굴 | StyleGAN-XL 또는 Stable Diffusion LoRA |
| 이미지-이미지 번역 | Pix2Pix / CycleGAN (Phase 8 · 04) 또는 ControlNet (Phase 8 · 08) |
| 빠른 1단계 텍스트-이미지 | diffusion의 적대적 증류 (SDXL-Turbo, SD3-Turbo) |
| diffusion 교육 내 perceptual loss | 이미지 crop에서 작은 GAN 판별기 |
| 멀티모달, 개방형 무엇이든 | 하지 마라 — diffusion 또는 flow matching 사용 |

GAN은 선명하지만狭窄하다. 도메인이 열리면 — 사진, 임의의 텍스트 프롬프트, 비디오 — diffusion로 전환. 적대적 트릭은 독립 실행형 생성기가 아닌 구성 요소 (perceptual losses, 증류)로 살아남는다.

## 결과물

`outputs/skill-gan-debugger.md`를 저장한다. Skill은 실패한 GAN 실행 (손실 곡선, 샘플 그리드, 데이터 세트 크기)을 가져와서 가능한 원인, 원라인 수정, 재실행 프로토콜의 순위 목록을 출력한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 기본 설정으로 실행한다. 그런 다음 `D_LR = 5 * G_LR`로 설정하고 다시 실행한다. G의 손실이 상수로 붕괴되는 속도는 얼마나 되는가?
2. **보통.** Goodfellow BCE 손실을 WGAN 손실로 교체: `loss_D = E[D(fake)] - E[D(real)]`, `loss_G = -E[D(fake)]`, D의 가중치를 `[-0.01, 0.01]`로 클립. 교육이 더 안정적인가? 벽시계 수렴을 비교한다.
3. **어려움.** 1-D 예제를 2-D 데이터로 확장 (링크에서 8개 가우시안의 mixture). 단계 1k, 5k, 10k에서 생성기가 캡처하는 8개 모드 중 몇 개인지 추적. Minibatch discrimination을 구현하고 다시 측정한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Generator | "G" | 노이즈-투-샘플 네트워크, `G: z → x̂`. |
| Discriminator | "D" | 분류기 `D: x → [0, 1]`, real vs fake. |
| Minimax | "게임" | 공동 목적의 `min_G max_D`. |
| Non-saturating loss | "수정" | G에 대해 `log(1 - D(G(z)))` 대신 `-log D(G(z))` 사용. |
| Mode collapse | "G가 하나의 것을 memorizes" | Generator가 다양한 데이터에도拘わらず few distinct 출력을 생성. |
| WGAN | "Wasserstein" | BCE를 Earth-Mover 거리 + gradient 페널티로 교체; 더 부드러운 gradient. |
| Spectral norm | "Lipschitz 트릭" | 기울기를 제한하기 위해 D의 가중치規範을限制; 교육을 안정화. |
| StyleGAN | "작동하는 것" | 매핑 네트워크 + AdaIN; 얼굴에 최고, 2026년에도 지속. |

## Production note: 원샷 추론은 GAN의 지속적인 이점이다

GAN은 더 이상 개방형 도메인 생성에서 샘플 품질에서 이기지 않지만 추론 비용에서 여전히 이긴다. Production 추론 문헌 어휘에서 GAN은 다음을 갖는다:

- **Prefill 없음, 디코드 단계 없음.** 단일 `G(z)` forward 통과. TTFT ≈ 총 지연.
- **KV-cache 압력 없음.** 유일한 상태는 가중치이다. 배치 크기는 캐시가 아닌 활성화 메모리에 의해 제한된다.
- **무엇보다 지속적인 배칭.** 모든 요청이 동일한 고정 FLOP를 취하므로 서버의 목표 점유율에서 정적 배치가通常 최적이다. 인플라이트 스케줄러가 필요하지 않다.

이것이 2026년 빠른 텍스트-이미지를 위한 지배적 기술인 GAN 증류 (SDXL-Turbo, SD3-Turbo, ADD, LCM)이다: 20-50단계 diffusion 파이프라인을 diffusion 기반의 분포를 유지하면서 1-4 GAN 스타일 forward 통과로崩溃시킨다. 적대적 손실은 느린 생성기를 빠른 것으로 변환하기 위한 교육 시간 노브로 survivives한다.

## 추가 자료

- [Goodfellow et al. (2014). Generative Adversarial Nets](https://arxiv.org/abs/1406.2661) — 원래 GAN 논문.
- [Radford et al. (2015). Unsupervised Representation Learning with DCGAN](https://arxiv.org/abs/1511.06434) — 첫 번째 안정적인 아키텍처.
- [Arjovsky, Chintala, Bottou (2017). Wasserstein GAN](https://arxiv.org/abs/1701.07875) — WGAN.
- [Miyato et al. (2018). Spectral Normalization for GANs](https://arxiv.org/abs/1802.05957) — SN.
- [Karras et al. (2020). Analyzing and Improving the Image Quality of StyleGAN](https://arxiv.org/abs/1912.04958) — StyleGAN2.
- [Karras et al. (2021). Alias-Free Generative Adversarial Networks](https://arxiv.org/abs/2106.12423) — StyleGAN3.
- [Sauer et al. (2023). Adversarial Diffusion Distillation](https://arxiv.org/abs/2311.17042) — SDXL-Turbo.