# AI 저작권 — 훈련 데이터, 출력, 공리주의

> 2024-2026년 저작권- AI 전투의 세 fronts. 훈련 데이터: Getty Images v. Stability AI(N.D. Cal., 2023년 1월)와 다수 집단소송이 Training 데이터 사용의 "합리적 사용" 지위를 도전한다; Kane et al. 2024는 훈련 데이터에서 저작권 보호 작품의 빈도가 모델 성능과 상관관계가 있음을 보여준다. 모델 출력: Andersen v. Stability AI(N.D. Cal., 2023년 2월)와 달리多家는 모델이 생성한 출력이 기존 작품과 충돌할 경우 copyright infringement를 주장한다. 공리주의적 정당화: Samuelson 2024는 AI의 저작권 예외가 전통적인 합리적 사용 원칙을侵食할 수 있다고 경고한다; Crews 2024는 AI 개발자가 훈련 데이터에 대한 사용료를 지불하는 compulsory licensing 체제를 제안한다. EU AI Act (2024)와 NOYB投诉(2024)은 훈련 데이터 privacy와 저작권分别の問題을separately 다룬다.

**유형:** 학습
**언어:** 없음
**선수 과목:** Phase 18 · 22 (투명성), Phase 18 · 23 (합성 데이터)
**소요 시간:** 약 60분

## 학습 목표

- AI 모델 훈련의 "합리적 사용" 대 "표면적 복사"를 구분하는 테스트를 설명한다.
- Getty Images v. Stability AI 사례의 현재 상태와 주요論点을 설명한다.
- 모델 출력에 대한 저작권 침해 주장의 두 가지 접근 방식(직접 침해, 의무違反)을 분석한다.
- 세 가지 공리주의적 정당화(변환적 사용, compulsory licensing, 지불 기금)를 비교한다.

## 문제

AI 모델은 저작권 보호 작품을 포함하는 대규모 코퍼스로 훈련된다. 생성된 출력은 기존 작품과 유사할 수 있다. 이것은 세 가지 법적 문제를生成한다: 훈련 데이터 사용의 합법성, 출력의 저작권 침해,版权所有자への补偿.

## 개념

### 훈련 데이터와 합리적 사용

합리적 사용 테스트 (Campbell v. Acuff-Rose, 1994):
1. 목적과 특성: 상업적인가, 변환적인가?
2. 작품의 특성.
3. 사용된 양과 중요성.
4. 시장에 대한 효과.

Getty Images v. Stability AI (N.D. Cal., 2023년 1월):
- Getty는 Stability AI가 12 million 개의 Getty 이미지를 훈련에 사용하고 유사한 이미지를 생성했다고 주장.
- Stability의 방어: 변환적 사용 — 모델은 특정 이미지를복제하지 않고 일반적인 미학적 패턴을 학습.
- Getty의 대응: 시장 효과가 명백함 — Getty 라이선스 대안 있음.
- 현재 상태: Discovery 진행 중; 2025년 말까지 결론 예상.

### 모델 출력 저작권

Andersen v. Stability AI (N.D. Cal., 2023년 2월):
- 예술가 집단소송: Stability AI의 출력이다.

The training data copyright question is distinct from output copyright. Getty's claim concerns the act of training itself—reproducing copyrighted material to extract patterns—rather than whether outputs infringe.

Two theories of liability:
- **직접 침해.** 모델이 생성한 특정 출력이 기존 작품과实质적으로 유사.
- **계약/의무 위반.** 훈련 데이터에 대한 사용 조건을 위반하여 모델이 학습.

직접 침해의 핵심 문제: 모델이 "기억"하는가, 아니면 "일반화"하는가? 메모리-Augmented 모델은 더 높은 위험.

### 변환적 사용

변환적 사용은 가장 흔한 방어이다. 그러나 Samuelson 2024는 다음과 같이 경고한다: AI의 "변환적" 사용 개념이 너무 넓어지고 있다. 전통적으로 변환성은 새로운 표현이나 메시지를 추가하는 것을 의미했다. AI 모델은 종종訓練 데이터의 구조적 특징을포함한다 — 이것은 전통적 의미에서 변환적이지 않다.

적용: 이미지 생성 모델이 사진을 재구성하는 것은 변환적이다; 텍스트 모델이 작가를模仿하여 글쓰는 것은 변환적이지 않을 수 있다.

### 공리주의적 정당화

