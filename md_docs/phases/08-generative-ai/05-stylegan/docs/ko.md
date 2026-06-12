# StyleGAN

> 대부분의 생성기는 `z`를 동시에 모든 레이어에 넣는다. StyleGAN은 분리했다: 먼저 `z`를 중간 `w`로 매핑한 다음 AdaIN을 통해 모든 해상도 수준에서 `w`를 *주입*한다. 그 단일 변경으로 잠재 공간이 풀려났고 7년 연속 포토리얼 얼굴을 해결된 문제로 만들었다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 8 · 03 (GANs), Phase 4 · 08 (Normalization), Phase 3 · 07 (CNNs)
**소요 시간:** ~45분

## 문제

DCGAN은 일련의 transposed convolutions을 통해 `z`를 이미지로 매핑한다. 문제: `z`가 모든 것을 제어한다 — 포즈, 조명, 정체성, 배경 — 강하게 얽혀 있다. `z`의 하나의 축을 따라 이동하면 네 가지가 모두 변경된다. "같은 사람, 다른 포즈"를 요청할 수 없다 — 표현이 그렇게 분해되지 않기 때문이다.

Karras et al. (2019, NVIDIA) 제안: `z`를 직접 conv 레이어에 공급하지 마라. 네트워크 입력으로 학습된 `4×4×512` 텐서를 공급한다. `z ∈ Z → w ∈ W`를 매핑하는 8층 MLP를 학습한다. AdaIN을 통해 각 해상도에서 `w`를 주입: 각 conv 피처 맵을 정규화한 다음 `w`의 affine projection으로 스케일링하고 shift한다. stochastic detail (피부 모공, 머리카락)를 위해 레이어당 노이즈를 추가한다.

결과: `W`는 "고수준 스타일" (포즈, 정체성)에 대해 대략 직교 축과 "세밀한 스타일" (조명, 색상)을 갖는다. 두 이미지의 스타일을 교환하려면 낮은 해상도 수준에는 이미지 A의 `w`를 사용하고 높은 해상도 수준에는 이미지 B의 `w`를 사용할 수 있다. 이것이 편집, 교차 도메인 양식화, 전체 "StyleGAN-inversion" 연구 라인을解锁했다.

## 개념

![StyleGAN: 매핑 네트워크 + AdaIN + 레이어당 노이즈](../assets/stylegan.svg)

**매핑 네트워크.** `f: Z → W`, 8층 MLP. `Z = N(0, I)^512`. `W`는 가우시안이 강제되지 않는다 — 데이터 적응 형태를 학습한다.

**합성 네트워크.** 학습된 상수 `4×4×512`에서 시작. 각 해상도 블록: `upsample → conv → AdaIN(w_i) → noise → conv → AdaIN(w_i) → noise`. 해상도가 두 배가 된다: 4, 8, 16, 32, 64, 128, 256, 512, 1024.

**AdaIN.**

```
AdaIN(x, y) = y_scale · (x - mean(x)) / std(x) + y_bias
```

여기서 `y_scale`과 `y_bias`는 `w`의 affine projection에서 온다. 각 피처 맵별로 정규화한 다음 재양식화. "스타일"은 여기서 피처 맵의 첫 번째 및 두 번째 차수 통계이다.

**레이어당 노이즈.** 각 피처 맵에 추가된 단일 채널 가우시안 노이즈, 학습된 per-channel factor로 스케일링. 전체 구조에 영향을 주지 않고 stochastic detail을 제어.

**Truncation 트릭.** 추론 시 `z`를 샘플링하고 `w = mapping(z)`를 계산한 다음 `w' = ŵ + ψ·(w - ŵ)` where `ŵ`는 많은 샘플에 대한 평균 `w`이다. `ψ < 1`는 다양성을 품질과 trade한다. 거의 모든 StyleGAN 데모는 `ψ ≈ 0.7`을 사용한다.

## StyleGAN 1 → 2 → 3

| 버전 | 연도 | 혁신 |
|---------|------|------------|
| StyleGAN | 2019 | 매핑 네트워크 + AdaIN + 노이즈 + 점진적 성장. |
| StyleGAN2 | 2020 | Weight demodulation이 AdaIN을 대체 (방울 ア티팩트修正); skip/residual 아키텍처; 경로 길이 정규화. |
| StyleGAN3 | 2021 | Alias-free convolution + equivariant 커널; 픽셀 그리드에 텍스처 고착 제거. |
| StyleGAN-XL | 2022 | 클래스 조건부, 1024², ImageNet. |
| R3GAN | 2024 | 더 강력한 reg로 재브랜딩; 20x 더 적은 매개변수로 FFHQ-1024에서 diffusion 격차 감소. |

