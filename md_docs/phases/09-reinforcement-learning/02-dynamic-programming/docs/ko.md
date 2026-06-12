# 동적 프로그래밍 — 정책 반복과 가치 반복

> 동적 프로그래밍은 치팅이 있는 RL입니다. 전이 함수와 보상 함수를 이미 알고 있습니다; `V` 또는 `π`가 멈출 때까지 벨만 방정식을 반복하기만 하면 됩니다. 이것은 모든 샘플링 기반 방법이 접근하려고 하는 벤치마크입니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 9 · 01 (MDPs)
**소요 시간:** ~75분

## 문제

알고 있는 모델이 있는 MDP가 있습니다: 모든 상태-행동 쌍에 대해 `P(s' | s, a)`와 `R(s, a, s')`를 쿼리할 수 있습니다. 재고 관리자는 수요 분포를 압니다. 보드 게임은 결정론적 전이를 가집니다. 그리드월드는 네 줄의 Python입니다. 당신은 *모델*을 가지고 있습니다.

모델 프리 RL(Q-learning, PPO, REINFORCE)은 모델이 없을 때를 위해 발명되었습니다 — 환경에서 샘플만 추출할 수 있습니다. 하지만 가지고 있다면, 더 빠르고 더 나은 방법이 있습니다: 동적 프로그래밍. Bellman이 1957년에 설계했습니다. 그들은 여전히 정확성을 정의합니다: 사람들이 "이 MDP의 최적 정책"이라고 말할 때, 그들은 DP가 반환할 정책을 의미합니다.

2026년에 세 가지 이유가 필요합니다. 첫째, RL 연구의 모든 표形式 환경(GridWorld, FrozenLake, CliffWalking)은 금책策策策를 생성하기 위해 DP로 해결됩니다. 둘째, 정확한 값을 사용하면 *디버그* 샘플링 방법이 가능합니다: Q-learning의 `V*(s_0)` 추정이 DP 답변과 30% 다르면, Q-learning에 버그가 있습니다. 셋째, 현대 오프라인 RL 및 계획 방법(MCTS, AlphaZero의 검색, 단계 9 · 10의 모델 기반 RL)은 모두 학습되거나 주어진 모델에서 벨만 백업을 반복합니다.

## 개념

![정책 반복과 가치 반복, 나란히](../assets/dp.svg)

**두 알고리즘, 모두 벨만에서 고정점 반복.**

**정책 반복.** 정책이 변경되지 때까지 두 단계를 교대로 반복합니다.

1. *평가:* 정책 `π`가 주어지면, `V(s) ← Σ_a π(a|s) Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`를 수렴할 때까지 반복적으로 적용하여 `V^π`를 계산합니다.
2. *개선:* `V^π`가 주어지면, `V^π`에 대해 탐욕적입니다: `π(s) ← argmax_a Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`.

수렴이 보장됩니다, 왜냐하면 (a) 각 개선 단계는 `π`를 동일하게 유지하거나 일부 상태에서 `V^π`를 엄격히 증가시키고, (b) 결정론적 정책의 공간이 유한합니다. 일반적으로 대규모 상태 공간에서도 ~5–20번의 외부 반복에서 수렴합니다.

**가치 반복.** 평가와 개선을 한 스윕으로 통합합니다. 벨만 *최적성* 방정식을 적용합니다:

`V(s) ← max_a Σ_{s',r} P(s',r|s,a) [r + γ V(s')]`

`max_s |V_{new}(s) - V(s)| < ε`가 될 때까지 반복합니다. 마지막에 탐욕적 행동을 취하여 정책을 추출합니다..iter迭代당 더 빠릅니다 — 내부 평가 루프가 없습니다 — 하지만 일반적으로 수렴하려면 더 많은 반복이 필요합니다.

**일반화된 정책 반복(GPI).** 통합 프레임입니다. 가치 함수와 정책이 양방향 개선 루프에 묶여 있습니다; 둘 다 상호 일관성으로 driving하는 모든 방법(async 가치 반복, 수정된 정책 반복, Q-learning, actor-critic, PPO)은 GPI의 인스턴스입니다.

**`γ < 1`이 중요한 이유.** 벨만 연산자는 sup-norm에서 `γ`-수축입니다: `||T V - T V'||_∞ ≤ γ ||V - V'||_∞`. 수축은 고유한 고정점과 기하학적 수렴을 의미합니다. `γ < 1`을 제거하면 보장이 사라집니다 — 유한한 수평선 또는 흡수 종착 상태가 필요합니다.

## 실습

### Step 1: GridWorld MDP 모델 구축

