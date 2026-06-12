# Actor-Critic — A2C와 A3C

> REINFORCE는 노이즈가 많습니다. `V̂(s)`를 학습하는 critic을 추가하고, 그것을 수익에서 빼면, 동일한 기대값을 가지지만 훨씬 낮은 분산을 가진 이점을 얻습니다. 그것이 actor-critic입니다. A2C는 동기적으로 실행하고; A3C는 스레드間で実行합니다. 둘 다 모든 현대 심층 RL 방법의 정신적 모델입니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 9 · 04 (TD Learning), Phase 9 · 06 (REINFORCE)
**소요 시간:** ~75분

## 문제

바닐라 REINFORCE는 작동하지만 분산이 심각합니다. 몬테 카를로 수익 `G_t`는 에피소드間で10배 이상의Swing을 할 수 있습니다. 그 노이즈에 `∇ log π`를 곱하고 평균을 내면, 동일한 거리를 이동하는 데 DQN 업데이트로 훨씬 적은 에피소드에서 이동할 수 있는 정책을 이동시키는 경사 추정기가数千 에피소드가 걸립니다.

분산은 원시 수익을 사용해서옵니다. 기본선 `b(s_t)` (학습된 값을 포함한 상태의 모든 함수)를 빼면, 기대값은 변경되지 않고 분산이 떨어집니다. 가장tractable 기본선은 `V̂(s_t)`입니다. 이제 `∇ log π`를 곱하는 양은 *이점*입니다:

`A(s, a) = G - V̂(s)`

행동이 평균 이상의 수익을 produced으면 좋은 것입니다; 이하면 나쁜 것입니다. 학습된 critic이 있는 REINFORCE는 *actor-critic*입니다. critic은 actor에게低분산 teacher를 제공합니다. 이것은 2015년 이후의 모든 deep-policy 방법(A2C, A3C, PPO, SAC, IMPALA)입니다.

## 개념

![Actor-critic: 정책 네트 plus 값 네트, TD 잔차としての 이점](../assets/actor-critic.svg)

**두 네트워크, 하나의 공유 손실:**

- **Actor** `π_θ(a | s)`: 정책. 샘플링하여 행동. 정책 기울기로 훈련.
- **Critic** `V_φ(s)`: 상태からの 예상 수익을 추정. `(V_φ(s) - target)²`를 최소화하도록 훈련.

**이점.** 두 가지 표준 형태:

- *MC 이점:* `A_t = G_t - V_φ(s_t)`. 불편, 더 높은 분산.
- *TD 이점:* `A_t = r_{t+1} + γ V_φ(s_{t+1}) - V_φ(s_t)`. 편향됨 (`V_φ` 사용), 훨씬 낮은 분산. *TD 잔차* `δ_t`라고도 합니다.

**n-단계 이점.** 둘 사이를 보간합니다:

`A_t^{(n)} = r_{t+1} + γ r_{t+2} + … + γ^{n-1} r_{t+n} + γ^n V_φ(s_{t+n}) - V_φ(s_t)`

`n = 1`은 순수 TD입니다. `n = ∞`은 MC입니다. 대부분의 구현은 Atari에 `n = 5`를 사용하고, MuJoCo의 PPO에 `n = 2048`을 사용합니다.

**일반화된 이점 추정 (GAE).** Schulman et al. (2016)이 모든 n-단계 이점에 대해 기하학적으로 가중 평균을 제안했습니다:

`A_t^{GAE} = Σ_{l=0}^{∞} (γλ)^l δ_{t+l}`

`λ ∈ [0, 1]`. `λ = 0`은 TD (낮은 분산, 높은 편향). `λ = 1`은 MC (높은 분산, 불편). `λ = 0.95`는 2026년 기본값 — 편향/분산 다이얼이 원하는 위치에 올 때까지 조정합니다.

**A2C: 동기적 이점 actor-critic.** `N` 평행 환경에서 `T` 단계를 수집합니다. 각 단계에 대한 이점을 계산합니다. 결합된 배치에서 actor와 critic을 업데이트합니다. 반복. A3C의 더 간단하고 확장 가능한 형제입니다.

**A3C: 비동기적 이점 actor-critic.** Mnih et al. (2016). `N` 작업자 스레드를 생성하고, 각각 환경을 실행합니다. 각 작업자가 자신의 rollout에서 로컬로 경사를 계산한 다음 비동기적으로 공유 매개변수 서버에 적용합니다. 리플레이 버퍼가 필요하지 않습니다 — 작업자가 다른 궤적을 실행하여 상관관계를 decorrelate합니다. A3C는 대규모로 CPU에서 훈련할 수 있음을 증명했습니다. 2026년, GPU 기반 A2C (배치된 평행 환경)가 주류입니다, 왜냐하면 GPU는 대용량 배치를 원하는 때문입니다.

