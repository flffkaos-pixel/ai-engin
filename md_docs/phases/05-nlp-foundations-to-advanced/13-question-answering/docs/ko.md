# 질의응답 시스템

> 세 가지 시스템이 현대 QA를 형성했다. 추출형은 범위를 찾았다. 검색 증강형은 이를 문서에 근거했다. 생성형은 답변을 생성했다. 모든 현대 AI 어시스턴트는 이 세 가지의 혼합이다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 11 (Machine Translation), Phase 5 · 10 (Attention Mechanism)
**Time:** ~75분

## 문제

사용자가 "첫 번째 iPhone은 언제 출시되었나요?"라고 입력하고 "2007년 6월 29일"을 기대한다. 직접적이고 근거가 있으며 올바른 답변이다.

세 가지 아키텍처가 지난 10년간 QA를 지배했다.

- **추출형 QA.** 질문과 답변이 포함된 구절이 주어지면 구절에서 답변 범위의 시작 및 끝 인덱스를 찾는다.
- **개방형 QA.** 구절이 주어지지 않는다. 먼저 관련 구절을 검색한 후 답변을 추출하거나 생성한다.
- **생성형/폐쇄형 QA.** 대규모 언어 모델이 파라메트릭 메모리에서 답변한다.

## 개념

**추출형.** 질문과 구절을 트랜스포머(BERT 계열)로 함께 인코딩한다. 답변의 시작 및 끝 토큰 인덱스를 예측하는 두 개의 헤드를 학습시킨다.

**RAG.** 두 단계. 먼저 검색기가 말뭉치에서 상위 `k`개 구절을 찾는다. 둘째, 리더(추출 또는 생성)가 이 구절들을 사용하여 답변을 생성한다.

**생성형.** 디코더 전용 LLM이 학습된 가중치에서 답변한다. 검색 단계 없음.

## 직접 구현하기

## 사용하기

```python
from transformers import pipeline

qa = pipeline("question-answering", model="deepset/roberta-base-squad2")

passage = "Apple Inc. released the first iPhone on June 29, 2007."
question = "When was the first iPhone released?"

answer = qa(question=question, context=passage)
print(answer)
```

## 최종 결과물

`outputs/skill-qa-architect.md`로 저장:

```markdown
---
name: qa-architect
description: QA 아키텍처, 검색 전략 및 평가 계획을 선택한다.
version: 1.0.0
phase: 5
lesson: 13
tags: [nlp, qa, rag]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Extractive QA | 답변 범위 찾기. 주어진 구절 내 시작/끝 인덱스 예측. |
| Open-domain QA | 말뭉치에 대한 QA. 구절이 주어지지 않음. |
| RAG | 검색 후 생성(Retrieval-Augmented Generation). |
| SQuAD | 표준 벤치마크. EM + F1 메트릭. |
| Hallucination | 생성된 답변이 검색된 컨텍스트에 의해 뒷받침되지 않음. |
| Refusal calibration | 답변할 수 없을 때 "모릅니다"라고 말하는 능력. |

## 추가 자료

- [Rajpurkar et al. (2016). SQuAD](https://arxiv.org/abs/1606.05250)
- [Karpukhin et al. (2020). Dense Passage Retrieval](https://arxiv.org/abs/2004.04906)
- [Lewis et al. (2020). Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)
- [Gao et al. (2023). RAG Survey](https://arxiv.org/abs/2312.10997)
