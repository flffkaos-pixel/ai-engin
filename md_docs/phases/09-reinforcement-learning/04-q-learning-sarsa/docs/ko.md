# 시간 차분 — Q-Learning과 SARSA

> 몬테 카를로는 에피소드가 끝날 때까지 기다립니다. TD는 다음 가치 추정을 부트스트랩하여 각 단계 후에 업데이트합니다. Q-learning은 오프정책이고 낙관적입니다; SARSA는 온정책이고 신중합니다. 둘 다 한 줄의 코드입니다. 둘 다 이 단계의 모든 깊은 RL 방법의 기반입니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 9 · 01 (MDPs), Phase 9 · 02 (Dynamic Programming), Phase 9 · 03 (Monte Carlo)
**소요 시간:** ~75분

## 문제

몬테 카를로는 작동하지만 두 가지 비용이 많이 드는 요구事项이 있습니다. 종료되는 에피소드가 필요하며, 최종 수익이 들어온 후에만 업데이트합니다. 에피소드가 1,000단계이면, MC는 아무것도 업데이트하기 위해 1,000단계를 기다립니다. 실제로는 고분산, 저편향, 느립니다.

동적 프로그래밍은 반대 프로파일을 가집니다 — 제로 분산 부트스트랩 백업 — 하지만 알려진 모델이 필요합니다.

시간 차분(TD) 학습은 차이를 나눕니다. 단일 전환 `(s, a, r, s')`에서, 한 단계 목표 `r + γ V(s')`를 형성하고 `V(s)`를 그것을 향해 nudge합니다. 모델 없음. 완전한 에피소드 없음. RHS에서 근사 `V`를 사용한 편향, 하지만 MC보다 현저히 낮은 분산과 단계 1からの 온라인 업데이트.

이것이 모든 현대 RL — DQN, A2C, PPO, SAC — 가 회전하는 피벗입니다. 단계 9의 나머지는 이 레슨에서 작성할 한 단계 TD 업데이트 위에 구축된 함수 근사와 트릭의 레이어입니다.

## 개념

![Q-learning vs SARSA: 오프정책 max vs 온정책 Q(s', a')](../assets/td.svg)

**V에 대한 TD(0) 업데이트:**

`V(s) ← V(s) + α [r + γ V(s') - V(s)]`

대괄호 안의 양은 TD 오류 `δ = r + γ V(s') - V(s)`입니다. MC에서 `G_t - V(s_t)`의 온라인 analogue입니다. 수렴은 `α`가 Robbins-Monro(`Σ α = ∞`, `Σ α² < ∞`)를 만족하고 모든 상태가 무한히 자주 방문되면 필요합니다.

**Q-learning.** 제어를 위한 오프정책 TD 방법:

`Q(s, a) ← Q(s, a) + α [r + γ max_{a'} Q(s', a') - Q(s, a)]`

`max`는 에이전트가 실제로 취하는 행동에 관계없이 `s'`からの 탐욕적 정책이 따를 것임을 가정합니다. 그 해제는 Q-learning이 ε-탐욕적으로 탐험하는 동안 `Q*`를 학습하게 합니다. Mnih et al. (2015)은 이것을 Atari에서 깊은 Q-learning으로 변환했습니다(레슨 05).

**SARSA.** 제어를 위한 온정책 TD 방법:

`Q(s, a) ← Q(s, a) + α [r + γ Q(s', a') - Q(s, a)]`

이름은 튜플 `(s, a, r, s', a')`입니다. SARSA는 탐욕적 `argmax`가 아니라 에이전트가 *실제로* 다음에 취하는 행동 `a'`를 사용합니다. 수렴하면 실행 중인 ε-탐욕적 `π`에 대해 `Q^π`가 되고, 극한에서 `ε → 0`이면 `Q*`가 됩니다.

**클리프 워킹 차이.** 클래식 클리프 워킹 작업에서(절벽으로 떨어짐 = 보상 -100), Q-learning은 절벽 가장자리를 따라 최적 경로를 학습하지만 탐험 중 가끔 페널티를 받습니다. SARSA는 탐험 노이즈를 Q-값에 factoring하기 때문에 절벽에서 한 걸음 떨어진 더 안전한 경로를 학습합니다. 훈련으로 둘 다 `ε → 0`에서 최적에 도달합니다. 실제로 그것이 중요합니다: 배포 시 실제로 탐험이 발생하면, SARSA의 행동이 더 보수적입니다.

**Expected SARSA.** `Q(s', a')`를 `π` 하에서의 기대값으로 교체:

`Q(s, a) ← Q(s, a) + α [r + γ Σ_{a'} π(a'|s') Q(s', a') - Q(s, a)]`

SARSA보다 낮은 분산(`a'`의 샘플 없음), 동일한 온정책 목표. 현대 교과서에서 자주 기본입니다.

