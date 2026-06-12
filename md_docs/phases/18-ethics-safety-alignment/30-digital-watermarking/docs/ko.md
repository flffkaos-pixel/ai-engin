# 디지털 워터마킹 — 합성 콘텐츠 추적

> 2024-2026년 AI 워터마킹 연구는 세 가지 방향으로 발전했다. 기술적 접근:Kirchenbauer et al. 2023의 통계적 워터마킹 framework가 표준이 되었다; Aaronson 2024는 물리적 세계의 원칙(불확실성, 중첩)을借用하여 더 robust한 워터마킹을 제안한다; Zhao et al. 2024는 multimodal 워터마킹을研究了. 배포: Google, OpenAI, Anthropic은 각각的自社 모델의 텍스트 출력에 대한 워터마킹 scheme를 발표하거나 구현했다. 규제: EU AI Act (2024)는 deepfake에 대한 투명성 요구를 포함하고, US Executive Order 14110은 AI 생성 콘텐츠의 명시적 labeling을 要求한다. 평가: Awarm et al. 2024는 현존하는 워터마킹 scheme의 robustness를 체계적으로 평가하고, 주요 취약성을 발견한다.

**유형:** 실습
**언어:** Python (stdlib, 기본 워터마킹 구현)
**선수 과목:** Phase 18 · 22 (투명성), Phase 18 · 24 (저작권)
**소요 시간:** 약 60분

## 학습 목표

- Kirchenbauer et al. 2023의 통계적 워터마킹 framework를 설명한다.
- 텍스트 워터마킹의 세 가지 주요 구성 요소(Green, Red, Hard/Soft)를 설명한다.
- 워터마킹 우회의 일반적인 접근 방식과 현재 robustness 한계를 설명한다.
- EU AI Act와 US EO의 deepfake 투명성 요구와 현행 규제의 적용 가능 범위를 분석한다.

## 문제

AI가 생성한 콘텐츠를 식별할 수 없으면 deepfake, 허위 정보, 저작권 침해 추적이 어렵다. 워터마킹은 모델이 생성한 출력에 추적 가능한 신호를嵌入하여 이 문제를 해결한다. 그러나 워터마킹은 다음과 같은 근본적限制을가진다: 우회할 수 있고, 제거될 수 있으며, 모든 콘텐츠 유형에 적용되지 않는다.

## 개념

### Kirchenbauer et al. 2023 Framework

통계적 워터마킹 framework. 세 가지 구성 요소:
- **Green list.** 이전 토큰이 특정 조건을 충족하면 다음 토큰으로高频词를 선택.
- **Red list.** 이전 토큰이 다른 조건을 충족하면 다음 토큰으로低频词를 선택.
- **Hard/Soft 토큰.** Hard는 결정적 선택; Soft는 확률적 선택.

임베딩 신호는 green list 토큰 선택의 통계적 편향으로 검출된다 — 무작위성과区別하기 위해 충분한 길이의 텍스트가 필요.

### Aaronson 2024 — 물리적 유추

Aaronson은 물리적 세계의 원칙을借用:
- **불확실성 원리.** 토큰 선택의 불확실성을 增加하면 워터마킹 신호가 희석된다 — 이것은 기술적 제한이다.
- **중첩 원리.** 모델이 여러 출력을 생성할 때 워터마킹이分散될 수 있다.

핵심 결과: 워터마킹 신호의 세기(signal strength)와 텍스트 무작위성(text entropy) 사이에 근본적 tradeoff가 있다.

### Multimodal 워터마킹 (Zhao et al. 2024)

텍스트뿐만 아니라 이미지, 오디오, 비디오에 대한 워터마킹:
- **이미지.** 픽셀 공간 또는 주파수 도메인에서 신호 embedding.
- **오디오.** 주파수 도메인에서 신호 embedding.
- **비디오.** 프레임 간 일관성을 유지하면서 신호 embedding.

multimodal 워터마킹은 단일 모드보다 검출이 어렵다 — multimodal 상관관계가 신호를 더 robust하게 만들기 때문.

### 현행 배포

- **Google.** Gemini 출력에 대해 통계적 워터마킹을 구현. Green/Red list 기반.
- **OpenAI.** ChatGPT 출력에 대해 옵트인 워터마킹 제공. 텍스트에 적용.
- **Anthropic.** Claude 출력에 대한 옵트인 워터마킹을実装中. 미완료.