**결합된 손실.**

`L(θ, φ) = -E[ A_t · log π_θ(a_t | s_t) ]  +  c_v · E[(V_φ(s_t) - G_t)²]  -  c_e · E[H(π_θ(·|s_t))]`

세 항: 정책 기울기 손실, 값 회귀, 엔트로피 보너스. `c_v ~ 0.5`, `c_e ~ 0.01`은 표준 시작 점입니다.

## 실습

### Step 1: critic

MSE로 업데이트되는 선형 critic `V_φ(s) = w · features(s)`:

```python
def critic_update(w, x, target, lr):
    v_hat = dot(w, x)
    err = target - v_hat
    for j in range(len(w)):
        w[j] += lr * err * x[j]
    return v_hat
```

표形式 환경에서 critic은数百 에피소드에서 수렴합니다. Atari에서 선형 critic을 공유 CNN trunk + 값 head로 교체합니다.

### Step 2: n-단계 이점

길이 `T`의 rollout과 부트스트랩된 최종 `V(s_T)`가 주어지면:

```python
def compute_advantages(rewards, values, gamma=0.99, lam=0.95, last_value=0.0):
    advantages = [0.0] * len(rewards)
    gae = 0.0
    for t in reversed(range(len(rewards))):
        next_v = values[t + 1] if t + 1 < len(values) else last_value
        delta = rewards[t] + gamma * next_v - values[t]
        gae = delta + gamma * lam * gae
        advantages[t] = gae
    returns = [a + v for a, v in zip(advantages, values)]
    return advantages, returns
```

`returns`는 critic 대상입니다. `advantages`는 `∇ log π`를 곱하는 것입니다.

### Step 3: 결합된 업데이트

```python
for step_i, (x, a, _r, probs) in enumerate(traj):
    adv = advantages[step_i]
    target_v = returns[step_i]

    # critic
    critic_update(w, x, target_v, lr_v)

    # actor
    for i in range(N_ACTIONS):
        grad_logpi = (1.0 if i == a else 0.0) - probs[i]
        for j in range(N_FEAT):
            theta[i][j] += lr_a * adv * grad_logpi * x[j]
```

온정책, 업데이트당 하나의 rollout, actor와 critic에 별도의 학습률.

### Step 4: 병렬화 (A3C vs A2C)

- **A3C:** `N` 스레드를 시작합니다. 각각 자신의 환경을 실행하고 자신의 순방향 패스를 실행합니다. 주기적으로 공유 마스터에 경사 업데이트를 푸시합니다. 마스터에 잠금이 없습니다 — 경주는 괜찮습니다, 그들은 그냥 노이즈를 추가합니다.
- **A2C:** 단일 프로세스에서 `N` 환경 인스턴스를 실행하고, 관찰을 `[N, obs_dim]` 배치로 쌓고, 배치된 순방향 패스, 배치된 역방향 패스. 더 높은 GPU 활용, 결정론적, 더reasoning하기 쉽습니다. 2026년 기본입니다.

우리의 토이 코드는 명확성을 위해 단일 스레드입니다; 배치된 A2C로 재작성하는 것은 numpy 3줄입니다.

## 함정

- **Actor 경사 전 critic 편향.** critic이 무작위이면, 그 기본선은 정보가 없고 순수 노이즈에서 훈련하고 있습니다. 정책 기울기를 켜기 전에 critic을数百 단계 워밍업하거나 느린 actor 학습률을 사용하세요.
- **이점 정규화.** 배치당 이점을 제로 평균/단위 표준으로 정규화합니다. 거의 비용 없이 훈련을 크게 안정화합니다.
- **공유 trunk.** 이미지 입력에서 actor와 critic에 공유 특성 추출기를 사용합니다. 별도 heads. 공유 특성은 두 손실에서 free-ride합니다.
- **온정책 계약.** A2C는 정확히 하나의 업데이트에 데이터를 재사용합니다. 더 많으면 경사가 편향됩니다 (PPO가 추가하는 중요도 샘플링 수정이 그 이유입니다).
- **엔트로피 붕괴.** `c_e > 0` 없이는 정책이数百 업데이트에서 near-결정론적으로 되어 탐험을 멈춥니다.
- **보상 척도.** 이점 크기는 보상 척도에依存합니다. 작업간 일관된 기울기 크기를 위해 보상을 정규화하세요 (예: 실행 표준 편차로 나누기).

## 활용

A2C/A3C는 2026년에 최종 선택이 거의 없지만 이후 모든 것이 세분화하는 아키텍처입니다:

| 방법 | A2C와의 관계 |
|------|------------|
| PPO | 여러 에포크 업데이트를 위한 클리핑된 중요도 비율이 있는 A2C |
| IMPALA | V-trace 오프정책 수정이 있는 A3C |
| SAC (단계 9 · 07) | 부드러운 값 critic이 있는 오프정책 A2C (다음 레슨) |
| GRPO (단계 9 · 12) | critic 없는 A2C — 그룹 상대 이점 |
| DPO | 샘플링 없이 선호도 순위 손실로 붕괴된 A2C |
| AlphaStar / OpenAI Five | 리그 훈련 + 모방 사전 훈련이 있는 A2C |

2026년 논문에서 "이점"을 보면 actor-critic을 생각하세요.

## 결과물

`outputs/skill-actor-critic-trainer.md`로 저장:

```markdown
---
name: actor-critic-trainer
description: 주어진 환경에 대한 A2C / A3C / GAE 구성을 생성하고, 이점 추정과 손실 가중치를 지정합니다.
version: 1.0.0
phase: 9
lesson: 7
tags: [rl, actor-critic, gae]
---

환경과 컴퓨트 예산이 주어지면 출력:

1. 병렬성. A2C (GPU 배치) vs A3C (CPU 비동기) 및 작업자 수.
2. Rollout 길이 T. 업데이트당 환경당 단계.
3. 이점 추정기. n-step 또는 GAE(λ); λ를 지정합니다.
4. 손실 가중치. `c_v` (값), `c_e` (엔트로피), 기울기 클립.
5. 학습률. Actor와 critic (사용하는 경우 별도).

> 시야 > 1000인 환경에서 단일 작업자 A2C 거부 (너무 온정책, 너무 느림). 이점 정규화 없이 shipping 거부. `c_e = 0`이고 관찰된 엔트로피 < 0.1인 모든 실행을 엔트로피 붕괴로 플래그.
```

## 연습 문제

1. **쉬움.** MC 이점(`G_t - V(s_t)`)으로 4×4 GridWorld에서 actor-critic을 훈련하세요. 레슨 06의 REINFORCE-실행-평균-기본선과 샘플 효율성을 비교하세요.
2. **보통.** TD 잔차 이점(`r + γ V(s') - V(s)`)으로 전환하세요. 이점 배치의 분산을 측정하세요. 얼마나 떨어지나요?
3. **어려움.** GAE(λ)를 구현하세요. `λ ∈ {0, 0.5, 0.9, 0.95, 1.0}`을 sweep하세요. 최종 수익 vs 샘플 효율성을 플롯하세요. 이 작업에서 편향/분산 스위트 스팟은 어디에 있나요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| Actor | "정책 네트" | `π_θ(a\|s)`, 정책 기울기로 업데이트됩니다. |
| Critic | "값 네트" | `V_φ(s)`, 수익 / TD 대상에 대한 MSE 회귀로 업데이트됩니다. |
| 이점 | "평균보다 얼마나 나은가" | `A(s, a) = Q(s, a) - V(s)` 또는 그 추정기. `∇ log π`의乗数. |
| TD 잔차 | "δ" | `δ_t = r + γ V(s') - V(s)`; 한 단계 이점 추정. |
| GAE | "보간 노브" | `λ`로 매개변수화된 n-단계 이점의 지수적으로 가중 평균. |
| A2C | "동기 actor-critic" | 환경에서 배치됨; rollout당 하나의 경사 단계. |
| A3C | "비동기 actor-critic" | 작업자 스레드가 공유 매개변수 서버에 경사를 푸시합니다. 원래 논문; 2026에는 덜 일반적입니다. |
| 부트스트래핑 | "시야에서 V 사용" | rollout을 자르고 `γ^n V(s_{t+n})`을 추가하여 합을 닫습니다. |

## 추가 자료

- [Mnih et al. (2016). Asynchronous Methods for Deep Reinforcement Learning](https://arxiv.org/abs/1602.01783) — A3C, 원래 비동기 actor-critic 논문.
- [Schulman et al. (2016). High-Dimensional Continuous Control Using Generalized Advantage Estimation](https://arxiv.org/abs/1506.02438) — GAE.
- [Sutton & Barto (2018). Ch. 13 — Actor-Critic Methods](http://incompleteideas.net/book/RLbook2020.pdf) — 기초; critic이 신경망일 때 Ch. 9의 함수 근사와 쌍을 이루어야 합니다.
- [Espeholt et al. (2018). IMPALA](https://arxiv.org/abs/1802.01561) — V-trace 오프정책 수정이 있는 확장 가능한 분산 actor-critic.
- [OpenAI Baselines / Stable-Baselines3](https://stable-baselines3.readthedocs.io/) — production A2C/PPO 구현, 읽을 가치가 있습니다.
- [Konda & Tsitsiklis (2000). Actor-Critic Algorithms](https://papers.nips.cc/paper/1786-actor-critic-algorithms) — 두 시간 눈금 actor-critic 분해에 대한 근본적인 수렴 결과.