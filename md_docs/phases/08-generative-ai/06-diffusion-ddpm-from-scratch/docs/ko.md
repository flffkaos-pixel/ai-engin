# Diffusion 모델 — Scratch에서 DDPM

> Ho, Jain, Abbeel (2020)은 이 분야에 그만둘 수 없는 레시피를 제공했다. 천 개의 작은 단계로 노이즈를 통해 데이터를 파괴한다. 하나의 신경망을 교육하여 노이즈를 예측한다. 추론 시 프로세스를 反転한다. 오늘날 모든 주류 이미지, 비디오, 3D 및 음악 모델은 이 루프에서 실행되며, 위에는 flow matching 또는 consistency 트릭이 있을 수 있다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 3 · 02 (Backprop), Phase 8 · 02 (VAE)
**소요 시간:** ~75분

## 문제

`p_data(x)`에 대한 샘플러가 필요하다. GAN은 종종 divergence하는 minimax 게임을 한다. VAE는 가우시안 decoder에서 blurry 샘플을 생성한다. 실제로 원하는 것: (a) 단일 안정 손실 (saddle point 없음, minimax 없음), (b) `log p(x)`에 대한 하한 (따라서 우도가 있음), (c) SOTA 품질과 일치하는 샘플.

Sohl-Dickstein et al. (2015)는 이론적 답을 가졌다: 점진적으로 가우시안 노이즈를 추가하는 Markov 연쇄 `q(x_t | x_{t-1})`를 정의하고, denoise하도록 역연쇄 `p_θ(x_{t-1} | x_t)`를 교육한다. Ho, Jain, Abbeel (2020)은 손실이 한 줄로 단순화될 수 있음을 보여주었다 — 노이즈 예측 — 그리고 수학을 정리했다. 2020년 이것은 호기심이었다. 2021년 state-of-the-art 샘플을 생성했다. 2022년 Stable Diffusion이 되었다. 2026년 이것은 기질이다.

## 개념

![DDPM: 순방향 노이즈, 역방향 denoise](../assets/ddpm.svg)

**순방향 프로세스 `q`.** `T` 작은 단계로 가우시안 노이즈를 추가한다. 닫힌 형식 — 수학이 다루기 쉬운 이유 — 누적 단계도 가우시안이라는 것이다:

```
q(x_t | x_0) = N( sqrt(α̅_t) · x_0,  (1 - α̅_t) · I )
```

여기서 `α̅_t = ∏_{s=1..t} (1 - β_s)`는 `β_t`의 스케줄이다. T=1000단계에서 1e-4에서 0.02까지 선형으로 `β_t`를 선택하면 `x_T`는 approximately `N(0, I)`.

**역방향 프로세스 `p_θ`.** 추가된 노이즈를 예측하는 신경망 `ε_θ(x_t, t)`를 학습한다. `x_t`가 주어지면:

```
x_{t-1} = (1 / sqrt(α_t)) · ( x_t - (β_t / sqrt(1 - α̅_t)) · ε_θ(x_t, t) )  +  σ_t · z
```

여기서 `σ_t`는 `sqrt(β_t)`이거나 학습된 분산이다. 표현은 ugly하지만 단순히 대수이다 — 사후 `q(x_{t-1} | x_t, x_0)`를 given `x_{t-1}`에 대해 풀고 `x_0`를 노이즈 예측 추정으로 대체한다.

**교육 손실.**

```
L_simple = E_{x_0, t, ε} [ || ε - ε_θ( sqrt(α̅_t) · x_0 + sqrt(1 - α̅_t) · ε,  t ) ||² ]
```

데이터에서 `x_0`를 샘플링하고, 무작위 `t`를 선택하고, `ε ~ N(0, I)`를 샘플링하고, 닫힌 형식으로 노이즈가 있는 `x_t`를 한 번에 계산하고, 노이즈에 회귀한다. 하나의 손실, minimax 없음, KL 없음, reparameterization 트릭 없음.

**샘플링.** `x_T ~ N(0, I)`로 시작. `t = T`에서 `1`까지 역방향 단계를 반복한다. 완료.

## 왜 작동하는가

세 가지 直観:

1. **Denoising은 쉽고; 생성은 어렵다.** `t=T`에서 데이터는 pure 노이즈이다 — net은 자명한 문제를 풀어야 한다. `t=0`에서 net은 몇 개의 픽셀만 정리해야 한다. 중간 `t`에서 문제는 어렵지만 net은 모든 노이즈 수준에서 동일한 가중치를 통해 많은 gradient를 흐른다.

2. **Score matching in disguise.** Vincent (2011)은 노이즈 예측이 `∇_x log q(x_t | x_0)`, *score*를 추정하는 것과 동등함을 증명했다. 역 SDE는 이 점수를 사용하여 밀도 gradient를 따라 위로 걸어간다 — 고확률 영역으로 향하는 guided random walk.

3. **ELBO가 단순 MSE로 축소된다.** 전체 변분 하한에는 각 타임스텝마다 KL 항이 있다. DDPM의 parameterization으로 those KL 항은 특정 계수를 가진 노이즈 예측에 MSE로 단순화된다; Ho는 계수를 떨어뜨리고 ("simple" 손실이라고 부름) 품질이 *개선되었다*.

## 실습

`code/main.py`는 1-D DDPM을 구현한다. 데이터는 두 모드 mixture이다. "net"은 `(x_t, t)`를 취하고 예측된 노이즈를 출력하는 tiny MLP이다. 교육은 one-line 손실이다. 샘플링은 역연쇄를 반복한다.

### Step 1: 순방향 스케줄 (닫힌 형식)

```python
betas = [1e-4 + (0.02 - 1e-4) * t / (T - 1) for t in range(T)]
alphas = [1 - b for b in betas]
alpha_bars = []
cum = 1.0
for a in alphas:
    cum *= a
    alpha_bars.append(cum)
```

### Step 2: 한 번에 `x_t` 샘플링

```python
def forward_sample(x0, t, alpha_bars, rng):
    a_bar = alpha_bars[t]
    eps = rng.gauss(0, 1)
    x_t = math.sqrt(a_bar) * x0 + math.sqrt(1 - a_bar) * eps
    return x_t, eps
```

### Step 3: DDPM 역방향 단계

```python
def reverse_step(x_t, t, eps_theta, betas, alpha_bars):
    beta_t = betas[t]
    alpha_t = 1 - beta_t
    alpha_bar_t = alpha_bars[t]
    sqrt_alpha = math.sqrt(alpha_t)
    pred_x0 = (x_t - math.sqrt(1 - alpha_bar_t) * eps_theta) / math.sqrt(alpha_bar_t)
    model_mean = sqrt_alpha * pred_x0
    if t > 0:
        model_var = beta_t
        noise = rng.gauss(0, 1)
        return model_mean + math.sqrt(model_var) * noise
    return model_mean
```

### Step 4: 전체 샘플링 루프

```python
def sample(x_T, T, eps_theta, betas, alpha_bars, rng):
    x = x_T
    for t in reversed(range(T)):
        eps_pred = eps_theta([x, t/T])
        x = reverse_step(x, t, eps_pred, betas, alpha_bars)
    return x
```

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| DDPM | "Denoising Diffusion Probabilistic Model" | 순방향 노이즈 추가 + 역방향 denoise 학습. |
| Forward process | "데이터를 노이즈로" | Markov 연쇄로 Gaussian 노이즈를 점진적으로 추가. |
| Reverse process | "노이즈를 데이터로" | 학습된 신경망이 노이즈를 예측하고 reverse. |
| Score matching | "밀도의 gradient 학습" | 노이즈 예측은 score 추정과 동등. |
| ELBO | "변분 하한" | diffusion 손실의 근본적 유도. |
| β schedule | "노이즈 증가 방식" | 선형, cosine 등; T=1000이 표준. |
| Sampling steps | "역방향 통과 수" | 더 많은 단계 = 더 나은 품질, 더 느림. |

## 추가 자료

- [Sohl-Dickstein et al. (2015). Deep Unsupervised Learning using Nonequilibrium Thermodynamics](https://arxiv.org/abs/1505.03570) — 원래 아이디어.
- [Ho et al. (2020). Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) — DDPM.
- [Nichol & Dhariwal (2021). Improved Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2102.09672) — 향상된 버전.