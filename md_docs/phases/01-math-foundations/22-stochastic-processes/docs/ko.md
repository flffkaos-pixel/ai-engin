# 확률 과정

> 구조가 있는 무작위성. 랜덤 워크, 마르코프 연쇄, 확산 모델 뒤의 수학.

**유형:** 학습
**언어:** Python
**선수 과목:** Phase 1, Lessons 06-07
**시간:** ~75분

## 학습 목표

- 1D 및 2D 랜덤 워크 시뮬레이션하고 변위의 √n 스케일링 검증하기
- 마르코프 연쇄 시뮬레이터 구축하고 고유분해를 통해 정상 분포 계산하기
- 목표 분포에서 샘플링하기 위한 Metropolis-Hastings MCMC 및 랑주뱅 역학 구현하기
- 순방향 확산 과정을 브라운 운동과 연결하고 역방향 과정이 데이터를 생성하는 방식 설명하기

## 문제

많은 AI 시스템은 시간에 따라 진화하는 무작위성을 포함합니다. 정적 무작위성이 아닌, 각 단계가 이전에 의존하는 구조화된 순차적 무작위성입니다.

언어 모델은 한 번에 하나씩 토큰 생성 — 확률 과정. 확산 모델은 이미지에 단계별로 노이즈 추가 후 역전 — 마르코프 연쇄. 강화학습 에이전트는 확률적 환경에서 행동 — 마르코프 결정 과정. MCMC 샘플링은 목표 사후분포를 정상 분포로 하는 마르코프 연쇄 구축.

## 개념

### 랜덤 워크

0에서 시작. 각 단계 ±1 (공정한 동전). n단계 후: E[위치] = 0, 하지만 기대 거리 = √n.

반직관적: 워크는 공정하지만(편향 없음), 시간이 지날수록 원점에서 점점 멀어짐. 표준편차 = √n.

ML에서 √n 스케일링: SGD 노이즈 ∝ 1/√batch_size. 임베딩 차원 ∝ √d.

### 마르코프 연쇄

다음 상태가 오직 현재 상태에만 의존: `P(X_{n+1} = j | X_n = i) = P_{ij}`

전이 행렬 P: 각 행의 합 = 1. P_{ij} = i→j 전이 확률.

**정상 분포**: π = π·P — 고정점. π는 P의 왼쪽 고유벡터(고윳값 1).

MCMC는 목표 분포를 정상 분포로 하는 마르코프 연쇄 구축.

### 랑주뱅 역학

```
x_new = x_old + ε/2 * ∇log p(x_old) + √ε * N(0, I)
        \_____________/                 \__________/
         기울기 항 (하강)             노이즈 항 (탐색)
```

기울기 하강에 가우시안 노이즈 추가. p(x)에서 샘플 생성 — 확산 모델의 역방향 과정 기초.

### 확산 모델 연결

**순방향**: `x_t = √(1-β_t) * x_{t-1} + √β_t * ε` — 각 단계에서 약간의 노이즈 추가. 큰 T 후 → 순수 가우시안 노이즈.

**역방향**: `x_{t-1} = 1/√(1-β_t) * (x_t - β_t/√(1-ᾱ_t) * ε_θ(x_t, t)) + σ_t * z`

학습된 노이즈 예측기 ε_θ로 노이즈 제거하며 역방향 이동. 최종 x_0 = 생성된 이미지.

## 빌드하기

```python
import random
import math

def random_walk_1d(n_steps):
    position = 0; positions = [0]
    for _ in range(n_steps):
        position += 1 if random.random() < 0.5 else -1
        positions.append(position)
    return positions

# 마르코프 연쇄
class MarkovChain:
    def __init__(self, transition_matrix):
        self.P = transition_matrix
        self.n = len(transition_matrix)

    def step(self, current_state):
        r = random.random()
        cumulative = 0
        for next_state in range(self.n):
            cumulative += self.P[current_state][next_state]
            if r <= cumulative:
                return next_state
        return self.n - 1

    def simulate(self, initial, n_steps):
        states = [initial]
        for _ in range(n_steps):
            states.append(self.step(states[-1]))
        return states
```

## 연습 문제

1. 1,000단계 1D 랜덤 워크 시뮬레이션. 마지막 위치의 분산이 ~1000임을 확인 (√n 규칙)
2. 2-상태 마르코프 연쇄 구축. 정상 분포를 직접 계산(π = πP)하고 시뮬레이션과 비교
3. 랑주뱅 역학으로 2D 가우시안 혼합에서 샘플링. 생성된 샘플 시각화

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 랜덤 워크 | S_n = Σ ±1. E[S_n]=0, sd=√n |
| 마르코프 연쇄 | P(X_{t+1} | X_t만). 전이 행렬 P |
| 정상 분포 | π = πP — 장기적 방문 빈도 |
| 랑주뱅 역학 | ∇log p(x) + 노이즈 — 확산의 기초 |
| 순방향 확산 | 점진적 노이즈 추가 → 순수 가우시안 |
| 역방향 확산 | 학습된 노이즈 제거 → 데이터 생성 |