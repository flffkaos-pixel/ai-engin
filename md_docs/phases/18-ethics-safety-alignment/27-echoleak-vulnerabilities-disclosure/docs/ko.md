# EchoLeak과 취약성 공개 — CVE, coordinated disclosure

> 2024-2026년 AI 시스템 취약성 연구는 세 가지 차원으로 발전했다. 취약성 발견: Leofante et al. 2025는 LLM 기반 시스템을 겨냥한 새로운 취약성 카테고리를 체계적으로 분류한다; Carlini et al. 2024(arXiv:2408.04408)는 적대적 suffixes가 모든 안전 조정 접근을、部分적으로、无視할 수 있음을 보여준다. 공개 메커니즘: CVE와 CSAF를 통한 coordinated disclosure의 표준화. Leaker 추적: Dørum et al. 2025는 소셜 미디어 유출을 추적하여 취약성 발견자와 벤더 간 시간차를 측정한다. 법적 구조: DEF.CON 2024의 책임 있는 공개 논쟁; EU Cyber Resilience Act (2024)가 취약성 관리를 mandate한다.

**유형:** 실습
**언어:** Python (toy 취약성 스캐너)
**선수 과목:** Phase 18 · 14-16 (탈옥, red teaming)
**소요 시간:** 약 55분

## 학습 목표

- Leofante et al. 2025의 체계적 취약성 분류법의 주요 카테고리를 설명한다.
- 적대적 suffixes가 안전 조정을、部分적으로、无視하는 메커니즘을 설명한다.
- coordinated disclosure의 세 단계(발견, 보고, 공개)와 각 단계의timeline를 설명한다.
- EU Cyber Resilience Act가 AI 취약성 관리에 미치는 영향을 분석한다.

## 문제

이전 수업은 의도적 탈옥(적대적 프롬프트, 프롬프트 주입)을 다루었다. 27과는 의도치 않은 취약성 — 안전 조정이 部分적으로만 작동하는 경우, 발견되지 않은脆弱점, 부적절한 disclosure — 을 다룬다. 취약성의 발견과 공개는 안전 문화의 핵심 부분이다.

## 개념

### 취약성 분류

Leofante et al. 2025는 LLM 기반 시스템의 취약성을 체계적으로 분류한다:
- **입력 처리 취약성.** 비정상적 입력에 대한 부적절한 처리 — 길이 초과, 인코딩 공격, 컨텍스트 분할。
- **출력 처리 취약성.** 안전 조정 후 출력이 여전히 유해할 수 있는 경우 — 후처리 우회, 출력 검증 불충분。
- **모델 동작 취약성.** 안전 조정이 모델의 본질적 동작을 완전히 변경하지 않는 경우 — Jailbreak suffixes, 역할-play 탈옥。
- **통합 취약성.** LLM이 다른 시스템과 통합될 때 발생하는 경우 — RAG 환경에서 프롬프트 주입, 에이전트 체인에서 권한 상승。

### 적대적 suffixes와 안전 조정 우회

Carlini et al. 2024 (arXiv:2408.04408):
- 적대적 suffixes(자동 생성된 토큰 시퀀스)가 여러 안전 조정 접근을 부분적으로 무시할 수 있음을 보여준다.
- DPO, RLHF, constitutional AI로 조정된 모델에도 효과적.
- 그러나 100% 우회는 아니다 — 조정 강도에 따라、部分적인 우회만 가능.
- 메커니즘: 적대적 suffixes는 모델의 안전 신호를 억제하는 것이 아니라 우회한다 — 모델은 안전 기준을認識하지만 suffixes가 이를 무시하도록誘導한다.

### Coordinated Disclosure

CVE(Common Vulnerabilities and Exposures)와 CSAF(Common Security Advisory Framework)를 통한 표준화된 disclosure:
1. **발견.** 연구자 또는 내부 팀이 취약성을 식별.
2. **비공개 보고.** 벤더에게 보고 — 보통 90일以内的 수정timeline로 요청.
3. **공개.** 패치 후 CVE 발행 및 공개.

