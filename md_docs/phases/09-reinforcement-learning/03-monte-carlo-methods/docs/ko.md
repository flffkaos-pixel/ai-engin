# 몬테 카를로 방법 — 완전한 에피소드からの学習

> 동적 프로그래밍은 모델이 필요합니다. 몬테 카를로는 에피소드만 있으면 됩니다. 정책을 실행하고, 수익을 관찰하고, 평균을 냅니다. RL에서 가장 간단한 아이디어 — 그리고 그것이下游のすべてをロック解除します.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 9 · 01 (MDPs), Phase 9 · 02 (Dynamic Programming)
**소요 시간:** ~75분

## 문제

동적 프로그래밍은 우아하지만 모델을 쿼리할 수 있다고 가정합니다 `P(s' | s, a)` 모든 상태와 행동에 대해. 현실 세계에서는 거의 없습니다. 로봇은 관절 토크 후 카메라 픽셀의 분포를 분석적으로 계산할 수 없습니다. 가격 알고리즘은 모든 가능한 고객 반응에 대해 적분할 수 없습니다. LLM은 토큰 후 가능한 모든 확장을 열거할 수 없습니다.

환경에서 *샘플*만 추출할 수 있는 방법이 필요합니다. 정책을 실행하세요. 궤적 `s_0, a_0, r_1, s_1, a_1, r_2, …, s_T`를 얻으세요.用它来估计值。那就是蒙特卡洛。

DP에서 MC로의 전환은 철학적으로 중요합니다: *알려진 모델 + 정확한 백업*에서 *샘플링된 rollout + 평균 수익*으로 이동합니다. 분산이 뛰지만 적용 가능성이 폭발합니다. 이 레슨 이후의 모든 RL 알고리즘 — TD, Q-learning, REINFORCE, PPO, GRPO —은 본질적으로 몬테 카를로 추정기이며, 때때로 부트스트래핑이 위에 레이어됩니다.

## 개념

![몬테 카를로: rollout, 수익 계산, 평균; 첫 방문 vs 매 방문](../assets/monte-carlo.svg)

**핵심 아이디어, 한 줄:** `V^π(s) = E_π[G_t | s_t = s] ≈ (1/N) Σ_i G^{(i)}(s)` 여기서 `G^{(i)}(s)`는 정책 `π` 하에서 `s` 방문 following의 관찰된 수익입니다.

**첫 방문 대 매 방문 MC.** `s`를 여러 번 방문하는 에피소드가 주어지면, 첫 방문 MC는 첫 방문의 수익만 计算하고; 매 방문 MC는 모든 방문을 计算합니다. 둘 다 극한에서 불편입니다. 첫 방문은 분석하기 더 간단합니다(iid 샘플). 매 방문은 에피소드당 더 많은 데이터를 사용하고 일반적으로 실제로 더 빨리 수렴합니다.

**증분 평균.** 모든 수익을 저장하는 대신, 실행 평균을 업데이트합니다:

`V_n(s) = V_{n-1}(s) + (1/n) [G_n - V_{n-1}(s)]`

재구성: `V_new = V_old + α · (target - V_old)` 여기서 `α = 1/n`. `1/n`을 상수 단계 크기 `α ∈ (0, 1)`로 교체하면 `π`의 변경을 추적하는 비정Stationary MC 추정기가 됩니다. 그 이동이 MC에서 TD로 모든 현대 RL 알고리즘으로의 전체 점프입니다.

**탐험이 이제 문제입니다.** DP는 열거로 모든 상태를 터치했습니다. MC는 정책이 방문하는 상태만 봅니다. `π`가 결정론적이면, 상태 공간의 전체 영역이 결코 샘플링되지 않고, 그 가치 추정이 영원히 0에 머무릅니다. 세 가지 수정, 역사적 순서로:

1. **탐험적 시작.** 각 에피소드를 무작위 (s, a) 쌍에서 시작합니다. 커버리지를 보장합니다; 실제로는 비현실적입니다(로봇을 임의의 상태로 "재설정"할 수 없습니다).
2. **ε-탐욕적.** 현재 Q에 대해 탐욕적으로 행동하되, 확률 `ε`로 무작위 행동을 선택합니다. 모든 상태-행동 쌍이 점근적으로 샘플링됩니다.
3. **오프정책 MC.** 행동 정책 `μ` 하에서 데이터를 수집하고, 중요도 샘플링을 통해 목표 정책 `π`에 대해 학습합니다. 높은 분산이지만 DQN과 같은 리플레이 버퍼 방법으로의 다리입니다.

**몬테 카를로 제어.** 평가 → 개선 → 평가, 정책 반복과 동일하지만, 평가는 샘플링 기반입니다:

1. `π`를 실행하고 에피소드를 얻습니다.
2. 관찰된 수익에서 `Q(s, a)`를 업데이트합니다.
3. `Q`에 대해 ε-탐욕적으로 `π`를 만들었습니다.
4. 반복합니다.

