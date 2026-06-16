# 정보 검색 및 검색

> BM25는 정밀하지만 깨지기 쉽다. Dense는 넓은 범위를 포착하지만 키워드를 놓친다. 하이브리드가 2026년의 기본값이다. 나머지는 튜닝이다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 02 (BoW + TF-IDF), Phase 5 · 04 (GloVe, FastText, Subword)
**Time:** ~75분

## 문제

사용자가 "누군가 돈을 받기 위해 거짓말을 하면 어떻게 되나요?"라고 입력하고 실제로 그것을 다루는 법률 조항을 찾길 기대한다. 키워드 검색은 완전히 놓친다(공유 어휘 없음). 의미 검색은 임베딩이 법률 텍스트로 학습되지 않은 경우 놓친다.

IR은 모든 RAG 시스템, 모든 검색 창, 모든 문서 사이트의 퍼지 조회 아래에 있는 파이프라인이다.

## 개념

네 개의 레이어.

1. **희소 검색 (BM25).** 빠르고 정확. 역색인에서 실행.
2. **밀집 검색.** 쿼리와 문서를 벡터로 인코딩. 최근접 이웃 검색.
3. **융합.** 희소와 밀집의 순위 리스트 병합. RRF(Reciprocal Rank Fusion)가 기본.
4. **교차 인코더 재순위화.** 상위 30개를 가져와 교차 인코더로 재순위화.

## 직접 구현하기

## 사용하기

| 규모 | 스택 |
|------|------|
| 1k-100k 문서 | 인메모리 BM25 + all-MiniLM-L6-v2 + RRF |
| 100k-10M 문서 | FAISS/pgvector + Elasticsearch/OpenSearch |
| 10M+ 문서 | Qdrant/Weaviate/Vespa/Milvus |

## 최종 결과물

`outputs/skill-retrieval-picker.md`로 저장:

```markdown
---
name: retrieval-picker
description: 주어진 말뭉치와 쿼리 패턴에 대한 검색 스택을 선택한다.
version: 1.0.0
phase: 5
lesson: 14
tags: [nlp, retrieval, rag, search]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| BM25 | Okapi BM25. 단어 빈도, IDF, 길이로 문서 점수 계산. |
| Dense retrieval | 벡터 검색. 쿼리+문서를 벡터로 인코딩, 최근접 이웃 검색. |
| Bi-encoder | 임베딩 모델. 쿼리와 문서를 독립적으로 인코딩. |
| Cross-encoder | 재순위화 모델. 쿼리+문서를 함께 인코딩. |
| RRF | 순위 융합. `1/(k + rank)` 합산. |
| Recall@k | 검색 메트릭. 관련 문서가 top-k에 있는 쿼리 비율. |

## 추가 자료

- [Robertson and Zaragoza (2009). BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)
- [Karpukhin et al. (2020). Dense Passage Retrieval](https://arxiv.org/abs/2004.04906)
- [Formal et al. (2021). SPLADE](https://arxiv.org/abs/2107.05720)
- [Cormack et al. (2009). Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [Khattab and Zaharia (2020). ColBERT](https://arxiv.org/abs/2004.12832)
