# 보상 모델링 및 RLHF

> 인간은 "좋은 어시스턴트 응답"에 대한 보상 함수를 작성할 수 없지만, 두 응답을 비교하고 더 나은 것을 선택할 수는 있다. 그 비교에 보상 모델을 피팅한 다음, 그 보상에 대해 언어 모델을 RL한다. Christiano 2017. InstructGPT 2022. GPT-3를 ChatGPT로 바꾼 레시피. 2026년에는 대부분 DPO로 대체되고 있지만 — 개념적 모델은 그대로 유지된다.

**Type:** 구축
**Languages:** Python
**Prerequisites:** Phase 5 · 05 (감정 분석), Phase 9 · 08 (PPO)
**Time:** ~45분

## 문제

다음-토큰-예측 목적 함수로 언어 모델을 훈련시켰다. 문법적으로 올바른 영어를 작성한다. 또한 거짓말을 하고, 횡설수설하며, 거절을 거부한다. 더 많은 사전훈련으로 이 문제를 고칠 수 없다 — 웹 텍스트가 문제이지 해결책이 아니다.

"명령 X에 대해 응답 A가 응답 B보다 낫다"고 말하는 *스칼라 보상*을 원한다. 그 보상 함수를 손으로 작성하는 것은 불가능하다. "도움됨(Helpfulness)"은 토큰에 대한 폐쇄형 표현식이 아니다. 그러나 인간은 두 출력을 비교하고 선호도를 표시할 수 있다. 이는 대규모로 수집하기에 저렴하다.

RLHF(Christiano et al. 2017; Ouyang et al. 2022)는 선호도를 보상 모델로 변환한 다음, PPO를 통해 그 보상에 대해 LM을 최적화한다. 세 단계로: SFT → RM → PPO. 이것이 ChatGPT, Claude, Gemini 및 2023–2025년의 모든 정렬된 LLM을 출시한 레시피이다.

2026년에는 PPO 단계가 대부분 DPO(Phase 10 · 08)로 대체되었다. 그러나 *보상 모델* 부분은 여전히 모든 Best-of-N 샘플러, 모든 검증 가능한 보상 RL 파이프라인, 그리고 프로세스 보상 모델을 사용하는 모든 추론 모델의 기반이 된다. RLHF를 이해하면 전체 정렬 스택을 이해하는 것이다.

## 개념

![3단계 RLHF: SFT, 쌍별 선호도에 대한 RM 훈련, KL 페널티를 포함한 PPO](../assets/rlhf.svg)

**1단계: 지도 미세조정(SFT).** 사전훈련된 베이스 모델에서 시작한다. 대상 행동(명령-수행 응답, 도움이 되는 응답 등)의 인간이 작성한 데모에 대해 미세조정한다. 결과: *좋은 행동 쪽으로 편향되었지만* 여전히 무제한의 행동 공간을 가진 모델 `π_SFT`.

**2단계: 보상 모델 훈련.**

- 프롬프트 `x`에 대한 응답 쌍 `(y_+, y_-)`을 수집하며, 인간이 "y_+가 y_-보다 선호됨"이라고 레이블링한다.
- 보상 모델 `R_φ(x, y)`를 훈련시켜 `y_+`에 더 높은 점수를 할당하게 한다.
- 손실: **Bradley-Terry 쌍별 로지스틱**:

  `L(φ) = -E[ log σ(R_φ(x, y_+) - R_φ(x, y_-)) ]`

  σ는 시그모이드이다. 보상의 차이는 선호도의 로그-오즈를 의미한다. BT는 1952년부터 표준이었으며(Bradley-Terry), 현대 RLHF에서 지배적인 선택이다.

- `R_φ`는 일반적으로 SFT 모델 위에 스칼라 헤드를 얹어 초기화된다. 동일한 트랜스포머 백본; 하나의 선형 레이어가 보상을 출력한다.

**3단계: KL 페널티를 포함한 RM에 대한 PPO.**

