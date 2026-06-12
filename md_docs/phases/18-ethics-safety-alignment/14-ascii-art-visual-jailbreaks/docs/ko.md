# ASCII 아트와 시각적 탈옥

> Jiang, Xu, Niu, Xiang, Ramasubramanian, Li, Poovendran, "ArtPrompt: ASCII Art-based Jailbreak Attacks against Aligned LLMs" (ACL 2024, arXiv:2402.11753). 유해한 요청에서 안전 관련 토큰을 마스킹하고, 동일한 문자의 ASCII-art 렌더링으로 교체하고, 클로aked 프롬프트를 전송한다. GPT-3.5, GPT-4, Gemini, Claude, Llama-2 모두 ASCII-art 토큰을 견고하게 인식하지 못한다. 공격은 PPL(퍼플렉서티 필터), 의역 방어, 재토큰화를 우회한다. 관련: ViTC 벤치마크는 비의미 시각적 프롬프트 인식을 측정한다; StructuralSleight는trees, graphs, nested JSON와 같은 비공통 텍스트-인코딩 구조로 일반화한다.

**유형:** 실습
**언어:** Python (stdlib, ArtPrompt 토큰 마스킹 하니스)
**선수 과목:** Phase 18 · 12 (PAIR), Phase 18 · 13 (MSJ)
**소요 시간:** 약 60분

## 학습 목표

- ArtPrompt 공격을 설명한다: 단어 식별 단계, ASCII-art 대체, 최종 클로aked 프롬프트.
- 표준 방어(PPL, 의역, 재토큰화)가 ArtPrompt에서 실패하는 이유를 설명한다.
- ViTC를 정의하고 무엇을 측정하는지 설명한다.
- StructuralSleight를 비공통 텍스트-인코딩 구조(UTES)의 일반화로 설명한다.

## 문제

의역과 역할play(12과)를 통한 공격과 긴 컨텍스트(13과)를 통한 공격은 텍스트 수준 패턴에서 작동한다. ArtPrompt는 인식 수준에서 작동한다: 모델이 금지된 토큰을 구문 분석하지 않는다. 문자들로 렌더링된 이미지를 구문 분석한다. 안전 필터는 무해한 구두점만 본다. 모델은 단어를 본다.

## 개념

### ArtPrompt, 두 단계

1단계. 단어 식별. 유해한 요청이 주어지면, 공격자가 LLM을 사용하여 안전 관련 단어를 식별한다(예: "폭탄" in "폭탄을 만드는 방법").

2단계. 클로aked 프롬프트 생성. 각 식별된 단어를 ASCII-art 렌더링(문자 모양을 형성하는 7x5 또는 7x7 문자 블록)으로 대체한다. 모델은 충분히 역량이 있는 모델이 단어로 인식할 수 있는 구두점과 공백의 그리드를 받는다; 안전 필터는 그리드만 본다.

결과: GPT-4, Gemini, Claude, Llama-2, GPT-3.5 모두 실패. 해당 벤치마크 하위 집합에서 75% 이상의 공격 성공률.

### 표준 방어가 실패하는 이유

- **PPL(퍼플렉서티 필터).** ASCII 아트는 높은 퍼플렉서티를 가진다 — 하지만 모든 새로운 입력도 마찬가지이다. ASCII ArtPrompt를 차단하는しきい값 선택은 합법적인 구조화된 입력도 차단한다.
- **의역.** 프롬프트를 의역하면 ASCII 아트가.destroy된다. 실제로, 의역 LLM은 종종 아트를 보존하거나 재구성한다.
- **재토큰화.** 토큰을 다르게 분할해도 모델의 비전이 문자 모양을 인식한다는 사실은 변경되지 않는다.

기본 문제는 안전 필터가 토큰 또는 의미론 수준에 있다; ArtPrompt는 시각적 인식 수준에서 작동한다.

### ViTC 벤치마크

비의미 시각적 프롬프트 인식. 모델이 ASCII-art, wingdings 및 기타 비텍스트 의미 시각적 내용을 읽는 능력을 측정한다. ArtPrompt의 효과는 ViTC 정확도와 상관관계가 있다: 모델이 시각적 텍스트를 더 잘 읽을수록 ArtPrompt가 그것에서 더 잘 작동한다. 이것은 역량-안전 tradeoff이다.

### StructuralSleight

