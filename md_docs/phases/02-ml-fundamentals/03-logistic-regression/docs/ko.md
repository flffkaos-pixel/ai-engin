# 로지스틱 회귀

> 로지스틱 회귀는 직선을 S-곡선으로 구부려 예/아니오 질문에 확률로 답합니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 2 Lesson 1-2
**시간:** ~90분

## 학습 목표

- 시그모이드 함수와 이진 교차 엔트로피 손실을 사용하여 로지스틱 회귀를 처음부터 구현하기
- 이진 분류를 위한 정밀도, 재현율, F1 점수, 혼동 행렬 계산 및 해석하기
- MSE가 분류에 실패하고 이진 교차 엔트로피가 볼록 비용 곡면을 만드는 이유 설명하기
- 다중 클래스 분류를 위한 소프트맥스 회귀 구축 및 임계값 튜닝 트레이드오프 평가하기

## 문제

종양 크기로 악성/양성 예측. 선형 회귀 시도 → 0.3, 1.7, -0.5 출력. 이 숫자들의 의미는? 분류에는 0과 1 사이의 경계 확률과 명확한 예/아니오 결정이 필요합니다.

로지스틱 회귀가 해결합니다. 동일한 선형 조합(wx+b)을 시그모이드 함수에 통과시켜 모든 숫자를 (0,1) 범위로 압축합니다. 출력은 확률입니다.

## 개념

### 선형 회귀가 분류에 실패하는 이유

- 경계 없는 숫자 출력 (음수, >1)
- 이상치에 민감 (50시간 공부한 학생 하나가 전체 라인 변경)
- 확률로 해석 불가

### 시그모이드 함수

`sigmoid(z) = 1 / (1 + e^(-z))`

- z ≫ 0 → sigmoid → 1
- z ≪ 0 → sigmoid → 0
- z = 0 → sigmoid = 0.5
- 항상 (0,1) 범위, 매끄럽고 미분 가능
- **시그모이드 미분**: σ'(z) = σ(z)(1-σ(z)) — 효율적 계산

### 이진 교차 엔트로피 손실

`Loss = -(1/n) Σ[y·log(p) + (1-y)·log(1-p)]`

MSE를 시그모이드와 함께 사용하면 비볼록 곡면(많은 지역 최소값). 교차 엔트로피가 볼록 최적화 생성.

### 다중 클래스: 소프트맥스 회귀

K개 클래스: `P(y=k|x) = exp(w_k^T x) / Σ exp(w_j^T x)`

손실: 범주형 교차 엔트로피 = `-log(p_true_class)`.

### 평가 지표

| 지표 | 의미 | 공식 |
|------|------|------|
| 정확도 | 전체 정답률 | (TP+TN)/Total |
| 정밀도 | 양성 예측 중 실제 양성 | TP/(TP+FP) |
| 재현율 | 실제 양성 중 발견한 비율 | TP/(TP+FN) |
| F1 | 정밀도-재현율 조화평균 | 2PR/(P+R) |

## 빌드하기

```python
import numpy as np

class LogisticRegression:
    def __init__(self, lr=0.01, epochs=1000):
        self.lr, self.epochs = lr, epochs

    def sigmoid(self, z):
        return 1 / (1 + np.exp(-z))

    def fit(self, X, y):
        n, d = X.shape
        self.w = np.zeros(d); self.b = 0.0
        for _ in range(self.epochs):
            z = X @ self.w + self.b
            p = self.sigmoid(z)
            dw = (1/n) * X.T @ (p - y)
            db = (1/n) * np.sum(p - y)
            self.w -= self.lr * dw
            self.b -= self.lr * db

    def predict_proba(self, X):
        return self.sigmoid(X @ self.w + self.b)

    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X) >= threshold).astype(int)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 시그모이드 | 모든 실수 → (0,1). 확률 출력 |
| 교차 엔트로피 | 분류용 표준 손실 — 볼록, 수치적 안정 |
| 결정 경계 | wx+b=0인 곳 — 시그모이드=0.5 |
| 정밀도 | "양성 예측이 맞았나" — 오탐지 최소화 |
| 재현율 | "실제 양성을 잡았나" — 미탐지 최소화 |