**n-단계 TD와 TD(λ).** 부트스트래핑하기 전에 `n` 스텝을 기다려서 TD(0)와 MC 사이를 보간합니다. `n=1`은 TD, `n=∞`은 MC. TD(λ)는 기하학적 가중치 `(1-λ)λ^{n-1}`로 모든 `n`에 대해 평균을 냅니다. 대부분의 깊은 RL은 3에서 20 사이의 `n`을 사용합니다.

## 실습

### Step 1: ε-탐욕적 정책에서 SARSA

```python
def sarsa(env, episodes, alpha=0.1, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})

    def choose(s):
        if random() < epsilon:
            return choice(ACTIONS)
        return max(Q[s], key=Q[s].get)

    for _ in range(episodes):
        s = env.reset()
        a = choose(s)
        while True:
            s_next, r, done = env.step(s, a)
            a_next = choose(s_next) if not done else None
            target = r + (gamma * Q[s_next][a_next] if not done else 0.0)
            Q[s][a] += alpha * (target - Q[s][a])
            if done:
                break
            s, a = s_next, a_next
    return Q
```

여덟 줄. Q-learning과의 *유일한* 차이점은 목표 줄입니다.

### Step 2: Q-learning

```python
def q_learning(env, episodes, alpha=0.1, gamma=0.99, epsilon=0.1):
    Q = defaultdict(lambda: {a: 0.0 for a in ACTIONS})
    for _ in range(episodes):
        s = env.reset()
        while True:
            a = choose(s, Q, epsilon)
            s_next, r, done = env.step(s, a)
            target = r + (gamma * max(Q[s_next].values()) if not done else 0.0)
            Q[s][a] += alpha * (target - Q[s][a])
            if done:
                break
            s = s_next
    return Q
```

`max`가 목표와 행동을 decoupling합니다. 그 기호 하나가 온정책과 오프정책의 차이입니다.

### Step 3: 학습 곡선

에피소드당 평균 수익을 추적합니다. Q-learning은 간단한 결정론적 GridWorld에서 더 빨리 수렴합니다; SARSA는 클리프 워킹에서 더 보수적입니다. `code/main.py`의 4×4 GridWorld에서, 둘 다 `α=0.1, ε=0.1`로 ~2,000 에피소드 후 near-optimal에 있습니다.

### Step 4: DP 진실과 비교

가치 반복(레슨 02)을 실행하여 `Q*`를 얻으세요. `max_{s,a} |Q_learned(s,a) - Q*(s,a)|`를 확인하세요. 건강한 표形式 TD 에이전트는 10,000 에피소드 후 4×4 GridWorld에서 `~0.5` 이내에 있습니다.

## 함정

- **초기 Q 값이 중요합니다.** 낙관적 초기화(음수 보상 작업에서 `Q = 0`)는 탐험을 장려합니다. 비관적 초기화는 탐욕적 정책을 영원히 갇힐 수 있습니다.
- **α 스케줄.** 상수 `α`는 비정Stationary 문제에 괜찮습니다. decaying `α_n = 1/n`은 이론적으로 수렴하지만 실제로는 너무 느립니다 — `[0.05, 0.3]`에서 `α`를 고정하고 학습 곡선을 모니터하세요.
- **ε 스케줄.** 높게 시작(`ε=1.0`), `ε=0.05`로 감소. "GLIE"(무한 탐험으로 한계에서 탐욕)는 수렴 조건입니다.
- **Q-learning의 최대 편향.** `max` 연산자는 `Q`가 노이즈일 때 위로 편향됩니다. 과대 추정으로 이어집니다 — Hasselt의 Double Q-learning(레슨 05의 DDQN에서 사용)이 두 개의 Q 테이블로 이를 수정합니다.
- **비종료 에피소드.** TD는终端 없이 학습할 수 있지만, 단계限制 또는限制에서 부트스트랩을 올바르게 처리해야 합니다. 표준:限制을 비종착으로 처리하고, 부트스트래핑을 계속합니다.
- **상태 해싱.** 상태가 튜플/텐서이면, 해시 가능한 키를 사용하세요(리스트가 아닌 튜플; raw가 아닌 반올림된 floats의 튜플).

## 활용

2026년 TD 환경:

| 작업 | 방법 | 이유 |
|------|------|------|
| 작은 표形式 환경 | Q-learning | 직접 최적 정책을 학습합니다. |
| 온정책 안전 Kritikal | SARSA / Expected SARSA | 탐험 중 보수적입니다. |
| 고차원 상태 | DQN (단계 9 · 05) | 리플레이와 대상 net이 있는 신경망 Q-함수. |
| 연속 행동 | SAC / TD3 (단계 9 · 07) | Q-network에 대한 TD 업데이트; 정책 net이 행동을 emission합니다. |
| LLM RL (보상 모델 기반) | PPO / GRPO (단계 9 · 08, 12) | GAE를 통한 TD 스타일 이점의 actor-critic. |
| 오프라인 RL | CQL / IQL (단계 9 · 08) | OOD 행동에 conservative 정규화가 있는 Q-learning. |