2026년 StyleGAN3는 여전히 (a) 높은 FPS에서 좁은 도메인 포토리얼리즘, (b) few-shot 도메인 적응 (100개 이미지로 새 데이터 세트 교육, 매핑 동결), (c) inversion 기반 편집 (실제 사진을 재구성하는 `w`를 찾은 다음 해당 `w`를 편집)의 기본이다. 개방형 도메인 텍스트-이미지의 경우 그것이 도구가 아니다 — diffusion이다.

## 실습

`code/main.py`는 1-D에서 toy "style-GAN lite"를 구현: 매핑 MLP, 학습된 상수 벡터를 취하고 `w` 파생 스케일/바이어스로 변조하는 합성 함수, 레이어당 노이즈. `w` 주입이 `z`를 generator 입력에 연결하는 것보다 낫거나 능가함을 보여준다.

### Step 1: 매핑 네트워크

```python
def mapping(z, M):
    h = z
    for i in range(num_layers):
        h = leaky_relu(add(matmul(M[f"W{i}"], h), M[f"b{i}"]))
    return h
```

### Step 2: adaptive instance normalization

```python
def adain(x, w_scale, w_bias):
    mu = mean(x)
    sd = std(x)
    x_norm = [(xi - mu) / (sd + 1e-8) for xi in x]
    return [w_scale * xi + w_bias for xi in x_norm]
```

Per-feature-map 스케일과 바이어스가 `w`에서 선형 projection을 통해 온다.

### Step 3: 레이어당 노이즈

```python
def add_noise(x, sigma, rng):
    return [xi + sigma * rng.gauss(0, 1) for xi in x]
```

## 함정

- **AdaIN은 스타일 혼합을 의미하지 않음; 상호 작용이 필요함.** 단순히 레이어에 `w`를 삽입하는 것은 스타일 혼합이 아님; 스타일 혼합은 두 이미지 사이의 해당 레벨에서 `w`를 교환하여 달성됨.
- **노이즈가 너무 크면 구조가崩溃함.** 작은 값으로 시작; 노이즈 스케일 학습을 위해 노이즈 재조정 모듈을 추가 고려.
- **매핑 네트워크가 너무 깊으면 정보가 손실될 수 있음.** 8층은 좋은 기본값이지만 작은 데이터에는 더 얕은 것이 나을 수 있음.

## 활용

2026년 StyleGAN 변형:

| 상황 | 선택 |
|-----------|------|
| 포토리얼 얼굴, 고정 포즈 | StyleGAN3 (가장 선명, 최소 매개변수) |
| 얼굴 편집/스타일 혼합 | StyleGAN3 + 래티언트 편집 도구 |
| Few-shot 도메인 적응 | 매핑 네트워크 동결, 합성 네트워크만 미세 조정 |
| 개방형 텍스트-이미지 | 사용하지 마라 — diffusion 사용 |

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|-----------------------|
| Mapping network | "z에서 w로" | 8층 MLP; 잠재 공간을 데이터 적응 형태로 변환. |
| AdaIN | "스타일 주입" | 피처 통계를 기반으로 각 conv 레이어를 변조. |
| Synthesis network | "이미지를 생성하는 부분" | 상수에서 시작하여 해상도를 높여감. |
| Per-layer noise | " stochastic detail" | 픽셀 그리드에固定되지 않은 무작위 variation. |
| Truncation trick | "품질 대 다양성" | `ψ < 1`로 평균 w로 회귀; 품질 향상だが多様性 감소. |
| Style mixing | "스타일 교환" | 한 이미지의 저해상도 w와 다른 이미지의 고해상도 w를混合. |

## 추가 자료

- [Karras et al. (2019). A Style-Based Generator Architecture for Generative Adversarial Networks](https://arxiv.org/abs/1812.04948) — StyleGAN.
- [Karras et al. (2020). Analyzing and Improving the Image Quality of StyleGAN](https://arxiv.org/abs/1912.04958) — StyleGAN2.
- [Karras et al. (2021). Alias-Free Generative Adversarial Networks](https://arxiv.org/abs/2106.12423) — StyleGAN3.
- [Richardson et al. (2021). Encoding in Style: a StyleGAN Encoder for Image-to-Image Translation](https://arxiv.org/abs/2108.00939) — 인코딩 및 편집.