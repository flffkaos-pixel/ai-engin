# LLM 평가 — RAGAS, DeepEval, G-Eval

> 정확 일치와 F1은 의미적 동등성을 놓친다. 인간 검토는 확장되지 않는다. LLM-as-judge가 프로덕션 답변이다 — 충분한 보정으로 숫자를 신뢰할 수 있어야 한다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 13 (Question Answering), Phase 5 · 14 (Information Retrieval)
**Time:** ~75분

## 문제

RAG 시스템이 "June 29th, 2007"이라고 답한다. 골드 참조는 "June 29, 2007"이다. Exact Match는 0점. F1은 ~75%. 인간은 100%를 줄 것이다.

2026년에는 이 문제를 소유한 세 가지 프레임워크가 있다.

- **RAGAS.** 네 가지 RAG 메트릭(신뢰성, 답변 관련성, 컨텍스트 정밀도, 컨텍스트 재현율).
- **DeepEval.** LLM을 위한 Pytest.
- **G-Eval.** LLM-as-judge with chain-of-thought.

## 개념

**LLM-as-judge.** 정적 메트릭을 루브릭이 주어진 출력에 점수를 매기는 LLM으로 대체.

## 직접 구현하기

## 사용하기

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams, LLMTestCase

metric = GEval(
    name="Correctness",
    criteria="The answer should be factually accurate and match the expected output.",
    evaluation_steps=[
        "Read the expected output.",
        "Read the actual output.",
        "List factual claims in the actual output.",
        "For each claim, mark supported or unsupported by the expected output.",
        "Return score = fraction supported.",
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
)

test = LLMTestCase(input="When was the first iPhone released?",
                   actual_output="June 29th, 2007.",
                   expected_output="June 29, 2007.")
metric.measure(test)
print(metric.score, metric.reason)
```

## 최종 결과물

`outputs/skill-eval-architect.md`로 저장:

```markdown
---
name: eval-architect
description: 보정된 판정자와 CI 게이트를 갖춘 LLM 평가 계획을 설계한다.
version: 1.0.0
phase: 5
lesson: 27
tags: [nlp, evaluation, rag]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| LLM-as-judge | 루브릭이 주어진 출력에 점수를 매기는 LLM 프롬프트. |
| RAGAS | 4개의 참조 없는 RAG 메트릭을 가진 오픈소스 평가 프레임워크. |
| Faithfulness | 검색된 컨텍스트에 의해 함의된 답변 주장의 비율. |
| Context precision | 상위-K 청크 중 실제로 관련 있었던 비율. |
| Context recall | 골드 답변 주장을 검색된 청크가 지원하는 비율. |
| G-Eval | 루브릭 + chain-of-thought 평가 단계 + 0-1 점수. |
| Calibration | 판정자 점수와 인간 점수 간 Spearman 상관관계. |

## 추가 자료

- [Es et al. (2023). RAGAS](https://arxiv.org/abs/2309.15217)
- [Liu et al. (2023). G-Eval](https://arxiv.org/abs/2303.16634)
- [DeepEval docs](https://deepeval.com/docs/metrics-introduction)
- [Zheng et al. (2023). Judging LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)
