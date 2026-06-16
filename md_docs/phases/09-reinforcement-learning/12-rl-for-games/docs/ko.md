# 게임을 위한 RL — AlphaZero, MuZero, 그리고 LLM-추론 시대

> 1992: TD-Gammon이 순수 TD로 백개먼에서 인간 챔피언을 이겼다. 2016: AlphaGo가 이세돌을 이겼다. 2017: AlphaZero가 체스, 쇼기, 바둑을 처음부터 지배했다. 2024: DeepSeek-R1이 동일한 레시피(PPO를 GRPO로 대체)가 추론에 작동함을 증명했다. 게임은 이 페이즈의 모든 돌파구를 주도하는 벤치마크이다.

**Type:** 구축
**Languages:** Python
**Prerequisites:** Phase 9 · 05 (DQN), Phase 9 · 08 (PPO), Phase 9 · 09 (RLHF), Phase 9 · 10 (MARL)
**Time:** ~120분

## 문제

게임은 RL이 원하는 모든 것을 가진다. 깔끔한 보상(승/패). 무한 에피소드(자기-대결 리셋). 완벽한 시뮬레이션(게임 자체가 시뮬레이터). 이산적이거나 작은 연속 행동 공간. 적대적 강건성을 강제하는 다중 에이전트 구조.

그리고 게임은 모든 주요 RL 돌파구가 테스트된 방법이다. TD-Gammon (백개먼, 1992). Atari-DQN (2013). AlphaGo (2016). AlphaZero (2017). OpenAI Five (Dota 2, 2019). AlphaStar (StarCraft II, 2019). MuZero (학습된 모델, 2019). AlphaTensor (행렬 곱셈, 2022). AlphaDev (정렬 알고리즘, 2023). DeepSeek-R1 (수학 추론, 2025) — 게임-RL 기술이 텍스트에서 작동한다는 최신 데모.

이 캡스톤은 세 가지 랜드마크 아키텍처 — AlphaZero, MuZero, GRPO — 를 단일 통합 렌즈로 조망한다: **자기-대결 + 탐색 + 정책 개선**. 각각은 이전 것을 일반화하며; 특히 GRPO는 LLM 추론에 적용된 AlphaZero 레시피로, 토큰을 행동으로, 수학적 검증을 승리 신호로 사용한다.

## 개념

![AlphaZero ↔ MuZero ↔ GRPO: 동일한 루프, 다른 환경](../assets/rl-games.svg)

**통합 루프.**

```
while True:
    trajectory = self_play(current_policy, search)     # 자기와 게임 실행
    policy_target = search.improved_policy(trajectory) # 탐색이 원시 정책 개선
    policy_net.update(policy_target, value_target)     # 탐색 출력에 대해 지도 학습
```

**AlphaZero (2017).** Silver et al. 알려진 규칙을 가진 게임(체스, 쇼기, 바둑)이 주어짐:

- 정책-가치 네트워크: 하나의 타워 `f_θ(s) → (p, v)`. `p`는 합법적 수에 대한 사전 확률. `v`는 예상 게임 결과.
- 몬테 카를로 트리 탐색 (MCTS): 각 수에서, 가능한 연속의 트리를 확장. `(p, v)`를 사전 + 부트스트랩으로 사용. UCB (PUCT)로 노드 선택: `a* = argmax Q(s, a) + c · p(a|s) · √N(s) / (1 + N(s, a))`.
- 자기-대결: 에이전트-대-에이전트 게임 실행. 수 `t`에서, MCTS 방문 분포 `π_t`가 정책 훈련 대상이 됨.
- 손실: `L = (v - z)² - π · log p + c · ||θ||²`. `z`는 게임 결과(+1 / 0 / -1).

인간 지식 제로. 수제 휴리스틱 제로. 각각 수천만 번의 자기-대결 게임 후 체스, 쇼기, 바둑을 마스터한 단일 레시피.

**MuZero (2019).** Schrittwieser et al. 규칙이 알려져 있어야 한다는 요구사항을 제거.