- 훈련 가능한 정책 `π_θ`를 `π_SFT`로 초기화한다. 동결된 *참조* `π_ref = π_SFT`를 유지한다.
- 응답 `y` 끝에서의 보상:

  `r_total(x, y) = R_φ(x, y) - β · KL(π_θ(·|x) || π_ref(·|x))`

  KL 페널티는 `π_θ`가 `π_SFT`로부터 임의로 벗어나는 것을 방지한다 — 이는 *정규화기(regularizer)*이지, 하드 신뢰 영역이 아니다. `β`는 일반적으로 `0.01`-`0.05`이다.
- 이 보상으로 PPO(Lesson 08)를 실행한다. 이점(Advantages)은 토큰 수준 궤적에서 계산되지만, RM은 전체 응답에만 점수를 매긴다.

**KL이 필요한 이유?** 그것 없이 PPO는 기꺼이 보상 해킹 전략을 찾을 것이다 — RM은 분포 내 완성에 대해서만 훈련되었다. 분포 외 응답이 인간이 작성한 어떤 것보다 높은 점수를 받을 수 있다. KL은 `π_θ`가 RM이 훈련된 매니폴드 근처에 유지되도록 한다. 이것은 RLHF에서 가장 중요한 단일 노브(knob)이다.

**2026년 현황:**

- **DPO** (Rafailov 2023): 폐쇄형 대수가 2단계+3단계를 선호도 데이터에 대한 단일 지도 손실로 축소한다. RM도 PPO도 필요 없다. 훨씬 적은 연산으로 정렬 벤치마크에서 동일한 품질. Phase 10 · 08에서 다룸.
- **GRPO** (DeepSeek 2024–2025): 크리틱 대신 그룹-상대 기준선을 사용하는 PPO, 인간이 훈련한 RM 대신 *검증기*(코드 실행 / 수학 답변 일치)로부터 보상. 추론 모델에서 지배적. Phase 9 · 12에서 다룸.
- **프로세스 보상 모델(PRM):** 부분 솔루션(각 추론 단계)에 점수를 매기며, 추론을 위한 RLHF 및 GRPO 변형 모두에서 사용됨.
- **헌법적 AI / RLAIF:** 인간 대신 정렬된 LLM을 사용하여 선호도를 생성. 선호도 예산을 확장.

## 직접 구현하기

이 레슨은 문자열로 표현된 작은 합성 "프롬프트"와 "응답"을 사용한다. RM은 토큰-가방 표현 위의 선형 스코어러이다. 실제 LLM은 없다 — 파이프라인의 *형태*가 중요하며, 규모는 중요하지 않다. `code/main.py` 참조.

### 단계 1: 합성 선호도 데이터

```python
PROMPTS = ["help me", "answer me", "explain this"]
GOOD_WORDS = {"clear", "specific", "kind", "thorough"}
BAD_WORDS = {"vague", "rude", "wrong", "short"}

def make_pair(rng):
    x = rng.choice(PROMPTS)
    y_good = rng.choice(list(GOOD_WORDS)) + " " + rng.choice(list(GOOD_WORDS))
    y_bad = rng.choice(list(BAD_WORDS)) + " " + rng.choice(list(BAD_WORDS))
    return (x, y_good, y_bad)
```

실제 RLHF에서 이는 인간 레이블러로 대체된다. 형태 — `(프롬프트, 선호_응답, 거부_응답)` — 는 동일하다.

### 단계 2: Bradley-Terry 보상 모델

선형 점수: `R(x, y) = w · bag(y)`. BT 쌍별 로그-손실을 최소화하도록 훈련:

```python
def rm_train_step(w, x, y_pos, y_neg, lr):
    r_pos = dot(w, bag(y_pos))
    r_neg = dot(w, bag(y_neg))
    p = sigmoid(r_pos - r_neg)
    for tok, cnt in bag(y_pos).items():
        w[tok] += lr * (1 - p) * cnt
    for tok, cnt in bag(y_neg).items():
        w[tok] -= lr * (1 - p) * cnt
```