레슨 01의 동일한 4×4 GridWorld를 사용합니다. 확률적 변형 추가: 확률 `0.1`로 에이전트가 무작위 수직 방향으로 미끄러집니다.

```python
SLIP = 0.1

def transitions(state, action):
    if state == TERMINAL:
        return [(state, 0.0, 1.0)]
    outcomes = []
    for direction, prob in action_probs(action):
        outcomes.append((apply_move(state, direction), -1.0, prob))
    return outcomes
```

`transitions(s, a)`는 `(s', r, p)`의 리스트를 반환합니다. 이것이 전체 모델입니다.

### Step 2: 정책 평가

정책 `π(s) = {action: prob}`가 주어지면, `V`가 멈출 때까지 벨만 방정식을 반복합니다:

```python
def policy_evaluation(policy, gamma=0.99, tol=1e-6):
    V = {s: 0.0 for s in states()}
    while True:
        delta = 0.0
        for s in states():
            v = sum(pi_a * sum(p * (r + gamma * V[s_prime])
                              for s_prime, r, p in transitions(s, a))
                   for a, pi_a in policy(s).items())
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < tol:
            return V
```

### Step 3: 정책 개선

`V`에 대해 탐욕적 정책으로 `π`를 교체합니다. `π`가 변경되지 않았으면 반환 — 최적에 도달했습니다.

```python
def policy_improvement(V, gamma=0.99):
    new_policy = {}
    for s in states():
        best_a = max(
            ACTIONS,
            key=lambda a: sum(p * (r + gamma * V[s_prime])
                              for s_prime, r, p in transitions(s, a)),
        )
        new_policy[s] = best_a
    return new_policy
```

### Step 4: 함께 연결

```python
def policy_iteration(gamma=0.99):
    policy = {s: "up" for s in states()}   # 임의의 시작
    for _ in range(100):
        V = policy_evaluation(lambda s: {policy[s]: 1.0}, gamma)
        new_policy = policy_improvement(V, gamma)
        if new_policy == policy:
            return V, policy
        policy = new_policy
```

4×4에서 일반적인 수렴: 4–6번의 외부 반복. `V*(0,0) ≈ -6`과 단계 수를 엄격히 줄이는 정책 출력.

### Step 5: 가치 반복 (하나의 루프 버전)

```python
def value_iteration(gamma=0.99, tol=1e-6):
    V = {s: 0.0 for s in states()}
    while True:
        delta = 0.0
        for s in states():
            v = max(sum(p * (r + gamma * V[s_prime])
                       for s_prime, r, p in transitions(s, a))
                   for a in ACTIONS)
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < tol:
            break
    policy = policy_improvement(V, gamma)
    return V, policy
```

동일한 고정점, 더 적은 코드.

## 함정

- **종착 처리 깜빡이기.** 흡수 상태에 벨만를 적용하면, 여전히 변경되지 않는 "최고 행동"을 선택합니다. `if s == terminal: V[s] = 0`으로 보호하세요.
- **sup-norm 대 L2 수렴.** 평균이 아닌 `max |V_new - V|`를 사용하세요. 이론적 보장은 sup-norm에 있습니다.
- **즉시 대 동기 업데이트.** `V[s]`를 즉시 업데이트(Gauss-Seidel)가 별도 `V_new` 딕셔너리(Jacobi)보다 더 빨리 수렴합니다. 프로덕션 코드는 즉시를 사용합니다.
- **정책 타이.** 두 행동이 동일한 Q-값을 가지면, `argmax`가 각 반복에서 다르게 타이를 끊어 "정책 안정" 확인이振动할 수 있습니다. 고정 순서에서 첫 번째 행동으로 안정적인 타이 브레이크 사용하세요.
- **상태 공간 폭발.** DP는 스윕당 `O(|S| · |A|)`. ~10⁷ 상태까지 작동합니다. 그 이상에서는 함수 근사화가 필요합니다(단계 9 · 05부터).

## 활용

2026년, DP는 정확성 기본선이며 플래너의 내부 루프입니다:

| 사용 사례 | 방법 |
|----------|------|
| 작은 표形式 MDP 정확하게 해결 | 가치 반복(더 간단) 또는 정책 반복(더 적은 외부 단계) |
| Q-learning / PPO 구현 확인 | 토이 환경에서 DP 최적 `V*`와 비교 |
| 모델 기반 RL (단계 9 · 10) | 학습된 전이 모델에서 벨만 백업 |
| AlphaZero / MuZero의 계획 | 몬테 카를로 트리 검색 = async 벨만 백업 |
| 오프라인 RL (CQL, IQL) | OOD 행동에 페널티가 있는 DP — conservative Q-반복 |

