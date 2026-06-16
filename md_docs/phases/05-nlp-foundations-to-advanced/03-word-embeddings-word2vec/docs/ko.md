# 단어 임베딩 — Word2Vec 처음부터 구현하기

> 단어는 그 주변에 있는 단어들로 알 수 있다. 얕은 신경망을 이 아이디어로 학습시키면 기하학이 자연스럽게 드러난다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 02 (BoW + TF-IDF), Phase 3 · 03 (Backpropagation from Scratch)
**Time:** ~75분

## 문제

TF-IDF는 `dog`와 `puppy`가 다른 단어임을 안다. 하지만 두 단어가 거의 같은 의미라는 것은 모른다. `dog`로 훈련된 분류기는 `puppy`에 대한 리뷰로 일반화할 수 없다. 동의어 목록을 나열하여 해결할 수 있지만, 드문 용어, 도메인 전문 용어, 예상치 못한 언어에서는 실패한다.

`dog`와 `puppy`가 공간상에서 가까이 위치하고, `king - man + woman`이 `queen` 근처에 위치하는 표현이 필요하다. `dog`로 훈련된 모델이 `puppy`에 신호를 무료로 전달할 수 있는 그런 공간이다.

Word2Vec이 그 공간을 제공했다. 2층 신경망, 조 단위 토큰 학습, 2013년에 발표되었다. 아키텍처는 거의 당황스러울 정도로 단순하다. 결과는 10년 동안 NLP를 재편했다.

## 개념

**분포 가설**(Firth, 1957): "단어는 그 주변에 있는 단어들로 알 수 있다." 두 단어가 비슷한 맥락에서 나타난다면, 아마도 비슷한 의미일 것이다.

Word2Vec은 이 아이디어를 활용하는 두 가지 방식이 있다.

- **Skip-gram.** 중심 단어가 주어졌을 때 주변 단어를 예측한다. `cat -> (the, sat, on)` (window size 2)
- **CBOW (continuous bag of words).** 주변 단어가 주어졌을 때 중심 단어를 예측한다. `(the, sat, on) -> cat`

Skip-gram은 학습이 느리지만 희귀 단어를 더 잘 처리한다. 표준이 되었다.

네트워크는 비선형성이 없는 하나의 은닉층을 가진다. 입력은 단어 집합 크기의 원-핫 벡터다. 출력은 단어 집합에 대한 소프트맥스다. 학습 후 출력층은 버린다. 은닉층 가중치가 바로 임베딩이다.

```
one-hot(center) ── W ──▶ hidden (d-dim) ── W' ──▶ softmax(vocab)
                          ^
                          this is the embedding
```

핵심 트릭: 10만 개 단어에 대한 소프트맥스는 비용이 엄청나게 비싸다. Word2Vec은 **네거티브 샘플링**을 사용하여 이진 분류 작업으로 변환한다. "이 맥락 단어가 이 중심 단어 근처에 나타났는가, 예/아니오"를 예측한다. 전체 단어 집합에 대한 소프트맥스를 계산하는 대신 학습 쌍당 소수의 부정(비동시 출현) 단어를 샘플링한다.

## 직접 구현하기

## 사용하기

처음부터 Word2Vec을 작성하는 것은 교육용이다. 프로덕션 NLP는 `gensim`을 사용한다.

```python
from gensim.models import Word2Vec

sentences = [
    ["the", "cat", "sat", "on", "the", "mat"],
    ["the", "dog", "ran", "across", "the", "room"],
]

model = Word2Vec(
    sentences,
    vector_size=100,
    window=5,
    min_count=1,
    sg=1,
    negative=5,
    workers=4,
    epochs=30,
)

print(model.wv["cat"])
print(model.wv.most_similar("cat", topn=3))
```

## 최종 결과물

`outputs/skill-embedding-probe.md`로 저장:

```markdown
---
name: embedding-probe
description: word2vec 모델을 검사한다. 유추를 실행하고, 이웃을 찾고, 품질을 진단한다.
version: 1.0.0
phase: 5
lesson: 03
tags: [nlp, embeddings, debugging]
---
```

## 실습

1. **쉬움.** 고양이와 개에 관한 20개 문장의 작은 말뭉치로 학습 루프를 실행한다. 200 에포크 후 `nearest(vocab, W, W[vocab["cat"]])`가 상위 3위 안에 `dog`를 반환하는지 확인한다.
2. **중간.** 빈번한 단어의 서브샘플링을 추가한다. 빈도가 `10^-5` 이상인 단어는 빈도에 비례하는 확률로 학습 쌍에서 제외된다. 희귀 단어 유사도에 미치는 영향을 측정한다.
3. **어려움.** 20 Newsgroups 말뭉치로 모델을 학습시킨다. `he - she`와 `doctor - nurse` 두 가지 편향 축을 계산한다. 직업 단어를 두 축에 투영한다.

## 주요 용어

| 용어 | 의미 |
|------|------|
| Word embedding | 단어를 벡터로 표현. 밀집 저차원(보통 100-300) 표현. |
| Skip-gram | 중심 단어로 맥락 단어 예측. 희귀 단어에 더 좋음. |
| Negative sampling | 전체 단어 집합 소프트맥스 대신 `k`개 무작위 단어로 이진 분류. |
| Static embedding | 단어당 하나의 벡터. 맥락 무관. 다의어에 실패. |
| Contextual embedding | 맥락에 따라 다른 벡터. 트랜스포머가 생성. |
| OOV | 어휘 외 단어. 학습에 없는 단어. Word2Vec은 벡터 생성 불가. |

## 추가 자료

- [Mikolov et al. (2013). Distributed Representations of Words and Phrases and their Compositionality](https://arxiv.org/abs/1310.4546)
- [Rong, X. (2014). word2vec Parameter Learning Explained](https://arxiv.org/abs/1411.2738)
- [gensim Word2Vec tutorial](https://radimrehurek.com/gensim/models/word2vec.html)