2026년 논문에서 "RL"이라 불리는 것의 90%는 Q-learning 또는 SARSA의 어떤 elaboration입니다. 더 깊이 읽기 전에 표形式 업데이트를 손가락으로 이해하세요.

## 결과물

`outputs/skill-td-agent.md`로 저장:

```markdown
---
name: td-agent
description: 표形式 또는 작은 특성 RL 작업에 대해 Q-learning, SARSA, Expected SARSA中选择합니다.
version: 1.0.0
phase: 9
lesson: 4
tags: [rl, td-learning, q-learning, sarsa]
---

표形式 또는 작은 특성 환경이 주어지면 출력:

1. 알고리즘. Q-learning / SARSA / Expected SARSA / n-step 변형. 온정책 vs 오프정책과 분산에 관련된 한 문장 이유.
2. 하이퍼파라미터. α, γ, ε,衰减 스케줄.
3. 초기화. Q_0 값(낙관적 vs 영)과 justification.
4. 수렴 진단. 목표 학습 곡선, DP가 가능하면 `|Q - Q*|` 확인.
5. 배포 주의. 추론에서 탐험이 어떻게 작동하나요? SARSA의 보수주의가 필요합니까?

> 10⁶보다 큰 상태 공간에 표形式 TD 적용 거부. 최대 편향caveat 없이 Q-learning 에이전트 shipping 거부. 훈련 전체에서 ε가 1.0으로 유지된 에이전트 플래그(착취 단계 없음).
```

## 연습 문제

1. **쉬움.** 4×4 GridWorld에서 Q-learning과 SARSA를 구현하세요. 2,000 에피소드에 대해 100 에피소드당 평균 수익을 플롯하세요. 누가 더 빨리 수렴하나요?
2. **보통.** 클리프 워킹 환경 구축(4×12, 마지막 행이 보상 -100와 시작점으로 재설정되는 절벽). Q-learning과 SARSA 최종 정책을 비교하세요. 각 정책이 취하는 경로의 스크린샷.哪个가 절벽에 더 가까워요?
3. **어려움.** Double Q-learning을 구현하세요. 노이즈 보상 GridWorld(단계별 보상에 Gaussian 노이즈 σ=5 추가)에서, Q-learning이 `V*(0,0)`를 의미 있는 양만큼 과대 추정하는 반면 Double Q-learning은 그렇지 않음을 보여주세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| TD 오류 | "업데이트 신호" | `δ = r + γ V(s') - V(s)`, 부트스트랩된 잔차. |
| TD(0) | "한 단계 TD" | 모든 전환 후 다음 상태의 추정만 사용하여 업데이트합니다. |
| Q-learning | "오프정책 RL 101" | 다음 상태 행동에 대한 `max`가 있는 TD 업데이트; 행동 정책에 관계없이 `Q*`를 학습합니다. |
| SARSA | "온정책 Q-learning" | 실제 다음 동작을 사용한 TD 업데이트; 현재 ε-탐욕적 π에 대해 `Q^π`를 학습합니다. |
| Expected SARSA | "저분산 SARSA" | 샘플된 `a'`를 π 하에서의 기대값으로 교체합니다. |
| GLIE | "올바른 탐험 스케줄" | 무한 탐험으로 한계에서의 탐욕; Q-learning 수렴에 필요합니다. |
| 부트스트래핑 | "현재 추정치를 목표에서 사용" | TD를 MC와区別하는 것. 편향의 원이지만 엄청난 분산 감소. |
| 최대화 편향 | "Q-learning이 과대 추정" | 노이즈 추정에 대한 `max`는 위로 편향됩니다; Double Q-learning으로 수정됩니다. |

## 추가 자료

- [Watkins & Dayan (1992). Q-learning](https://link.springer.com/article/10.1007/BF00992698) — 원래 논문과 수렴 증명.
- [Sutton & Barto (2018). Ch. 6 — Temporal-Difference Learning](http://incompleteideas.net/book/RLbook2020.pdf) — TD(0), SARSA, Q-learning, Expected SARSA.
- [Hasselt (2010). Double Q-learning](https://papers.nips.cc/paper_files/paper/2010/hash/091d584fced301b442654dd8c23b3fc9-Abstract.html) — 최대화 편향 수정.
- [Seijen, Hasselt, Whiteson, Wiering (2009). A Theoretical and Empirical Analysis of Expected SARSA](https://ieeexplore.ieee.org/document/4927542) — expected SARSA 동기.
- [Rummery & Niranjan (1994). On-line Q-learning using connectionist systems](https://www.researchgate.net/publication/2500611_On-Line_Q-Learning_Using_Connectionist_Systems) — SARSA라는 이름을 만든 논문(당시 "수정된 연결주의 Q-learning"이라 불림).
- [Sutton & Barto (2018). Ch. 7 — n-step Bootstrapping](http://incompleteideas.net/book/RLbook2020.pdf) — TD(0)을 TD(n)으로 일반화, Q-learning에서 eligibility traces로, 나중에 PPO의 GAE로.