# 규제 프레임워크 — EU AI Act, US Executive Order, UK AI Bill

> 2024-2026년 주요 규제는 세 가지 핵심 질문에 대한不同的 답변을 제공한다. EU AI Act (2024년 8월 발효, 2026년 완전 적용): 위험 기반 접근 — unacceptable-risk 시스템 금지, 고위험 시스템 규제, 일반 목적 AI 별도 규칙. US Executive Order 14110 (2023년 10월, Biden): 안전한 AI를 위한 연방 활동, NIST AI Frameworks, 이민을 위한 AI 안전성에 중점. UK AI Bill (202202024년 3월 포기, 2025년再導入): 규제 당국创设, 세 단계 경고 시스템, sandboxing. 주요 불일치: EU는 사전 예방적 접근, US는事后적, UK는 경고-중간-카타스트로피 3단계. 국경 간 적용: EU AI Act는 EU 고객에게 서비스하는 모든 AI 시스템에 적용; US EO는 연방 기관에만 직접 적용; UK는 국내에만 적용.

**유형:** 학습
**선수 과목:** Phase 18 · 18 (안전 프레임워크), Phase 18 · 22 (투명성)
**소요 시간:** 약 65분

## 학습 목표

- EU AI Act의 unacceptable-risk 시스템 목록과 고위험 시스템 기준을 설명한다.
- US Executive Order 14110의 주요 조치와 NIST AI Framework의 역할을 설명한다.
- UK AI Bill의 세 단계 경고 시스템과 sandboxing 메커니즘을 설명한다.
- 세 규제 프레임워크의 주요 차이를 비교하고 국경 간適用の 함의를 분석한다.

## 문제

세 가지 주요 규제 프레임워크가 동시에 발전하고 있다. 각각은 동일한 질문에 다른 답변을 제공한다: 어떤 AI가 금지되어야 하는가? 규제 대상은 누구인가? 규제를 어떻게 집행하는가? 기업은 여러 관할권에서 운영되며, 규제가 충돌하거나 상이한 요구를課하는 경우 compliance가 복잡해진다.

## 개념

### EU AI Act (2024년 8월 발효)

**위험 기반 분류:**
- **Unacceptable risk (금지):** 사회적 점수화, 실시간 생체 인식을 통한 일상적 공공 공간 감시, 어린이에 의한 성적 착취 등을 유발하는 AI.
- **High-risk (규제):** 고용(채용, 승진, 해고), 신용, 교육 평가, 사법, 인프라.
- **Limited risk (투명성 의무):** 챗봇, deepfake.
- **Minimal risk (규제 없음):** 스팸 필터 등.

**일반 목적 AI (GPAI) 별도 규칙:**
-基础 모델 공급자에 대한 의무 — 기술 문서, 훈련 데이터 문서, 에너지 소비 보고.
- Very large GPAI 모델 (10^25 FLOPs 이상)에는 추가 의무.
- European AI Office가 GPAI 규칙을 감독.

**타임라인:** 2026년까지 완전 적용. Unacceptable risk는 6개월 후 적용.

### US Executive Order 14110 (2023년 10월)

Biden 행정 命令. 주요 조치:
- NIST AI Framework 개발 지시.
- 연방 기관을 위한 AI 안전 및 보안 가이드라인.
- 이민 노동자를 위한 "AI 안전성" 개념 포함.
- 이중 용도AI의 군사적应用监控.
-网络安全 및 AI 안전 연구에 대한 자금 지원.

**한계:** 행정 命令은 연방 기관에만 직접 적용. 민간 부문에는直接적인 법적 구속력이 없다. 의회를 통한 입법이 필요.

### UK AI Bill (2025년 再導入)

2024년 3월 최초 도입 — 총선으로 인해 포기. 2025년再導入 예정. 구조:
- **three-tier warning system:** Alert (정보 공유), Assurance (심사), Action (금지/제약).
- **Regulator:** 새로운 AI Authority가 기존 규제 기관을 조율.
- **Sandboxing:** 혁신을 지원하는 규제 샌드박스 — 신기술을 보호된 환경에서 테스트.

**EU와의 차이:** UK는 특정 위험 카테고리를 명시적으로 나열하지 않음. 대신 영향 기반 접근.

