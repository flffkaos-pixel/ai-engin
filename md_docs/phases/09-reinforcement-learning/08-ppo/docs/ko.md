# 근접 정책 최적화 (PPO)

> A2C는 하나의 업데이트 후 각 rollout을 버립니다. PPO는 정책 기울기를 클리핑된 중요도 비율로 감싸서 동일한 데이터에서 10+ 에포크를 수행할 수 있습니다 정책이爆発하지 않고. Schulman et al. (2017). 여전히 2026년의 기본 정책 기울기 알고리즘입니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 9 · 06 (REINFORCE), Phase 9 · 07 (Actor-Critic)
**소요 시간:** ~75분

## 문제

A2C (레슨 07)는 온정책입니다: 경사 `E_{π_θ}[A · ∇ log π_θ]`는 *현재* `π_θ`에서 샘플링된 데이터가 필요합니다. 하나의 업데이트를 수행하면 `π_θ`가 변경됩니다; 사용한 데이터는 이제 오프정책입니다. 재사용하면 경사가 편향됩니다.

Rollout은 expensive합니다. Atari에서 8개 환경 × 128단계 = 1024 전환과 환경 시간의 몇 초에 걸친 하나의 rollout. 하나의 경사 단계 후 그것을 버리는 것은 낭비입니다.

신뢰 영역 정책 최적화 (TRPO, Schulman 2015)는 첫 번째 수정でした: 각 업데이트에서 old와 new 정책 사이의 KL 발산이 `δ` 아래로 유지되도록 제한합니다. 이론적으로 깔끔하지만, 업데이트마다 共役 기울기 해를 요구합니다. 2026년에 TRPO를 실행하는 사람은 없습니다.

PPO (Schulman et al. 2017)는 단일 추가 코드 줄로 하드 신뢰 영역 제약을 간단한 클리핑된 목적 함수로 교체합니다. 에포크당 10개의 rollout. 共役 기울기 없음. 충분한 이론적 보장. 9년이 지난 후에도 여전히 MuJoCo에서 RLHF까지 모든 것에 대한 기본 정책 기울기 알고리즘입니다.

## 개념

![PPO 클리핑된 서rogate 목적: 비율 클리핑 1 ± ε](../assets/ppo.svg)

**중요도 비율.**

`r_t(θ) = π_θ(a_t | s_t) / π_{θ_old}(a_t | s_t)`

이것은 데이터를 수집한 정책 대비 새로운 정책의 우도 비율입니다. `r_t = 1`은 변경 없음을 의미합니다. `r_t = 2`는 새로운 정책이 old보다 `a_t`를 취할 확률이 두 배임을 의미합니다.

**클리핑된 서rogate.**

`L^{CLIP}(θ) = E_t [ min( r_t(θ) A_t, clip(r_t(θ), 1-ε, 1+ε) A_t ) ]`

두 항:

- 이점 `A_t > 0`이고 비율이 `1 + ε` 너머로 증가하려고 하면, 클립이 기울기를 평탄하게 합니다 — 좋은 행동을 `+ε` above old 확률 이상으로 further 밀지 마세요.
- 이점 `A_t < 0`이고 비율이 `1 - ε` 너머로 증가하려고 하면 (비교하여 나쁜 행동을 더 가능하게 만들 것임을 의미), 클립이 기울기를 제한합니다 — 나쁜 행동을 `-ε` 아래로 밀지 마세요.

`min`은 다른 방향을 처리합니다: 비율이 *유리한* 방향으로 이동했으면, 여전히 기울기를 얻습니다 (해를할 것입니다 측면에서 클리핑 없음).

일반적인 `ε = 0.2`. `r_t`의 함수로 목적을 플롯: "좋은 측면"의 평평한 지붕과 "나쁜 측면"의 평평한 바닥이 있는 조각별 선형 함수.

**전체 PPO 손실.**

