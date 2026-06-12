# 정책 기울기 — 처음부터 REINFORCE

> 가치를 추정하는 것을 중단합니다. 정책을 직접 매개변수화하고, 예상 수익의 기울기를 계산하고, 올라갑니다. Williams (1992)는 그것을 하나의 정리로 썼습니다. 이것이 PPO, GRPO 및 모든 LLM RL 루프가 존재하는 이유입니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 3 · 03 (Backpropagation), Phase 9 · 03 (Monte Carlo), Phase 9 · 04 (TD Learning)
**소요 시간:** ~75분

## 문제

Q-learning과 DQN은 *가치* 함수를 매개변수화합니다. `argmax Q`로 행동을 선택합니다. 이산 행동과 이산 상태에는 괜찮습니다. 행동이 연속적일 때(10차원 토크에 대한 `argmax`?) 또는 확률적 정책을 원할 때(`argmax`는 구조적으로 결정론적입니다) 문제가됩니다.

정책 기울기는 대신 *정책*을 매개변수화합니다. `π_θ(a | s)`는 행동에 대한 분포를 출력하는 신경망입니다. 그것에서 샘플링하여 행동합니다. `θ`에 대한 예상 수익의 기울기를 계산합니다. 올라갑니다. `argmax` 없습니다. 벨만 재귀 없습니다. `J(θ) = E_{π_θ}[G]`에 대한 경사 상승만.

REINFORCE 정리(Williams 1992)는 이 기울기가 계산 가능함을 알려줍니다: `∇J(θ) = E_π[ G · ∇_θ log π_θ(a | s) ]`. 에피소드를 실행합니다. 수익을 계산합니다. 모든 단계에서 `∇ log π_θ(a | s)`를 곱합니다. 평균을냅니다. 경사 상승. 끝.

2026년의 모든 LLM-RL 알고리즘 — PPO, DPO, GRPO —은 REINFORCE의 개선입니다. 손가락으로 그것을 이해하는 것이 이 단계의 나머지와 단계 10 · 07 (RLHF 구현) 및 단계 10 · 08 (DPO)를 위한 전제 조건입니다.

## 개념

![정책 기울기: 소프트맥스 정책, log-π 기울기, 수익 가중 업데이트](../assets/policy-gradient.svg)

**정책 기울기 정리.** `θ`로 매개변수화된 모든 정책 `π_θ`에 대해:

`∇J(θ) = E_{τ ~ π_θ}[ Σ_{t=0}^{T} G_t · ∇_θ log π_θ(a_t | s_t) ]`

여기서 `G_t = Σ_{k=t}^{T} γ^{k-t} r_{k+1}`는 단계 `t`からの 할인된 수익입니다. 기대치는 `π_θ`에서 샘플링된 완전한 궤적 `τ`에 대한 것입니다.

**증명은 짧습니다.** 기대치 아래서 `J(θ) = Σ_τ P(τ; θ) G(τ)`를 미분합니다. `∇P(τ; θ) = P(τ; θ) ∇ log P(τ; θ)` (log-미분 트릭)를 사용합니다. `log P(τ; θ) = Σ log π_θ(a_t | s_t) + 환경 항` (θ에 의존하지 않음)으로 분해합니다. 환경 항은 사라집니다. 대수 두 줄로 정리를 얻습니다.

**분산 감소 트릭.** 바닐라 REINFORCE는 끔찍한 분산을 가집니다 — 수익이 노이즈이고, `∇ log π`가 노이즈이고,它们的 곱은 매우 노이즈가 많습니다. 두 가지 표준 수정:

1. **기본선 차감.** 모든 기본선 `b(s_t)` (a에 의존하지 않는)에 대해 `G_t`를 `G_t - b(s_t)`로 교체합니다. `E[b(s_t) · ∇ log π(a_t | s_t)] = 0`이기 때문에 불편입니다. 일반적인 선택: critic에 의해 학습된 `b(s_t) = V̂(s_t)` → actor-critic (레슨 07).
2. **수익-투-고.** `Σ_t G_t · ∇ log π_θ(a_t | s_t)`를 `Σ_t G_t^{from t} · ∇ log π_θ(a_t | s_t)`로 교체합니다. 주어진 행동에 대해 미래 수익만 중요합니다 — 과거 수익은 제로 평균 노이즈를贡献합니다.

결합하면:

`∇J ≈ (1/N) Σ_{i=1}^{N} Σ_{t=0}^{T_i} [ G_t^{(i)} - V̂(s_t^{(i)}) ] · ∇_θ log π_θ(a_t^{(i)} | s_t^{(i)})`

이는 기본선을 가진 REINFORCE이며, A2C (레슨 07)와 PPO (레슨 08)의 직접적 조상입니다.

**이산 행동을 위한 표준 선택:**

`π_θ(a | s) = exp(f_θ(s, a)) / Σ_{a'} exp(f_θ(s, a'))`

여기서 `f_θ`는 행동당 점수를 출력하는 신경망입니다. 기울기에 깔끔한 형태가 있습니다:

