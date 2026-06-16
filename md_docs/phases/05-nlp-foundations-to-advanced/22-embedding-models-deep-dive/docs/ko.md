# 임베딩 모델 — 2026 심층 분석

> Word2Vec은 단어당 벡터를 제공했다. 현대 임베딩 모델은 구절당 벡터를 제공하며, 교차 언어, 희소/밀집/다중 벡터 뷰를 지원하고 인덱스에 맞게 크기 조정된다. 잘못 고르면 RAG가 잘못된 것을 검색한다.

**Type:** Learn
**Languages:** Python
**Prerequisites:** Phase 5 · 03 (Word2Vec), Phase 5 · 14 (Information Retrieval)
**Time:** ~60분

## 문제

RAG 시스템이 40%의 시간 동안 잘못된 구절을 검색한다. 원인은 벡터 데이터베이스나 프롬프트가 아니라 임베딩 모델인 경우가 많다.

2026년 임베딩 선택은 다섯 가지 축에 걸쳐 이루어진다:

1. **밀집 vs 희소 vs 다중 벡터.**
2. **언어 적용 범위.**
3. **컨텍스트 길이.**
4. **차원 예산.**
5. **오픈 vs 호스팅.**

## 개념

**밀집 임베딩.** 구절당 하나의 벡터(보통 384-3,072차원).

**희소 임베딩.** SPLADE 스타일. 트랜스포머가 각 어휘 토큰에 가중치를 예측하고 대부분을 0으로 설정.

**다중 벡터 (늦은 상호작용).** ColBERTv2. 토큰당 하나의 벡터. MaxSim 점수 계산.

**BGE-M3.** 단일 모델이 밀집, 희소, 다중 벡터 표현을 동시에 출력.

## 직접 구현하기

## 사용하기

```python
from sentence_transformers import SentenceTransformer
import numpy as np

encoder = SentenceTransformer("BAAI/bge-small-en-v1.5")
corpus = ["The first iPhone launched in 2007.", "Apple released the iPod in 2001."]
emb = encoder.encode(corpus, normalize_embeddings=True)

query = "When was the iPhone released?"
q_emb = encoder.encode([query], normalize_embeddings=True)[0]
scores = emb @ q_emb
print(sorted(enumerate(scores), key=lambda x: -x[1]))
```

## 최종 결과물

`outputs/skill-embedding-picker.md`로 저장:

```markdown
---
name: embedding-picker
description: 주어진 말뭉치와 배포에 대한 임베딩 모델, 차원 및 검색 모드를 선택한다.
version: 1.0.0
phase: 5
lesson: 22
tags: [nlp, embeddings, retrieval]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Dense embedding | 텍스트당 하나의 고정 크기 벡터. |
| Sparse embedding | 학습된 BM25. 대부분 0. |
| Multi-vector | ColBERT 스타일. 토큰당 벡터. |
| Matryoshka | 처음 N 차원이 독립적으로 유효한 작은 임베딩. |
| MTEB | Massive Text Embedding Benchmark. |
| BEIR | 제로샷 검색 벤치마크. |

## 추가 자료

- [Reimers, Gurevych (2019). Sentence-BERT](https://arxiv.org/abs/1908.10084)
- [Muennighoff et al. (2022). MTEB](https://arxiv.org/abs/2210.07316)
- [Chen et al. (2024). BGE-M3](https://arxiv.org/abs/2402.03216)
- [Kusupati et al. (2022). Matryoshka Representation Learning](https://arxiv.org/abs/2205.13147)
- [Santhanam et al. (2022). ColBERTv2](https://arxiv.org/abs/2112.01488)
