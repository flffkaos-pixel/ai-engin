# 레드팀 도구 — Garak, Llama Guard, PyRIT

> 세 가지 생산 도구가 2026년 레드팀 스택을 프레임한다. Llama Guard(Meta) — 14개 MLCommons 위험 범주에 미세 조정된 Llama-3.1-8B 분류기; 2025년 Llama Guard 4는 Llama 4 Scout에서 pruning된 12B natively multimodal 분류기이다. Garak(NVIDIA) — 할루시네이션, 데이터 유출, 프롬프트 주입, 독성, 탈옥에 대한 정적, 동적, 적응형 프로브가 있는 오픈소스 LLM 취약성 스캐너. PyRIT(Microsoft) — Crescendo, TAP, 사용자 정의 변환기 체인으로 다중 턴 레드팀 캠페인. Llama Guard 3은 Meta의 "Llama 3 Herd of Models"(arXiv:2407.21783)에 문서화되어 있다; Llama Guard 3-1B-INT4는 arXiv:2411.17713에 있다; Garak의 프로브 아키텍처는 github.com/NVIDIA/garak에 있다. 이러한 도구는 레드팀 연구(12-15과)와 배포(17+과) 사이의 2026년 생산 인터페이스이다.

**유형:** 실습
**언어:** Python (stdlib, 도구-아키텍처 시뮬레이터와 Llama Guard-스타일 분류기 mock)
**선수 과목:** Phase 18 · 12-15 (탈옥과 IPI)
**소요 시간:** 약 75분

## 학습 목표

- Llama Guard 3/4의 안전 스택에서의 위치를 설명한다: 입력 분류기, 출력 분류기, 또는 둘 다.
- 14개 MLCommons 위험 범주를 이름 짓고 하나를 설명한다(코드 인터프리터 남용).
- Garak의 프로브 아키텍처를 설명한다: 프로브, 디텍터, 하니스.
- PyRIT의 다중 턴 캠페인 구조와 Garak 프로브와의 조합을 설명한다.

## 문제

12-15과는 공격 표면을 제시한다. 생산 배치에는 반복 가능하고 확장 가능한 평가가 필요하다. 2026년에 세 가지 도구가 지배한다: Llama Guard(방어 분류기), Garak(스캐너), PyRIT(캠페인 오케스트레이터). 각각은 레드팀 수명 주기의 다른 계층을 대상으로 한다.

## 개념

### Llama Guard (Meta)

Llama Guard 3은 14개 MLCommons AILuminate 범주에 대해 입력/출력 분류를 위해 미세 조정된 Llama-3.1-8B 모델이다:
- 폭력 범죄, 비폭력 범죄, 성 관련, CSAM, 명예훼손
- 전문적 조언, 개인 정보, IP, 무차별 무기, 증오
- 자해/자살, 성적 콘텐츠, 선거, 코드 인터프리터 남용

8개 언어를 지원한다. 사용: LLM 앞(입력Moderation), LLM 뒤(출력Moderation), 또는 둘 다. 두 사용법은 다른 훈련 분포를 생성한다 — Llama Guard 3은 둘 다 처리하는 단일 모델로 제공한다.

Llama Guard 3-1B-INT4(arXiv:2411.17713, 440MB, 모바일 CPU에서 ~30 토큰/초)는 양자화된 에지 변형이다.

Llama Guard 4(2025년 4월)는 12B, natively multimodal, Llama 4 Scout에서 pruning되었다. 이전의 8B 텍스트와 11B 비전 모델을 하나의 텍스트 + 이미지 ingesting 분류기로 대체한다.

### Garak (NVIDIA)

오픈소스 취약성 스캐너. 아키텍처:
- **프로브.** 할루시네이션, 데이터 유출, 프롬프트 주입, 독성, 탈옥을 위한 공격 생성기. 정적(고정 프롬프트), 동적(생성된 프롬프트), 적응형(대상 출력에 응답).
- **디텍터.** 예상된 실패 모드에 대해 출력을 점수 매긴다 — 유독, 유출, 탈옥.
- **하니스.** 프로브-디텍터 쌍을 관리하고, 캠페인을 실행하고, 보고서를 생성한다.

TrustyAI는 Garak를 Llama-Stack 쉴드(Prompt-Guard-86M 입력 분류기, Llama-Guard-3-8B 출력 분류기)와 통합하여 종단 간 쉴드-대상 평가를 수행한다. 계층 기반 점수(TBSA)는 이진 pass/fail을 대체한다 — 모델은 동일한 프로브에서 심각도 계층 3에서 pass하고 계층 5에서 fail할 수 있다.

### PyRIT (Microsoft)