수백 번의 업데이트 후, `w`는 좋은 단어 토큰에 양의 가중치를, 나쁜 단어 토큰에 음의 가중치를 할당한다.

### 단계 3: RM 위의 PPO-스타일 정책

장난감 정책은 어휘에서 단일 토큰을 생성한다. RM 하에서 토큰에 점수를 매기고, `log π_θ(token | prompt)`를 계산하고, KL-대-참조 페널티를 추가하고, 클리핑된 PPO 대리를 적용한다.

```python
def rlhf_step(theta, ref, w, prompt, rng, eps=0.2, beta=0.1, lr=0.05):
    logits_theta = policy_logits(theta, prompt)
    probs = softmax(logits_theta)
    token = sample(probs, rng)
    logits_ref = policy_logits(ref, prompt)
    probs_ref = softmax(logits_ref)
    reward = dot(w, bag([token])) - beta * kl(probs, probs_ref)
    # ppo-style 업데이트 on theta, reward를 return으로 처리
    ...
```

### 단계 4: KL 모니터링

매 업데이트마다 평균 `KL(π_θ || π_ref)`를 추적한다. `~5-10`을 넘으면 정책이 `π_SFT`에서 멀리 떨어진 것이다 — `β`가 낮아지거나 보상 해킹이 시작된 것이다. 이는 실제 RLHF에서 최상위 진단 도구이다.

### 단계 5: TRL을 사용한 프로덕션 레시피

