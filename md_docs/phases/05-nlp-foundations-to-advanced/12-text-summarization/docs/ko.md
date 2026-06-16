# 텍스트 요약

> 추출 시스템은 문서가 말한 것을 알려준다. 추상 시스템은 저자가 의미한 것을 알려준다. 다른 작업, 다른 함정.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 02 (BoW + TF-IDF), Phase 5 · 11 (Machine Translation)
**Time:** ~75분

## 문제

2,000단어 뉴스 기사가 피드에 들어온다. 그것을 담을 120단어가 필요하다. 기사에서 가장 중요한 세 문장을 고르거나(추출) 내용을 자신의 말로 다시 쓸 수 있다(추상). 둘 다 요약이라고 불리지만 완전히 다른 문제다.

추출 요약은 순위 문제다. 각 문장에 점수를 매기고 상위 `k`개를 반환한다. 출력은 항상 문법적이다. 위험은 기사 전체에 분산된 내용을 놓치는 것이다.

추상 요약은 생성 문제다. 트랜스포머가 입력에 조건화된 새 텍스트를 생성한다. 출력은 유창하고 압축적이지만 소스에 없는 사실을 환각할 수 있다.

## 개념

**추출.** 기사를 노드가 문장이고 엣지가 유사도인 그래프로 취급한다. PageRank(또는 유사한 것)를 실행하여 문장에 점수를 매긴다. **TextRank**가 표준 구현이다.

**추상.** 트랜스포머 인코더-디코더(BART, T5, Pegasus)를 문서-요약 쌍으로 미세 조정한다. 추론 시 모델이 문서를 읽고 교차 어텐션을 통해 토큰별로 요약을 생성한다.

## 직접 구현하기

## 사용하기

```python
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

article = """(long news article text)"""

summary = summarizer(article, max_length=120, min_length=60, do_sample=False)
print(summary[0]["summary_text"])
```

## 최종 결과물

`outputs/skill-summary-picker.md`로 저장:

```markdown
---
name: summary-picker
description: 추출 또는 추상 중 선택, 라이브러리 지정, 사실성 검사.
version: 1.0.0
phase: 5
lesson: 12
tags: [nlp, summarization]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Extractive | 문장 선택. 소스에서 그대로 반환. 환각 없음. |
| Abstractive | 재작성. 소스에 조건화된 새 텍스트 생성. 환각 가능. |
| ROUGE | 요약 메트릭. 시스템 출력과 참조 간 N-그램/LCS 중첩. |
| TextRank | 그래프 기반 추출. 문장 유사도 그래프의 PageRank. |
| Factuality | 요약 주장이 소스에 의해 뒷받침되는지 여부. |
| Hallucination | 요약에 소스가 지원하지 않는 내용. |

## 추가 자료

- [Mihalcea and Tarau (2004). TextRank](https://aclanthology.org/W04-3252/)
- [Lewis et al. (2019). BART](https://arxiv.org/abs/1910.13461)
- [Zhang et al. (2019). PEGASUS](https://arxiv.org/abs/1912.08777)
- [Lin (2004). ROUGE](https://aclanthology.org/W04-1013/)
- [Maynez et al. (2020). On Faithfulness and Factuality](https://arxiv.org/abs/2005.00661)