"최적 가치 함수"라고 말할 때마다, "DP 고정점"을 의미합니다. 논문에서 `V*` 또는 `Q*`를 볼 때, 이 루프를 상상하세요.

## 결과물

`outputs/skill-dp-solver.md`로 저장:

```markdown
---
name: dp-solver
description: 정책 반복 또는 가치 반복을 통해 작은 표形式 MDP를 정확하게 해결합니다. 수렴 동작를 보고합니다.
version: 1.0.0
phase: 9
lesson: 2
tags: [rl, dynamic-programming, bellman]
---

알고 있는 모델이 있는 MDP가 주어지면 출력:

1. 선택. 정책 반복 vs 가치 반복. |S|, |A|, γ에 관련된 이유.
2. 초기화. V_0, 시작 정책. 수렴 민감도.
3. 중지. sup-norm 허용 오차 ε. 예상 스윕 수.
4. 확인. V*(s_0) 정확하게 계산. 탐욕적 정책 추출.
5. 사용. 이 기본선을 샘플링 기반 방법 디버그/평가에 사용하는 방법.

> 10⁷의 상태 공간에서 DP 실행 거부. sup-norm 확인 없이 수렴 주장 거부. 무한 수평선 작업에서 γ ≥ 1을 보장 위반으로 플래그.
```

## 연습 문제

1. **쉬움.** 4×4 GridWorld에서 `γ ∈ {0.9, 0.99}`로 가치 반복을 실행하세요. `max |ΔV| < 1e-6`이 될 때까지 몇 번의 스윕이 필요한가요? `V*`를 4×4 그리드로 출력하세요.
2. **보통.** *확률적* GridWorld(미끄러짐 확률 `0.1`)에서 정책 반복 vs 가치 반복을 비교하세요. 카운트: 스윕, 벽시계 시간, 최종 `V*(0,0)`. 어떤 것이 반복에서 더 빨리 수렴하나요? 벽시계에서?
3. **어려움.** 수정된 정책 반복 구축: 평가 단계에서 수렴 대신 `k` 스윕만 실행하세요. `k ∈ {1, 2, 5, 10, 50}`에 대해 `V*(0,0)` 오류 vs `k`를 플롯하세요. 곡선이 평가/개선 균형에 대해 무엇을 말하나요?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 정책 반복 | "DP 알고리즘" | 정책이 변경될 때까지 평가(`V^π`)와 개선(`V^π`에 대한 탐욕적 `π`)을 교대로 반복합니다. |
| 가치 반복 | "더 빠른 DP" | 한 스윕에서 적용된 벨만 최적성 백업; 기하학적으로 `V*`로 수렴합니다. |
| 벨만 연산자 | "재귀" | `(T V)(s) = max_a Σ P (r + γ V(s'))`; sup-norm에서 `γ`-수축. |
| 수축 | "DP가 수렴하는 이유" | `\|\|T x - T y\|\| ≤ γ \|\|x - y\|\|`인 연산자 `T`는 고유한 고정점을 가집니다. |
| GPI | "모두 DP" | 일반화된 정책 반복: `V`와 `π`를 상호 일관성으로 driving하는 모든 방법. |
| 동기 업데이트 | "Jacobi 스타일" | 스윕 전체에서旧的 `V`를 사용합니다; 분석하기 쉽지만 느립니다. |
| 즉시 업데이트 | "Gauss-Seidel 스타일" | 업데이트되는 동안 `V`를 사용합니다; 실제로는 더 빨리 수렴합니다. |

## 추가 자료

- [Sutton & Barto (2018). Ch. 4 — Dynamic Programming](http://incompleteideas.net/book/RLbook2020.pdf) — 정책 반복과 가치 반복의 표준 제시.
- [Bertsekas (2019). Reinforcement Learning and Optimal Control](http://www.athenasc.com/rlbook.html) — 수축 매핑 인수의 엄격한 처리.
- [Puterman (2005). Markov Decision Processes](https://onlinelibrary.wiley.com/doi/book/10.1002/9780470316887) — 수정된 정책 반복과 그 수렴 분석.
- [Howard (1960). Dynamic Programming and Markov Processes](https://mitpress.mit.edu/9780262582300/dynamic-programming-and-markov-processes/) — 원래 정책 반복 논문.
- [Bertsekas & Tsitsiklis (1996). Neuro-Dynamic Programming](http://www.athenasc.com/ndpbook.html) — 이후 모든 레슨에서 사용하는 근사-DP / 깊은 RL로의 다리.