- 고정 환경 대신, *잠재 동역학 모델* `(h, g, f)`를 학습:
  - `h(s)`: 관찰을 잠재 상태로 인코딩.
  - `g(s_latent, a)`: 다음 잠재 상태 + 보상 예측.
  - `f(s_latent)`: 정책 사전 + 가치 예측.
- MCTS는 *학습된 잠재 공간*에서 실행. 동일한 탐색, 동일한 훈련 루프.
- 바둑, 체스, 쇼기 *그리고* Atari에서 작동 — 하나의 알고리즘, 규칙 지식 불필요.

**확률적 MuZero (2022).** 확률적 동역학과 기회 노드 추가; 백개먼-급 게임으로 확장.

**Muesli, Gumbel MuZero (2022-2024).** 샘플 효율성과 결정론적 탐색의 개선.

**GRPO (2024-2025).** DeepSeek-R1 레시피. 언어-모델 추론에 적용된 동일한 AlphaZero 형태 루프:

- "게임": 수학/코딩/추론 문제에 답변. "승리" = 검증기(테스트 케이스 통과, 숫자 답변 일치)가 1을 반환.
- 정책: LLM. 행동: 토큰. 상태: 프롬프트 + 지금까지의 응답.
- 크리틱(PPO-스타일 V_φ) 없음. 대신, 각 프롬프트에 대해 정책에서 `G`개의 완성을 샘플링. 각각에 대한 보상 계산. **그룹-상대적 이점** `A_i = (r_i - mean_r) / std_r`을 REINFORCE-스타일 업데이트의 신호로 사용.
- 드리프트 방지를 위한 참조 정책에 대한 KL 페널티(RLHF처럼).
- 전체 손실:

  `L_GRPO(θ) = -E_{q, {o_i}} [ (1/G) Σ_i A_i · log π_θ(o_i | q) ] + β · KL(π_θ || π_ref)`

보상 모델, 크리틱, MCTS 없음. 그룹-상대적 기준선이 세 가지를 모두 대체. 추론 벤치마크에서 PPO-RLHF 품질과 일치하거나 능가하며 훨씬 적은 연산 사용.

**R1 레시피 전체.** DeepSeek-R1 (DeepSeek 2025)은 한 논문에 두 모델:

- **R1-Zero.** DeepSeek-V3 베이스 모델에서 시작. SFT 없음. GRPO를 두 가지 보상 구성 요소와 함께 직접 적용: *정확도 보상*(규칙 기반 — 최종 답변이 올바른 숫자로 파싱되었는지 / 코드가 단위 테스트를 통과했는지) 및 *형식 보상*(완성이 사고 체인을 `<think>…</think>` 태그로 감쌌는지). 수천 단계에 걸쳐 평균 응답 길이가 ~100에서 ~10,000 토큰으로 증가하고 수학 벤치마크 점수가 o1-preview 수준에 근접. 모델이 처음부터 추론을 학습. 단점: 사고 체인이 종종 읽기 어렵고, 언어를 혼합하며, 문체적 광택이 부족.
- **R1.** R1-Zero의 가독성 문제를 4단계 파이프라인으로 해결:
  1. **콜드-스타트 SFT.** 깔끔한 형식의 수천 개의 긴 CoT 데모 수집. 베이스 모델을 이들에 대해 지도 미세조정. 읽기 쉬운 시작점 제공.
  2. **추론 지향 GRPO.** 정확도+형식 보상에 *언어 일관성* 보상을 추가하여 코드-스위칭 방지.
  3. **리젝션 샘플링 + SFT 2라운드.** RL 체크포인트에서 ~600K 추론 궤적 샘플링, 올바른 최종 답변과 읽기 쉬운 CoT만 유지, ~200K 비-추론 SFT 예제(작문, QA, 자기-인식)와 결합. 베이스 다시 미세조정.
  4. **전-스펙트럼 GRPO.** 추론(규칙 기반 보상)과 일반 정렬(도움됨/무해함 선호도 기반 보상)을 모두 다루는 한 번 더 RL 라운드.

