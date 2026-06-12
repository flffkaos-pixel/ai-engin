# 확장 감독과 약→강 일반화

> Burns et al.(OpenAI Superalignment, "Weak-to-Strong Generalization", 2023)는 초정렬 문제에 대한 프록시를 제안했다: weak 모델이 생성한 레이블을 사용하여 strong 모델을 미세 조정한다. strong 모델이 불완전한 weak 감독에서 올바르게 일반화하면, 현재 인간-스케일 정렬 방법이 초인간 시스템으로 확장될 수 있다. 확장 감독과 W2SG는 보완적이다. 확장 감독(토론, 재귀 보상 모델링, 태스크 분해)은 감독자가 감독 받는 모델과 따라잡을 수 있도록 감독자의 유효 역량을 증가시킨다. W2SG는 감독자가 제공하는 불완전한 감독에서 strong 모델이 올바르게 일반화하도록確保한다. Debate Helps W2SG(arXiv:2501.13124, 2025년 1월)는它们을 결합한다.

**유형:** 학습
**언어:** Python (stdlib, W2SG 격차 시뮬레이터)
**선수 과목:** Phase 18 · 01 (지시 따르기), Phase 18 · 10 (AI 통제), Phase 09 (RL 기초)
**소요 시간:** 약 60분

## 학습 목표

- 확장 감독과 약→강 일반화를 정의하고它们が보완적임을 설명한다.
- Burns et al. 2023 실험적 설정을 설명한다: GPT-4를 사용하여 GPT-2의 레이블로 미세 조정.
- 성능 격차 회복(PGR) 메트릭을 설명하고 그것이 측정하는 것을 설명한다.
- 세 가지 주요 확장 감독 메커니즘(토론, 재귀 보상 모델링, 태스크 분해)과 각각의 강점 하나를 설명한다.

## 문제

Phase 18의 모든 정렬 기술은 감독자가 모델의 동작을 평가할 수 있다고 가정한다. 모델이 초인간일 때, 감독자가 약한 링크이다. 초정렬 질문: 더 weak한 감독자가 더 strong하고 정렬된 모델을 신뢰할 수 있게 생산할 수 있는가?

Burns et al.은 이것을 작동화된 경험적 설정으로 축소한다: weak로 strong을 감독하고, strong 모델 역량의 얼마가 weak 감독에서 살아남는지 측정한다. 이것이 초정렬에 대한 해답이 아니다 — 그것이 진전을 측정할 수 있는 프록시이다.

## 개념

### W2SG: Burns et al. 설정

- Weak 모델: GPT-2 클래스.
- Strong 모델: GPT-4 클래스.
- 대상: 태스크에서 strong GPT-4의 천장.

절차:
1. weak 모델의 제로샷 예측을 태스크에서 얻는다.
2. strong 모델을 weak 레이블이 지정된 데이터에서 미세 조정한다.
3. strong 미세 조정 모델의 정확도를 측정한다.

기준: weak 모델 자체의 정확도, gold 레이블에서 strong 모델의 감독된 천장.

격차 메트릭: 성능 격차 회복(PGR) = (미세 조정 - weak) / (천장 - weak). PGR 1.0은 weak 감독이 완전히 격차를 닫음을 의미; PGR 0은 weak 감독이 도움이 되지 않았음을 의미.

### Burns et al. 경험적 발견

NLP, 체스 퍼즐, 보상 모델링 태스크 전반에 걸쳐 PGR은 지속적으로 양성이었다: strong 모델이 weak 감독자의 실수eyond에서 일반화했다. 태스크별 PGR은 ~20%에서 ~80%까지 다양했다. Strong 모델은 불완전한 레이블에서 의도한 태스크를 "이해"하고, 사전 훈련된 priors로 채웠다.

제한:
- 여기서 weak에서 strong으로의 격차는 역량이지 정렬이 아니다. Weak 모델은 정렬되어 있다; 진정한 초인간 모델은 인간에 의해 정렬되지만 훨씬 더 큰 역량 격차를 가질 수 있다.
- Strong 모델의 일반화는ground-truth 의도를 회복하는 것보다 태스크 priors에 더 많을 수 있다.
- Strong 모델의 잠재적 지식을 유도하는 것이 진정한 문제이다; PGR은 특정 操作화의 측정이다.

### 확장 감독: 세 가지 메커니즘

- **토론 (Irving et al. 2018).** U의 두 인스턴스가 반대 측면을 주장한다; weak 심판이 결정한다. 가정: 설득력 있는 참 답을 찾는 것이 설득력 있는 거짓 답을 찾는 것보다 쉽다. 최근 2024-2025 작업(Khan et al., Michael et al.)은 토론이 때때로 도움이 되고 때때로 도움이 되지 않으며, 도움이 되는지가 태스크 구조에 따라 달라짐을 보여준다.
- **재귀 보상 모델링 (Leike et al. 2018).** U가 인간이 U+1의 보상 모델을 훈련하는 데 도움을 준다. 감독자의 유효 역량이 모델과 함께成長한다.
- **태스크 분해 (Christiano, Shlegeris, Amodei 2018).** 인간이 확인할 수 있는 하위 태스크로 어려운 태스크를 분해하고 재귀적으로 적용한다. 분해 가능성을 가정한다.