`∇_θ log π_θ(a | s) = ∇_θ f_θ(s, a) - Σ_{a'} π_θ(a' | s) ∇_θ f_θ(s, a')`

즉, 취한 행동의 점수 minus 정책 아래에서의 기대값.

**연속 행동을 위한 가우시안 정책.** `π_θ(a | s) = N(μ_θ(s), σ_θ(s))`. `∇ log N(a; μ, σ)`는 닫힌 형태를 가집니다. 그것이 단계 9 · 07의 SAC에 필요한 전부입니다.

## 실습

### Step 1: 소프트맥스 정책 네트워크

```python
def policy_logits(theta, state_features):
    return [dot(theta[a], state_features) for a in range(N_ACTIONS)]

def softmax(logits):
    m = max(logits)
    exps = [exp(l - m) for l in logits]
    Z = sum(exps)
    return [e / Z for e in exps]
```

표形式 환경에 대해 선형 정책(행동당 하나의 가중치 벡터)을 사용합니다. Atari의 경우, CNN을 넣고 소프트맥스 head를 유지합니다.

### Step 2: 샘플링과 로그 확률

```python
def sample_action(probs, rng):
    x = rng.random()
    cum = 0
    for a, p in enumerate(probs):
        cum += p
        if x <= cum:
            return a
    return len(probs) - 1

def log_prob(probs, a):
    return log(probs[a] + 1e-12)
```

### Step 3: 로그 확률을 캡처한 rollout

```python
def rollout(theta, env, rng, gamma):
    trajectory = []
    s = env.reset()
    while not done:
        logits = policy_logits(theta, s)
        probs = softmax(logits)
        a = sample_action(probs, rng)
        s_next, r, done = env.step(s, a)
        trajectory.append((s, a, r, probs))
        s = s_next
    return trajectory
```

### Step 4: REINFORCE 업데이트

```python
def reinforce_step(theta, trajectory, gamma, lr, baseline=0.0):
    returns = compute_returns(trajectory, gamma)
    for (s, a, _, probs), G in zip(trajectory, returns):
        advantage = G - baseline
        grad_log_pi_a = [-p for p in probs]
        grad_log_pi_a[a] += 1.0
        for i in range(N_ACTIONS):
            for j in range(len(s)):
                theta[i][j] += lr * advantage * grad_log_pi_a[i] * s[j]
```

기울기 `∇ log π(a|s) = e_a - π(·|s)` (a의 원핫 minus 확률)는 소프트맥스 정책 기울기의 핵심입니다. 그것을 근육 기억에 새기세요.

### Step 5: 기본선

최근 에피소드에 걸친 `G`의 실행 평균이면 분산 감소에 충분하여 4×4 GridWorld가 실행됩니다; 수렴하는 데 ~500 에피소드가 걸립니다. 기본선을 학습된 `V̂(s)`로 업그레이드하면 actor-critic을 얻습니다.

## 함정

- **기울기 폭발.** 수익이 huge할 수 있습니다. `∇ log π`에 곱하기 전에 배치에서 `G`를 `~N(0, 1)`로 항상 정규화하세요.
- **엔트로피 붕괴.** 정책이 너무 일찍 near-결정론적 행동으로 수렴하고, 탐험을 멈추고, 갇힙니다. 수정: 목적에 엔트로피 보너스 `β · H(π(·|s))`를 추가합니다.
- **높은 분산.** 바닐라 REINFORCE는 수천 에피소드가 필요합니다. critic 기본선(레슨 07) 또는 TRPO/PPO의 신뢰 영역(레슨 08)이 표준 수정입니다.
- **샘플 비효율.** 온정책은 한 업데이트 후 모든 전환을 버립니다. 중요도 샘플링을 통한 오프정책 수정은 데이터를 다시 가져오지만 분산 비용이 듭니다 (PPO의 비율은 클리핑된 IS 가중치입니다).
- **비정Stationary 기울기.** 100 에피소드 전의 동일한 기울기는古い `π`를 사용합니다. 온정책 방법은 이 이유로 몇 rollout마다 업데이트합니다.
- **크레딧 할당.** 수익-투-고 없이는 과거 수익이 노이즈를 contribution합니다. 항상 수익-투-고를 사용하세요.

## 활용

2026년, REINFORCE는 직접 실행되는 것이 드물지만 그 기울기 공식은 어디에나 있습니다:

| 사용 사례 | 파생 방법 |
|----------|----------|
| 연속 제어 | 가우시안 정책이 있는 PPO / SAC |
| LLM RLHF | 참조 모델에 대한 KL 페널티가 있는 PPO, 토큰 수준 정책에서 실행 |
| LLM 추론 (DeepSeek) | GRPO — critic 없는 REINFORCE, 그룹 상대 기본선 |
| 다중 에이전트 | 중앙 집중형 critic REINFORCE (MADDPG, COMA) |
| 이산 행동 로봇 공학 | A2C, A3C, PPO |
| 선호도만 있는 설정 | DPO — 선호도 우도 손실로 다시 작성된 REINFORCE, 샘플링 없음 |

