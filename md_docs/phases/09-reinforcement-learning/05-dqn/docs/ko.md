# 심층 Q-네트워크 (DQN)

> 2013: Mnih은 원시 픽셀에서 하나의 Q-learning 네트워크를 훈련시켜 7개의 Atari 게임에서 모든 고전 RL 에이전트를 이겼습니다. 2015: 49개 게임으로 확장, Nature에 게재, deep-RL 시대를 촉발했습니다. DQN은 함수 근사를 안정적으로 만드는 세 가지 트릭을 더한 Q-learning입니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 3 · 03 (Backpropagation), Phase 9 · 04 (Q-learning, SARSA)
**소요 시간:** ~75분

## 문제

표形式 Q-learning은 모든 (상태, 행동) 쌍에 대해 별도의 Q-값이 필요합니다. 체스 보드는 ~10⁴³ 개의 상태를 가집니다. Atari 프레임은 210×160×3 = 100,800 개의 특성입니다. 표形式 RL은 수천 개의 상태에서 죽습니다, 심지어 수십억 개의 상태에서는 말할 것도 없습니다.

，事後에 보이듯 명확한 수정: Q-테이블을 신경망 `Q(s, a; θ)`로 교체합니다. 하지만，事後에 보이는 것처럼 명확한 것을 깨닫는 데 수십 년이 걸렸습니다. Q-learning과 함께한 순진한 함수 근사는 "치명적 삼각형" — 함수 근사 + 부트스트래핑 + 오프정책 학습 — 에서 발산합니다. Mnih et al. (2013, 2015)는 학습을 안정화하는 세 가지 엔지니어링 트릭을identifiziert했습니다:

1. **경험 리플레이**는 전환의 상관관계를 decorrelates합니다.
2. **대상 네트워크**는 부트스트랩 대상을 동결합니다.
3. **보상 클리핑**은 기울기 크기를 정규화합니다.

Atari의 DQN은 원시 픽셀에서 단일 하이퍼파라미터 세트로 수십 개의 제어 문제를 해결한 첫 번째架构였습니다. 이후 구축된 모든 "심층 RL" — DDQN, Rainbow, Dueling, Distributional, R2D2, Agent57 —은 이 세 트릭 기본 위에 쌓아 올린 것입니다.

## 개념

![DQN 훈련 루프: 환경, 리플레이 버퍼, 온라인 네트, 대상 네트, 벨만 TD 손실](../assets/dqn.svg)

**목적.** DQN은 신경 Q-함수에서 한 단계 TD 손실을 최소화합니다:

`L(θ) = E_{(s,a,r,s')~D} [ (r + γ max_{a'} Q(s', a'; θ^-) - Q(s, a; θ))² ]`

`θ` = 온라인 네트워크, 매 단계 경사 하강법으로 업데이트. `θ^-` = 대상 네트워크, 주기적으로 `θ`에서 복사 (~10,000 단계마다). `D` = 과거 전환의 리플레이 버퍼.

**세 가지 트릭, 중요도 순서:**

**경험 리플레이.** ~10⁶ 전환의 링 버퍼. 각 훈련 단계에서 미니배치를 무작위로 균일하게 샘플링합니다. 이것은 시간적 상관관계를 끊습니다(연속 프레임은 거의 동일), 네트워크가 드문 보상 전환을 여러 번 학습할 수 있게 하고, 연속적인 경사 업데이트의 상관관계를 decorrelates합니다. Without it, on-policy TD with a neural net diverges on Atari.

**대상 네트워크.** 벨만 방정식의 양쪽에서 동일한 네트워크 `Q(·; θ)`를 사용하면 대상이 모든 업데이트에서 이동합니다 — "자기 꼬리를 쫓는 것." 수정: 동결된 가중치가 있는 두 번째 네트워크 `Q(·; θ^-)`를 유지합니다. 매 `C` 단계마다 `θ → θ^-`를 복사합니다. 이것은数千의 경사 단계에 대해 회귀 대상을 안정화합니다. 부드러운 업데이트 `θ^- ← τ θ + (1-τ) θ^-` (DDPG, SAC에서 사용)는 더 부드러운 변형입니다.

