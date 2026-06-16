# 자연어 추론 — 텍스트 함의

> "t가 h를 함의한다"는 인간 독자가 t를 읽으면 h가 참이라고 결론내릴 것임을 의미한다. NLI는 함의/모순/중립을 예측하는 작업이다. 표면적으로는 지루하지만 프로덕션에서는 핵심적인 역할을 한다.

**Type:** Learn
**Languages:** Python
**Prerequisites:** Phase 5 · 05 (Sentiment Analysis), Phase 5 · 13 (Question Answering)
**Time:** ~60분

## 문제

요약기를 만들었다. 요약이 생성되었다. 요약에 환각이 포함되어 있지 않은지 어떻게 알 수 있는가?

챗봇을 만들었다. "예"라고 답변했다. 답변이 검색된 구절에 의해 뒷받침되는지 어떻게 알 수 있는가?

세 가지 문제 모두 자연어 추론(NLI)으로 귀결된다. NLI는 전제 `t`와 가설 `h`가 주어졌을 때 `h`가 `t`에 의해 함의되는지, 모순되는지, 또는 중립인지(관련 없음)를 묻는다.

## 개념

**세 가지 레이블.** 함의, 모순, 중립.

**아키텍처.** 트랜스포머 인코더(BERT, RoBERTa, DeBERTa)가 `[CLS] premise [SEP] hypothesis [SEP]`를 읽는다. `[CLS]` 표현이 3방향 소프트맥스에 공급된다.

## 직접 구현하기

## 사용하기

```python
from transformers import pipeline

nli = pipeline("text-classification", model="facebook/bart-large-mnli", top_k=None)

premise = "The cat is sleeping on the couch."
hypothesis = "There is a cat in the room."

result = nli({"text": premise, "text_pair": hypothesis})[0]
print(result)
```

## 최종 결과물

`outputs/skill-nli-picker.md`로 저장:

```markdown
---
name: nli-picker
description: 분류/신뢰성/제로샷 작업을 위한 NLI 모델을 선택한다.
version: 1.0.0
phase: 5
lesson: 21
tags: [nlp, nli, zero-shot]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| NLI | 자연어 추론. 전제-가설 관계의 3방향 분류. |
| RTE | 텍스트 함의 인식. NLI의 구식 이름. |
| Entailment | t가 주어지면 h가 참이라고 결론내림. |
| Contradiction | t가 주어지면 h가 거짓이라고 결론내림. |
| Neutral | t에서 h로 추론 불가. |
| Zero-shot classification | 레이블을 가설로 표현, 최대 함의 선택. |
| Faithfulness | 생성된 답변이 검색된 컨텍스트에 의해 뒷받침되는지 여부. |

## 추가 자료

- [Bowman et al. (2015). SNLI](https://arxiv.org/abs/1508.05326)
- [Williams, Nangia, Bowman (2017). MultiNLI](https://arxiv.org/abs/1704.05426)
- [Nie et al. (2019). Adversarial NLI](https://arxiv.org/abs/1910.14599)
- [Yin, Hay, Roth (2019). Zero-shot Text Classification](https://arxiv.org/abs/1909.00161)
- [He et al. (2021). DeBERTa](https://arxiv.org/abs/2006.03654)