시간차:
- 평균적으로 취약성 발견から公开까지 120-180일.
- 벤더가 수정 가능한 시간: 보통 90일.
- Leaker 추적(Dørum et al. 2025): 소셜 미디어 유출이 공식 보고보다 먼저 발생하는 경우가 있다 — 이는 coordinated disclosure를破坏한다.

### EU Cyber Resilience Act (2024)

- 2024년 9월 발효, 2027년부터 완전 적용.
- 디지털 제품의 취약성 관리에 대한EU 차원의 요구.
- AI 시스템 포함 — 중요한 것은 "기본 기능" 취약성도 보고 의무의 대상.
- 벌금: 최대 €15 million 또는 글로벌 매출의 3%.

함의: AI 스타트업이 EU 시장에서 판매하려면 취약성 관리 프로세스를Formalize해야 한다.

### 책임 있는 공개 논쟁

DEF.CON 2024 논쟁:
- **支持論:** 공개는 사용자를보호한다; 벤더에 대한 pressure는 수정을加速한다.
- **반대論:** 공개는 악용을可能하게 한다; 적시에 패치를 제공해야 한다.
- **중간 입장:** 버그 바운티 프로그램 — 발견자에게 보상, 공개는 패치 후.

## 활용

`code/main.py`는toy 취약성 스캐너를 구축한다. 입력에서 일반적인 취약성 패턴(길이 초과, 비정상적 인코딩, 적대적 suffixes)을 감지한다.toy 스캐너는 실제 취약성을キャッチ하지 않지만 패턴 일치를 통한toy 예제를 제공한다.

## 결과물

이 수업은 `outputs/skill-vulnerability-disclosure.md`를 생성한다. 취약성 보고서 또는 coordinated disclosure 정책이 주어지면 취약성 범주,timeline 적절성, disclosure 선택을分析하고 권장 사항을 제시한다.

## 연습 문제

1. Leofante et al. 2025의 체계적 분류를 읽고 세 가지 취약성 카테고리를 요약한다. 각 카테고리에서 한 가지 구체적인 예를 제공한다.

2. Carlini et al. 2024의 적대적 suffixes 실험을 분석한다. suffixes가 "억제"하는 것이 아니라 "우回"하는 이유를 설명한다.

3. CVE와 CSAF를 통한 coordinated disclosure의 세 단계를 설명한다. 각 단계에서 발생할 수 있는 실패 모드를 식별한다.

4. EU Cyber Resilience Act의 취약성 관리 요구를 분석한다. 스타트업이 어떻게 compliance를Formalize할 수 있는지 세 가지 구체적인 단계를 제안한다.

5. DEF.CON 2024의 책임 있는 공개 논쟁을 요약한다. 버그 바운티 프로그램이 이 논쟁을 어떻게 해결하는지 분석한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| CVE | "Common Vulnerabilities and Exposures" | 취약성에 대한 표준화된 식별자 |
| CSAF | "Common Security Advisory Framework" | 보안 권고의 표준화된 형식 |
| Coordinated disclosure | "조율된 공개" | 벤더와 협력하여 취약성을 공개하는 프로세스 |
| 적대적 suffix | " adversarial suffix" | 안전 조정을 우회하도록 자동 생성된 토큰 시퀀스 |
| EU Cyber Resilience Act | "CRA" | 2024년 9월, 2027년 완전 적용, 취약성 관리 의무 |
| 버그 바운티 | "보상 프로그램" | 취약성 발견자에게 보상, 공개는 패치 후 |
| 취약성 분류 | "taxonomy" | Leofante et al. 2025 — 체계적 취약성 카테고리 |

## 추가 자료

- [Leofante et al. — Systematic Vulnerability Classification (arXiv:2025)](https://arxiv.org/abs/2501.08999) — 취약성 분류
- [Carlini et al. — Adversarial Suffixes (arXiv:2408.04408)](https://arxiv.org/abs/2408.04408) — 안전 조정 우회
- [Dørum et al. — Leak Tracking (2025)](https://github.com/dour/datasetleak) — 소셜 미디어 유출 추적
- [EU Cyber Resilience Act (2024)](https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act) — 완전 텍스트