완만한 조건에서 `Q*`와 `π*`로 수렴합니다(모든 쌍이 무한히 자주 방문, `α`가 Robbins-Monro를 만족).

## 실습

### Step 1: rollout → (s, a, r) 리스트

```python
def rollout(env, policy, max_steps=200):
    trajectory = []
    s = env.reset()
    for _ in range(max_steps):
        a = policy(s)
        s_next, r, done = env.step(s, a)
        trajectory.append((s, a, r))
        s = s_next
        if done:
            break
    return trajectory
```

모델 없음, `env.reset()`과 `env.step(s, a)`만 있습니다. gym 환경과 동일한 인터페이스이지만 분리된 상태.

### Step 2: 수익 계산 (역방향 스윕)

```python
def returns_from(trajectory, gamma):
    returns = []
    G = 0.0
    for _, _, r in reversed(trajectory):
        G = r + gamma * G
        returns.append(G)
    return list(reversed(returns))
```

한 번 통과, `O(T)`. 역방향 재귀 `G_t = r_{t+1} + γ G_{t+1}`는 다시 합산하는 것을避けます.

### Step 3: 첫 방문 MC 평가

```python
def mc_policy_evaluation(env, policy, episodes, gamma=0.99):
    V = defaultdict(float)
    counts = defaultdict(int)
    for _ in range(episodes):
        trajectory = rollout(env, policy)
        returns = returns_from(trajectory, gamma)
        seen = set()
        for t, ((s, _, _), G) in enumerate(zip(trajectory, returns)):
            if s in seen:
                continue
            seen.add(s)
            counts[s] += 1
            V[s] += (G - V[s]) / counts[s]
    return V
```

세 줄이 작동합니다: 첫 방문 시 상태를 seen으로 표시, 카운트 증가, 실행 평균 업데이트.

### Step 4: ε-탐욕적 MC 제어 (온-policy)

```python
def mc_control(env, episodes, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})
    counts = defaultdict(lambda: {a: 0 for a in ACTIONS})

    def policy(s):
        if random() < epsilon:
            return choice(ACTIONS)
        return max(Q[s], key=Q[s].get)

    for _ in range(episodes):
        trajectory = rollout(env, policy)
        returns = returns_from(trajectory, gamma)
        seen = set()
        for (s, a, _), G in zip(trajectory, returns):
            if (s, a) in seen:
                continue
            seen.add((s, a))
            counts[s][a] += 1
            Q[s][a] += (G - Q[s][a]) / counts[s][a]
    return Q, policy
```

### Step 5: DP 금책策策との比較

MC의 `V^π` 추정은 에피소드가 ∞로 갈 때 DP 결과(레슨 02)와 일치해야 합니다. 실제로: 4×4 GridWorld에서 50,000 에피소드가 DP 답변의 `~0.1` 이내에 있습니다.

## 함정

- **무한 에피소드.** MC는 에피소드가 *종료*되기를 요구합니다. 정책이 영원히 루프할 수 있으면, `max_steps`로 제한하고cap를 암묵적 실패로 처리하세요. 무작위 정책의 GridWorld는 routinely 시간 초과됩니다 — 이것은 정상이며, 올바르게 count하는지 확인하세요.
- **분산.** MC는 전체 수익을 사용합니다. 긴 에피소드에서 분산이 큽니다 — 끝에서 불행한 수익이 하나 있으면 `V(s_0)`가 동일한 양만큼 shift됩니다. TD 방법(레슨 04)이 이것을 줄입니다.
- **상태 커버리지.** 새 Q에서 타이가 있는 탐욕적 MC는 하나의 행동만 시도합니다. 반드시 탐험해야 합니다(ε-탐욕적, 탐험적 시작, UCB).
- **비정Stationary 정책.** `π`가 변경되면(MC 제어에서처럼), 오래된 수익은 다른 정책에서 나온 것입니다. 상수-α MC는 이것을 처리합니다; 샘플 평균 MC는 처리하지 못합니다.
- **오프정책 중요도 샘플링.** 가중치 `π(a|s)/μ(a|s)`가 궤적을 가로질러 곱해집니다. 분산이 시야와 함께 폭발합니다. 에피소드당 가중 IS 또는 TD로 제한하세요.

## 활용

2026년 몬테 카를로 방법의 역할:

| 사용 사례 | 왜 MC인가 |
|----------|----------|
| 짧은 시야 게임 (블랙잭, 포커) | 에피소드가 자연스럽게 종료됩니다; 수익이 깔끔합니다. |
| 기록된 정책의 오프라인 평가 | 저장된 궤적에 대한 평균 할인 수익. |
| 몬테 카를로 트리 검색 (AlphaZero) | 트리 리프からの MC rollouts가 선택을 안내합니다. |
| LLM RL 평가 | 주어진 정책에 대해 샘플링된 완성품에 대한 평균 보상 계산. |
| PPO의 기본선 추정 | 이점 목표 `A_t = G_t - V(s_t)`가 MC `G_t`를 사용합니다. |
| RL 가르치기 | 실제로 작동하는 가장 간단한 알고리즘 — 부트스트래핑을 제거하여 핵심을 보기. |

