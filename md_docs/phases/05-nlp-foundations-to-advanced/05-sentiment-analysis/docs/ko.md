# 감정 분석

> 표준 NLP 작업. 고전적 텍스트 분류에 대해 알아야 할 대부분이 여기에 있다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 02 (BoW + TF-IDF), Phase 2 · 14 (Naive Bayes)
**Time:** ~75분

## 문제

"The food was not great." 긍정인가 부정인가?

감정 분석은 간단해 보인다. 리뷰어가 좋아하거나 싫어하는 것을 말한다. 문장에 레이블을 붙인다. 이것이 표준 NLP 작업이 된 이유는 모든 쉬워 보이는 사례 뒤에 어려운 사례가 숨어 있기 때문이다. 부정은 의미를 뒤집는다. 풍자는 반전시킨다. "Not bad at all"은 두 개의 부정 단어가 있음에도 긍정이다. 이모지가 주변 텍스트보다 더 많은 신호를 전달한다. 도메인 어휘가 중요하다.

감정 분석은 고전적 NLP의 실험실이다. 모든 순진한 기준선이 특정 실패 모드를 가진 이유를 이해하면, 왜 더 풍부한 모델이 발명되었는지 이해하게 된다.

## 개념

고전적 감정 분석은 두 단계 레시피다.

1. **표현.** 텍스트를 특징 벡터로 변환한다. BoW, TF-IDF 또는 n-그램.
2. **분류.** 레이블된 예제로 선형 모델을 학습시킨다.

## 직접 구현하기

## 사용하기

scikit-learn이 여섯 줄로 정확히 처리한다.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words=None)),
    ("clf", LogisticRegression(C=1.0, max_iter=1000)),
])
pipe.fit(X_train, y_train)
print(pipe.score(X_test, y_test))
```

## 최종 결과물

`outputs/prompt-sentiment-baseline.md`로 저장:

```markdown
---
name: sentiment-baseline
description: 새 데이터셋을 위한 감정 분석 기준선을 설계한다.
phase: 5
lesson: 05
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Polarity | 긍정 또는 부정 이진 레이블 |
| Aspect-based sentiment | 텍스트에 언급된 특정 개체나 속성에 대한 감성 |
| Negation scoping | "not" 이후 토큰에 접두사 `NOT_` 추가 |
| Laplace smoothing | 카운트에 1을 더함 |
| L2 regularization | 가중치 축소 |

## 추가 자료

- [Pang and Lee (2008). Opinion Mining and Sentiment Analysis](https://www.cs.cornell.edu/home/llee/opinion-mining-sentiment-analysis-survey.html)
- [Wang and Manning (2012). Baselines and Bigrams](https://aclanthology.org/P12-2018/)
- [scikit-learn text feature extraction docs](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction)
