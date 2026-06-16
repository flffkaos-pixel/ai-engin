# 구조화된 출력 및 제약 디코딩

> LLM에 JSON을 요청하라. 대부분의 경우 JSON을 얻는다. 프로덕션에서 "대부분"이 문제다. 제약 디코딩은 로짓을 편집하여 "대부분"을 "항상"으로 만든다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 17 (Chatbots), Phase 5 · 19 (Subword Tokenization)
**Time:** ~60분

## 문제

분류기가 LLM에 프롬프트한다: "{positive, negative, neutral} 중 하나를 반환하라." 모델이 "The sentiment is positive — this review is overwhelmingly favorable because..."을 반환한다. 파서가 충돌한다. 분류기의 F1은 0.0이다.

자유 형식 생성은 계약이 아니다. 제안일 뿐이다. 프로덕션 시스템에는 계약이 필요하다.

세 가지 레이어가 있다:

1. **프롬프팅.** 정중하게 요청. 최신 모델에서 ~80% 작동.
2. **네이티브 구조화 출력 API.** OpenAI `response_format`, Anthropic 도구 사용, Gemini JSON 모드.
3. **제약 디코딩.** 모델이 유효하지 않은 토큰을 방출할 수 없도록 로짓 수정.

## 개념

각 생성 단계에서 LLM은 전체 어휘에 대한 로짓 벡터를 생성한다. *로짓 프로세서*가 모델과 샘플러 사이에 위치한다. 대상 문법에서 현재 위치에 대해 어떤 토큰이 유효한지 계산하고 유효하지 않은 모든 토큰의 로짓을 음의 무한대로 설정한다.

## 직접 구현하기

## 사용하기

```python
import outlines
from pydantic import BaseModel
from typing import Literal

class Review(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float
    evidence_span: str

model = outlines.models.transformers("meta-llama/Llama-3.2-3B-Instruct")
generator = outlines.generate.json(model, Review)

result = generator("Classify: 'The wait staff was attentive and the food arrived hot.'")
print(result)
```

## 최종 결과물

`outputs/skill-structured-output-picker.md`로 저장:

```markdown
---
name: structured-output-picker
description: 구조화된 출력 접근법, 스키마 설계 및 검증 계획을 선택한다.
version: 1.0.0
phase: 5
lesson: 20
tags: [nlp, llm, structured-output]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Constrained decoding | 각 생성 단계에서 유효하지 않은 토큰 로짓 마스킹. |
| Logit processor | (logits, state) -> masked_logits 함수. |
| FSM | 유한 상태 기계. O(1) 유효-다음-토큰 조회. |
| CFG | 문맥 자유 문법. 재귀 처리. |
| Schema field order | 첫 번째 필드가 결정을 강제함. 추론 전에 답변 금지. |
| Guided decoding | vLLM의 이름. 인퍼런스 서버에 통합. |
| JSON mode | JSON 문법만 보장. 스키마 일치 보장 안 함. |

## 추가 자료

- [Willard, Louf (2023). Efficient Guided Generation](https://arxiv.org/abs/2307.09702)
- [XGrammar (2024)](https://arxiv.org/abs/2411.15100)
- [vLLM — Structured Outputs](https://docs.vllm.ai/en/latest/features/structured_outputs.html)
- [OpenAI — Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs)
- [Instructor library](https://python.useinstructor.com/)
