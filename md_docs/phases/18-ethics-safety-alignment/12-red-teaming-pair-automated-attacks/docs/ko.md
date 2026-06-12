# 레드팀: PAIR와 자동화된 공격

> Chao, Robey, Dobriban, Hassani, Pappas, Wong (NeurIPS 2023, arXiv:2310.08419). PAIR — Prompt Automatic Iterative Refinement — 은 표준화된 자동화된 블랙박스 탈옥이다. 빨간 팀 시스템 프롬프트가 있는 공격자 LLM이 대상 LLM에 대한 탈옥을 반복적으로 제안하고, 자체 채팅 历史에 시도 및 응답을 누적하여 인컨텍스트 피드백으로 사용한다. PAIR는 일반적으로 20쿼리 내에서 성공하며, GCG(Zou et al.의 토큰-레벨 그래디언트 검색)보다 훨씬 효율적이며 화이트박스 액세스가 필요 없다. PAIR는 이제 JailbreakBench(arXiv:2404.01318)와 HarmBench에서 표준 기준이며, GCG, AutoDAN, TAP, Persuasive Adversarial Prompt와 함께 제공한다.

**유형:** 실습
**언어:** Python (stdlib,toy 대상에 대한 mock PAIR 루프)
**선수 과목:** Phase 18 · 01 (지시 따르기), Phase 14 (에이전트 공학)
**소요 시간:** 약 75분

## 학습 목표

- PAIR 알고리즘을 설명한다: 공격자 시스템 프롬프트, 반복 개선, 인컨텍스트 피드백.
- 대상이 블랙박스일 때 PAIR가 GCG보다 엄격히 더 효율적인 이유를 설명한다.
- 네 가지 다른 자동화 공격 기준(GCG, AutoDAN, TAP, PAP)을 이름 짓고 각각의 구별되는 특징을 하나씩 설명한다.
- JailbreakBench와 HarmBench 평가 프로토콜을 설명하고, 각각에서 "공격 성공률"이 무엇을 의미하는지 설명한다.

## 문제

레드팀은、かつては 수동 활동이었다. 소수의 전문가 테스터가 적대적 프롬프트를 구성하고哪些 것이 작동했는지 추적했다. 이것은 확장되지 않는다: 공격 성공률에는 통계적 표본이 필요하고, 대상은 모든 모델 출시로 움직이는 목표이다. PAIR는 블랙박스 대상과 함께 최적화 문제로 레드팀을 작동화한다.

## 개념

### PAIR 알고리즘

입력:
- 대상 LLM T (공격하는 모델).
- 심판 LLM J (응답이 탈옥인지 점수 매김).
- 공격자 LLM A (레드팀 최적화기).
- 목표 문자열 G: "[유해한 지시]로 응답".
- 예산 K (일반적으로 20쿼리).

루프, k in 1..K:
1. A는 목표 G와 지금까지의 (프롬프트, 응답) 쌍의 历史으로 프롬프트된다.
2. A가 새 프롬프트 p_k를 emitted한다.
3. p_k를 T에 제출; 응답 r_k를 받는다.
4. J가 (p_k, r_k)를 목표에 대해 점수 매긴다.
5. 점수 >=しきい값이면 중지 — 탈옥 발견.
6. 그렇지 않으면 (p_k, r_k)를 A의 历史에 추가; 계속.

경험적 결과(NeurIPS 2023): GPT-3.5-turbo, Llama-2-7B-chat에 대해 50% 이상의 공격 성공률; 평균 성공 쿼리가 10-20 범위.

### PAIR이 효율적인 이유

GCG(Zou et al. 2023)는 적대적 토큰 접미사에 대한 그래디언트 검색이다; 화이트박스 모델 액세스가 필요하고 읽기 불가능한 접미사를 생성한다. PAIR는 블랙박스이며 모델 간에 전이되는 자연어 공격을 생성한다. PAIR의 인컨텍스트 피드백은 각 거부에서 학습할 수 있게 한다; GCG에는 해당 것이 없다(각 새 토큰 업데이트가 이전 진행 상황을 다시 발견해야 함).

### 관련 자동화된 공격

- **GCG (Zou et al. 2023, arXiv:2307.15043).** 적대적 접미사에 대한 토큰-레벨 그래디언트 검색. 화이트박스, 전이 가능, 읽기 불가능한 문자열을 생성.
- **AutoDAN (Liu et al. 2023).** 계층적 목적에 의해引导되는 프롬프트에 대한 진화적 검색.
- **TAP (Mehrotra et al. 2024).** 가지치기가 있는 공격 트리 — 여러 PAIR 스타일 rollout을分支.
- **PAP (Zeng et al. 2024).** Persuasive Adversarial Prompts — 인간 설득 기술을 프롬프트 템플릿으로 인코딩.

