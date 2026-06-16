# 토픽 모델링 — LDA와 BERTopic

> LDA: 문서는 토픽의 혼합, 토픽은 단어에 대한 분포. BERTopic: 문서는 임베딩 공간에서 클러스터링, 클러스터가 토픽. 같은 목표, 다른 분해.

**Type:** Learn
**Languages:** Python
**Prerequisites:** Phase 5 · 02 (BoW + TF-IDF), Phase 5 · 03 (Word2Vec)
**Time:** ~45분

## 문제

10,000개의 고객 지원 티켓, 50,000개의 뉴스 기사, 또는 200,000개의 트윗이 있다. 읽지 않고 컬렉션이 무엇에 관한 것인지 알아야 한다. 레이블된 카테고리가 없고 얼마나 많은 카테고리가 있는지조차 모른다.

토픽 모델링은 감독 없이 이에 답한다. 말뭉치를 주면 작은 일관된 토픽 집합과 각 문서에 대한 토픽 분포를 반환한다.

## 개념

**LDA 생성 이야기.** 각 토픽은 단어에 대한 분포다. 각 문서는 토픽의 혼합이다.

**BERTopic 파이프라인.** 1. 문서 인코딩 → 2. UMAP 차원 축소 → 3. HDBSCAN 클러스터링 → 4. 클래스 기반 TF-IDF로 상위 단어 추출.

## 직접 구현하기

## 사용하기

```python
from bertopic import BERTopic

topic_model = BERTopic(embedding_model="sentence-transformers/all-MiniLM-L6-v2", min_topic_size=15, verbose=True)
topics, probs = topic_model.fit_transform(documents)
info = topic_model.get_topic_info()
print(info.head(20))
```

## 최종 결과물

`outputs/skill-topic-picker.md`로 저장:

```markdown
---
name: topic-picker
description: 말뭉치에 대해 LDA 또는 BERTopic을 선택한다.
version: 1.0.0
phase: 5
lesson: 15
tags: [nlp, topic-modeling]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Topic | 말뭉치가 다루는 주제. 단어 분포(LDA) 또는 유사 문서 클러스터(BERTopic). |
| Mixed membership | 문서가 여러 토픽에 속함. |
| UMAP | 차원 축소. 국소 구조를 보존하는 매니폴드 학습. |
| HDBSCAN | 밀도 클러스터링. 가변 크기 클러스터, 이상치에 -1 레이블. |
| c_v coherence | 토픽 품질 메트릭. 상위 토픽 단어들의 평균 상호 정보량. |

## 추가 자료

- [Blei, Ng, Jordan (2003). Latent Dirichlet Allocation](https://www.jmlr.org/papers/volume3/blei03a/blei03a.pdf)
- [Grootendorst (2022). BERTopic](https://arxiv.org/abs/2203.05794)
- [Röder, Both, Hinneburg (2015). Topic Coherence Measures](https://svn.aksw.org/papers/2015/WSDM_Topic_Evaluation/public.pdf)
- [BERTopic documentation](https://maartengr.github.io/BERTopic/)
