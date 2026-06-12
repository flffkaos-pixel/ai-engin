# 플로|matching과 정류 흐름

> 확산 모델은 노이즈에서 데이터까지 20-50 스텝의 샘플링 단계를 거칩니다. 플로|matching(Lipman et al., 2023)과 정류 흐름(Rectified flow, Liu et al., 2022)은 직선 경로를 학습합니다. 더 곧은 경로는 더 적은 단계, 더 빠른 추론을 의미합니다. Stable Diffusion 3, Flux.1, AudioCraft 2는 모두 2024년에 플로|matching으로 전환했습니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 8 · 06 (DDPM), Phase 1 · Calculus
**소요 시간:** ~45분

## 문제

DDPM의 역과정은 `N(0, I)`에서 데이터 분포까지 1,000단계 확률적 워크입니다. DDIM은 이를 20-50개의 결정론적 단계로 축소했습니다. 더 적은 단계를 원합니다 — 이상적으로는 하나. 방해물은 역과정을 푸는 ODE가 경직(stiff)하다는 것입니다; 경로가 곡선입니다.

노이즈에서 데이터까지의 경로가 *직선*이 되도록 모델을 학습시킬 수 있다면, `t=1`에서 `t=0`까지의 단일 오일러 단계가 작동할 것입니다. 플로|matching은 이를 직접 구축합니다: `x_1 ~ N(0, I)`에서 `x_0 ~ data`까지의 직선 보간을 정의하고, 시간 미분과 일치하도록 벡터장 `v_θ(x, t)`를 학습시키고, 추론 시 적분합니다.

정류 흐름(Rectified flow, Liu 2022)은 더 나아갑니다: 점진적으로 경로를 곧게 만드는 reflow 절차를 사용하여 점점 선형에 가까운 ODE를 생성합니다. 2번의 reflow 반복 후, 2단계 샘플러가 50단계 DDPM 품질과 일치합니다.

## 개념

![플로|matching: 노이즈와 데이터 사이의 직선 보간](../assets/flow-matching.svg)

### 직선 플로

정의:

```
x_t = t · x_1 + (1 - t) · x_0,   t ∈ [0, 1]
```

여기서 `x_0 ~ data`이고 `x_1 ~ N(0, I)`. 이 직선に沿っての時間微分は 상수입니다:

```
dx_t / dt = x_1 - x_0
```

신경 벡터장 `v_θ(x_t, t)`를 정의하고 이 미분과 일치하도록 학습시킵니다:

```
L = E_{x_0, x_1, t} || v_θ(x_t, t) - (x_1 - x_0) ||²
```

이것이 **조건부 플로|matching** 손실(Lipman 2023)입니다. 학습은 시뮬레이션 프리입니다: 학습 중 ODE를 풀어展开하지 않습니다. 그냥 `(x_0, x_1, t)`를 샘플링하고 회귀합니다.

### 샘플링

추론 시, 학습된 벡터장을 시간倒退로 적분합니다:

```
x_{t-Δt} = x_t - Δt · v_θ(x_t, t)
```

`t=1`에서 `x_1 ~ N(0, I)`로 시작하여 `t=0`까지 오일러 단계로下山합니다.

### 정류 흐름 (Liu 2022)

직선 플로가 작동하지만, 학습된 경로는 실제로 *직선이 아닙니다* — 많은 `x_0`가 동일한 `x_1`에 매핑될 수 있기 때문에 곡선입니다. 정류 흐름의 reflow 단계:

1. 무작위 쌍으로 플로 모델 v_1을 학습시킵니다.
2. v_1을 `x_1`에서 해당 `x_0`로 적분하여 N개의 쌍 `(x_1, x_0)`를 샘플링합니다.
3. 해당 쌍에서 v_2를 학습시킵니다. 쌍이 이제 "ODE 매칭"되었으므로, 그 사이의 직선 보간자는 실제로 더 평탄합니다.
4. 반복합니다.

실제로 2번의 reflow 반복으로 거의 선형에 도달하여 2-4단계 추론이 가능해집니다. SDXL-Turbo, SD3-Turbo, LCM은 모두 플로|matching에서 증류된 모델입니다.

### 2024년 이미지에서 이것이 승리한 이유

세 가지 이유:

