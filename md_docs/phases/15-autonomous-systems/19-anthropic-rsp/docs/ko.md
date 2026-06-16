# Anthropic Responsible Scaling Policy v3.0

> RSP v3.0은 2026년 2월 24일부터 발효되어 2023년 정책을 대체했다. 2계층 완화: Anthropic이 일방적으로 할 것과 업계 전체 권장 사항(RAND SL-4 보안 표준 포함)으로 프레이밍된 것. Frontier Safety Roadmaps 및 Risk Reports를 일회성 산출물이 아닌 상시 문서로 추가. 2023년 일시 중지 약속 철회. AI R&D-4 임계값 도입: 일단 넘으면, Anthropic은 정렬 위험과 완화책을 식별하는 긍정적 사례를 게시해야 함. Claude Opus 4.6은 이를 넘지 않음. Anthropic은 v3.0 발표에서 "이를 자신 있게 배제하기가 어려워지고 있다"고 밝힘. SaferAI는 2023년 RSP를 2.2로 평가; v3.0을 1.9로 하향 조정하여 Anthropic을 OpenAI 및 DeepMind와 함께 "약함" RSP 카테고리에 넣음. 정량적 임계값이 정성적 임계값으로 대체됨; 일시 중지 조항 제거가 가장 날카로운 후퇴.

**Type:** 학습
**Languages:** Python (stdlib, RSP threshold decision engine)
**Prerequisites:** Phase 15 · 06 (AAR), Phase 15 · 07 (RSI)
**Time:** ~45분

## 문제

프론티어 연구소는 부분적으로 기술 문서, 부분적으로 거버넌스 문서, 부분적으로 규제 기관에 대한 신호인 확장 정책을 발행한다. RSP v3.0은 현재 Anthropic 문서다. 이를 면밀히 읽는 것이 중요한 이유는 준수가 구속력이 있어서가 아니라(그렇지 않음), 프레이밍이 연구소가 치명적 위험을 어떻게 개념화하고 대중에게 트레이드오프를 어떻게 전달하는지 형성하기 때문이다.

v3.0과 v2.0의 차이가 유용한 단위다. 추가된 것: Frontier Safety Roadmaps, Risk Reports, AI R&D-4 임계값. 제거된 것: 2023년 일시 중지 약속. 재프레이밍된 것: Anthropic-일방적과 업계-권장으로 분할된 2계층 완화 일정. 외부 검토 — SaferAI — 점수를 2.2(v2)에서 1.9(v3.0)로 하향 조정했다. 이것이 확장 정책이 더 정교해 보이면서 덜 엄격해질 수 있는 방법이다.

## 개념

### 2계층 완화 일정

- **Anthropic 일방적 조치**: 다른 연구소가 무엇을 하든 관계없이 Anthropic이 할 것. 특정 임계값 이상에서 훈련 중단, 특정 보안 조치, 특정 배포 게이트.
- **업계 전체 권장 사항**: Anthropic이 업계가 집단적으로 해야 한다고 생각하는 것. RAND SL-4 보안 표준 포함. 이는 Anthropic 측의 약속이 아니라 정책 옹호다.

2계층 구조는 v2에 없었다. 이는 독자가 각 약속이 어느 열에 있는지 봐야 함을 의미한다. "업계 전체 권장" 열의 보안 조치는 Anthropic의 약속이 아니라 희망이다.

### AI R&D-4 임계값

이는 RSP v3.0이 중요한 다음 임계값으로 명명하는 역량 수준이다. 구체적으로: 경쟁력 있는 비용으로 AI 연구의 상당 부분을 자동화할 수 있는 모델. Anthropic이 모델이 이를 넘는다고 믿으면, 지속적인 확장 전에 정렬 위험과 완화책을 식별하는 긍정적 사례를 게시해야 한다.

Claude Opus 4.6은 v3.0 발표에 따라 이를 넘지 않는다. 문서는 "이를 자신 있게 배제하기가 어려워지고 있다"고 추가한다. 그 표현은 중요하다; 임계값이 사변적 한계가 아닌 실시간 우려가 될 만큼 가깝다는 것을 인정한다.

레슨 6(자동화된 정렬 연구)과 레슨 7(재귀적 자기 개선)은 이 임계값에 직접적으로 연결된다. 연구 품질 기준을 넘는 자동화된 정렬 연구원은 AI R&D-4 임계값이 접근하고 있다는 증거다.

### Frontier Safety Roadmaps 및 Risk Reports

v3.0은 두 가지 아티팩트 유형을 상시 문서로 승격시킨다:

- **Frontier Safety Roadmap**: 계획된 안전 작업, 역량 기대치 및 완화 연구를 설명하는 미래 지향적 문서.
- **Risk Report**: 출시 후 특정 모델에 대한 회고적 문서, 관찰된 역량과 잔여 위험 설명.

둘 다 공개다. 둘 다 선언된 주기로 업데이트된다. 유용성: 독자는 Roadmap에서 Anthropic이 하겠다고 한 것과 Risk Report에서 보고하는 것을 비교할 수 있다.

### 일시 중지 조항 제거

2023년 RSP는 명시적 일시 중지 약속을 포함했다: 모델이 특정 역량 임계값을 넘으면, 완화책이 마련될 때까지 훈련이 일시 중지된다. v3.0은 명시적 일시 중지를 더 부드러운 공식(긍정적 사례 게시, 완화책이 적절하면 진행)으로 대체한다. SaferAI와 다른 분석가들은 이를 새 문서에서 가장 강력한 후퇴로 직접 지적했다.