### JailbreakBench와 HarmBench

둘 다(2024) 평가标准化:

- JailbreakBench(arXiv:2404.01318). 10개 OpenAI 정책 범주의 100개 유해한 동작. ASR(공격 성공률)이 기본 메트릭. 심판(GPT-4-turbo, Llama Guard, StrongREJECT)이 필요.
- HarmBench(Mazeika et al. 2024). 7개 범주의 510개 동작, 의미론적 및 기능적 해머 테스트. 18개 공격 대 33개 모델 비교.

ASR은 일반적으로 고정된 쿼리 예산에서 보고된다. 공격을 비교하려면 예산을 맞춰야 한다; 200쿼리에서 90% ASR은 20에서 85% ASR과 비교할 수 없다.

### 2026년 배치에 중요한 이유

모든 프론티어 실험실은 이제 출시 전에 생산 모델에 대해 PAIR와 TAP를 실행한다. ASR 궤적이 모델 카드(26과)와 안전 사례 부록(18과)에 나타난다. 공격이 exotic하지 않다 — 표준 인프라이다.

## 활용

`code/main.py`는toy PAIR 루프를 구축한다. 대상은 명백한 유해한 프롬프트를 거부하는 모의 분류기(키워드 필터)이다. 공격자는 파라프레이징, 역할play 프레이밍, 인코딩을 시도하는 규칙 기반 개선이다. 심판이 응답을 점수 매긴다. 키워드 필터 against에 대해 5-15회 반복으로 공격자가 성공하는 것을 보고, 시맨틱 필터 against에는 실패하는 것을 볼 수 있다.

## 결과물

이 수업은 `outputs/skill-attack-audit.md`를 생성한다. 레드팀 평가 보고서가 주어지면 감사를 실행한다: 어떤 공격이 실행되었는지(PAIR, GCG, TAP, AutoDAN, PAP), 각기 어떤 예산에서, 어떤 심판으로, 어떤 유해한 동작 세트에서(JailbreakBench, HarmBench, 내부).

## 연습 문제

1. `code/main.py`를 실행한다. 세 가지 내장 공격자 전략에 대한 평균-성공-쿼리를 보고한다. 각이 활용하는 대상-방어 가정을 설명한다.

2. 네 번째 공격자 전략을 구현한다(예: 다른 언어への 번역, base64 인코딩). 키워드 필터 대상과 시맨틱 필터 대상 모두에서 새로운 평균-성공-쿼리를 보고한다.

3. Chao et al. 2023 Figure 5(PAIR 대 GCG 비교)를 읽는다. PAIR의 효율성 이점에도 불구하고 GCG가 선호되는 두 가지 시나리오를 설명한다.

4. JailbreakBench는 고정된 목표 세트에 대해 ASR을 보고한다. 공격 다양성(성공한 프롬프트의 분산)을 측정하는 추가 메트릭을 설계한다. 방어 평가에 왜 다양성이 중요한지 설명한다.

5. TAP(Mehrotra 2024)는 가지내기 + 가지치리로 PAIR를 확장한다. TAP 스타일 확장을 `code/main.py`에 스케치하고 계산 비용 대 성공률 tradeoff를 설명한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| PAIR | "자동화된 탈옥" | Prompt Automatic Iterative Refinement; 공격자-LLM + 심판-LLM 루프 |
| GCG | "그래디언트 탈옥" | 적대적 접미사에 대한 화이트박스 토큰-레벨 그래디언트 검색 |
| 공격 성공률 (ASR) | "k 쿼리에서 % 탈옥" | 기본 메트릭; 쿼리 예산과 심판 정체性と 함께 보고되어야 함 |
| 심판 LLM | "점수 매기는 사람" | 응답이 유해한 목표를 만족하는지 등급을 매기는 LLM |
| JailbreakBench | "평가" | 태그된 범주의 표준화된 유해한 동작 세트 |
| HarmBench | "더 넓은 벤치" | 510개 동작, 기능적 + 의미론적 해머 테스트 |
| TAP | "공격 트리" | 가지치기가 있는 PAIR; 더 높은 컴퓨팅에서 더 나은 ASR |

## 추가 자료

- [Chao et al. — Jailbreaking Black Box LLMs in Twenty Queries (arXiv:2310.08419)](https://arxiv.org/abs/2310.08419) — PAIR 논문, NeurIPS 2023
- [Zou et al. — Universal and Transferable Adversarial Attacks on Aligned LLMs (arXiv:2307.15043)](https://arxiv.org/abs/2307.15043) — GCG 논문
- [Chao et al. — JailbreakBench (arXiv:2404.01318)](https://arxiv.org/abs/2404.01318) — 표준화된 평가
- [Mazeika et al. — HarmBench (ICML 2024)](https://arxiv.org/abs/2402.04249) — 더 넓은 평가