결과는 오픈 가중치에서 AIME 및 MATH-500에서 o1과 일치하며, 증류할 만큼 작음. 동일한 논문은 R1의 추론 흔적으로 SFT하여 6개의 증류된 밀집 모델(Qwen-1.5B에서 Llama-70B)도 출시 — 학생에서 RL 없음. 강력한 RL 교사의 증류는 학생 규모에서 처음부터 RL을 하는 것보다 일관되게 더 나은 성능.

**추론에 PPO 대신 GRPO를 사용하는 이유.** DeepSeekMath 논문(2024년 2월)의 세 가지 이유: (1) 훈련할 가치 네트워크 없음, 메모리 절반; (2) 그룹 기준선이 추론 작업이 생성하는 희소한 궤적-끝 보상을 자연스럽게 처리; (3) 프롬프트당 정규화는 PPO의 단일 크리틱이 할 수 없는, 극도로 다양한 난이도의 문제에서 이점을 비교 가능하게 만듦.

**탐색-없음 vs 탐색-기반.** 게임은 분기되었다:

- *완전 정보 장기 게임* (바둑, 체스): 여전히 탐색 기반. AlphaZero / MuZero가 지배.
- *LLM 추론*: 아직 프로덕션에 MCTS 없음; 전체 롤아웃에 GRPO, 추론 연산을 위한 Best-of-N. 프로세스 보상 모델(PRM)이 단계 수준 탐색이 다시 추가될 가능성을 암시.

## 직접 구현하기

`code/main.py`의 코드는 **축소된 GRPO**를 구현 — 여러 그룹의 샘플을 가진 밴딧. 알고리즘은 LLM에서와 동일; 정책과 환경만 더 단순. 2025년 혁신인 *손실*과 *그룹-상대적 이점*을 가르친다.

### 단계 1: 작은 검증기 환경

```python
QUESTIONS = [
    {"prompt": "q1", "correct": 3},
    {"prompt": "q2", "correct": 1},
]

def verify(prompt_idx, answer_token):
    return 1.0 if answer_token == QUESTIONS[prompt_idx]["correct"] else 0.0
```

실제 GRPO에서 검증기는 단위 테스트를 실행하거나 수학적 동등성을 확인한다.

### 단계 2: 정책: 프롬프트당 K개의 답변 토큰에 대한 소프트맥스

```python
def policy_probs(theta, p_idx):
    return softmax(theta[p_idx])
```

프롬프트에 조건화된 LLM의 최종 계층 출력과 동등.

### 단계 3: 그룹 샘플링 및 그룹-상대적 이점

```python
def grpo_step(theta, p_idx, G=8, beta=0.01, lr=0.1, rng=None):
    probs = policy_probs(theta, p_idx)
    samples = [sample(probs, rng) for _ in range(G)]
    rewards = [verify(p_idx, s) for s in samples]
    mean_r = sum(rewards) / G
    std_r = stddev(rewards) + 1e-8
    advs = [(r - mean_r) / std_r for r in rewards]

    for a, A in zip(samples, advs):
        grad = onehot(a) - probs
        for i in range(len(probs)):
            theta[p_idx][i] += lr * A * grad[i]
    # KL 페널티: theta를 참조 쪽으로 당김
    for i in range(len(probs)):
        theta[p_idx][i] -= beta * (theta[p_idx][i] - reference[p_idx][i])
```

그룹-상대적 이점은 2024년 DeepSeek 트릭. 크리틱 불필요. "기준선"은 그룹 평균이며, 정규화는 그룹 표준편차를 사용.

### 단계 4: REINFORCE 기준선(가치-없음)과 비교

동일한 설정, 동일한 연산, 일반 REINFORCE. GRPO가 더 빠르고 안정적으로 수렴.

### 단계 5: 엔트로피와 KL 관찰

RLHF와 동일한 진단: 참조에 대한 평균 KL, 정책 엔트로피, 시간에 따른 보상. 이것들이 안정화되면 훈련 완료.

## 함정