변경에 대한 정책 논쟁: 2023년의 정량적 임계값은 2026년 시대의 역량 벤치마크가 재조정되었기 때문에 도달 불가능한 것으로 판명되었다. 반대 논쟁: 확장 정책의 일시 중지 조항은 약속 장치다; 이를 제거하면 정책의 신뢰성이 제거된다.

### SaferAI의 하향 조정

SaferAI는 RSP 스타일 문서를 평가하는 독립 조직이다. 공개 평가: 2023년 Anthropic RSP가 2.2점을 받았다(4.0이 최고 현재 RSP이고 1.0이 명목상인 척도에서). v3.0은 1.9점을 받았다. 이는 Anthropic을 "중간"에서 "약함"으로 이동시켰으며, OpenAI 및 DeepMind와 함께 약함 카테고리에 합류했다.

SaferAI에 따른 하향 조정 요인:
- 정량적 임계값이 정성적 임계값으로 대체됨.
- 일시 중지 약속 제거됨.
- AI R&D-4 임계값 완화책이 특정 조치보다 "긍정적 사례"로 설명됨.
- 검토 메커니즘이 제한된 독립적 감독하에 Anthropic의 Safety Advisory Group에 의존함.

### 이 레슨이 아닌 것

이는 규정 준수에 관한 레슨이 아니다. RSP v3.0은 규제가 아니다; 아무것도 Anthropic이 이를 따르도록 강제하지 않는다. 레슨은 문서를 가지고 마땅한 특수성과 회의론으로 읽는 것이다. 확장 정책은 프론티어 연구소가 치명적 위험 태세에 대해 발행하는 주요 공개 신호다. 그것들을 잘 읽는 것은 프론티어 역량에 의존하는 모든 사람의 실용적 기술이다.

## 사용하기

`code/main.py`는 RSP 임계값 평가 형태를 반영하는 작은 결정 엔진을 구현한다: 후보 모델과 일련의 역량 측정값이 주어지면, AI R&D-4 임계값이 넘어졌는지, 필요한 긍정적 사례 섹션, 배포가 진행될 수 있는지 여부를 반환한다. 의도적으로 간단하다; 요점은 문서의 로직을 명시적으로 만드는 것이다.

## 출시하기

`outputs/skill-scaling-policy-review.md`는 v3.0 참조(2계층 구조, 임계값, 일시 중지 약속, 독립적 검토)에 대해 확장 정책(Anthropic, OpenAI, DeepMind 또는 내부)을 검토한다.

## 연습문제

1. `code/main.py`를 실행하라. 다른 역량 수준에서 세 개의 합성 모델을 공급하라. 임계값 평가자가 예상대로 작동하고 올바른 긍정적 사례 템플릿을 생성하는지 확인하라.

2. RSP v3.0 전체(32페이지)를 읽어라. "업계 전체 권장" 계층에 있는 모든 약속을 식별하라. 그 약속 중 v2에서 "Anthropic 일방적"이었을 것은 무엇인가?

3. SaferAI의 RSP 평가 방법론을 읽어라. 그들의 루브릭을 문서에 적용하여 v3.0에 대한 1.9 점수를 재현하라. 어떤 루브릭 행이 하향 조정을 가장 많이 주도했는가?

4. 2023년 일시 중지 약속이 제거되었다. 2026년 벤치마크 재조정 문제를 인정하면서 정책의 신뢰성을 보존하는 대체 약속을 제안하라.

5. RSP v3.0을 OpenAI Preparedness Framework v2(레슨 20)와 비교하라. v3.0이 더 강한 한 영역을 골라라. Preparedness Framework가 더 강한 한 영역을 골라라.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|---|---|---|
| RSP | "Anthropic의 확장 정책" | Responsible Scaling Policy; v3.0 2026년 2월 24일 발효 |
| AI R&D-4 | "연구 자동화 임계값" | 경쟁력 있는 비용으로 상당한 AI 연구를 자동화하는 역량 |
| 긍정적 사례 (Affirmative case) | "안전 정당화" | 위험이 식별되고 완화책이 적절하다는 게시된 논증 |
| Frontier Safety Roadmap | "전방 계획" | 계획된 안전 작업과 예상 역량에 관한 상시 문서 |
| Risk Report | "모델에 대한 회고" | 출시 후 관찰된 역량과 잔여 위험에 관한 상시 문서 |
| 2계층 완화 (Two-tier mitigation) | "일방적 vs 업계" | 분리된 Anthropic 약속 vs 업계 권장 사항 |
| 일시 중지 약속 (Pause commitment) | "2023년 조항" | 훈련을 일시 중지하겠다는 명시적 약속; v3.0에서 제거됨 |
| SaferAI 등급 (SaferAI rating) | "독립적 RSP 등급" | 제3자 루브릭; v3.0 1.9점 (v2는 2.2) |

## 추가 읽을거리

- [Anthropic — Responsible Scaling Policy v3.0](https://anthropic.com/responsible-scaling-policy/rsp-v3-0) — 전체 32페이지 정책.
- [Anthropic — RSP v3.0 announcement](https://www.anthropic.com/news/responsible-scaling-policy-v3) — v2의 변경 사항 요약.
- [Anthropic — Frontier Safety Roadmap](https://www.anthropic.com/research/frontier-safety) — RSP v3.0에서 연결된 상시 문서.
- [Anthropic — Risk Report: Claude Opus 4.6](https://www.anthropic.com/research/risk-report-claude-opus-4-6) — 현재 프론티어 모델에 대한 회고.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — AI R&D-4를 측정된 자율성에 연결.