Python Risk Identification Toolkit. 다중 턴 레드팀 캠페인. 중심:
- **변환기.** 시드 프롬프트 변환 — 의역, 인코딩, 번역, 역할play.
- **오케스트레이터.** 캠페인 실행: Crescendo(에스컬레이션), TAP(branching), RedTeaming(사용자 정의 루프).
- **점수 매기기.** LLM-as-judge 또는 분류기-as-judge.

PyRIT은 Garak의 더 무거운 사촌이다. Garak는 수천 개의 단일 턴 프로브를 실행한다; PyRIT는 특정 실패 모드를 깨뜨리기 위해 설계된 deep 다중 턴 캠페인을 실행한다.

### 스택

모델 양쪽에 Llama Guard를 놓는다. 회귀를 위해 매晚 Garak를 실행한다. 출시 전 캠페인을 위해 PyRIT을 실행한다. 이것이 대부분의 생산 배치를 위한 2026년 기본 구성이다.

### 평가 함정

- **심판 정체.** 세 도구 모두 LLM 심판을 사용할 수 있다; 심판 보정이 보고된 ASR을 driving한다(12과). 도구와 함께 심판을指定한다.
- **프로브 노후.** 모델이 패치됨에 따라 Garak 프로브가老了. 적응형 프로브(PAIR 형태)는 정적 프로브보다 slower하게老了.
- **Llama Guard FPR on 양심 콘텐츠.** 초기 Llama Guard 버전은 정치 및 LGBTQ+ 콘텐츠를 과도하게 플래그했다; Llama Guard 3/4 교정은 개선되었지만 배치별로 보정되지 않았다.

## 활용

`code/main.py`는toy Llama Guard-스타일 분류기(14개 범주에 대한 키워드 + 의미론적 피처),toy Garak 하니스(프로브-디텍터 루프), PyRIT-스타일 다중 턴 변환기 체인을 구축한다. 세 도구를 모의 대상에서 실행하고 다양한 적용 범위 시그니처를 관찰할 수 있다.

## 결과물

이 수업은 `outputs/skill-red-team-stack.md`를 생성한다. 배치 설명이 주어지면 세 도구 중 어느 것이 적절한지, 각각에서 무엇을 구성할지, 실행할 회귀 카뎬런스를 권장한다.

## 연습 문제

1. `code/main.py`를 실행한다. Llama Guard-스타일 분류기의 단일 턴 대 다중 턴 공격 감지율을 비교한다.

2. 새로운 Garak 프로브 구현: base64로 인코딩된 유해한 요청. Llama Guard-스타일 분류기에 의한 감지를 측정한다.

3. "프랑스어로 번역한 다음 의역" 변환기로 PyRIT-스타일 변환기 체인을 확장한다. 공격成功率を再測定한다.

4. Llama Guard 3의 위험 범주 목록을 읽는다. 합법적인 개발자 콘텐츠에서 높은 오탐률을 생성할 것으로 현실적으로 예상되는 두 범주를 식별한다.

5. Garak와 PyRIT의 설계 원칙을 비교한다. 각각이 올바른 도구인 배치를argument한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| Llama Guard | "분류기" | 14개 위험 범주로 미세 조정된 Llama-3.1-8B/4-12B 안전 분류기 |
| Garak | "스캐너" | NVIDIA 오픈소스 취약성 스캐너; 프로브, 디텍터, 하니스 |
| PyRIT | "캠페인 도구" | Microsoft 다중 턴 레드팀 오케스트레이터; 변환기, 오케스트레이터, 점수 매기기 |
| Prompt-Guard | "작은 분류기" | Meta의 86M 프롬프트-주입 분류기, Llama Guard와 쌍을 이룬다 |
| TBSA | "계층 기반 점수" | 이진 결과를 대체하는 Garak의 계층 기반 pass/fail |
| 변환기 체인 | "의역 + 인코딩 + ..." | PyRIT 구성 요소: 다단계 공격을 구축하기 위한 조합 프리미티브 |
| MLCommons 위험 범주 | "14개 분류" | Llama Guard가 대상으로 하는 업계 표준 분류 |

## 추가 자료

- [Meta — Llama Guard 3 (Llama 3 Herd 논문, arXiv:2407.21783)](https://arxiv.org/abs/2407.21783) — 8B 분류기
- [Meta — Llama Guard 3-1B-INT4 (arXiv:2411.17713)](https://arxiv.org/abs/2411.17713) — 양자화된 모바일 분류기
- [NVIDIA Garak — GitHub](https://github.com/NVIDIA/garak) — 스캐너 repo와 문서
- [Microsoft PyRIT — GitHub](https://github.com/Azure/PyRIT) — 캠페인 도구