1. **시뮬레이션 프리 학습** — 학습 중 ODE 풀어展开 없음, 구현이 간단합니다.
2. **더 나은 손실 기하학** — 직선 경로는 일관된 신호 대 잡음비를 가지지만, DDPM ε-손실은 스케줄 가장자리에서 나쁜 SNR을 가집니다.
3. **더 빠른 추론** — SDXL-Turbo 품질의 4-8단계; 일관성 증류로 1단계.

## 플로|matching 대 DDPM — 정확한 연결

가우시안-조건부 경로의 플로|matching은 특정 노이즈 스케줄을 사용하는 확산과 *동등합니다*. `x_t = α(t) x_0 + σ(t) x_1` 스케줄을 선택하면, 플로|matching은 `v = α'·x_0 - σ'·x_1`로 Stratonovich-재구성된 확산을 복구합니다. 둘은 가우시안 경로에 대해 대수적으로 동등합니다.

플로|matching이 추가한 것: 목표의 *명확성*(평범한 속도), 더 깔끔한 손실, 비-가우시안 보간자로 실험할 수 있는 면허.

## 실습

`code/main.py`는 두 모드 가우시안 혼합에서 1차원 플로|matching을 구현합니다. 벡터장 `v_θ(x, t)`는 직선 목표와 함께 학습된 작은 MLP입니다. 추론 시 1, 2, 4, 20 오일러 단계를 적분하고 샘플 품질을 비교합니다.

### Step 1: 학습 손실

```python
def train_step(x0, net, rng, lr):
    x1 = rng.gauss(0, 1)
    t = rng.random()
    x_t = t * x1 + (1 - t) * x0
    target = x1 - x0
    pred = net_forward(x_t, t)
    loss = (pred - target) ** 2
    # backprop + update
```

### Step 2: 다단계 추론

```python
def sample(net, num_steps):
    x = rng.gauss(0, 1)
    for i in range(num_steps):
        t = 1.0 - i / num_steps
        dt = 1.0 / num_steps
        x -= dt * net_forward(x, t)
    return x
```

### Step 3: 단계 수 비교

4단계 샘플러가 이미 20단계 품질과 일치할 것으로 예상하세요 — 지연 시간에 큰 차이입니다.

## 함정

- **시간 파라미터화.** 플로|matching은 `t ∈ [0, 1]`을 사용하며 `t=0`은 데이터, `t=1`은 노이즈입니다. DDPM은 `t ∈ [0, T]`를 사용하며 `t=0`은 데이터, `t=T`는 노이즈입니다. 같은 방향, 다른 스케일. 논문들이 이것을 지속적으로 잘못 사용합니다.
- **스케줄 선택.** 정류 흐름의 직선은 "the" 플로|matching 스케줄이지만, 더 나은 스케일 커버리를 위해 코사인이나 로짓-정규 t-샘플링(SD3이这样做)을 사용할 수 있습니다.
- **Reflow 비용.** reflow용paired 데이터셋 생성은 샘플당 전체 추론 패스입니다. 정말 1-2단계 추론이 필요할 때만 reflow하세요.
- **분류기 프리 guidance는 여전히 적용됩니다.** 선형 결합에서 ε를 v로 바꾸기만 하면 됩니다: `v_cfg = (1+w) v_cond - w v_uncond`.

## 활용

| 사용 사례 | 2026년 스택 |
|----------|------------|
| 텍스트-이미지, 최고 품질 | 플로|matching: SD3, Flux.1-dev |
| 텍스트-이미지, 1-4단계 | 증류 플로|matching: Flux.1-schnell, SD3-Turbo, SDXL-Turbo |
| 실시간 추론 | 플로|matching 기본에서 일관성 증류 (LCM, PCM) |
| 오디오 생성 | 플로|matching: Stable Audio 2.5, AudioCraft 2 |
| 비디오 생성 | 확산과 혼합된 플로|matching (Sora, Veo, Stable Video) |
| 과학 / 물리학 (입자 궤적, 분자) | 플로|matching + 등변 벡터장 |

2025-2026년에 논문에서 "확산보다 빠름"이라고 말하는 것은 거의 항상 플로|matching + 증류입니다.

## 결과물