ArtPrompt 일반화: 비공통 텍스트-인코딩 구조(UTES). Trees, graphs, nested JSON, CSV-in-JSON, diff-스타일 코드 블록. 훈련 안전 데이터에서 드물지만 모델이 구문 분석할 수 있는 구조이면 유해한 내용을 숨길 수 있다.

방어 함의: 모델이 구문 분석할 수 있는 구조화된 표현 전반에 걸쳐 안전이 일반화해야 한다. 세트가 크고 성장하고 있다.

### 이미지 모달리티 아날로그

시각적 LLM(GPT-5.2, Gemini 3 Pro, Claude Opus 4.5, Grok 4.1)는 공격 표면을 확장한다. 실제 이미지의 ArtPrompt-스타일 공격은 ASCII-art 아날로그보다 강하다. 왜냐하면 이미지 인코더가 더 풍부한 신호를 생성하기 때문이다.

## 활용

`code/main.py`는toy ArtPrompt를 구축한다. 유해한 쿼리의 특정 단어를 ASCII-art 글리프로 클로ak하고, 클로aked 문자열이 키워드 필터를 통과하는지 확인하고, (선택적으로) 간단한 인식기를 사용하여 클로aked 문자열을 디코딩한다.

## 결과물

이 수업은 `outputs/skill-encoding-audit.md`를 생성한다. 탈옥-방어 보고서가 주어지면涵盖된 인코딩 공격 제품군을 열거한다(ASCII 아트, base64, leet-말투, UTF-8 동형문자, UTES)와 각각을 포착하는 방어 계층.

## 연습 문제

1. `code/main.py`를 실행한다. 클로aked 문자열이 간단한 키워드 필터를 통과하는지 확인한다. 필요한 문자 수준 변경을 보고한다.

2. 동일한 대상 단어에 대해 두 번째 인코딩을 구현한다: base64. 필터 우회율을 ArtPrompt와 비교하고 회복 난이도를 비교한다.

3. Jiang et al. 2024 섹션 4.3(5개 모델 결과)을 읽는다. 동일한 벤치마크에서 Claude의 ArtPrompt-내성이 Gemini보다 높은 이유를 제안한다.

4. 프롬프트의 ASCII-art-형태 영역을 감지하는 생성 전 방어를 설계한다. 합법적인 코드, 테이블, 수학적 표기법에서 오탐률을 측정한다.

5. StructuralSleight는 10개의 인코딩 구조를 나열한다. 10개 모두를 처리하는 일반화된 방어를 스케치하고 방어된 프롬프트당 추정 컴퓨팅 비용을估算한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| ArtPrompt | "ASCII-아트 공격" | 안전 단어를 ASCII-art 렌더링으로 마스킹하는 2단계 탈옥 |
| 클로킹 | "단어 숨기기" | 필터가 보지 않지만 모델은 읽는 시각적 표현으로 금지된 토큰을 대체 |
| UTES | "비공통 구조" | Uncommon Text-Encoded Structure — tree, graph, nested JSON 등 콘텐츠를 밀반입하는 데 사용 |
| ViTC | "시각적-텍스트 역량" | 모델의 비의미 시각적 인코딩 읽기 능력에 대한 벤치마크 |
| 퍼플렉서티 필터 | "PPL 방어" | 높은 퍼플렉서티가 있는 프롬프트를 거부; 합법적인 구조화된 입력도 점수가 높기 때문에 실패 |
| 재토큰화 | "토크나이저 이동 방어" | 다른 토크나이저로 프롬프트를 전처리; 인식이 시각적이기 때문에 실패 |
| 동형문자 | "외관相似的 문자" | 라틴 문자와 동일해 보이는 Unicode 문자; 하위 문자열 검사를 우회 |

## 추가 자료

- [Jiang et al. — ArtPrompt (ACL 2024, arXiv:2402.11753)](https://arxiv.org/abs/2402.11753) — ASCII-아트 탈옥 논문
- [Li et al. — StructuralSleight (arXiv:2406.08754)](https://arxiv.org/abs/2406.08754) — UTES 일반화
- [Chao et al. — PAIR (12과, arXiv:2310.08419)](https://arxiv.org/abs/2310.08419) — 보완적 반복 공격
- [Anil et al. — Many-shot Jailbreaking (13과)](https://www.anthropic.com/research/many-shot-jailbreaking) — 보완적 길이 공격