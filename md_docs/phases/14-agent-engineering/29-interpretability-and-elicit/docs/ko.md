# 해석 가능성: Elicit, TransformerLens, SAE

> 해석 가능성은 모델이 LLM 내부에서 무엇을 계산하는지 설명한다. Elicit는 사전을 학습한다. TransformerLens는 잔류 스트림을 가져와서 구성한다. SAE는 숨겨진 유닛 희소성을 부과한다. 세 가지 방법 모두 신경망을 이해하는 동일한 목표에 대한 보기다.

**Type:** Learn
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 05 (Model Router)
**Time:** ~45분

## 문제

LLM이 출력을 생성한다. 무슨 근거로? 해석 가능성 방법은 신경망 내부를 열어 숨겨진 표현을 검사한다. 운영 용도는 감사, 디버깅 및 편향 감지이다. 연구는 해석 가능성 그 자체이다.

## 개념

### Elicit (Anthropic, 2023-)

- 대규모 LLM에서 사전을 학습.
- 사전의 "특징"은 개별 뉴런이 아닌 활성화 패턴을 나타냄.
- 인간 해석 가능성과 목표 특징 제어를 위한 이 특징을 사용.

"Elicit"이라는 이름 — 활성화에서 특징을 이끌어내는 데서 유래.

### TransformerLens (Neel Nanda, 2022-)

- 잔류 스트림을 가져와 구성 요소로 분해.
- 주의 패턴, MLP 계산, 잔류 흐름 경로를 검사.
- "로그인에 대한 모든 정보"를 단일 잔류 스트림 벡터로 설명.
- 작은 모델(예: 1.4B, 2.7B)에 중점을 두며, 이는 큰 모델이지만 연구를 위해 충분히 제어 가능한 규모.

### Sparse Autoencoders (SAE)

- 숨겨진 유닛에 희소성을 부과하여 해석 가능한 특징을 학습.
- 잠재 공간을 해석 가능한 활성화 패턴으로 분해.
- 특정 동작을 구동하는 특징을 격리.
- Anthropic의 연구와 오픈소스 SAE 라이브러리가 이 분야를 주도.

### 세 가지 접근법의 직관

작은 눈사태를 상상해 보라:

- **TransformerLens = 쌓인 눈을 층별로 검사.**
- **SAE = 눈사태 패턴을 희소 특징으로 분해.**
- **Elicit = 사전을 학습하여 활성화에서 특징을 이끌어냄.**

세 가지 모두 동일한 질문에 답한다: 신경망 내부에서 발생하는 일과 그 이유.

### 해석 가능성 대 운영 사용

| 사용 | 해석 가능성이 제공하는 것 | 더 나은 방법 |
|------|-------------------------|-----------|
| 감사 | 특징이 편향되거나 유해한지 | 레슨 27-28 가드레일 + HITL |
| 디버깅 | 어떤 활성화 패턴이 잘못된 출력을 유발하는지 | 표준 로깅/추적 |
| 편향 감지 | 모델이 인구 통계를 특징으로 인코딩하는지 | 레슨 30 평가 |
| 연구 | 신경망 계산 메커니즘 | -- |

실제 프로덕션 관찰 가능성(레슨 23-24)은 해석 가능성 API보다 더 실용적이다. 해석 가능성은 규제 감사 또는 특수한 디버깅에 유용하다.

### 이 패턴이 잘못되는 경우

- **해석 가능성과 관찰 가능성을 혼동.** LLM-as-judge 점수 > 잔류 스트림 분석이 프로덕션 디버깅에 더 유용함.
- **Edict + TransformerLens를 생산에 오버엔지니어링.** 둘 다 리소스 집약적이며 신속한 추론을 위해 설계되지 않음.
- **"해석 가능" = "안전"이라고 가정.** 해석 가능성 도구는 설명하지만 방어하지는 않음.

## 직접 구현하기

`code/main.py`는 해석 가능성 기본 요소의 장난감 구현:

- 간단한 "신경망" (가중치가 있는 2-레이어 MLP).
- 숨겨진 유닛 활성화를 희소 특징으로 분해하는 SAE.
- 활성화 패턴에서 "해석"을 추출하는 특징 추출기.
- SAE 없이 신경망 플러스 해석 가능성.

실행:

```
python3 code/main.py
```

출력: 입력당 특징 활성화, 신경망이 무엇을 계산하는지 직관.

## 활용하기

- **Elicit / SAE** for model internals research or specialized auditing.
- **TransformerLens** for mechanistic interpretability research.
- **Standard observability** (레슨 23-24) for production debugging.

## 배포하기

`outputs/skill-interpretability-setup.md` scaffolds a feature extraction pipeline with SAE and interpretability dashboard.

## 연습 문제

1. 간단한 신경망을 MLP로 교체. SAE가 특성 특징을 얼마나 잘 격리하는가?
2. 0이 아닌 특징과 활성화 패턴을 시각화. SAE가 의미 있는 특징을 학습했는가?
3. "해석 가능" 활성화가 포함된 더 큰 데이터 세트로 실험.
4. 다른 희소성 임계값이 SAE 특징 품질에 미치는 영향 측정.
5. TransformerLens README 읽기. 어떤 모델과 메커니즘을 연구할 것인가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Interpretability | "신경망 투명성" | LLM 내부에서 계산이 발생하는 이유 설명 |
| SAE | "희소 특징 학습" | 희소성을 부과하여 해석 가능한 특징 학습 |
| Elicit | "사전 학습" | LLM 활성화에서 특징 추출 |
| TransformerLens | "메커니즘 분석" | 잔류 스트림 및 주의 패턴 분해 |
| Feature | "활성화 패턴" | 다양한 입력에서 일관되게 활성화되는 숨겨진 유닛 |

## 추가 자료

- [Anthropic, Elicit](https://transformer-circuits.pub/2022/elicit) — dictionary learning from activations
- [TransformerLens](https://github.com/TransformerLensOrg/TransformerLens) — residual stream decomposition
- [SAE by Anthropic](https://transformer-circuits.pub/2023/monosemantic-features) — sparse autoencoders for monosemantic features
- [OpenAI, Sparse Autoencoders](https://openai.com/index/extracting-concepts-from-gpt-4/) — extract concepts from GPT-4
