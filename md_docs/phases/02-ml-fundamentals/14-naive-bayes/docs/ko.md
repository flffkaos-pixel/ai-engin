# 나이브 베이즈

> "순진한" 가정은 틀렸지만, 어쨌든 작동합니다. 그게 이 방법의 아름다움입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 2, Lessons 01-07
**시간:** ~75분

## 학습 목표

- 텍스트 분류를 위해 라플라스 평활화로 다항 나이브 베이즈를 처음부터 구현하기
- 순진한 독립성 가정이 수학적으로는 틀렸지만 실제로 올바른 클래스 순위를 생성하는 이유 설명
- 다항, 베르누이, 가우시안 나이브 베이즈 변형 비교하고 주어진 특성 유형에 적합한 것 선택
- 고차원 희소 데이터에서 로지스틱 회귀와 비교 평가하고 작동하는 편향-분산 트레이드오프 설명

## 개념

### 왜 "순진한" 가정이 작동하는가

모든 특성이 클래스에 대해 조건부 독립이라고 가정 — 대부분 틀림. 하지만 상대적 확률 순위는 보존되어 분류 결정이 정확함.

### 변형

| 변형 | 특성 유형 | 예시 |
|------|---------|------|
| 다항 | 단어 개수 (이산) | 텍스트 분류 |
| 베르누이 | 이진 (존재/부재) | 단어 출현 여부 |
| 가우시안 | 연속 (정규분포) | 수치 특성 |

### 나이브 베이즈 vs 로지스틱 회귀

- **NB**: 생성 모델 — P(x|y) 모델링. 적은 데이터에서 우수, 빠름. 과도한 확신 경향
- **LR**: 판별 모델 — P(y|x) 직접 모델링. 충분한 데이터에서 우수, 보정된 확률

NB는 모든 특성이 독립이라 가정하므로 "확률"이 보정되지 않음 → 신뢰도 추정에 부적합.

## 빌드하기

```python
class MultinomialNB:
    def __init__(self, alpha=1.0):
        self.alpha = alpha  # 라플라스 평활화

    def fit(self, X, y):
        self.classes = np.unique(y)
        n_features = X.shape[1]
        self.log_prior = {}
        self.log_likelihood = {}
        for c in self.classes:
            X_c = X[y == c]
            self.log_prior[c] = np.log(len(X_c) / len(X))
            count = X_c.sum(axis=0) + self.alpha
            self.log_likelihood[c] = np.log(count / count.sum())

    def predict(self, X):
        scores = np.array([[self.log_prior[c] + (X[i] @ self.log_likelihood[c])
                           for c in self.classes] for i in range(len(X))])
        return self.classes[np.argmax(scores, axis=1)]
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 조건부 독립 | P(x₁,x₂|y) = P(x₁|y)P(x₂|y) — 틀렸지만 순위 유지 |
| 라플라스 평활화 | 관측되지 않은 특성에 α 추가 — 0 확률 방지 |
| 생성 vs 판별 | P(x,y) vs P(y|x) — NB가 생성, LR이 판별 |