세 가지 접근:
- **변환적 사용.** AI가 훈련 데이터를 변환하여 새로운 값을 만들면 합리적 사용. 그러나 Samuelson이 지적하듯 범위가模糊하다.
- **Compulsory licensing (Crews 2024).** 훈련 데이터 사용에 대한 법적 사용료. 데이터 접근에 대한 market-based 보상 메커니즘. 그러나 측정이 어렵다 — 개별 작품이 훈련에 얼마나 기여했는지 어떻게 결정하는가?
- **지불 기금.** AI 개발자가 pooled 기금에 기여하고版权所有자へ比例分配. 데이터 접근 추적 없이 작동. 그러나 충분한 보상을 보장하지 않을 수 있다.

### EU AI Act와 분리

EU AI Act (2024)는 Training 데이터 privacy와 저작권을separately 다룬다:
- **Privacy.** GDPR 적용 — 개인 데이터 처리의 합법성 요구.
- **저작권.**Directive 2019/790 — 텍스트 및 데이터 마이닝의 선택적 예외; 版权所有자가 "reserved"를 명시적으로 표기하면 예외 적용 안 됨.

EU의 "opt-out" 모델은 US의 합리적 사용 방어와 대조적이다.版权所有자가 명시적으로 거부하지 않는 한 US는 합리적 사용으로 간주.

## 활용

이 수업에는 코드가 없다. Getty Images v. Stability AI와 Andersen v. Stability AI의 filed complaints을 읽는다. 각 사건의 주요 주장을 요약하고 공통된法律 문서를identifying한다.

## 결과물

이 수업은 `outputs/skill-copyright-analysis.md`를 생성한다. AI 모델의 훈련 데이터 출처 또는 생성된 출력에 대한 저작권 주장이 주어지면, 훈련 데이터 사용의 합리적 사용 분석, 출력 침해 평가, 공리주의적 정당화 적용을 수행한다.

## 연습 문제

1. Getty Images v. Stability AI의 filed complaint를 읽는다. Getty의 네 가지 주요 주장을 이름 짓고 각각에 대한 Stability의 예상 방어를 분석한다.

2. Samuelson 2024의 "변환성 침식" 논문을 읽는다. 전통적 변환성 개념과 AI가 적용하는 "변환적 사용" 개념의 차이를 설명한다.

3. Compulsory licensing 체제(Crews 2024)를 설계한다. 개별 작품의 기여도를 어떻게 측정하는지, 보상分配 규칙을 어떻게設計하는지 설명한다.

4. 모델이 "기억" 대 "일반화"하는 것을 구분하는 empirical 테스트를 설계한다. 메모리-Augmented 모델이 더 높은 기억 위험을持つ 이유를 설명한다.

5. EU AI Act의 opt-out 모델과 US 합리적 사용 방어를 비교한다. 각 모델이 AI 개발자와版权所有자에게 어떤 인센티브를 부여하는지 분석한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 합리적 사용 | "fair use defense" | 저작권 침해에 대한 방어 — 네 가지 요소 테스트 |
| 변환적 사용 | "transformative use" | 원작과 다른 목적이나 특성으로 사용하는 것 |
| 직접 침해 | "output infringement" | 모델 출력이 기존 작품과实质적으로 유사 |
| 의무 위반 | "training terms violation" | 훈련 데이터 사용 조건 위반 |
| compulsory licensing | "사용료 체제" | 훈련 데이터 사용에 대한 법적 사용료 |
| opt-out 모델 | "EU 저작권 모델" | 명시적 거부 없으면 training 허용 |
| 메모리-Augmented | "RAG/검색-Augmented" | 검색 증강으로 특정 훈련 데이터를 더 잘 기억하는 모델 |

## 추가 자료

- [Getty Images v. Stability AI — Complaint (N.D. Cal., 2023)](https://www.courtlistener.com/docket/65821701/getty-images-us-inc-v-stability-ai/) — filed complaint
- [Andersen v. Stability AI — Complaint (N.D. Cal., 2023)](https://www.courtlistener.com/docket/65902236/andersen-v-stability-ai/) — 예술가 집단소송
- [Samuelson — AI and Copyright (2024)](https://journals.library.stanford.edu/slt/issue/24/1) — 변환성 침식
- [Crews — Compulsory Licensing for AI Training Data (2024)](https://www.copyright.gov/blog/crews-ai-licensing/) — 사용료 체제 제안
- [EU AI Act — Training data provisions (2024)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)