# 결정 트리와 랜덤 포레스트

> 결정 트리는 단순한 순서도입니다. 하지만 그것들의 숲은 ML에서 가장 강력한 도구 중 하나입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lessons 09, 06
**시간:** ~90분

## 학습 목표

- 최적의 결정 트리 분할을 찾기 위한 지니 불순도, 엔트로피, 정보 이득 계산 구현하기
- 사전 가지치기 제어(최대 깊이, 최소 샘플)로 결정 트리 분류기를 처음부터 구축하기
- 부트스트랩 샘플링과 특성 무작위화로 랜덤 포레스트 구성, 분산 감소 이유 설명하기
- MDI 특성 중요도와 순열 중요도 비교, MDI가 편향되는 시기 식별하기

## 문제

표 형식 데이터 — 행은 샘플, 열은 특성, 예측할 목표 열. 신경망을 던질 수 있지만, 표 형식 데이터에서는 트리 기반 모델이 딥러닝을 지속적으로 능가합니다. 구조화 데이터 Kaggle 대회는 트랜스포머가 아닌 XGBoost와 LightGBM이 지배합니다.

트리는 혼합 특성 유형 처리, 비선형 관계 처리, 해석 가능. 랜덤 포레스트는 많은 트리를 평균화하여 적당한 크기의 데이터셋에서 과적합에 매우 강합니다.

## 개념

### 결정 트리의 작동 방식

특성 공간을 예/아니오 질문 시퀀스로 직사각형 영역으로 분할:

```
나이 < 30?
├─ Yes → 소득 > 50k?
│   ├─ Yes → 승인
│   └─ No  → 거부
└─ No  → 신용점수 > 700?
    ├─ Yes → 승인
    └─ No  → 거부
```

루트에서 시작, 리프에 도달할 때까지 가지 따라감.

### 분할 기준: 불순도 측정

**지니 불순도**: `Gini(S) = 1 - Σ p_k²`

순수 노드(한 클래스만): 0. 50/50: 0.5. 낮을수록 좋음.

**엔트로피**: `Entropy(S) = -Σ p_k·log₂(p_k)`

순수: 0. 50/50: 1.0.

**정보 이득**: `IG = Impurity(parent) - Σ(|S_child|/|S_parent|)·Impurity(child)`

가장 큰 IG를 가진 분할 선택.

### 랜덤 포레스트

앙상블 방법: 여러 트리 구축, 투표로 결합.

랜덤성의 두 가지 원천:
1. **배깅**: 각 트리는 데이터의 부트스트랩 샘플로 훈련
2. **특성 무작위화**: 각 분할에서 무작위 특성 부분집합만 고려

이 이중 무작위화가 트리 간 상관관계를 줄여 분산 감소.

### 특성 중요도

- **MDI (평균 불순도 감소)**: 이 특성이 분할에서 불순도를 얼마나 줄였는지. 고유값 많은 특성에 편향
- **순열 중요도**: 특성 값을 섞었을 때 성능 저하 측정. 모델 독립적, 더 신뢰성

## 빌드하기

```python
class DecisionTree:
    def __init__(self, max_depth=10, min_samples=2):
        self.max_depth, self.min_samples = max_depth, min_samples

    def gini(self, y):
        _, counts = np.unique(y, return_counts=True)
        probs = counts / len(y)
        return 1 - np.sum(probs ** 2)

    def best_split(self, X, y):
        best_gain, best_feat, best_thresh = -1, None, None
        for feat in range(X.shape[1]):
            thresholds = np.unique(X[:, feat])
            for thresh in thresholds:
                left = y[X[:, feat] <= thresh]
                right = y[X[:, feat] > thresh]
                if len(left) >= self.min_samples and len(right) >= self.min_samples:
                    gain = self.gini(y) - (len(left)*self.gini(left) + len(right)*self.gini(right))/len(y)
                    if gain > best_gain:
                        best_gain, best_feat, best_thresh = gain, feat, thresh
        return best_feat, best_thresh, best_gain
```

## 연습 문제

1. 결정 트리 훈련하고 트리 시각화. 어떤 특성이 루트 분할인가?
2. 단일 트리 vs 랜덤 포레스트(n=100) 정확도 비교. 앙상블이 얼마나 개선되는가?
3. MDI vs 순열 중요도로 특성 순위 매기고 차이 관찰

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 지니/엔트로피 | 노드 불순도 — 낮을수록 좋음 |
| 정보 이득 | 분할 전후 불순도 감소량 |
| 부트스트랩 | 복원 추출로 샘플 생성 |
| 랜덤 포레스트 | 배깅 + 특성 무작위화 — 분산 감소 |
| OOB 오차 | Out-of-Bag — 부트스트랩에 포함되지 않은 샘플로 검증 |