장난감 파이프라인을 이해했다면, 실제 라이브러리 사용자가 작성하는 동일한 루프는 다음과 같다. Hugging Face의 [TRL](https://huggingface.co/docs/trl)이 참조 구현이다 — 2단계용 `RewardTrainer`와 3단계용 (KL-대-참조가 내장된) `PPOTrainer`.

```python
# Stage 2: 쌍별 선호도로부터 보상 모델
from trl import RewardTrainer, RewardConfig
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
rm = AutoModelForSequenceClassification.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct", num_labels=1
)

# dataset rows: {"prompt", "chosen", "rejected"} — Bradley-Terry 형식
trainer = RewardTrainer(
    model=rm,
    tokenizer=tok,
    train_dataset=preference_data,
    args=RewardConfig(output_dir="./rm", num_train_epochs=1, learning_rate=1e-5),
)
trainer.train()
```

```python
# Stage 3: SFT 참조에 대한 KL 페널티를 포함한 RM에 대한 PPO
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

policy = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-checkpoint")
ref    = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-checkpoint")  # 동결

ppo = PPOTrainer(
    config=PPOConfig(learning_rate=1.41e-5, batch_size=64, init_kl_coef=0.05,
                     target_kl=6.0, adap_kl_ctrl=True),
    model=policy, ref_model=ref, tokenizer=tok,
)

for batch in dataloader:
    responses = ppo.generate(batch["query_ids"], max_new_tokens=128)
    rewards   = rm(torch.cat([batch["query_ids"], responses], dim=-1)).logits[:, 0]
    stats     = ppo.step(batch["query_ids"], responses, rewards)
    # stats includes: mean_kl, clip_frac, value_loss — 세 가지 PPO 진단 정보
```

라이브러리가 해주는 세 가지. `adap_kl_ctrl=True`는 적응형-β 스케줄을 구현한다: 관찰된 KL이 `target_kl`을 초과하면 β가 두 배가 되고; 절반 미만이면 β가 반으로 줄어든다. 참조 모델은 관례상 동결된다 — 실수로 `policy`와 파라미터를 공유하지 않도록 해야 한다. 그리고 값 헤드는 정책과 동일한 백본(`AutoModelForCausalLMWithValueHead`가 스칼라 MLP 헤드를 부착)에 위치하므로, TRL이 `policy/kl`과 `value/loss`를 별도로 보고한다.

## 함정

- **과최적화 / 보상 해킹.** RM은 불완전하다; `π_θ`는 높은 점수를 받지만 나쁜 적대적 완성을 찾는다. 증상: 보상은 무한정 상승하지만 인간 평가 점수는 정체되거나 하락한다. 해결: 조기 중단, `β` 증가, RM 훈련 데이터 확장.
- **길이 해킹.** 도움이 되는 응답에 대해 훈련된 RM은 종종 암묵적으로 길이에 보상을 준다. 정책은 응답을 늘리는 법을 배운다. 해결: 길이 정규화된 보상, 또는 길이 인식 RM을 사용한 RLAIF.
- **너무 작은 RM.** RM은 적어도 정책만큼 커야 한다. 작은 RM은 정책의 출력을 충실하게 점수 매길 수 없다.
- **KL 튜닝.** 너무 낮은 β → 드리프트 및 보상 해킹. 너무 높은 β → 정책이 거의 변하지 않음. 표준 트릭은 단계당 고정 KL을 목표로 하는 *적응형* β이다.
- **선호도 데이터 노이즈.** ~30%의 인간 레이블은 노이즈가 있거나 모호하다. 일치-필터링된 데이터로 RM을 훈련하거나 BT에 온도를 사용하여 보정한다.
- **오프-정책 문제.** PPO 데이터는 첫 번째 에폭 후 약간 오프-정책이다. Lesson 08에서와 같이 클립 비율을 모니터링한다.

## 활용하기

2026년 RLHF는 계층화되어 있다:

| 계층 | 대상 | 방법 |
|-------|--------|--------|
| 명령 수행, 도움됨, 무해함 | 정렬 | DPO(Phase 10 · 08)가 RLHF-PPO보다 선호됨. |
| 추론 정확성(수학, 코드) | 능력 | 검증기 보상을 사용한 GRPO(Phase 9 · 12). |
| 장기 다단계 작업 | 에이전트 | 단계별 프로세스 보상 모델을 사용한 PPO / GRPO. |
| 안전 / 거부 행동 | 안전 | 별도의 안전 RM을 사용한 RLHF-PPO, 또는 헌법적 AI. |
| 추론 시 Best-of-N | 빠른 정렬 | 디코드 시간에 RM 사용; 정책 훈련 불필요. |
| 보상 증류 | 추론 연산 | 동결된 LM 위에 작은 "보상 헤드" 훈련. |

RLHF는 2022–2024년에 *그 방법*이었다. 2026년에는 프로덕션 정렬 파이프라인이 DPO 우선이며, PPO는 RM 집약적 또는 안전-중요 단계에만 사용된다.

## 결과물

`outputs/skill-rlhf-architect.md`로 저장:

```markdown
---
name: rlhf-architect
description: 언어 모델에 대한 RLHF / DPO / GRPO 정렬 파이프라인 설계 (RM, KL, 데이터 전략 포함)
version: 1.0.0
phase: 9
lesson: 9
tags: [rl, rlhf, alignment, llm]
---

베이스 LM, 대상 행동(정렬 / 추론 / 거부 / 에이전트), 선호도 또는 검증기 예산이 주어지면 출력:

1. 단계. SFT? RM? DPO? GRPO? 정당성과 함께.
2. 선호도 또는 검증기 출처. 인간, AI 피드백, 규칙 기반, 단위-테스트-통과, 또는 보상 증류.
3. KL 전략. 고정 β, 적응형 β, 또는 DPO(암시적 KL).
4. 진단 정보. 평균 KL, 보상 안정성, 과최적화 방어(홀드아웃 인간 평가).
5. 안전 게이트. 레드-팀 세트, 거부율, 도움됨 RM과 분리된 안전 RM.

KL 모니터 없이 RLHF-PPO를 출시하는 것을 거부. 대상 정책보다 작은 RM 사용을 거부. 길이 전용 보상을 거부. 블라인드 인간 평가 세트를 보류하지 않은 파이프라인은 과최적화 보호가 부족하다고 플래그.
```

## 연습문제

1. **쉬움.** `code/main.py`에서 Bradley-Terry 보상 모델을 500개의 합성 선호도 쌍으로 훈련하라. 보류된 100쌍에 대한 쌍별 정확도를 측정하라. 90%를 초과해야 한다.
2. **중간.** `β ∈ {0.0, 0.1, 1.0}`으로 장난감 PPO-RLHF 루프를 실행하라. 각각에 대해 RM 점수 vs KL-대-참조를 업데이트에 걸쳐 플롯하라. 어떤 실행이 보상 해킹하는가?
3. **어려움.** 동일한 선호도 데이터에 대해 DPO(폐쇄형 선호도-우도 손실)를 구현하고, 사용된 연산과 달성된 최종 RM 점수에서 RLHF-PPO 파이프라인과 비교하라.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| RLHF | "정렬 RL" | 3단계 SFT + RM + PPO 파이프라인 (Christiano 2017, Ouyang 2022). |
| 보상 모델 (RM) | "점수 매기는 네트" | Bradley-Terry를 통해 쌍별 선호도에 피팅된 학습된 스칼라 함수. |
| Bradley-Terry | "쌍별 로지스틱 손실" | `P(y_+ ≻ y_-) = σ(R(y_+) - R(y_-))`; 표준 RM 목적 함수. |
| KL 페널티 | "참조 근처에 머물러라" | 보상 내 `β · KL(π_θ || π_ref)`; 보상 해킹 방지 정규화기. |
| 보상 해킹 | "Goodhart의 법칙" | 정책이 RM의 결함을 이용; 증상: 보상 상승, 인간 평가 평탄. |
| RLAIF | "AI-레이블된 선호도" | 레이블이 인간 대신 다른 LM에서 오는 RLHF. |
| PRM | "프로세스 보상 모델" | 부분 추론 단계에 점수 매김; 추론 파이프라인에서 사용. |
| 헌법적 AI | "Anthropic의 방법" | 명시적 규칙에 의해 안내되는 AI 생성 선호도. |

## 추가 자료

- [Christiano et al. (2017). Deep Reinforcement Learning from Human Preferences](https://arxiv.org/abs/1706.03741) — RLHF를 시작한 논문.
- [Ouyang et al. (2022). InstructGPT — Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — ChatGPT 뒤의 레시피.
- [Stiennon et al. (2020). Learning to summarize with human feedback](https://arxiv.org/abs/2009.01325) — 요약을 위한 초기 RLHF.
- [Rafailov et al. (2023). Direct Preference Optimization](https://arxiv.org/abs/2305.18290) — DPO; 2026년 포스트-RLHF 기본값.
- [Bai et al. (2022). Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073) — RLAIF 및 자기-비판 루프.
- [Anthropic RLHF paper (Bai et al. 2022). Training a Helpful and Harmless Assistant](https://arxiv.org/abs/2204.05862) — HH 논문.
- [Hugging Face TRL library](https://huggingface.co/docs/trl) — 프로덕션 `RewardTrainer` 및 `PPOTrainer`. 적응형-KL 및 값-헤드 세부사항에 대해 트레이너 소스 읽기.
- [Hugging Face — Illustrating Reinforcement Learning from Human Feedback](https://huggingface.co/blog/rlhf) by Lambert, Castricato, von Werra, Havrilla — 다이어그램과 함께 3단계 파이프라인의 표준 워크스루.
- [von Werra et al. (2020). TRL: Transformer Reinforcement Learning](https://github.com/huggingface/trl) — 라이브러리; `examples/`에는 Llama, Mistral, Qwen을 위한 종단간 RLHF 스크립트가 있음.
- [Sutton & Barto (2018). Ch. 17.4 — Designing Reward Signals](http://incompleteideas.net/book/RLbook2020.pdf) — 보상-가설 관점; 보상 해킹에 대해 생각하기 위한 필수 전제 조건.
