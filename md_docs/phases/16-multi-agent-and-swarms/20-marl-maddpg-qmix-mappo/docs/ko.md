# MARL — MADDPG, QMIX, MAPPO

> 다중 에이전트 조정 강화 학습 유산으로, 2026년에도 LLM 에이전트 시스템에 여전히 영향을 미칩니다. **MADDPG** (Lowe et al., NeurIPS 2017, arXiv:1706.02275)는 CTDE (Centralized Training, Decentralized Execution)를 도입했습니다: 각 critic는 훈련 중 모든 에이전트의 상태와 행동을 보고, 테스트 시에는 지역 actor만 실행됩니다. 협력적, 경쟁적, 혼합 설정 모두에 작동합니다. **QMIX** (Rashid et al., ICML 2018, arXiv:1803.11485)는 단조 mixing network로 value decomposition합니다; 에이전트별 Q가 결합하여 joint Q가 되어 `argmax`가 깔끔하게 분배됩니다 — StarCraft Multi-Agent Challenge (SMAC)에서 dominate합니다. **MAPPO** (Yu et al., NeurIPS 2022, arXiv:2103.01955)는 중앙 집중식 value function이 있는 PPO입니다; particle-world, SMAC, Google Research Football, Hanabi에서 최소한의 튜닝으로 "놀랍도록 효과적"입니다. 이것들은 decentralally 행동해야 하는 에이전트 팀의 훈련 정책 기초를 형성합니다. MAPPO는 **2026년 협력적 MARL 기본 baseline**입니다. 이 레슨은 작은 그리드 월드toy에서 각각을 빌드하고 LLM 에이전트 훈련에 앞서 세 가지 아이디어를 muscle memory에 새겨줍니다.

**유형:** 학습
**언어:** Python (stdlib, NumPy 없는 작은 구현)
**선수 과목:** Phase 09 (Reinforcement Learning), Phase 16 · 09 (Parallel Swarm Networks)
**소요 시간:** ~90분

## 문제

LLM 에이전트 시스템은 에이전트 간 조정 정책 — 언제 양보하고, 언제 행동하고, 어느 동료에게 전화할 것인가 — 을 훈련也越来越多습니다. 이러한 정책을 훈련하는 방법을 알려주는 문헌은 Multi-Agent Reinforcement Learning (MARL)이며, LLM 물결 이전에 존재했고 지배적인 알고리즘 소규모 세트가 있습니다.

패턴 어휘 없이 MARL 논문을 읽는 것은 고통스럽습니다. Decentralized execution의 Centralized training (CTDE), value decomposition, centralized critics은 모두 buzzwords가 아닙니다 — 특정 문제에 대한 특정 답변들입니다:

- 독립 RL (각 에이전트가 혼자 학습)은 각 에이전트의 관점에서 non-stationary합니다. 나쁩니다.
- 중앙 집중식 RL (한 에이전트가 모두 제어)는 확장되지 않고 실행 제약 조건을 위반합니다.
- CTDE는 둘 다의 장점을 얻습니다: 전역 정보로 훈련, 지역 정책으로 배포합니다.

## 개념

### 세 가지 환경 논문들이 사용합니다

- **Particle World (multi-agent particle env).** 협력/경쟁 작업이 있는 간단한 2D 물리. MADDPG의 원래 테스트베드.
- **StarCraft Multi-Agent Challenge (SMAC).** 부분 관찰이 있는 협력적 micro-management. QMIX의 테스트베드. 이산 행동, 연속 상태.
- **Google Research Football, Hanabi, MPE.** MAPPO baselines.

다른 환경들은 다른 행동/관찰 유형을 가집니다. 알고리즘들이 그에 따라 선택합니다.

### MADDPG (2017) — CTDE 패턴

각 에이전트 `i`는 자신의 관찰을 행동으로 매핑하는 actor `mu_i(o_i)`를 가집니다. 각 에이전트는 또한 훈련 중 모든 관찰과 모든 행동을 보는 critic `Q_i(x, a_1, ..., a_n)`을 가집니다. Actor는 critic의 평가에 대해 policy gradient로 업데이트됩니다.