`L(θ, φ) = L^{CLIP}(θ) - c_v · (V_φ(s_t) - V_t^{target})² + c_e · H(π_θ(·|s_t))`

A2C와 동일한 actor-critic 구조. 세 계수, 일반적으로 `c_v = 0.5`, `c_e = 0.01`, `ε = 0.2`.

**훈련 루프.**

1. `N` 평행/env에서 `T` 단계마다 `N × T` 전환을 수집합니다.
2. 이점을 계산합니다 (GAE), 상수로 동결합니다.
3. 현재 `π_θ`의 스냅샷으로 `π_{θ_old}`를 동결합니다.
4. `K` 에포크에 대해, 각 미니배치 `(s, a, A, V_target, log π_old(a|s))`:
   - `r_t(θ) = exp(log π_θ(a|s) - log π_old(a|s))`를 계산합니다.
   - `L^{CLIP}` + 값 손실 + 엔트로피를 적용합니다.
   - 경사 단계.
5. rollout을 버립니다. 단계 1로 돌아갑니다.

`K = 10`이고 미니배치 크기 64가 표준 하이퍼파라미터 세트입니다. PPO는 강력합니다: 정확한 숫자는 ±50% 이내에서 거의 문제가 되지 않습니다.

**KL-페널티 변형.** 원래 논문은 적응형 KL 페널티를 사용한 대안을 제안했습니다: `L = L^{PG} - β · KL(π_θ || π_old)` 및 `β`를 관찰된 KL에 따라 조정합니다. 클리핑 버전이 지배적이되었습니다; KL 변형은 RLHF에서 생존합니다 (KL to the reference policy는 항상 원하는 별도의 제약이기 때문에).

## 실습

### Step 1: rollout 시간에 `log π_old(a | s)`를 캡처

```python
for step in range(T):
    probs = softmax(logits(theta, state_features(s)))
    a = sample(probs, rng)
    s_next, r, done = env.step(s, a)
    buffer.append({
        "s": s, "a": a, "r": r, "done": done,
        "v_old": value(w, state_features(s)),
        "log_pi_old": log(probs[a] + 1e-12),
    })
    s = s_next
```

스냅샷은 한 번만 촬영됩니다, rollout 시간에. 업데이트 epochs 동안 변경되지 않습니다.

### Step 2: GAE 이점 계산 (레슨 07)

A2C와 동일. 배치에서 정규화합니다.

### Step 3: 클리핑된 서rogate 업데이트

```python
for _ in range(K_EPOCHS):
    for mb in minibatches(buffer, size=64):
        for rec in mb:
            x = state_features(rec["s"])
            probs = softmax(logits(theta, x))
            logp = log(probs[rec["a"]] + 1e-12)
            ratio = exp(logp - rec["log_pi_old"])
            adv = rec["advantage"]
            surrogate = min(
                ratio * adv,
                clamp(ratio, 1 - EPS, 1 + EPS) * adv,
            )
            # backprop -surrogate, add value loss, subtract entropy
            grad_logpi = onehot(rec["a"]) - probs
            if (adv > 0 and ratio >= 1 + EPS) or (adv < 0 and ratio <= 1 - EPS):
                pg_grad = 0.0  # clipped
            else:
                pg_grad = ratio * adv
            for i in range(N_ACTIONS):
                for j in range(N_FEAT):
                    theta[i][j] += LR * pg_grad * grad_logpi[i] * x[j]
```

"클리핑 → 제로 기울기" 패턴이 PPO의 핵심입니다. 새로운 정책이 이미 유리한 방향으로 너무 많이 드IFT했으면, 업데이트가 중지됩니다.

### Step 4: 값과 엔트로피

A2C와 동일한 critic 대상에 대한 표준 MSE와 actor에 대한 엔트로피 보너스를 추가합니다.

### Step 5: 진단

매 업데이트마다 세 가지 주시:

- **평균 KL** `E[log π_old - log π_θ]`. `[0, 0.02]` 내에 있어야 합니다. `0.1`를 넘으면 `K_EPOCHS` 또는 `LR`을 줄이세요.
- **클립 분수** — 비율이 `[1-ε, 1+ε]` 밖에 있는 샘플의 분수. `~0.1-0.3`이어야 합니다. `~0`이면 클립이 절대 트리거되지 않습니다 → `LR` 또는 `K_EPOCHS`를 높이세요. `~0.5+`이면 rollout에 과적합됩니다 →它们을 낮추세요.
- **설명된 분산** `1 - Var(V_target - V_pred) / Var(V_target)`. Critic 품질 지표. Critic이 학습함에 따라 1을 향해 올라가야 합니다.

## 함정

- **클립 계수 오튜닝.** `ε = 0.2`가 사실상의 표준입니다. `0.1`로 가면 업데이트가 너무 겁줍니다; `0.3+`는 불안정을 초래합니다.
- **너무 많은 에포크.** `K > 20`은 규칙적으로 불안정하게 만듭니다, 왜냐하면 정책이 `π_old`에서 far 드IFT하기 때문입니다. 특히 큰 네트워크에서는 에포크를 제한하세요.
- **보상 정규화 없음.** 큰 보상 척도는 클립 범위를 침식합니다. 이점을 계산하기 전에 보상을 정규화하세요 (실행 std).
- **이점 정규화 깜빡이기.** 배치당 제로 평균/단위 std 정규화가 표준입니다. 그것을 건너뛰면 대부분의 벤치마크에서 PPO가 망가집니다.
- **학습률 감소 없음.** PPO는 영으로의 선형 LR 감소에서benefits합니다. 상수 LR은 often 더 나쁩니다.
- **중요도 비율 수학 오류.** 수치적 안정성을 위해 항상 `exp(log_new - log_old)`, `new / old`가 아닙니다.
- **잘못된 기울기 부호.** 서rogate를 최대화 = *최소화* `-L^{CLIP}`. 뒤집힌 부호가 가장 흔한 PPO 버그입니다.

## 활용

PPO는 2026년에 놀라운 수의 도메인에서 기본 RL 알고리즘입니다:

| 사용 사례 | PPO 변형 |
|----------|---------|
| MuJoCo / 로봇 공학 제어 | 가우시안 정책, GAE(0.95)가 있는 PPO |
| Atari / 이산 게임 | 범주형 정책, 롤링 128단계 rollouts가 있는 PPO |
| LLM용 RLHF | 참조 모델에 대한 KL 페널티가 있는 PPO, 응답 끝에서 RMからの 보상 |
| 대규모 게임 에이전트 | IMPALA + PPO (AlphaStar, OpenAI Five) |
| 추론 LLM | GRPO (레슨 12) — critic 없는 PPO 변형 |
| 선호도 전용 데이터 | DPO — PPO+KL의 닫힌 형태 붕괴, 온라인 샘플링 없음 |

PPO *손실 형태* — 클리핑된 서rogate + 값 + 엔트로피 —는 DPO, GRPO 및 거의 모든 RLHF 파이프라인의 스캐폴딩입니다.

## 결과물

`outputs/skill-ppo-trainer.md`로 저장:

```markdown
---
name: ppo-trainer
description: 주어진 환경에 대한 PPO 훈련 구성과 진단 플랜을 생성합니다.
version: 1.0.0
phase: 9
lesson: 8
tags: [rl, ppo, policy-gradient]
---

환경과 훈련 예산이 주어지면 출력:

1. Rollout 크기. `N` envs × `T` 단계.
2. 업데이트 스케줄. `K` 에포크, 미니배치 크기, LR 스케줄.
3. 서rogate 매개변수. `ε` (클립), `c_v`, `c_e`, 이점 정규화 켜기.
4. 이점. 명시적 `γ`와 `λ`가 있는 GAE(`λ`).
5. 진단 플랜. KL, 클립 분수, 경고가 있는 설명된 분산 임계값.

> `K > 30` 또는 `ε > 0.3` 거부 (안전하지 않은 신뢰 영역). 이점 정규화 또는 KL/클립 모니터링 없이 PPO 실행 거부. 지속적으로 0.4 이상인 클립 분수를 드rift으로 플래그.
```

