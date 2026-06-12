# LLM 기능의 A/B 테스트 — GrowthBook, Statsig 및 분위기 문제

> 전통적인 A/B 테스트는 비결정론적 LLM을 위해 설계되지 않았습니다. 중요한 구분: evals는 "모델이 작업을 수행할 수 있는가?"를 answered. A/B 테스트는 "사용자가 신경 쓰는가?"를 answered. 둘 다 필요합니다; 분위기 검사로 shipping하는 것은 끝났습니다. 2026년 테스트 항목: 프롬프트 엔지니어링 (문구), 모델 선택 (GPT-4 vs GPT-3.5 vs OSS; 정확도 vs 비용 vs 지연 시간), 생성 파라미터 (temperature, top-p). 실제 사례: 챗봇 보상 모델 변형이 +70% 대화 길이 및 +30% 리텐션을 제공; Nextdoor AI 제목 实验은 보상 함수 개선 후 +1% CTR을 제공; Khan Academy Khanmigo는 지연 시간 대 수학 정확도 축에서 iterated. 플랫폼 분할: **Statsig** (2025년 9월 $1.1B에 OpenAI에 인수) — 순차 테스트, CUPED, 올인원. **GrowthBook** — 오픈소스, warehouse-네이티브, Bayesian + Frequentist + Sequential 엔진, CUPED, SRM 확인, Benjamini-Hochberg + Bonferroni 수정. warehouse-SQL 기본 설정과 "OpenAI에 인수됨"이 조직에 중요한지에 따라 선택합니다.

**유형:** 학습
**언어:** Python (stdlib, toy 순차 테스트 시뮬레이터)
**선수 과목:** Phase 17 · 13 (관찰 가능성), Phase 17 · 20 (점진적 배포)
**소요 시간:** ~60분

## 학습 목표

- eval ("모델이 작업을 수행할 수 있는가")과 A/B 테스트 ("사용자가 신경 쓰는가")를区別합니다.
- 세 가지 테스트 가능한 축 (프롬프트, 모델, 파라미터)을 열거하고 각각의 메트릭을 선택합니다.
- CUPED, 순차 테스트, Benjamini-Hochberg 다중 비교 수정을 설명합니다.
- warehouse-SQL 자세와 기업 인수stance에 따라 Statsig 또는 GrowthBook을 선택합니다.

## 문제

시스템 프롬프트를 수동으로 조정했습니다. 더 나아 보입니다. shipping합니다. 전환이 노이즈로 변경됩니다. 메트릭을 탓합니다. 또는 새 모델을 shipping했고 전환이 움직이지 않았습니다 — 모델이 degrades했거나 변경이 너무 작아서 감지할 수 없었습니까? A/B 없이 shipping했기 때문에 모릅니다.

Eval은 레이블된 세트에서 모델이 작업을 수행할 수 있는지 answered. 사용자가 출력을 선호하는지는 answered하지 않습니다. 제어된 온라인 실험만이 그것을 answered하며, 실험이 충분한 검정력을 가지고, 비결정론을 통제하고, 다중 비교를 수정하는 경우에만 가능합니다.

## 개념

### Eval 대 A/B 테스트

**Eval** — 오프라인, 레이블된 세트, judge (루브릭 또는 LLM-as-judge 또는 인간). 답변: "이 고정 분포에서 출력이 올바른가 / 유용한가 / 안전한가?"

**A/B 테스트** — 온라인, 라이브 사용자, 무작위화. 답변: "새 변형이 중요한 사용자 수준 메트릭을 이동하는가?"

둘 다 필요합니다. Eval은 노출 전에 회귀를 catches; A/B는 후에 제품 영향을 확인합니다.

### 테스트할 내용

1. **프롬프트 엔지니어링** — 문구, 시스템 프롬프트 구조, 예제. 메트릭: 작업 성공, 사용자 리텐션, 요청당 비용.
2. **모델 선택** — GPT-4 vs GPT-3.5-Turbo vs Llama-OSS. 메트릭: 정확도 (작업) + 요청당 비용 + 지연 시간 P99. 다중 목표.
3. **생성 파라미터** — temperature, top-p, max_tokens. 메트릭: 작업 특정 (출력 다양성 vs 결정론).

### CUPED — 분산 감소

사전 실험 데이터를 사용한 통제 실험. 비교 전에 사전 기간 분산을 회귀시킵니다. 일반적인 분산 감소: 30-70%. 유효 표본 크기가 무료로 증가합니다.

구현: Statsig와 GrowthBook 모두 구현합니다.

### 순차 테스트

고전적인 A/B는 고정 표본 크기를 가정합니다. 순차 테스트 ("peek-and-decide")는 반복적인 확인에서 위양성률을 통제합니다. 항상 유효한 순차 절차 (mSPRT, Howard의 confidence sequences)를 사용하면 명확한 승자에서 early停止할 수 있습니다.

### 다중 비교 수정

95% 신뢰도에서 20개의 A/B 테스트를 실행하면 우연에 의해 하나의 위양성이 발생합니다. Bonferroni 수정은 테스트당 α를 tightening합니다; Benjamini-Hochberg는 위양성 발견률을 통제합니다. GrowthBook은 둘 다 구현합니다.

### SRM — 표본 비율 불일치