`outputs/skill-fm-tuner.md`를 저장하세요. Skill은 확산 스타일 모델 사양을 가져와서 플로|matching 학습 설정으로 변환합니다: 스케줄 선택, 시간 샘플링 분포(균일 / 로짓-정규), 옵티마이저, reflow 플랜, 목표 단계 수, 평가 프로토콜.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하고 1단계 vs 20단계 MSE vs 실제 데이터 분포를 비교하세요.
2. **보통.** 균일 `t` 샘플링에서 로짓-정규(중간 t에 집중)로 전환하세요. 모델 품질이 향상되나요?
3. **어려움.** 하나의 reflow 반복을 구현하세요: 첫 번째 모델을 적분하여paired (x_0, x_1)를 생성하고, 쌍에서 두 번째 모델을 학습시키고, 1단계 샘플 품질을 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 플로|matching | "직선 확산" | 보간자를 따라 `x_1 - x_0`와 일치하도록 `v_θ(x, t)`를 학습시킵니다. |
| 정류 흐름 | "Reflow" | 학습된 플로를 곧게 만드는 반복 절차. |
| 속도장 | "v_θ" | 모델 출력 — `x_t`를 이동시킬 방향. |
| 직선 보간자 | "경로" | `x_t = (1-t)·x_0 + t·x_1`; 평범한 목표 미분. |
| 오일러 샘플러 | "1차 ODE 솔버" | 가장 단순한 적분기; 경로가 직선일 때 잘 작동합니다. |
| 로짓-정규 t | "SD3 샘플링" | 경사가 가장 강한 중간 값으로 `t` 샘플링을 집중시킵니다. |
| 일관성 증류 | "1단계 샘플러" | 모든 `x_t`를 직접 `x_0`로 매핑하는 학생을 학습시킵니다. |
| 속도 기반 CFG | "v-CFG" | `v_cfg = (1+w) v_cond - w v_uncond`; 같은 트릭, 새로운 변수. |

## 프로덕션 노트: Flux.1-schnell은 가장 빠른 플로|matching입니다

플로|matching의 프로덕션 승리는 Flux.1-schnell — 1-4 추론 단계로 증류되면서도 Flux-dev等级的 품질을 유지하는 플로|matching DiT입니다. Niels의 "8GB 머신에서 Flux 실행" 노트북이 기준 디플로이먼트 레시피입니다: T5 + CLIP 인코딩, 양자화된 MMDiT 디노이즈(schnell의 경우 4단계 vs dev의 경우 50), VAE 디코딩. 비용 회계:

| 변형 | 단계 | L4에서 1024²의 지연 시간 | 총 FLOPs (상대적) |
|------|------|--------------------------|-------------------|
| Flux.1-dev (raw) | 50 | ~15초 | 1.0× |
| Flux.1-schnell | 4 | ~1.2초 | 0.08× (12× 빠름) |
| SDXL-base | 30 | ~4초 | 0.25× |
| SDXL-Lightning 2단계 | 2 | ~0.3초 | 0.03× |

프로덕션 규칙: **플로|matching 기본 + 증류 = 2026년 빠른 텍스트-이미지의 기본값.** 모든 주요 공급자가 이 콤비를 배송합니다: SD3-Turbo (SD3 + 플로 + 증류), Flux-schnell (Flux-dev + 정류 흐름 곧게 만들기), CogView-4-Flash. 순수 확산 기본은 레거시 체크포인트에만 존재합니다.

## 추가 자료

- [Liu, Gong, Liu (2022). Flow Straight and Fast: Learning to Generate and Transfer Data with Rectified Flow](https://arxiv.org/abs/2209.03003) — 정류 흐름.
- [Lipman et al. (2023). Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747) — 플로|matching.
- [Esser et al. (2024). Scaling Rectified Flow Transformers for High-Resolution Image Synthesis](https://arxiv.org/abs/2403.03206) — SD3, 대규모의 정류 흐름.
- [Albergo, Vanden-Eijnden (2023). Stochastic Interpolants](https://arxiv.org/abs/2303.08797) — FM + 확산을 포괄하는 일반 프레임워크.
- [Song et al. (2023). Consistency Models](https://arxiv.org/abs/2303.01469) — 확산 / 플로의 1단계 증류.
- [Sauer et al. (2023). Adversarial Diffusion Distillation (SDXL-Turbo)](https://arxiv.org/abs/2311.17042) — turbo 변형.
- [Black Forest Labs (2024). Flux.1 models](https://blackforestlabs.ai/announcing-black-forest-labs/) — 프로덕션의 플로|matching.