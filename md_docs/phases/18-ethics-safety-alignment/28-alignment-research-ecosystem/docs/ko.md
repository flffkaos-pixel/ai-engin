# 정렬 연구 생태계 — MATS, Redwood, Apollo, METR

> 다섯 조직이 2026년 비연구소 정렬 연구 계층을 정의한다. MATS (ML Alignment & Theory Scholars): 2021년 말 이후 527명 이상의 연구자, 180개 이상의 논문, 10,000회 이상 인용, h-지수 47; 2024년 여름 코호트는 약 90명의 학자와 40명의 멘토와 함께 501(c)(3)으로 설립; 2025년 이전 졸업생의 80%가 안전/보안 분야에서 일하며 200명 이상이 Anthropic, DeepMind, OpenAI, 영국 AISI, RAND, Redwood, METR, Apollo에 재직. Redwood Research: Buck Shlegeris가 설립한 응용 정렬 연구소; AI Control 도입(레슨 10); 영국 AISI와 통제 안전 사례 협력. Apollo Research: 프론티어 연구소를 위한 배포 전 책략 평가; In-Context Scheming(레슨 8) 및 Towards Safety Cases for AI Scheming 저술. METR (Model Evaluation and Threat Research): 과제 기반 역량 평가, 자율 과제 시간 범위 연구; "Common Elements of Frontier AI Safety Policies"는 연구소 프레임워크를 비교. Eleos AI Research: 모델 웰페어 배포 전 평가(레슨 19); Claude Opus 4 웰페어 평가 수행.

**Type:** Learn
**Languages:** none
**Prerequisites:** Phase 18 · 01-27 (이전 Phase 18 레슨)
**Time:** ~45분

## 학습 목표

- 비연구소 정렬 연구 생태계의 다섯 조직과 그들의 핵심 산출물을 식별한다.
- MATS의 규모(학자, 논문, h-지수)와 인재 파이프라인으로서의 역할을 설명한다.
- Redwood의 AI Control 의제와 영국 AISI와의 파트너십을 설명한다.
- METR의 과제 기반 평가 방법론을 설명한다.

## 문제

프론티어 연구소(레슨 18)는 내부적으로 안전 평가를 생산하고 선별된 결과를 발표한다. 연구소 외부의 생태계는 평가가 검증되고, 새로운 실패 모드가 처음 발견되며, 인재가 훈련되는 곳이다. 생태계를 이해하면 어떤 연구 결과가 누구에 의해 신뢰받는지 해석하는 데 도움이 된다.

## 개념

### MATS (ML Alignment & Theory Scholars)

2021년 말 시작. 연구 멘토십 프로그램; 학자는 10-12주 동안 특정 정렬 문제에 대해 선임 연구자와 함께 작업.

규모 (2026):
- 창립 이후 527명 이상의 연구자.
- 180개 이상의 논문 발표.
- 10,000회 이상 인용.
- h-지수 47.
- 2024년 여름: 90명의 학자 + 40명의 멘토; 501(c)(3)으로 설립.

경력 결과: 2025년 이전 졸업생의 약 80%가 안전/보안 분야에서 일함. 200명 이상이 Anthropic, DeepMind, OpenAI, 영국 AISI, RAND, Redwood, METR, Apollo에 재직.

### Redwood Research

응용 정렬 연구소. Buck Shlegeris 설립. AI Control 의제 도입(레슨 10). 영국 AISI와 통제 안전 사례 협력. DeepMind 및 Anthropic에 평가 설계 자문.

표준 논문: Greenblatt, Shlegeris et al., "AI Control" (arXiv:2312.06942, ICML 2024); Alignment Faking (Greenblatt, Denison, Wright et al., arXiv:2412.14093, Anthropic 공동).

스타일: 특정 위협 모델, 최악의 경우 공격자, 스트레스 테스트 가능한 구체적 프로토콜.

### Apollo Research

프론티어 연구소를 위한 배포 전 책략 평가. In-Context Scheming 저술(레슨 8, arXiv:2412.04984). 2025년 OpenAI 반-책략 훈련 협력 파트너. Towards Safety Cases for AI Scheming (2024) 제작.

스타일: 기만이 나타날 수 있는 에이전틱 환경 평가; 세 가지 기둥 분해(정렬 오류, 목표 지향성, 상황 인식).

### METR (Model Evaluation and Threat Research)

과제 기반 역량 평가. 자율 과제 완료 시간 범위 연구. "Common Elements of Frontier AI Safety Policies" (metr.org/common-elements, 2025)는 연구소 프레임워크를 비교.

Apollo와 AI 책략 안전 사례 스케치 공동 저술.