- **검증기 게이밍을 통한 보상 해킹.** GRPO는 RLHF의 위험을 상속: 검증기가 틀리거나 이용 가능하면 LLM이 익스플로잇을 찾음. 강건한 검증기(여러 테스트 케이스, 형식 증명)가 중요.
- **그룹 크기가 너무 작음.** 그룹 기준선의 분산은 `1/√G`로 감. `G = 4` 미만에서 이점 신호가 노이즈가 많음; 표준 선택은 `G = 8`에서 `64`.
- **길이 편향.** 길이가 다른 LLM 완성은 다른 로그-확률을 가짐. 토큰 수로 정규화하거나, 시퀀스 수준 로그-확률을 사용하거나, 최대 길이로 자름.
- **순수 자기-대결 사이클.** AlphaZero-스타일 훈련은 일반-합 게임에서 지배 루프에 갇힐 수 있음. 다양한 상대 풀(리그 플레이, Lesson 10)로 완화.
- **탐색-정책 불일치.** AlphaZero는 정책이 탐색 출력을 모방하도록 훈련. 정책 네트가 탐색의 분포를 표현하기에 너무 작으면 훈련이 정체.
- **연산 바닥.** MuZero / AlphaZero는 막대한 연산 필요. 단일 절제는 종종 수백 GPU-시간. 학습을 위한 축소 데모(예: Connect Four의 AlphaZero)가 존재.
- **검증기 커버리지.** 버그가 있는 솔루션에 대해 통과하는 단위 테스트는 버그를 강화. 엣지 케이스를 잡는 검증기를 설계.

## 활용하기

2026년 게임-RL 환경, 도메인별:

| 도메인 | 지배적 방법 |
|--------|-----------------|
| 2인 제로-섬 보드 게임 (바둑, 체스, 쇼기) | AlphaZero / MuZero / KataGo |
| 불완전 정보 카드 게임 (포커) | CFR + 딥러닝 (DeepStack, Libratus, Pluribus) |
| Atari / 픽셀 게임 | Muesli / MuZero / IMPALA-PPO |
| 대규모 멀티플레이어 전략 (Dota, StarCraft) | PPO + 자기-대결 + 리그 (OpenAI Five, AlphaStar) |
| LLM 수학/코드 추론 | GRPO (DeepSeek-R1, Qwen-RL, 오픈 복제) |
| LLM 정렬 | DPO / RLHF-PPO (GRPO 아님; 검증기는 선호도, 검증 가능하지 않음) |
| 로보틱스 | PPO + DR (게임-RL은 아니지만, 동일한 정책-경사 도구 사용) |
| 조합 문제 | AlphaZero 변형 (AlphaTensor, AlphaDev) |

*레시피* — 자기-대결, 탐색-증강 개선, 정책 증류 — 는 텍스트, 픽셀, 물리적 제어에 걸쳐 있음. GRPO는 가장 최근 사례; 더 많은 것이 올 것이다.

## 결과물

`outputs/skill-game-rl-designer.md`로 저장:

```markdown
---
name: game-rl-designer
description: 주어진 도메인에 대한 게임-RL 또는 추론-RL 훈련 파이프라인 (AlphaZero / MuZero / GRPO) 설계
version: 1.0.0
phase: 9
lesson: 12
tags: [rl, alphazero, muzero, grpo, self-play]
---

대상(완전-정보 게임 / 불완전-정보 / Atari / LLM 추론 / 조합)이 주어지면 출력:

1. 환경 적합성. 알려진 규칙? 마르코프? 확률적? 다중 에이전트? AlphaZero vs MuZero vs GRPO 결정.
2. 탐색 전략. MCTS (학습된 사전으로 PUCT), Gumbel-샘플링, best-of-N, 또는 없음.
3. 자기-대결 계획. 대칭적 자기-대결 / 리그 / 오프라인 데이터 / 검증기 생성.
4. 대상 신호. 게임 결과 / 검증기 보상 / 선호도 / 학습된 모델. 강건성 계획 포함.
5. 진단. 기준선 대비 승률, ELO 곡선, 검증기 통과율, 참조 대비 KL.

불완전-정보 게임에 AlphaZero 추천 거부 (CFR로 연결). 신뢰할 수 있는 검증기 없이 GRPO 추천 거부. 고정 기준선 상대 세트 없는 게임-RL 파이프라인 거부 (자기-대결 ELO는 그렇지 않으면 보정되지 않음).
```

## 연습문제