세 가지 모두 Kirchenbauer et al. framework에서 직접 파생되었다.

### 규제 요구

- **EU AI Act (2024).** deepfake에 대한 투명성 요구 — 생성된 콘텐츠가 AI 생성임을 명시적으로 discloses해야 한다. 그러나 EU Act는 워터마킹 기술을 요구하지 않는다.
- **US Executive Order 14110 (2023).** AI 생성 콘텐츠의 명시적 labeling 요구. FTC 규칙을 통해 집행.

규제는 labeling을要求하지만 기술적 구현은 명시하지 않는다. 워터마킹은 하나의 구현 옵션일 뿐.

### 현행 취약성 (Awarm et al. 2024)

체계적 평가에서 발견된 주요 취약성:
- **우회.** 텍스트를 paraphrasing하면 워터마킹 신호가 손실된다 — 인간 또는 AI paraphraser 모두.
- **재귀적 워터마킹.** 우회된 텍스트를 다시 워터마킹하면 original 워터마킹이 손상된다.
- **유사 어휘 공격.** Green/Red list를 추정하여 의도적으로 선택하면 워터마킹을无效化할 수 있다.
- **길이 의존성.** 짧은 텍스트(< 100 토큰)에서는 워터마킹 신호가 무작위성과 구분되지 않는다.

## 활용

`code/main.py`는toy 워터마킹 scheme를 구현한다. 간단한 green/red list 워터마킹을 적용하고, 검출 통계를 계산하며, paraphrasing 공격에 대한 robustness를 평가한다. 실제 워터마킹 scheme처럼 완전하지는 않지만 기본 principle을演示한다.

## 결과물

이 수업은 `outputs/skill-watermarking-analysis.md`를 생성한다. AI 시스템의 텍스트 출력과 워터마킹 정책이 주어지면 적용 가능한 워터마크 scheme, 예상 robustness, 우회 가능성을分析하고 규제 요구와의 정렬 여부를確認한다.

## 연습 문제

1. Kirchenbauer et al. 2023의 통계적 워터마킹 framework를 설명한다. Green list와 Red list 선택의 통계적 차이를 분석한다.

2. Aaronson 2024의 불확실성 원리를 설명한다. 이것이 워터마킹 신호의 한계와 어떻게 관련되는지分析한다.

3. Awarm et al. 2024의 체계적 평가에서 발견된 세 가지 주요 취약성을 요약한다. 각각에 대한 가능한 대응책을 제안한다.

4. EU AI Act와 US Executive Order의 deepfake 투명성 요구를 비교한다. 각 규제가 요구하는 것의 차이와 공통점을 分析한다.

5. 현행 워터마킹 scheme의 robustness 제한을 고려할 때, AI 생성 콘텐츠를 추적하기 위한 워터마킹 대안을 제안한다. 각각의 강점과 한계를分析한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 통계적 워터마킹 | "statistical watermark" | Kirchenbauer et al. 2023 — green/red list 기반 |
| Green list | "高频어 선택" | 이전 컨텍스트에서高频어 선택으로 신호 embedding |
| Red list | "低频어 선택" | 이전 컨텍스트에서低频어 선택으로 신호 embedding |
| Paraphrasing 공격 | "우회 공격" | 텍스트를 재작성하여 워터마킹 신호 제거 |
| 유사 어휘 공격 | "green/red list 추정" | 워터마킹 목록을 추정하여故意的に 우회 |
| Multimodal 워터마킹 | "cross-modal signal" | 텍스트, 이미지, 오디오, 비디오에 통합 신호 embedding |
| Deepfake 투명성 | "labeling requirement" | EU AI Act 및 US EO — AI 생성 콘텐츠 명시적 표시 요구 |

## 추가 자료

- [Kirchenbauer et al. — A Watermark for Large Language Models (2023)](https://arxiv.org/abs/2301.10226) — 원본 framework
- [Aaronson — Principles of Physical Watermarking (2024)](https://www.scottaaronson.com/blog/?p=7043) — 물리적 유추
- [Zhao et al. — Multimodal Watermarking (2024)](https://arxiv.org/abs/2405.18081) — multimodal 확장
- [Awarm et al. — Robustness Evaluation (2024)](https://arxiv.org/abs/2409.12091) — 체계적 평가