현대 깊은 RL 알고리즘(PPO, SAC)은 순수 MC(전체 수익)에서 순수 TD(한 단계 부트스트랩)까지 `n`-단계 수익 또는 GAE를 통해 보간합니다. 두 끝점은 동일한 추정기의 인스턴스입니다.

## 결과물

`outputs/skill-mc-evaluator.md`로 저장:

```markdown
---
name: mc-evaluator
description: 몬테 카를로 rollouts을 통해 정책을 평가하고 DP 비교가 가능하면 수렴 보고서를 생성합니다.
version: 1.0.0
phase: 9
lesson: 3
tags: [rl, monte-carlo, evaluation]
---

환경(에피소드, reset+step API)과 정책이 주어지면 출력:

1. 방법. 첫 방문 vs 매 방문 MC. 이유.
2. 에피소드 예산.目标 수, 분산 진단, 예상 표준 오차.
3. 탐험 플랜. ε 스케줄(필요한 경우) 또는 탐험적 시작.
4. 금책策策 비교. 표形式이면 DP 최적 `V*`; 그렇지 않으면 Q-learning / PPO 기본선からの bound.
5. 종료 확인. 최대 단계 한계, 시간 초과, 비종료 궤적 처리.

비에피소드 작업에서 유한한 시야 한계 없이 MC 실행 거부. 표形式 작업에 대해 상태당 100 에피소드 미만의 V^π 추정치를 보고 거부. 제로 분산 행동이 있는 정책을 탐험 위험으로 플래그.
```

## 연습 문제

1. **쉬움.** 4×4 GridWorld에서 균일 무작위 정책의 첫 방문 MC 평가를 구현하세요. 10,000 에피소드 실행. 에피소드 함수의 `V(0,0)`를 DP 답변에 대해 플롯하세요.
2. **보통.** `ε ∈ {0.01, 0.1, 0.3}`로 ε-탐욕적 MC 제어를 구현하세요. 20,000 에피소드 후 평균 수익을 비교하세요. 곡선이 어떻게 생겼나요? 편향-분산 균형 tradeoff는 어디에 있나요?
3. **어려움.** *오프정책* MC를 중요도 샘플링으로 구현: 균일 무작위 정책 `μ` 하에서 데이터를 수집하고, 결정론적 최적 정책 `π`에 대한 `V^π`를 추정하세요. 평범 IS vs 에피소드당 IS vs 가중 IS를 비교하세요.哪个의 분산이 가장 낮나요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 몬테 카를로 | "무작위 샘플링" | 분포からの iid 샘플에 대한 평균을 통해 기대치를 추정합니다. |
| 수익 `G_t` | "미래 보상" | 단계 `t`에서 에피소드 끝까지의 할인된 보상 합: `Σ_{k≥0} γ^k r_{t+k+1}`. |
| 첫 방문 MC | "각 상태를 한 번만 count" | 에피소드의 첫 번째 방문만 가치 추정에 기여합니다. |
| 매 방문 MC | "모든 방문 사용" | 모든 방문이 기여합니다; 약간 편향되었지만 더 샘플 효율적입니다. |
| ε-탐욕적 | "탐험 노이즈" | 확률 `1-ε`로 탐욕적 행동 선택; 확률 `ε`로 무작위 행동. |
| 중요도 샘플링 | "잘못된 분포からの 샘플링에 대한 보정" | `μ` 데이터에서 `V^π`를 추정하기 위해 `π(a\|s)/μ(a\|s)` 곱으로 수익을 재가중합니다. |
| 온-policy | "내 자신의 데이터에서 학습" | 목표 정책 = 행동 정책. 바닐라 MC, PPO, SARSA. |
| 오프정책 | "다른 사람의 데이터에서 학습" | 목표 정책 ≠ 행동 정책. 중요도 샘플링된 MC, Q-learning, DQN. |

## 추가 자료

- [Sutton & Barto (2018). Ch. 5 — Monte Carlo Methods](http://incompleteideas.net/book/RLbook2020.pdf) — 표준 처리.
- [Singh & Sutton (1996). Reinforcement Learning with Replacing Eligibility Traces](https://link.springer.com/article/10.1007/BF00114726) — 첫 방문 vs 매 방문 분석.
- [Precup, Sutton, Singh (2000). Eligibility Traces for Off-Policy Policy Evaluation](http://incompleteideas.net/papers/PSS-00.pdf) — 오프정책 MC와 분산 제어.
- [Mahmood et al. (2014). Weighted Importance Sampling for Off-Policy Learning](https://arxiv.org/abs/1404.6362) — 현대 저분산 IS 추정기.
- [Tesauro (1995). TD-Gammon, A Self-Teaching Backgammon Program](https://dl.acm.org/doi/10.1145/203330.203343) — MC/TD 자가 플레이가 초인간 플레이로 수렴하는 첫 번째 대규모 경험적 시연; 이 단계의後半のすべての 레슨의 개념적 선구자.