1. **쉬움.** `code/main.py`에서 GRPO 밴딧을 구현. `G=8`로 2개 프롬프트 × 4개 답변 토큰에서 훈련. < 1,000 업데이트에서 수렴.
2. **중간.** PPO (클리핑)와 바닐라 REINFORCE를 연결. 동일한 밴딧에서 GRPO와 샘플 효율성 및 보상 분산 비교.
3. **어려움.** 길이-2 "추론 체인"으로 확장: 에이전트가 두 토큰을 방출하고 검증기가 쌍에 보상. GRPO가 2단계 시퀀스에 걸쳐 신용 할당을 어떻게 처리하는지 측정. (힌트: *전체 시퀀스*당 그룹 이점 계산, 두 토큰 위치로 전파.)

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| MCTS | "학습된 네트로 트리 탐색" | 몬테 카를로 트리 탐색; 학습된 `(p, v)` 사전을 사용한 UCB1/PUCT 선택. |
| AlphaZero | "자기-대결 + MCTS" | MCTS 방문 및 게임 결과와 일치하도록 훈련된 정책-가치 네트. |
| MuZero | "학습된 모델 AlphaZero" | 학습된 동역학을 통해 잠재 공간에서 동일한 루프. |
| GRPO | "크리틱-없는 PPO" | 그룹 상대적 정책 최적화; 그룹-평균 기준선 + KL을 가진 REINFORCE. |
| PUCT | "AlphaZero의 UCB" | `Q + c · p · √N / (1 + N_a)` — 가치 추정과 사전의 균형. |
| 자기-대결 | "에이전트 vs 과거 자기" | 제로-섬의 표준; 대칭적 훈련 신호. |
| 리그 플레이 | "모집단 기반 자기-대결" | 과거 + 현재 + 익스플로이터가 상대로 샘플링됨. |
| 검증기 보상 | "검증 가능한 RL" | 보상이 결정론적 검사기(테스트 통과, 답변 일치)에서 옴. |
| 프로세스 보상 | "PRM" | 최종 답변뿐만 아니라 각 추론 단계에 점수 매김. |

## 추가 자료

- [Silver et al. (2017). Mastering the game of Go without human knowledge (AlphaGo Zero)](https://www.nature.com/articles/nature24270).
- [Silver et al. (2018). A general reinforcement learning algorithm that masters chess, shogi, and Go through self-play (AlphaZero)](https://www.science.org/doi/10.1126/science.aar6404).
- [Schrittwieser et al. (2020). Mastering Atari, Go, chess and shogi by planning with a learned model (MuZero)](https://www.nature.com/articles/s41586-020-03051-4).
- [Vinyals et al. (2019). Grandmaster level in StarCraft II (AlphaStar)](https://www.nature.com/articles/s41586-019-1724-z).
- [DeepSeek-AI (2024). DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models (GRPO)](https://arxiv.org/abs/2402.03300) — GRPO와 그룹-상대적 기준선을 도입한 논문.
- [DeepSeek-AI (2025). DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948) — 전체 4단계 R1 레시피 + R1-Zero 절제.
- [Brown et al. (2019). Superhuman AI for multiplayer poker (Pluribus)](https://www.science.org/doi/10.1126/science.aay2400) — 대규모 CFR + 딥러닝.
- [Tesauro (1995). Temporal Difference Learning and TD-Gammon](https://dl.acm.org/doi/10.1145/203330.203343) — 모든 것을 시작한 논문.
- [Hugging Face TRL — GRPOTrainer](https://huggingface.co/docs/trl/main/en/grpo_trainer) — 사용자 정의 보상 함수로 GRPO 적용을 위한 프로덕션 참조.
- [Qwen Team (2024). Qwen2.5-Math — GRPO replication](https://github.com/QwenLM/Qwen2.5-Math) — 여러 규모에서 R1 레시피의 오픈 복제.
- [Sutton & Barto (2018). Ch. 17 — Frontiers of Reinforcement Learning](http://incompleteideas.net/book/RLbook2020.pdf) — R1이 LLM 규모로 구현하는 자기-대결, 탐색, "설계된 보상"에 대한 교과서 프레이밍.