**보상 클리핑.** Atari 보상 크기는 1에서 1000+까지 다양합니다. `{-1, 0, +1}`로 클리핑하면 단일 게임이 기울기를 지배하는 것을 방지합니다. 보상 크기가 중요한 경우 잘못되었지만, 부호만 중요한 Atari에는 괜찮습니다.

**Double DQN.** Hasselt (2016)은 최대화 편향을修正합니다: 온라인 네트를 사용하여 행동을 *선택*하고, 대상 네트를 사용하여 그것을 *평가*합니다.

`target = r + γ Q(s', argmax_{a'} Q(s', a'; θ); θ^-)`

drop-in replacement, 지속적으로 더 좋습니다. 기본적으로 사용하세요.

**다른 개선 (Rainbow, 2017):** 우선순위 리플레이(높은 TD 오류 전환을 더 많이 샘플링), dueling architecture(분리된 `V(s)`와 이점 heads), noisy networks(학습된 탐험), n-단계 수익, distributional Q (C51/QR-DQN), multi-step bootstrapping. 각각 몇 퍼센트를追加합니다; 획득은 roughly 추가적입니다.

## 실습

여기의 코드는 stdlib만 있는 numpy-무료 — 단일 은닉층 MLP를 손으로 쓴 연속 GridWorld에서 사용하므로 모든 훈련 단계가 마이크로초에서 실행됩니다. 알고리즘은 대규모의 Atari DQN과 동일합니다.

### Step 1: 리플레이 버퍼

```python
class ReplayBuffer:
    def __init__(self, capacity):
        self.buf = []
        self.capacity = capacity
    def push(self, s, a, r, s_next, done):
        if len(self.buf) == self.capacity:
            self.buf.pop(0)
        self.buf.append((s, a, r, s_next, done))
    def sample(self, batch, rng):
        return rng.sample(self.buf, batch)
```

Atari의 경우 ~50,000 용량; 우리의 토이 환경에는 5,000으로 충분합니다.

### Step 2: 작은 Q-네트워크 (수동 MLP)

```python
class QNet:
    def __init__(self, n_in, n_hidden, n_actions, rng):
        self.W1 = [[rng.gauss(0, 0.3) for _ in range(n_in)] for _ in range(n_hidden)]
        self.b1 = [0.0] * n_hidden
        self.W2 = [[rng.gauss(0, 0.3) for _ in range(n_hidden)] for _ in range(n_actions)]
        self.b2 = [0.0] * n_actions
    def forward(self, x):
        h = [max(0.0, sum(w * xi for w, xi in zip(row, x)) + b) for row, b in zip(self.W1, self.b1)]
        q = [sum(w * hi for w, hi in zip(row, h)) + b for row, b in zip(self.W2, self.b2)]
        return q, h
```

순방향 통과: 선형 → ReLU → 선형. 그것이 전체 네트워크입니다.

### Step 3: DQN 업데이트

```python
def train_step(online, target, batch, gamma, lr):
    grads = zeros_like(online)
    for s, a, r, s_next, done in batch:
        q, h = online.forward(s)
        if done:
            y = r
        else:
            q_next, _ = target.forward(s_next)
            y = r + gamma * max(q_next)
        td_error = q[a] - y
        accumulate_grads(grads, online, s, h, a, td_error)
    apply_sgd(online, grads, lr / len(batch))
```

형태는 두 가지 차이점을 제외하고 레슨 04의 Q-learning과 동일합니다: (a) 테이블 인덱싱 대신 미분 가능한 `Q(·; θ)`를 통해 backprop하고, (b) 대상은 `Q(·; θ^-)`를 사용합니다.

### Step 4: 외부 루프

각 에피소드에 대해, `Q(·; θ)`에서 ε-탐욕적으로 행동하고, 전환을 버퍼에 푸시하고, 미니배치를 샘플링하고, 경사 단계를 수행하고, 주기적으로 `θ^- ← θ`를 동기화합니다. 패턴:

```python
for episode in range(N):
    s = env.reset()
    while not done:
        a = epsilon_greedy(online, s, epsilon)
        s_next, r, done = env.step(s, a)
        buffer.push(s, a, r, s_next, done)
        if len(buffer) >= batch:
            train_step(online, target, buffer.sample(batch), gamma, lr)
        if steps % sync_every == 0:
            target = copy(online)
        s = s_next
```

16-dim 원핫 상태를 가진 작은 GridWorld에서, 에이전트는 ~500 에피소드에서 near-optimal 정책을 학습합니다. Atari에서 이를 200M 프레임으로 확장하고 CNN 특성 추출기를 추가합니다.

## 함정

- **치명적 삼각형.** 함수 근사 + 오프정책 + 부트스트래핑은 발산할 수 있습니다. DQN은 대상 네트 + 리플레이로 완화합니다; 둘 다 제거하지 마세요.
- **탐험.** ε는 반드시 감소해야 합니다, 일반적으로 훈련 첫 ~10%에서 1.0에서 0.01로. 충분한 초기 탐험이 없으면 Q-네트는 지역 분지에서 수렴합니다.
- **과대 추정.** 노이즈가 있는 Q에 대한 `max`는 위로 편향됩니다. 프로덕션에서 항상 Double DQN을 사용하세요.
- **보상 척도.** 보상을 클리핑하거나 정규화하세요; 기울기 크기는 보상 크기에 비례합니다.
- **리플레이 버퍼 콜드스타트.** 버퍼에数千의 전환이 있을 때까지 훈련하지 마세요. ~20 샘플의 초기 기울기는 과적합됩니다.
- **대상 동기 빈도.** 너무 자주 ≈ 대상 네트 없음; 너무 드물면 ≈ 오래된 대상. Atari DQN은 10,000 환경 단계를 사용합니다. 경험적 규칙: 훈련 시야의 ~1/100마다 동기화.
- **관찰 전처리.** Atari DQN은 상태를 Markov로 만들기 위해 4개의 프레임을 쌓습니다. 속도 정보가 있는 모든 환경은 프레임 스택 또는 순환 상태가 필요합니다.

## 활용

2026년, DQN은 거의 최첨단이 아니지만 여전히 참조 오프정책 알고리즘으로 남아 있습니다:

| 작업 | 선택 방법 | DQN이 아닌 이유 |
|------|----------|---------------|
| 이산 행동 Atari 유사 | Rainbow DQN 또는 Muesli | 동일한 프레임워크, 더 많은 트릭. |
| 연속 제어 | SAC / TD3 (단계 9 · 07) | DQN에는 정책 네트워크가 없습니다. |
| 온정책 / 고처리량 | PPO (단계 9 · 08) | 리플레이 버퍼 없음; 확장이 더 쉬움. |
| 오프라인 RL | CQL / IQL / Decision Transformer | Conservative Q 대상, 부트스트래핑 폭발 없음. |
| 큰 이산 행동 공간 (추천) | 행동을embedding한 DQN, 또는 IMPALA | 괜찮; 장식은 중요합니다. |
| LLM RL | PPO / GRPO | 단계 수준이 아닌 시퀀스 수준; 다른 손실. |

교훈은 여전합니다. 리플레이와 대상 네트워크는 SAC, TD3, DDPG, SAC-X, AlphaZero의 자가 플레이 버퍼 및 모든 오프라인 RL 방법에 나타납니다. 보상 클리핑은 PPO의 이점 정규화로 이어집니다. 아키텍처는 청사진입니다.

## 결과물

`outputs/skill-dqn-trainer.md`로 저장:

```markdown
---
name: dqn-trainer
description: 이산 행동 RL 작업에 대한 DQN 훈련 설정(버퍼, 대상 동기, ε 스케줄, 보상 클리핑)을 생성합니다.
version: 1.0.0
phase: 9
lesson: 5
tags: [rl, dqn, deep-rl]
---

이산 행동 환경(관찰 형태, 행동 수, 시야, 보상 척도)이 주어지면 출력:

1. 네트워크. 아키텍처 (MLP / CNN / Transformer), 특성 차원, 깊이.
2. 리플레이 버퍼. 용량, 미니배치 크기, 워밍업 크기.
3. 대상 네트워크. 동기 전략 (C 단계마다 하드 또는 소프트 τ).
4. 탐험. ε 시작 / 끝 / 스케줄 길이.
5. 손실. Huber vs MSE, 기울기 클립 값, 보상 클리핑 규칙.
6. Double DQN. 명시적 비활성화 이유가 없는 한 기본적으로 켜짐.

대상 네트워크, 리플레이 버퍼 또는 ε가 1로 유지된 DQN을 shipping하기 거부. 연속 행동 작업 (SAC / TD3로 라우팅). 단계당 평균보다 > 10×인 보상 범위를 클리핑 또는 척도 정규화가 필요하다고 플래그.
```

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. 에피소드당 수익 곡선을 플롯하세요. 실행 평균이 -10을 초과하는 데 몇 에피소드가 걸리나요?
2. **보통.** 대상 네트워크를 비활성화하세요 (벨만 대상의 양쪽에서 온라인 네트를 사용). 훈련 불안정성을 측정하세요 — 수익이 진동하거나 발산하나요?
3. **어려움.** Double DQN 추가: 온라인 네트를 사용하여 `argmax a'`를 선택하고, 대상 네트로 평가합니다. 노이즈 보상 GridWorld에서 1,000 에피소드 후 Double DQN 유무와 함께 `Q(s_0, best_a)` vs 진실 `V*(s_0)`의 편향을 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| DQN | "심층 Q-러닝" | 신경 Q-함수, 리플레이 버퍼 및 대상 네트워크와 함께한 Q-러닝. |
| 경험 리플레이 | "셔플된 전환" | 각 경사 단계에서 균일하게 샘플링된 링 버퍼; 데이터를 decorrelates합니다. |
| 대상 네트워크 | "동결된 부트스트랩" | 벨만 대상에서 사용되는 Q의 주기적 복사; 학습을 안정화합니다. |
| 치명적 삼각형 | "RL이 발산하는 이유" | 함수 근사 + 부트스트래핑 + 오프정책 = 수렴 보장 없음. |
| Double DQN | "최대화 편향 수정" | 온라인 네트가 행동을 선택하고, 대상 네트가 그것을 평가합니다. |
| Dueling DQN | "V와 A heads" | Q = V + A - mean(A)로 분해; 동일한 출력, 더 나은 기울기 흐름. |
| Rainbow | "모든 트릭" | 하나의 것에서 DDQN + PER + dueling + n-step + noisy + distributional. |
| PER | "우선순위 리플레이" | TD 오류 크기에 비례하여 전환을 샘플링합니다. |

## 추가 자료

- [Mnih et al. (2013). Playing Atari with Deep Reinforcement Learning](https://arxiv.org/abs/1312.5602) — deep RL을 시작시킨 2013년 NeurIPS 워크숍 논문.
- [Mnih et al. (2015). Human-level control through deep reinforcement learning](https://www.nature.com/articles/nature14236) — Nature 논문, 49게임 DQN.
- [Hasselt, Guez, Silver (2016). Deep Reinforcement Learning with Double Q-learning](https://arxiv.org/abs/1509.06461) — DDQN.
- [Wang et al. (2016). Dueling Network Architectures](https://arxiv.org/abs/1511.06581) — dueling DQN.
- [Hessel et al. (2018). Rainbow: Combining Improvements in Deep RL](https://arxiv.org/abs/1710.02298) — 쌓인 트릭 논문.
- [OpenAI Spinning Up — DQN](https://spinningup.openai.com/en/latest/algorithms/dqn.html) — 명확한 현대 설명.
- [Sutton & Barto (2018). Ch. 9 — On-policy Prediction with Approximation](http://incompleteideas.net/book/RLbook2020.pdf) — DQN의 대상 네트워크와 리플레이 버퍼를 억제하도록 설계된 "치명적 삼각형"(함수 근사 + 부트스트래핑 + 오프정책)에 대한 교과서 처리.
- [CleanRL DQN 구현](https://docs.cleanrl.dev/rl-algorithms/dqn/) — 절제 연구에 사용되는 참조 단일 파일 DQN; 이 레슨의 from-scratch 버전과 함께 읽기에 좋습니다.