## 연습 문제

1. **쉬움.** `ε=0.2, K=4`로 4×4 GridWorld에서 PPO를 실행하세요. 일치된 환경 단계에서 A2C (rollout당 하나의 에포크)와 샘플 효율성을 비교하세요.
2. **보통.** `K ∈ {1, 4, 10, 30}`을 sweep하세요. 환경 단계 vs 수익을 플롯하고 업데이트당 평균 KL을 추적하세요. 이 작업에서 어떤 `K`에서 KL이爆発하나요?
3. **어려움.** 적응형 KL 페널티로 클리핑된 서rogate를 교체하세요 (`KL > 2·target`이면 `β`를 두 배로, `KL < target/2`이면 절반으로). 최종 수익, 안정성 및 클립 없음을 비교하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 중요도 비율 | "r_t(θ)" | `π_θ(a\|s) / π_old(a\|s)`; 데이터를 수집한 정책からの偏差. |
| 클리핑된 서rogate | "PPO의 주요 트릭" | `min(r·A, clip(r, 1-ε, 1+ε)·A)`; 유리한 측면의 클립 너머에서 평평한 기울기. |
| 신뢰 영역 | "TRPO / PPO 의도" | 단调 개선을 보장하기 위해 각 업데이트의 KL을 제한합니다. |
| KL 페널티 | "부드러운 신뢰 영역" | 대안 PPO: `L - β · KL(π_θ || π_old)`. 적응형 `β`. |
| 클립 분수 | "클리핑이 트리거되는 빈도" | 진단 — 0.1-0.3이어야 합니다; 바깥은 mistuned를 의미합니다. |
| 다중 에포크 훈련 | "데이터 재사용" | 각 rollout에서 K 에포크; 샘플 효율성을 위해 traded되는 분산 비용. |
| 온정책-ish | "대부분 온정책" | PPO는 명목상으로 온정책이지만 K>1 에포크는 slightly-off-policy 데이터를 안전하게 사용합니다. |
| PPO-KL | "다른 PPO" | KL-페널티 변형; RLHF에서 사용됩니다, KL to-reference가 이미 제약이기 때문에. |

## 추가 자료

- [Schulman et al. (2017). Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347) — 논문.
- [Schulman et al. (2015). Trust Region Policy Optimization](https://arxiv.org/abs/1502.05477) — PPO의 전구자.
- [Andrychowicz et al. (2021). What Matters In On-Policy RL? A Large-Scale Empirical Study](https://arxiv.org/abs/2006.05990) — 모든 PPO 하이퍼파라미터가 절제됨.
- [Ouyang et al. (2022). Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — InstructGPT; RLHF의 PPO 레시피.
- [OpenAI Spinning Up — PPO](https://spinningup.openai.com/en/latest/algorithms/ppo.html) — PyTorch로 된 명확한 현대 설명.
- [CleanRL PPO 구현](https://github.com/vwxyzjn/cleanrl) — 많은 논문에서 사용되는 참조 단일 파일 PPO.
- [Hugging Face TRL — PPOTrainer](https://huggingface.co/docs/trl/main/en/ppo_trainer) — 언어 모델에서의 PPO용 production 레시피; 레슨 09 (RLHF)와 함께 읽으세요.
- [Engstrom et al. (2020). Implementation Matters in Deep Policy Gradients](https://arxiv.org/abs/2005.12729) — "37 코드 수준 최적화" 논문; 어떤 PPO 트릭이 load-bearing이고 어떤 것이 folklore인지.