스타일: 장기 과제 평가, 경험적 역량 측정, 프레임워크 종합.

### Eleos AI Research

모델 웰페어 배포 전 평가. 시스템 카드의 섹션 5.3에 문서화된 Claude Opus 4 웰페어 평가 수행. 레슨 19의 웰페어 관련 주장에 대한 외부 방법론 검증 제공.

### 흐름

MATS가 연구자를 훈련한다. 졸업생은 Anthropic, DeepMind, OpenAI (연구소 안전 팀) 또는 Redwood, Apollo, METR, Eleos (외부 평가)로 간다. 외부 평가자는 연구소 및 영국 AISI / CAISI와 협력한다. 발표물은 다음 코호트를 위해 MATS로 피드백된다.

### 이 계층이 중요한 이유

단일 출처 평가는 신뢰할 수 없다: 연구소가 자체 모델을 평가하는 것은 구조적 이해 충돌이 있다. 외부 평가자는 연구소가 과소보고할 수 있는 실패 모드를 제기하고 검증할 수 있다. 2024년 Sleeper Agents 논문(레슨 7)은 Anthropic + Redwood; Alignment Faking은 Anthropic + Redwood; In-Context Scheming은 Apollo; Anti-Scheming은 Apollo + OpenAI. 다중 조직 구조가 품질 관리이다.

### Phase 18에서의 위치

레슨 7-11은 Redwood 및 Apollo 작업을 참조; 레슨 18은 METR의 프레임워크 비교를 참조; 레슨 19는 Eleos를 참조. 레슨 28은 Phase의 나머지가 의존하는 생태계에 대한 명시적 조직 지도이다.

## 사용하기

코드 없음. METR의 "Common Elements of Frontier AI Safety Policies"를 외부 종합이 연구소 내부 정책 작업에 가치를 더하는 방법의 예시로 읽는다.

## 결과물

이 레슨은 `outputs/skill-ecosystem-map.md`를 생성한다. 정렬 주장 또는 평가가 주어지면 조직, 발행처, 방법론 스타일을 식별하고 알려진 대응 조직과 교차 확인한다.

## 실습

1. 레슨 7-15에서 하나의 논문을 선택하고 관련 조직을 식별한다. 저자를 MATS 졸업생 및 현재 생태계 소속과 교차 확인한다.

2. METR의 "Common Elements of Frontier AI Safety Policies"를 읽는다. 그들이 강조하는 세 가지 연구소 간 수렴점과 가장 큰 두 가지 발산점을 식별한다.

3. MATS의 경력 결과는 약 80%가 안전/보안이다. 이 선택 압력이 적응적(분야를 훈련)인지 편향적(이단적 입장을 걸러냄)인지 논증한다.

4. Redwood와 Apollo는 모두 통제/책략 작업을 하지만 다른 스타일로 한다. 하나의 실패 모드를 선택하고 각각이 어떻게 조사할지 설명한다.

5. Eleos AI는 유일한 순수 모델 웰페어 조직이다. 다른 웰페어 인접 질문(인지 자유, 로봇 체화 등)에 초점을 맞춘 가상의 두 번째 조직을 설계하고 그 방법론을 설명한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| MATS | "멘토십 프로그램" | ML Alignment & Theory Scholars; 2021년 이후 527명 이상의 연구자 |
| Redwood Research | "통제 연구소" | 응용 정렬; AI Control 저자; 영국 AISI 파트너 |
| Apollo Research | "책략 평가" | 프론티어 연구소를 위한 배포 전 책략 평가 |
| METR | "과제 범위 평가" | 과제 기반 역량 평가; 프레임워크 종합 |
| Eleos AI | "웰페어 연구소" | 모델 웰페어 배포 전 평가 |
| 인재 파이프라인 | "MATS -> 연구소" | MATS 졸업생이 Anthropic, DM, OpenAI, Redwood, Apollo, METR로 이동 |
| 외부 평가 | "비연구소 검증" | 모델 생산자가 아닌 기관의 평가; 신뢰도 추가 |

## 추가 자료

- [MATS (ML Alignment & Theory Scholars)](https://www.matsprogram.org/) — 멘토십 프로그램
- [Redwood Research](https://www.redwoodresearch.org/) — AI Control 논문
- [Apollo Research](https://www.apolloresearch.ai/) — 책략 평가
- [METR — Common Elements of Frontier AI Safety Policies](https://metr.org/blog/2025-03-26-common-elements-of-frontier-ai-safety-policies/) — 프레임워크 비교
- [Eleos AI Research](https://www.eleosai.org/research) — 모델 웰페어 방법론