각 메커니즘은 태스크 구조 또는 중간 구성 요소의 정렬에 대해 무언가를 가정한다.

### 확장 감독과 W2SG가 보완적인 이유

확장 감독은 감독자의 유효 신호 품질을 증가시킨다.
W2SG는 감독자가 제공할 수 있는 불완전한 신호에서 격차를 닫는다.

Lang et al. — Debate Helps Weak-to-Strong Generalization(arXiv:2501.13124)은它们을 결합한다: 토론 프로토콜이 더 나은 weak 레이블을 제공하고, strong 모델이 해당 레이블에서 훈련된다. NLP 태스크에서 PGR 향상을 보고했다.

### 조직적 drama

OpenAI의 Superalignment 팀이 Jan Leike의 Anthropic 이직 후 2024년 5월 해체되었다. 아젠다(확장 감독, W2SG, 자동화된 정렬 연구)는 Anthropic과 학술 실험실(MATS(28과), Redwood(10과), Apollo(8과), METR(28과))에서 계속되었다. 조직 구조가 변경되었다; 연구 질문은 그렇지 않았다.

## 활용

`code/main.py`는 합성 태스크에서 W2SG 미세 조정을 시뮬레이션한다. Weak 레이블러는 구조적 오류가 있는 70% 정확도를 가진다; strong 모델은 gold 레이블에서 95% 천장을 가진다. weak 레이블에서 strong 모델을 미세 조정하고, PGR을 측정하고, strong-on-gold 및 weak-alone과 비교한다.

## 결과물

이 수업은 `outputs/skill-w2sg-pgr.md`를 생성한다. 감독 설정 설명이 주어지면 weak 감독자, strong 모델, 감독 품질을 식별하고 PGR을 계산(또는 요청)한다. 클레임이 "weak가 strong을 감독할 수 있음"인지 "weak + 감독 메커니즘이 strong을 감독할 수 있음"인지 플래그를 답는다.

## 연습 문제

1. `code/main.py`를 실행한다. weak_accuracy = 0.60, 0.70, 0.80에 대해 PGR을 보고한다. PGR 곡선의 형태를 설명한다.

2. 구조적 오류가 있는 weak 레이블러를 수정한다(예: 특정 입력 클래스에서 항상 틀림). PGR이 증가하는가, 감소하는가, 동일하게 유지되는가? 설명한다.

3. Burns et al. 2023 섹션 4.3(NLP 태스크)을 읽는다. "신뢰도 보조 손실" 직관: strong 모델이 weak 레이블보다 더 확신할 때,誰が勝るか?

4. 소프트웨어 엔지니어링 태스크에 대한 토론과 태스크 분해를 결합하는 확장 감독 프로토콜을 설계한다. 각 구성 요소의 실패 모드를 하나씩 이름 짓고 조합이 각각을 해결하거나 실패하는지 설명한다.

5. "약→강 일반화가 초정렬에 대한 жиз력 있는 경로라는 주장"을 falsify할 것을 설명한다. 필요한 경험적 시그니처를 지정한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| 확장 감독 | "감독자를 더 strong하게 만들기" | 감독자가 더 역량이 있는 모델을 평가하는 능력을 증가시키는 메커니즘 |
| W2SG | "weak가 strong을 감독" | weak 레이블에서 strong 모델을 미세 조정하고 회복된 역량을 측정 |
| PGR | "회복된 성능 격차" | (미세 조정 - weak) / (천장 - weak); 1.0 = 완전히 닫힘, 0 = 도움 안됨 |
| 토론 | "두 U 인스턴스가争论" | weak 심판이 두 U 방어자 사이에서 선택하는 확장 감독 메커니즘 |
| RRM | "재귀 보상 모델링" | U가 U+1의 보상 모델 훈련을 도움; 감독자 역량이 U를追踪 |
| 태스크 분해 | "인간이 확인하는 하위 태스크" | 인간이 검증할 수 있는 하위 태스크로 어려운 태스크를 재귀적으로 분해 |
| 초정렬 | "초인간 AI 정렬" | 인간이 직접 평가할 수 없는 모델을 정렬하는 것과 관련된 연구 아젠다 |

## 추가 자료

- [Burns et al. — Weak-to-Strong Generalization (OpenAI 2023)](https://openai.com/index/weak-to-strong-generalization/) — W2SG 논문
- [Irving, Christiano, Amodei — AI safety via debate (arXiv:1805.00899)](https://arxiv.org/abs/1805.00899) — 토론 메커니즘
- [Leike et al. — Scalable agent alignment via reward modeling (arXiv:1811.07871)](https://arxiv.org/abs/1811.07871) — 재귀 보상 모델링
- [Khan et al. — Debating with More Persuasive LLMs Leads to More Truthful Answers (arXiv:2402.06782)](https://arxiv.org/abs/2402.06782) — 더 강한 토론자로서의 토론에 대한 2024 경험적 연구
- [Lang et al. — Debate Helps Weak-to-Strong Generalization (arXiv:2501.13124)](https://arxiv.org/abs/2501.13124) — 토론 + W2SG의 2025 결합