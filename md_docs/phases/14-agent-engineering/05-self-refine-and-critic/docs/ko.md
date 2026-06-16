# Self-Refine와 CRITIC: 반복적 출력 개선

> Self-Refine (Madaan et al., 2023)은 하나의 LLM을 세 가지 역할(생성, 피드백, 개선)로 루프에서 사용한다. 평균 이득: 7개 작업에서 +20 절대치. CRITIC (Gou et al., 2023)은 외부 도구를 통해 검증을 라우팅하여 피드백 단계를 강화한다. 2026년에는 이 패턴이 모든 프레임워크에서 "evaluator-optimizer"(Anthropic) 또는 가드레일 루프(OpenAI Agents SDK)로 제공된다.

**Type:** Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 03 (Reflexion)
**Time:** ~60분

## 학습 목표

- Self-Refine의 세 가지 프롬프트(generate, feedback, refine)를 설명하고 개선 프롬프트에 히스토리가 중요한 이유를 설명한다.
- CRITIC의 핵심 통찰을 설명한다: LLM은 외부 근거 없이 자체 검증에 신뢰할 수 없다.
- 히스토리와 선택적 외부 검증기가 있는 stdlib Self-Refine 루프를 구현한다.
- 이 패턴을 Anthropic의 "evaluator-optimizer" 워크플로우와 OpenAI Agents SDK의 출력 가드레일에 매핑한다.

## 문제

에이전트가 거의 맞는 답변을 생성한다. 코드 한 줄에 문법 오류가 있을 수 있다. 요약이 너무 길 수 있다. 계획이 엣지 케이스를 놓칠 수 있다. 원하는 것은: 에이전트가 자신의 출력을 비판한 다음 수정하는 것이다.

Self-Refine은 단일 모델, 훈련 데이터 없음, RL 없이도 작동함을 보여준다. 하지만 한계가 있다: LLM은 하드 사실에 대한 자체 검증에 취약하다. CRITIC은 수정 방안을 제시한다 — 검증 단계를 외부 도구(검색, 코드 인터프리터, 계산기, 테스트 러너)를 통해 라우팅한다.

이 두 논문은 2026년의 반복적 개선 기본값을 정의한다: 생성, 검증(가능하면 외부에서), 개선, 검증기가 통과할 때까지 반복.

## 개념

### Self-Refine (Madaan et al., NeurIPS 2023)

하나의 LLM, 세 가지 역할:

```
generate(task)            -> output_0
feedback(task, output_0)  -> critique_0
refine(task, output_0, critique_0, history) -> output_1
feedback(task, output_1)  -> critique_1
refine(task, output_1, critique_1, history) -> output_2
...
stop when feedback says "no issues" or budget exhausted.
```

핵심 세부사항: `refine`은 전체 히스토리(모든 이전 출력과 비판)를 보므로 실수를 반복하지 않는다. 논문에서 이를 제거했다: 히스토리를 빼면 품질이 급격히 떨어진다.

주요 결과: GPT-4를 포함한 7개 작업(수학, 코드, 약어, 대화)에서 평균 +20 절대 개선. 훈련, 외부 도구, 단일 모델이 필요 없다.

### CRITIC (Gou et al., arXiv:2305.11738, v4 Feb 2024)

Self-Refine의 약점: 피드백 단계는 LLM이 스스로 점수를 매기는 것이다. 사실적 주장에 대해 이는 신뢰할 수 없다(환각은 종종 이를 생성한 모델에게 설득력 있게 보인다). CRITIC은 `feedback(task, output)`을 `verify(task, output, tools)`로 대체하며, `tools`에는 다음이 포함된다:

- 사실적 주장을 위한 검색 엔진.
- 코드 정확성을 위한 코드 인터프리터.
- 산술을 위한 계산기.
- 도메인별 검증기(단위 테스트, 타입 검사기, 린터).

검증기는 도구 결과에 근거한 구조화된 비판을 생성한다. 그런 다음 개선기가 이 비판을 조건화한다.

주요 결과: CRITIC은 비판이 근거가 있기 때문에 사실적 작업에서 Self-Refine을 능가한다. 외부 검증기가 없는 작업(창작 글쓰기, 포맷팅)에서는 CRITIC이 Self-Refine으로 축소된다.

### 중지 조건

두 가지 일반적인 형태:

1. **검증기 통과.** 외부 테스트가 성공을 반환. 가능할 때 선호됨 (단위 테스트, 타입 검사기, 가드레일 어설션).
2. **피드백 없음.** 모델이 "출력이 괜찮습니다"라고 말함. 저렴하지만 신뢰할 수 없음; 최대 반복 제한과 함께 사용.

2026년 기본값: 결합. "검증기가 통과하거나 모델이 괜찮다고 말하고 반복 >= 2이거나 반복 >= max_iterations이면 중지."

### Evaluator-Optimizer (Anthropic, 2024)

Anthropic의 2024년 12월 게시물은 이를 다섯 가지 워크플로우 패턴 중 하나로 명명한다. 두 가지 역할:

- Evaluator: 출력을 평가하고 비판을 생성.
- Optimizer: 비판에 따라 출력을 수정.

Evaluator가 통과할 때까지 루프. Anthropic의 프레이밍에서 Self-Refine/CRITIC이다. Anthropic이 추가하는 중요한 엔지니어링 세부사항: evaluator와 optimizer 프롬프트는 모델이 도장 찍기만 하지 않도록 상당히 달라야 한다.