```
actor update:    grad_theta_i J = E[grad_theta mu_i(o_i) * grad_a_i Q_i(x, a_1..n) at a_i=mu_i(o_i)]
critic update:   TD on Q_i(x, a_1..n) given next-state joint estimate
```

CTDE 이유: 훈련 시간에 모든 사람의 행동을 압니다; 이를 사용하여 각 critic의 variance를 줄입니다. 배포 시점에서 각 에이전트는 `o_i`만 보고 `mu_i(o_i)`를 호출합니다.

실패 모드: Critic들은 N 에이전트만큼 성장합니다 (입력에 모든 행동 포함). 근사 없이는 ~10 에이전트 이상 확장되지 않습니다.

### QMIX (2018) — value decomposition

협력 전용. 전역 reward는 에이전트별 Q-values의 단조 함수의 합입니다:

```
Q_tot(tau, a) = f(Q_1(tau_1, a_1), ..., Q_n(tau_n, a_n)),   df/dQ_i >= 0
```

단조성은 `argmax_a Q_tot`가 각 에이전트가 독립적으로 `argmax_{a_i} Q_i`를 선택하여 계산할 수 있음을 보장합니다. 그것이 **정확히 decentraled execution 속성**입니다. 훈련 시간에 mixing network가 에이전트별 Q에서 `Q_tot`를 생성합니다.

QMIX가 SMAC에서 이기는 이유: 협력적 StarCraft micro-management는 지역 obs, 전역 reward가 있는 동형 에이전트를 가집니다 — value decomposition에 완벽한 적합.

실패 모드: 단조성 제약이 제한적입니다; 일부 작업은 단조 분해 가능하지 않은reward 구조를 가집니다 (팀을 위해 희생하는 한 에이전트). 확장 (QTRAN, QPLEX)이 이를 완화합니다.

### MAPPO (2022) — 과소평가된 기본값

Multi-Agent PPO: 중앙 집중식 value function이 있는 PPO. 각 에이전트는 자체 정책을 가집니다; 모든 에이전트는 전체 상태를 보는 value function을 공유합니다 (또는 에이전트별). Yu et al. 2022는 다섯 가지 벤치마크에서 MAPPO를 MADDPG, QMIX 및 해당 확장과 비교했습니다:

- MAPPO는 particle-world, SMAC, Google Research Football, Hanabi, MPE에서 off-policy MARL 방법과 같거나 능가합니다.
- 최소한의 hyperparameter 튜닝 필요.
- 안정적인 훈련; 시드 간 재현 가능.

2026년, MAPPO는 협력적 MARL의 기본 baseline입니다; 새로운 방법은 이를 이겨야 합니다.

### LLM 에이전트 엔지니어가 신경 써야 하는 이유

세 가지 직접적 사용:

1. **라우터 훈련.** 메타 에이전트가 어떤 하위 에이전트가 작업을 처리할지 선택합니다. N개의 분산 하위 에이전트와 하나의 중앙 집중식 라우터가 있는 MARL 문제입니다. MAPPO가 적합합니다.
2. **롤 출현.** 생성적 에이전트 시뮬레이션에서 시간이 지남에 따라 보완적 역할을 채택하도록 에이전트를 훈련시키는 것은 MARL 문제의 변장입니다. QMIX 스타일 value decomposition은 구성적으로 보완성을 강제합니다.
3. **멀티 에이전트 도구 사용.** 에이전트가 도구를 공유하고 예산을 두고 경쟁할 때, CTDE를 통해 훈련하면 리소스 제약 조건을 존중하는 배포 가능한 지역 정책을 생성합니다.

실용적 주의사항: 2026년 현재, 대부분의 프로덕션 LLM 에이전트 시스템은 정책을 훈련하기보다 prompting합니다. MARL은 (a) 많은 상호작용 데이터, (b) 명확한 reward 신호, (c) 훈련 인프라 투자 의지가 있을 때 등장합니다.