### 주요 불일치

| 차원 | EU AI Act | US EO 14110 | UK AI Bill |
|------|-----------|-------------|------------|
| 접근 | 사전 예방적, 위험 분류 | 事後적, 기관 중심 | 경고 시스템, 영향 기반 |
| 적용 범위 | EU 고객 서비스的所有 AI | 연방 기관 + 군사 계약자 | UK 기반 조직 |
| GPAI | 명시적 별도 규칙 | 간접적 (NIST 통해) | 설계 중 |
| 금지 시스템 | 명시적 목록 | 없음 | 경고/조치 체계 |

### 국경 간 적용

- **EU AI Act:** EU 고객에게 서비스하는 모든 AI 시스템에 적용 — EU 소재가 아니어도 적용. GDPR의 역외 적용과 유사.
- **US EO:** 연방 기관에만 직접 적용; 군사 계약자에 대한 우회적 적용; 민간 부문은 FTC 등의 집행 행동으로 규제.
- **UK AI Bill:** UK 기반 조직에 적용; EU와의 상호 운용성 목표로 설계.

**企业的 함의:** EU 고객이 있으면 EU AI Act의 고위험 규칙을 준수해야 할 수 있다. US 민간 기업은 연방 계약에 참여하려면 NIST Framework을 준수해야 할 수 있다. 다국적 기업은 복수의 규제 프레임워크를 동시에 준수해야 한다.

## 활용

이 수업에는 코드가 없다. EU AI Act의 Annex III(고위험 응용 분야)와 NIST AI Framework의 두 가지 사용 사례 문서를 읽는다. 각 문서의 규제 의무를 비교한다.

## 결과물

이 수업은 `outputs/skill-regulatory-mapping.md`를 생성한다. AI 시스템의 설명이 주어지면 세 규제 프레임워크(EA, US EO, UK Bill) 각각 하에서 분류, 의무, 적용 가능성을 분석하고 compliance 전략을 제안한다.

## 연습 문제

1. EU AI Act의 Annex III 고위험 응용 분야 목록을 읽는다. 세 가지 응용 분야를 선택하고 각 응용 분야에 대한 구체적인 의무를 분석한다.

2. US Executive Order 14110의 조치 목록을 NIST AI Framework와 비교한다. NIST Framework이 EO의 요구를 어떻게 구체화하는지追踪한다.

3. UK AI Bill의 three-tier 경고 시스템을 분석한다. 이 시스템이 EU의 위험 분류와 어떻게 다른지, 각 접근 방식의 장점을 설명한다.

4. 국경 간 적용 문제를 분석한다. EU에 고객이 있는 US 기반 AI 스타트업의 compliance 전략을 설계한다.

5. 세 규제 프레임워크 중 하나가 다른 것들보다 AI 혁신을 더 지원한다고 주장하거나 반박한다.argument에 필요한 가정을 명시한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| EU AI Act | "EU 규제" | 2024년 8월 발효, 위험 기반 분류, 2026년 완전 적용 |
| US EO 14110 | "Biden 행정 命令" | 연방 기관 중심, NIST Framework 통해 적용 |
| UK AI Bill | "UK 규제" | three-tier 경고 시스템, AI Authority 창설 |
| Unacceptable risk | "금지된 AI" | EU AI Act — 사회적 점수화 등 |
| High-risk | "규제 대상 AI" | EU AI Act — 고용, 신용, 교육 등 |
| GPAI | "General Purpose AI" | foundation 모델에 대한 별도 규칙 |
| NIST AI Framework | "US 기술 표준" | AI 안전 및 보안에 대한 Federal guidance |
| Sandboxing | "혁신 샌드박스" | 규제 보호 하에 신기술 테스트 |

## 추가 자료

- [EU AI Act — Official Journal (2024)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689) — 완전 텍스트
- [US Executive Order 14110 (2023)](https://www.whitehouse.gov/briefings-statements/ai/) —行政 命令
- [NIST AI Framework (2023)](https://airc.nist.gov/AI_Risk_Management_Framework) — 기술 표준
- [UK AI Bill — Parliament (2025 재도입)](https://bills.parliament.uk/bills/3457) — UK Bill 텍스트