### OpenAI Agents SDK 출력 가드레일

OpenAI Agents SDK는 이 패턴을 "출력 가드레일"로 제공한다. 가드레일은 에이전트의 최종 출력에서 실행되는 검증기다. 가드레일이 발동하면(`OutputGuardrailTripwireTriggered` 발생), 출력이 거부되고 에이전트가 재시도할 수 있다. 가드레일은 도구를 호출하거나(CRITIC 스타일) 순수 함수(Self-Refine 스타일)일 수 있다.

### 2026년 함정

- **도장 찍기 루프.** 같은 프롬프트 스타일로 생성과 비판을 수행하는 같은 모델은 "괜찮아 보입니다"로 수렴한다. 구조적으로 다른 프롬프트나 더 작고 저렴한 비판 모델을 사용하라.
- **과잉 개선.** 각 개선 패스는 지연 시간과 토큰을 추가한다. 1-3회 패스로 예산을 정하고, 그 후에는 사람 검토로 에스컬레이션하라.
- **사소한 작업에서의 CRITIC.** 외부 검증기가 없으면 CRITIC이 Self-Refine으로 퇴화한다; 스텁 검증기에 지연 시간을 지불하지 마라.

## 직접 구현하기

`code/main.py`는 장난감 작업(주어진 주제에 대한 짧은 글머리 기호 목록 생성)에 Self-Refine과 CRITIC을 구현한다. 검증기는 형식을 확인한다(3개 글머리 기호, 각각 60자 미만). CRITIC은 알려진 환각을 처벌하는 외부 "사실 검증기"를 추가한다.

구성 요소:

- `generate` — 스크립트 기반 생성기.
- `feedback` — LLM 스타일 자체 비판.
- `verify_external` — CRITIC 스타일 근거 기반 검증기.
- `refine` — 히스토리가 주어진 출력 재작성.
- 중지 조건 — 검증기 통과 또는 최대 4회 반복.

실행:

```
python3 code/main.py
```

Self-Refine 실행과 CRITIC 실행을 비교하라. CRITIC은 Self-Refine이 놓친 사실적 오류를 잡는다. 외부 검증기에 자체 비판가가 없는 근거가 있기 때문이다.

## 활용하기

Anthropic의 evaluator-optimizer는 Claude 친화적 언어의 이 패턴이다. OpenAI Agents SDK의 출력 가드레일은 CRITIC 형태다(가드레일이 도구를 호출할 수 있음). LangGraph는 Self-Refine처럼 읽히는 반성 노드를 제공한다. Google의 Gemini 2.5 Computer Use는 모든 행동이 커밋 전에 검증되는 CRITIC 변형인 단계별 안전 평가기를 추가한다.

## 배포하기

`outputs/skill-refine-loop.md`는 작업 형태, 검증기 가용성, 반복 예산에 따라 evaluator-optimizer 루프를 구성한다. 생성기, 평가기/검증기, 최적화기용 프롬프트와 중지 정책을 출력한다.

## 연습 문제

1. max_iterations=1로 장난감을 실행하라. CRITIC이 여전히 도움이 되는가?
2. 외부 검증기를 노이즈가 있는 것(랜덤 30% 거짓 양성)으로 교체하라. 루프는 어떻게 되는가? 이것이 2026년 대부분의 가드레일 스택 현실이다.
3. "generator-critic on different models" 변형을 구현하라: 큰 모델이 생성, 작은 모델이 비판. 같은 모델보다 나은가?
4. CRITIC 섹션 3 (arXiv:2305.11738 v4)을 읽어라. 세 가지 검증 도구 범주를 명명하고 각각에 예를 들어라.
5. OpenAI Agents SDK의 `output_guardrails`를 CRITIC의 검증기 역할에 매핑하라. SDK가 무엇을 잘못하고 있고, 무엇을 올바르게 하고 있는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Self-Refine | "스스로 수정하는 LLM" | 하나의 모델에서 generate -> feedback -> refine 루프, 히스토리 포함 |
| CRITIC | "도구 기반 검증" | 피드백을 외부 검증기(검색, 코드, 계산, 테스트)로 대체 |
| Evaluator-Optimizer | "Anthropic 워크플로우 패턴" | 두 역할 — 평가기가 점수 부여, 최적화기가 수정 — 수렴까지 반복 |
| Output guardrail | "사후 확인" | 에이전트가 출력을 생성한 후 실행되는 OpenAI Agents SDK 검증기 |
| Verify step | "비판 단계" | 핵심 결정: 근거 기반 또는 자체 평가 |
| Refine history | "모델이 이미 시도한 것" | 이전 출력 + 비판이 개선 프롬프트 앞에 추가; 빼면 품질 붕괴 |
| Rubber-stamp loop | "자체 동의 실패" | 같은 프롬프트 비판이 "괜찮아 보임" 반환; 구조적으로 다른 프롬프트로 수정 |
| Stop condition | "수렴 테스트" | 검증기 통과 OR 피드백 없음 AND 반복 제한; 절대 단일 조건으로 하지 마라 |

## 추가 자료

- [Madaan et al., Self-Refine (arXiv:2303.17651)](https://arxiv.org/abs/2303.17651) — 표준 논문
- [Gou et al., CRITIC (arXiv:2305.11738)](https://arxiv.org/abs/2305.11738) — 도구 기반 검증
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — evaluator-optimizer 워크플로우 패턴
- [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/) — CRITIC 형태의 출력 가드레일