해시 할당 randomizes 사용자를 변형으로 분할합니다. 50/50 분할이 47/53을 전달하면 무언가 깨졌습니다 — SRM 확인이 플래그를 지정합니다. 두 플랫폼 모두 구현합니다.

### Statsig 대 GrowthBook

**Statsig**:
- 2025년 9월 $1.1B에 OpenAI에 인수됨. 호스팅, SaaS.
- 순차 테스트, CUPED, held-out populations.
- 올인원: 기능 플래그 + 실험 + 관찰 가능성.
- 최적 적합: 번들 제품 Already 원하는 팀, OpenAI 소유권을 신경 쓰지 않음.

**GrowthBook**:
- 오픈소스 (MIT); warehouse-네이티브 (Snowflake/BigQuery/Redshift에서 직접 읽기).
- 다중 엔진: Bayesian, Frequentist, Sequential.
- CUPED, SRM, Bonferroni, BH 수정.
- 자체 호스팅 또는 관리형 클라우드.
- 최적 적합: warehouse-SQL 숍, 데이터 팀이 메트릭 레이어를 통제, OSS 원하는 경우.

### 비결정론이 검정력을 복잡하게 합니다

동일한 프롬프트가 다양한 출력을 생성합니다. 전통적인 전력 계산은 IID 관찰을 가정합니다. LLM 비결정론으로, 유효 표본 크기는 공칭보다 낮습니다. 안전 마진으로 필요한 표본 크기에 ~1.3-1.5x를 곱합니다.

### 실제 사례 결과

- 챗봇 보상 모델 변형: +70% 대화 길이, +30% 리텐션.
- Nextdoor 제목 줄: 보상 함수 개선 후 +1% CTR.
- Khan Academy Khanmigo: 지연 시간 대 수학 정확도 tradeoff의 반복.

### 안티패턴: 분위기로 shipping

모든 시니어 엔지니어가 "더 나아 보인다"는 이유로 A/B 없이 shipping된 기능을 이름 짓할 수 있습니다. 그 중 대부분은 팀이 months 동안 알아차리지 못한 제품 메트릭을 회귀시켰습니다. A/B는 강제 함수입니다.

### 기억해야 할 숫자

- Statsig가 OpenAI에 인수: $1.1B, 2025년 9월.
- GrowthBook: 오픈소스 MIT; Bayesian + Frequentist + Sequential.
- CUPED 분산 감소: 30-70%.
- LLM 비결정론 → 표본 크기 버퍼 +30-50%.

## 활용

`code/main.py`는 고정 및 순차 경계가 있는 순차 A/B 테스트를 시뮬레이션합니다. 순차가 early停止할 수 있는 방법을 보여줍니다.

## 결과물

이 레슨은 `outputs/skill-ab-plan.md`를 산출합니다. 기능 변경, 작업, 기준 given으로 플랫폼, 게이트, 표본 크기를 선택합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 기준 3% 전환에서 예상 5% 리프트에 80% 검정력에 필요한 표본 크기는 얼마입니까?
2. 의료 규제 온프레미스 고객을 위해 Statsig 또는 GrowthBook을 선택하세요.
3. 요청당 해결된 티켓 비용에서 GPT-4 vs GPT-3.5를 테스트하는 A/B를 디자인하세요. 기본 메트릭, 가드레일 메트릭, 보조的是什么?
4. 카나리가 통과하지만 A/B가 -1.2% 전환을 보여줍니다. shipping합니까? 승인 기준을 작성하세요.
5. 사전 기간 분산이 사후의 60%인 경우 CUPED를 적용하세요. 유효 표본 크기 부스트를 계산하세요.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| Eval | "오프라인 테스트" | 모델 capability의 레이블된 세트 평가 |
| A/B 테스트 | "실험" | 사용자에 대한 라이브 무작위 비교 |
| CUPED | "분산 감소" | 분산 감소를 위한 사전 기간 회귀 |
| 순차 테스트 | "peek-ok 테스트" | early 중지를 허용하는 항상 유효한 절차 |
| 다중 비교 | "가족 오류" | 많은 테스트를 실행하면 위양성이 증가합니다 |
| Bonferroni | "타이트 수정" | 테스트 수로 α를 나눕니다 |
| Benjamini-Hochberg | "BH FDR" | 덜 보수적인 위양성 발견률 통제 |
| SRM | "나쁜 분할" | 할당 버그의 표본 비율 불일치 |
| Statsig | "OpenAI 소유" | 2025년 인수된 상업용 올인원 |
| GrowthBook | "OSS 것" | MIT warehouse-네이티브 플랫폼 |
| mSPRT | "순차 확률 比 테스트" | 고전적인 순차 절차 |

## 추가 자료

- [GrowthBook — AI를 A/B 테스트하는 방법](https://blog.growthbook.io/how-to-a-b-test-ai-a-practical-guide/)
- [Statsig — 프롬프트를 넘어: 데이터 중심 LLM 최적화](https://www.statsig.com/blog/llm-optimization-online-experimentation)
- [Statsig 대 GrowthBook 비교](https://www.statsig.com/perspectives/ab-testing-feature-flags-comparison-tools)
- [Deng et al. — CUPED](https://www.exp-platform.com/Documents/2013-02-CUPED-ImprovingSensitivityOfControlledExperiments.pdf)
- [Howard — Confidence Sequences](https://arxiv.org/abs/1810.08240)