### RL 밖의 디자인 패턴으로서의 CTDE

훈련 없이도, CTDE는 유용한 아키텍처 패턴입니다:

- *디자인* 중에는 전팀 가시성을 가정합니다.
- *런타임*에는 분산 실행을 적용합니다: 각 에이전트는 `o_i`만 봅니다.

패턴은 에이전트별 상태를 명시적으로 유지하고 부분 관찰 가능성에 대해 미리 생각하도록 강제합니다. 많은 프로덕션 멀티 에이전트 시스템은 조용히 모든 곳에서 공유 상태를 가정합니다 — CTDE 규율이 그것을 방지합니다.

### 비정상성 문제

여러 에이전트가 동시에 학습할 때, 각 에이전트의 환경 (다른 사람의 정책 포함)이 비정상적입니다. 고전적 단일 에이전트 RL 증명이 무너집니다. 이 레슨의 MARL 알고리즘들이 모두 이것을 해결합니다:

- MADDPG: 전역 critic이 모든 행동을 봐서 값 추정치가 정상적입니다.
- QMIX: value decomposition이 최적성이 잘 정의된 joint-Q 공간으로 학습을 이동합니다.
- MAPPO: 중앙 집중식 value function이 다른 사람의 정책 변경으로 인한 variance를 완화합니다.

LLM 에이전트 시스템에서 비정상성은 "내 에이전트가 지난달에 작동했는데, 다른上游 에이전트가 변경되었으므로 내 에이전트가 오작동합니다."로 나타납니다. CTDE로 MARL을 훈련하는 것이 원칙적인 수정입니다; 프롬프트 수준 수정이 더 빠르지만 덜 지속 가능합니다.

### 이 레슨이 다루지 않는 것

실제 네트워크 훈련은 Phase 09 주제입니다. 이 레슨은 gradient 업데이트 없이 CTDE, value-decomposition, centralized-value 패턴을 시연하는 스크립트된 정책 버전을 빌드합니다. 목표는 전체 MARL 라이브러리 (PyMARL, MARLlib, RLlib multi-agent)를拾う前に 패턴을 내재화하는 것입니다.

## 빌드

`code/main.py`가 작은 2-에이전트 협력 그리드 월드에서 세 가지 패턴 시연을 구현합니다:

- 환경: 4x4 그리드의 2 에이전트, 하나의 reward 펠릿. Reward = 어떤 에이전트가 펠릿에 도달하면 1; 작업 완료.
- `IndependentAgents` — 각 에이전트가 다른 사람을 환경으로 취급합니다. Baseline.
- `MADDPGStyle` — 중앙 집중식 critic이 joint value를 계산합니다; actor 정책이 그것에서 업데이트됩니다. 스크립트된 정책 개선.
- `QMIXStyle` — 단조 mixer로 value decomposition.
- `MAPPOStyle` — 중앙 집중식 value function; 정책이 공유 baseline에 대해 업데이트됩니다.

네 가지 모두 동일한 에피소드를 실행하고 평균 steps-to-goal을 보고합니다. CTDE 변형이 독립 baseline보다 짧은 경로로 수렴합니다.

실행:

```
python3 code/main.py
```

예상 출력: 독립 에이전트는 평균 ~6 steps; CTDE 변형은 ~3.5 steps로 수렴합니다 (4x4 그리드의 최적은 3). 패턴 차이가 스크립트된 정책에도 나타납니다.

## 활용

`outputs/skill-marl-picker.md`는 주어진 멀티 에이전트 작업에 대한 MARL 알고리즘을 선택하는 스킬입니다: 협력 vs 경쟁, 동형 vs 이종, 행동 공간 유형, 규모, reward 신호.

## 결과물

프로덕션의 MARL은 드뭅니다. 사용할 때:

- **MAPPO로 시작하세요.** 2022년 논문이 이것을 baseline으로 확립했습니다; 먼저 재현하면 더 정교한 방법을 찾는 주를 절약합니다.
- **모든 에이전트의 관찰 및 행동 스트림을 로그하세요.** 에이전트별 추적 없이 MARL 디버깅은 불가능합니다.
- **훈련 코드를 실행 코드와 분리하세요.** CTDE는 규율입니다; 실행 경로가 실제로 `o_i`만 보도록 하세요.
- **Reward shaping 경고.** MARL은 reward 디자인에 극도로 민감합니다. Shaping의 하나의 조정 버그가 에이전트가 그것을 exploit하는 방법을 배웁니다. 적대적 테스트를 실행하세요.
- **LLM 에이전트의 경우**, 먼저 프롬프트 수준 정책을 고려하세요. 상호작용 데이터 + reward 신호 + 인프라가 모두 있을 때만 MARL 훈련에 투자하세요.

## 연습문제

1. `code/main.py`를 실행하세요. 독립 에이전트와 MAPPO 스타일 에이전트 간의 steps-to-goal 격차를 측정하세요. 6x6 그리드에서 격차가 커지거나 작아집니까?
2. 경쟁적 변형을 구현하세요: 두 에이전트, 하나의 펠릿, 첫 번째로 도달한 사람만 reward를 받습니다. 어떤 패턴이 경쟁을 깔끔하게 처리합니까? MADDPG가 역사적으로 그렇습니다.
3. MADDPG (arXiv:1706.02275) Section 3을 읽으세요. 정확한 critic 업데이트 규칙을 자신의 말로 의사코드에서 기호적으로 구현하세요.
4. MAPPO (arXiv:2103.01955)를 읽으세요. 저자들이 왜 중앙 집중식 value + PPO가 해당 벤치마크에서 off-policy MARL을 이기는 주장합니까? 세 가지最强的 주장을 나열하세요.
5. 가설적 LLM 에이전트 시스템 (예: research agent + summarizer + coder)에 CTDE를 디자인 패턴으로 적용하세요. 디자인 시간에可以利用하지만 런타임에는利用不可한joint 정보는 무엇입니까?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| MARL | "Multi-Agent RL" | 멀티 에이전트 시스템용 강화 학습. |
| CTDE | "Centralized Training, Decentralized Execution" | 전역 정보로 훈련; 지역 정책으로 배포. |
| MADDPG | "Multi-Agent DDPG" | 모든 관찰 + 행동을 보는 에이전트별 critic이 있는 CTDE. |
| QMIX | "Value decomposition" | 에이전트별 Q의 단조 mixing. 협력 전용. |
| MAPPO | "Multi-Agent PPO" | 중앙 집중식 value function이 있는 PPO. 2026년 기본 baseline. |
| Value decomposition | "개별 Q의 합" | Joint Q가 에이전트별 Q의 단조 함수로 표현됨. |
| Non-stationarity | "움직이는 목표" | 다른 사람이 학습함에 따라 각 에이전트의 환경이 변경됩니다. 핵심 MARL 문제. |
| On-policy / off-policy | "현재에서 학습 / 리플레이" | PPO는 on-policy (MAPPO); DDPG와 Q-learning은 off-policy. |
| SMAC | "StarCraft Multi-Agent Challenge" | 협력적 micromanagement 벤치마크; QMIX의 토착지. |

## 추가 자료

- [Lowe et al. — Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments](https://arxiv.org/abs/1706.02275) — MADDPG; NeurIPS 2017
- [Rashid et al. — QMIX: Monotonic Value Function Factorisation for Deep Multi-Agent Reinforcement Learning](https://arxiv.org/abs/1803.11485) — QMIX; ICML 2018
- [Yu et al. — The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games](https://arxiv.org/abs/2103.01955) — MAPPO; NeurIPS 2022
- [BAIR blog post on MAPPO](https://bair.berkeley.edu/blog/2021/07/14/mappo/) — MAPPO 결과의 읽기 쉬운 프레임
- [SMAC repository](https://github.com/oxwhirl/smac) — StarCraft Multi-Agent Challenge