2026년 훈련 스크립트에서 `loss = -advantage * log_prob`를 읽으면, 그것은 기본선을 가진 REINFORCE입니다.Entire papers (DPO, GRPO, RLOO)는 이 한 줄 위에 있는 분산 감소 트릭입니다.

## 결과물

`outputs/skill-policy-gradient-trainer.md`로 저장:

```markdown
---
name: policy-gradient-trainer
description: 주어진 작업에 대한 REINFORCE / actor-critic / PPO 훈련 구성을 생성하고 분산 문제를 진단합니다.
version: 1.0.0
phase: 9
lesson: 6
tags: [rl, policy-gradient, reinforce]
---

환경(이산 / 연속 행동, 시야, 보상 통계)이 주어지면 출력:

1. 정책 head. 소프트맥스(이산) 또는 가우시안(연속), 매개변수 수.
2. 기본선. 없음(바닐라), 실행 평균, 학습된 `V̂(s)`, 또는 A2C critic.
3. 분산 제어. 수익-투-고는 기본적으로 켜짐, 수익 정규화, 기울기 클립 값.
4. 엔트로피 보너스. 계수 β와衰减 스케줄.
5. 배치 크기. 업데이트당 에피소드; 온정책 데이터 신선도 계약.

> 500단계 시야에서 기본선 없는 REINFORCE 거부. 소프트맥스 head로 연속 행동 제어 거부. β = 0이고 관찰된 정책 엔트로피 < 0.1인 모든 실행을 엔트로피 붕괴로 플래그.
```

## 연습 문제

1. **쉬움.** 선형 소프트맥스 정책으로 4×4 GridWorld에서 REINFORCE를 구현하세요. 기본선 없이 1,000 에피소드 훈련하세요. 학습 곡선을 플롯하세요; 수익의 분산(표준 편차)을 측정하세요.
2. **보통.** 실행 평균 기본선을 추가하세요. 다시 훈련하세요. 바닐라 실행과 샘플 효율성과 분산을 비교하세요. 기본선이 수렴 단계수를 얼마나 줄여주나요?
3. **어려움.** 엔트로피 보너스 `β · H(π)`를 추가하세요. `β ∈ {0, 0.01, 0.1, 1.0}`을 sweep하세요. 최종 수익과 정책 엔트로피를 플롯하세요. 이 작업에서 스위트 스팟은 어디에 있나요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 정책 기울기 | "정책을 직접 훈련" | `∇J(θ) = E[G · ∇ log π_θ(a\|s)]`; log-미분 트릭에서 파생됩니다. |
| REINFORCE | "원래 PG 알고리즘" | Williams (1992); 로그 정책 기울기에 곱해진 몬테 카를로 수익. |
| Log-미분 트릭 | "점수 함수 추정기" | `∇P(τ;θ) = P(τ;θ) · ∇ log P(τ;θ)`; 기대값의 기울기를 다룰 수 있게 합니다. |
| 기본선 | "분산 감소" | `G`에서 빼는 모든 `b(s)`; `E[b · ∇ log π] = 0`이기 때문에 불편합니다. |
| 수익-투-고 | "미래 수익만 count" | 전체 `G_0` 대신 `G_t^{from t}`; 정확하고更低 분산. |
| 엔트로피 보너스 | "탐험 장려" | 정책이 붕괴하는 것을 방지하는 `+β · H(π(·\|s))` 항. |
| 온정책 | "방금 본 것으로 훈련" | 기대값이 현재 정책에 대한 것입니다 — 오래된 데이터를 직접 재사용할 수 없습니다. |
| 이점 | "평균보다 얼마나 나은가" | `A(s, a) = G(s, a) - V(s)`; REINFORCE-기본선이 곱하는 부호 있는 양. |

## 추가 자료

- [Williams (1992). Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning](https://link.springer.com/article/10.1007/BF00992696) — 원래 REINFORCE 논문.
- [Sutton et al. (2000). Policy Gradient Methods for Reinforcement Learning with Function Approximation](https://papers.nips.cc/paper_files/paper/1999/hash/464d828b85b0bed98e80ade0a5c43b0f-Abstract.html) — 함수 근사가 있는 현대적인 정책 기울기 정리.
- [Sutton & Barto (2018). Ch. 13 — Policy Gradient Methods](http://incompleteideas.net/book/RLbook2020.pdf) — 교과서 제시.
- [OpenAI Spinning Up — VPG / REINFORCE](https://spinningup.openai.com/en/latest/algorithms/vpg.html) — PyTorch 코드로 된 명확한 교육적 설명.
- [Peters & Schaal (2008). Reinforcement Learning of Motor Skills with Policy Gradients](https://homes.cs.washington.edu/~todorov/courses/amath579/reading/PolicyGradient.pdf) — 분산 감소와 TRPO, PPO로 연결되는 자연스러운 기울기 관점.