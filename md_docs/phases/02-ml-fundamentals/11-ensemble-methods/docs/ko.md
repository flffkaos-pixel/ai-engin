# 앙상블 방법

> 약한 학습기 그룹이 올바르게 결합되면 강한 학습기가 됩니다. 은유가 아닌 정리입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 2, Lesson 10
**시간:** ~120분

## 학습 목표

- AdaBoost와 그래디언트 부스팅을 처음부터 구현, 부스팅이 순차적으로 편향을 줄이는 방법 설명
- 배깅 앙상블 구축, 상관관계 없는 모델 평균화가 편향 증가 없이 분산 감소 시연
- 배깅, 부스팅, 스태킹을 각 방법이 목표로 하는 오차 구성 요소 측면에서 비교
- 앙상블 다양성 평가, 약한 학습기가 더 독립적일수록 다수결 정확도 향상 설명

## 개념

### 앙상블이 작동하는 이유

정확도 p>0.5의 N개 독립 분류기 → N이 커질수록 다수결이 개별보다 우수. 예: p=0.6 분류기 21개 → 다수결 정확도 ≈ 0.83.

### 배깅 (Bootstrap Aggregating)

1. 데이터에서 N개 부트스트랩 샘플 생성 (복원 추출)
2. 각 샘플로 모델 훈련
3. 예측 평균화 (회귀) 또는 다수결 (분류)

**효과**: 분산 감소. 각 모델이 다른 데이터 부분집합을 보므로 오차가 평균화됨. 랜덤 포레스트 = 배깅 + 특성 무작위화.

### 부스팅

약한 학습기를 순차적으로 훈련. 각각이 이전 실수를 수정:

**AdaBoost**: 오분류 샘플 가중치 증가 → 다음 모델이 집중.
**그래디언트 부스팅**: 각 모델이 잔차 (y - 이전 예측)에 적합.

부스팅은 편향 감소. 순차적 특성으로 인해 과적합 위험 — 작은 학습률과 조기 종료로 완화.

### 스태킹

서로 다른 모델 유형의 예측을 입력으로 사용하는 메타 학습기 훈련. 각 기본 모델이 어디서 강한지 학습.

### 비교

| 방법 | 오차 감소 | 작동 방식 |
|------|----------|----------|
| 배깅 | 분산 ↓ | 독립적 모델 평균화 |
| 부스팅 | 편향 ↓ | 순차적 오차 수정 |
| 스태킹 | 둘 다 | 메타 모델이 결합 학습 |

## 빌드하기

```python
# 간단한 그래디언트 부스팅
class GradientBoosting:
    def __init__(self, n_estimators=100, lr=0.1, max_depth=3):
        self.n_estimators, self.lr, self.max_depth = n_estimators, lr, max_depth

    def fit(self, X, y):
        self.trees = []
        self.base_pred = np.mean(y)
        residuals = y - self.base_pred
        for _ in range(self.n_estimators):
            tree = DecisionTree(max_depth=self.max_depth)
            tree.fit(X, residuals)
            self.trees.append(tree)
            residuals -= self.lr * tree.predict(X)

    def predict(self, X):
        pred = np.full(len(X), self.base_pred)
        for tree in self.trees:
            pred += self.lr * tree.predict(X)
        return pred
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 배깅 | 병렬 앙상블 — 분산 감소 |
| 부스팅 | 순차적 앙상블 — 편향 감소 |
| 스태킹 | 메타 학습기 — 모델 가중치 학습 |
| 약한 학습기 | 랜덤보다 약간 나은 — 앙상블로 강해짐 |