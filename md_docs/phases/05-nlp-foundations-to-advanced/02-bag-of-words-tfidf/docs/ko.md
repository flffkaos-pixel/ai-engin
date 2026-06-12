# Bag-of-Words & TF-IDF

> 단어 개수 세기 → 벡터. 놀랍도록 강력한 기준선.

**유형:** 빌드 | **언어:** Python | **시간:** ~60분

## 개념
- BoW: 단어별 등장 횟수 벡터 — 순서 무시
- TF-IDF: TF(단어 빈도) × IDF(역문서 빈도) — 흔한 단어 페널티
- IDF = log(N/DF)

## 빌드
```python
from sklearn.feature_extraction.text import TfidfVectorizer
vec = TfidfVectorizer(max_features=10000)
X = vec.fit_transform(docs)
```