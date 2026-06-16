# Bag of Words, TF-IDF 및 텍스트 표현

> 먼저 세고, 나중에 생각하라. TF-IDF는 2026년에도 특정 작업에서 임베딩을 능가한다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 01 (Text Processing), Phase 2 · 02 (Linear Regression from Scratch)
**Time:** ~75분

## 문제

모델은 숫자가 필요하다. 당신에게는 문자열이 있다.

모든 NLP 파이프라인은 같은 질문에 답해야 한다. 가변 길이 토큰 스트림을 분류기가 사용할 수 있는 고정 크기 벡터로 어떻게 변환할 것인가? 이 분야가 처음 찾은 답은 가장 단순하면서도 작동하는 방법이었다. 단어를 세고, 벡터를 만든다.

그 벡터는 어떤 임베딩 모델보다 더 많은 프로덕션 NLP를 책임져 왔다. 스팸 필터, 주제 분류기, 로그 이상 탐지, 검색 랭킹(BM25 이전), 1세대 감정 분석, 학술 NLP 벤치마크의 첫 10년. 2026년 실무자들은 여전히 좁은 분류 작업에서 먼저 이것을 사용한다. 빠르고, 해석 가능하며, 단어 존재 여부가 중요한 작업에서는 4억 파라미터 임베딩 모델과 구별하기 어려운 경우가 많다.

이 레슨에서는 BoW(Bag of Words)와 TF-IDF를 처음부터 직접 구현한다. 그 다음 scikit-learn이 동일한 작업을 세 줄로 수행하는 방법을 보여준다. 마지막으로 임베딩을 사용해야 하는 실패 지점을 설명한다.

## 개념

**Bag of Words (BoW)** 는 순서를 무시한다. 각 문서에 대해 각 단어가 등장한 횟수를 센다. 벡터 길이는 단어 집합 크기와 같다. 위치 `i`는 단어 `i`의 등장 횟수다.

**TF-IDF**는 BoW에 가중치를 재조정한다. 모든 문서에 등장하는 단어는 정보가 없으므로 가중치를 낮춘다. 말뭉치 전체에서는 드물지만 특정 문서에 자주 등장하는 단어는 신호이므로 가중치를 높인다.

```
TF-IDF(w, d) = TF(w, d) * IDF(w)
             = count(w in d) / |d| * log(N / df(w))
```

여기서 `TF`는 문서 내 단어 빈도, `df`는 문서 빈도(해당 단어를 포함하는 문서 수), `N`은 전체 문서 수다. `log`는 보편적인 단어에 대한 가중치가 제한되도록 한다.

핵심 속성: 둘 다 해석 가능한 축을 가진 희소 벡터를 생성한다. 훈련된 분류기의 가중치를 보고 어떤 단어가 문서를 특정 클래스로 밀어내는지 읽을 수 있다. 768차원 BERT 임베딩으로는 이것이 불가능하다.

## 직접 구현하기

### Step 1: 단어 집합 구축

```python
def build_vocab(docs):
    vocab = {}
    for doc in docs:
        for token in doc:
            if token not in vocab:
                vocab[token] = len(vocab)
    return vocab
```

입력: 토큰화된 문서 리스트(모든 단어 수준 토크나이저 사용 가능, 이 레슨의 `code/main.py`는 단순화된 소문자 방식을 사용). 출력: `{word: index}` 딕셔너리. 안정적인 삽입 순서는 단어 인덱스 0이 첫 번째 문서에서 처음 본 단어임을 의미한다. 관례는 다양하며 scikit-learn은 알파벳순으로 정렬한다.

### Step 2: bag of words

```python
def bag_of_words(docs, vocab):
    matrix = [[0] * len(vocab) for _ in docs]
    for i, doc in enumerate(docs):
        for token in doc:
            if token in vocab:
                matrix[i][vocab[token]] += 1
    return matrix
```

### Step 3: 단어 빈도와 문서 빈도

```python
import math


def term_frequency(doc_bow, doc_length):
    return [c / doc_length if doc_length else 0 for c in doc_bow]


def document_frequency(bow_matrix):
    df = [0] * len(bow_matrix[0])
    for row in bow_matrix:
        for j, count in enumerate(row):
            if count > 0:
                df[j] += 1
    return df


def inverse_document_frequency(df, n_docs):
    return [math.log((n_docs + 1) / (d + 1)) + 1 for d in df]
```

### Step 4: TF-IDF

```python
def tfidf(bow_matrix):
    n_docs = len(bow_matrix)
    df = document_frequency(bow_matrix)
    idf = inverse_document_frequency(df, n_docs)
    out = []
    for row in bow_matrix:
        length = sum(row)
        tf = term_frequency(row, length)
        out.append([tf_j * idf_j for tf_j, idf_j in zip(tf, idf)])
    return out
```

### Step 5: L2 정규화

```python
def l2_normalize(matrix):
    out = []
    for row in matrix:
        norm = math.sqrt(sum(x * x for x in row))
        out.append([x / norm if norm else 0 for x in row])
    return out
```

## 사용하기

scikit-learn이 프로덕션 버전을 제공한다.

```python
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

docs = ["the cat sat on the mat", "the dog sat on the mat", "the cat ran"]

bow_vectorizer = CountVectorizer()
bow = bow_vectorizer.fit_transform(docs)
print(bow_vectorizer.get_feature_names_out())
print(bow.toarray())

tfidf_vectorizer = TfidfVectorizer()
tfidf = tfidf_vectorizer.fit_transform(docs)
print(tfidf.toarray().round(3))
```

## 최종 결과물

`outputs/prompt-vectorization-picker.md`로 저장:

```markdown
---
name: vectorization-picker
description: 텍스트 분류 작업에 대해 BoW, TF-IDF, 임베딩 또는 하이브리드를 추천한다.
phase: 5
lesson: 02
---
```

## 실습

1. **쉬움.** L2 정규화된 TF-IDF 출력에서 `cosine_similarity(doc_vec_a, doc_vec_b)`를 구현한다. 동일한 문서는 1.0, 어휘가 완전히 다른 문서는 0.0이 나오는지 확인한다.
2. **중간.** `bag_of_words`에 `n-gram` 지원을 추가한다. 파라미터 `n`은 `n`-gram에 대한 카운트를 생성한다.
3. **어려움.** 위의 TF-IDF 가중치 임베딩 하이브리드를 GloVe 100d 벡터를 사용하여 구축한다. 20 Newsgroups 데이터셋에서 일반 TF-IDF, 일반 평균 풀 임베딩과 분류 정확도를 비교한다.

## 주요 용어

| 용어 | 의미 |
|------|------|
| BoW | 단어 빈도 벡터. 순서를 무시한다. |
| TF | 단어 빈도. 문서 내 단어 등장 횟수. |
| DF | 문서 빈도. 단어를 포함하는 문서 수. |
| IDF | 역문서 빈도. `log(N / df)`. 모든 곳에 등장하는 단어의 가중치를 낮춘다. |
| Sparse vector | 대부분 0인 벡터. |
| Cosine similarity | L2 정규화된 벡터의 내적. |

## 추가 자료

- [scikit-learn — feature extraction from text](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction)
- [Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval](https://www.sciencedirect.com/science/article/pii/0306457388900210)
- ["Why TF-IDF Still Beats Embeddings" — Ashfaque Thonikkadavan (Medium)](https://medium.com/@cmtwskb/why-tf-idf-still-beats-embeddings-ad85c123e1b2)
