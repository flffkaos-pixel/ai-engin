# 베이즈 정리

> 확률은 무엇을 기대하는지에 관한 것입니다. 베이즈 정리는 무엇을 배우는지에 관한 것입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lesson 06 (확률 기초)
**시간:** ~75분

## 학습 목표

- 사전확률, 가능도, 증거로부터 사후확률을 계산하기 위해 베이즈 정리 적용하기
- 라플라스 평활화와 로그 공간 계산으로 나이브 베이즈 텍스트 분류기를 처음부터 구축하기
- MLE와 MAP 추정을 비교하고 MAP가 L2 정규화와 어떻게 대응하는지 설명하기
- A/B 테스트를 위한 베타-이항 켤레 사전분포로 순차적 베이지안 업데이트 구현하기

## 문제

의료 검사가 99% 정확합니다. 양성 판정을 받았습니다. 실제로 병에 걸렸을 확률은?

대부분 99%라고 말합니다. 실제 답은 병이 얼마나 희귀한지에 달려 있습니다. 10,000명 중 1명이 걸린다면, 양성 결과는 약 1%의 확률만 줍니다. 나머지 99%는 건강한 사람들의 오탐지입니다.

이것이 베이즈 정리입니다. 모든 스팸 필터, 의료 진단, 불확실성을 정량화하는 ML 모델이 이와 동일한 추론을 사용합니다. 믿음에서 시작하여 증거를 보고 업데이트합니다.

## 개념

### 베이즈 정리

```
P(A|B) = P(B|A) * P(A) / P(B)
```

네 가지 구성 요소:

| 부분 | 이름 | 의미 |
|------|------|------|
| P(A\|B) | 사후확률 | 증거 B를 본 후 업데이트된 믿음 |
| P(B\|A) | 가능도 | A가 참일 때 증거 B의 확률 |
| P(A) | 사전확률 | 증거를 보기 전 믿음 |
| P(B) | 증거 | 모든 가능성 아래 B를 볼 총 확률 |

### 의료 검사 예시

```
P(병) = 0.0001          (사전확률: 병이 희귀)
P(양성|병) = 0.99       (가능도: 검사가 잡아냄)
P(양성|건강) = 0.01     (오탐지율)

P(양성) = 0.99*0.0001 + 0.01*0.9999 = 0.010098
P(병|양성) = 0.99*0.0001 / 0.010098 = 0.0098 = 0.98%
```

1% 미만! 사전확률이 지배합니다. 조건이 희귀하면 정확한 검사도 대부분 오탐지를 만듭니다.

### 스팸 필터 예시

"lottery" 단어가 포함된 이메일 — 스팸 확률 30% → 95.5%로. 실제 스팸 필터는 수백 개 단어에 동시에 베이즈를 적용합니다.

### 나이브 베이즈: 독립성 가정

```
P(클래스 | 특성1, 특성2, ..., 특성n) ∝ P(클래스) * ∏ P(특성i | 클래스)
```

모든 특성이 클래스가 주어졌을 때 조건부 독립이라고 가정합니다. "나이브"(순진한) 가정이지만 실제로 놀랍도록 잘 작동합니다.

### MLE vs MAP

- **MLE**(최대가능도추정): P(데이터|파라미터)만 최대화. 충분한 데이터로 잘 작동
- **MAP**(최대사후확률): P(파라미터|데이터) ∝ P(데이터|파라미터) * P(파라미터) 최대화. 사전확률 포함
- **MAP + 정규분포 사전 = L2 정규화**: 베이지안 관점에서 가중치 감쇠는 "가중치가 0 근처에 있다"는 사전 믿음

## 빌드하기

### 나이브 베이즈 텍스트 분류기

```python
import math
from collections import defaultdict

class NaiveBayesClassifier:
    def __init__(self, alpha=1.0):  # 라플라스 평활화
        self.alpha = alpha
        self.class_probs = {}
        self.word_given_class = defaultdict(lambda: defaultdict(float))

    def fit(self, docs, labels):
        # 클래스 사전확률 계산
        n = len(labels)
        for c in set(labels):
            self.class_probs[c] = sum(1 for l in labels if l == c) / n

        # P(단어|클래스) 계산 (로그 공간, 라플라스 평활화)
        vocab = set(w for doc in docs for w in doc)
        for c in self.class_probs:
            c_docs = [d for d, l in zip(docs, labels) if l == c]
            total_words = sum(len(d) for d in c_docs)
            for w in vocab:
                count = sum(d.count(w) for d in c_docs)
                self.word_given_class[c][w] = (count + self.alpha) / (total_words + self.alpha * len(vocab))

    def predict(self, doc):
        # 로그 공간 계산 (수치적 안정성)
        best_class, best_score = None, float('-inf')
        for c in self.class_probs:
            score = math.log(self.class_probs[c])
            for w in doc:
                prob = self.word_given_class[c].get(w, self.alpha / (self.alpha * 1000))
                score += math.log(prob)
            if score > best_score:
                best_class, best_score = c, score
        return best_class
```

### 켤레 사전분포 (베타-이항)

```python
# A/B 테스트: 전환율 추정
# Beta(α, β) 사전분포 → 이항 가능도 → Beta(α+성공, β+실패) 사후분포

alpha_prior, beta_prior = 1, 1  # 균등 사전분포

# 데이터 관측: 100번 중 30번 전환
successes, trials = 30, 100

# 사후분포 업데이트
alpha_post = alpha_prior + successes
beta_post = beta_prior + (trials - successes)

# 사후분포 평균 = 최적 전환율 추정치
expected_rate = alpha_post / (alpha_post + beta_post)
# = 31/102 ≈ 0.304
```

## 연습 문제

1. 스팸/정상 이메일 데이터셋으로 나이브 베이즈 훈련, 다양한 α로 정확도 비교
2. A/B 테스트 시뮬레이션: 100명당 전환율 30%인 페이지 vs 35%인 페이지. 베이지안 사후분포로 B가 실제로 더 나은 확률은?
3. MLE(정규화 없음)와 MAP(L2 정규화 = 정규분포 사전) 선형 회귀의 가중치 비교

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 사전확률 | 증거 전 믿음 |
| 가능도 | 가설이 주어졌을 때 증거의 확률 |
| 사후확률 | 증거 후 업데이트된 믿음 |
| 나이브 베이즈 | 조건부 독립성 가정을 가진 베이지안 분류기 |
| 켤레 사전분포 | 같은 계열의 사후분포를 만드는 사전분포 (계산이 쉬움) |
| MAP | 최대사후확률 — 사전확률로 정규화된 MLE |