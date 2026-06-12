# K-최근접 이웃과 거리

> 모든 것을 저장하세요. 이웃을 보고 예측하세요. 실제로 작동하는 가장 단순한 알고리즘입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lesson 14
**시간:** ~90분

## 학습 목표

- K와 거리 가중 투표를 구성 가능한 KNN 분류 및 회귀를 처음부터 구현하기
- L1, L2, 코사인, 민코프스키 거리 측정법 비교하고 주어진 데이터 유형에 적합한 것 선택하기
- 차원의 저주 설명하고 KNN이 고차원 공간에서 성능 저하되는 이유 시연하기
- 효율적 최근접 이웃 검색을 위한 KD-트리 구축, 브루트포스보다 나은 시기 분석하기

## 개념

### KNN 작동 방식

1. 쿼리에서 모든 학습점까지 거리 계산
2. 거리순 정렬
3. 가장 가까운 K개 점 선택
4. 분류: 다수결, 회귀: 평균

학습 단계 없음 — "게으른 학습". 전체 학습 세트 저장.

### K 선택

- **K=1**: 각 점이 자신의 이웃 — 과적합, 노이즈에 민감
- **K=전체**: 항상 다수 클래스 예측 — 과소적합
- **최적 K**: 교차 검증으로 찾음. 홀수 K가 동점 방지

### 거리 가중치

가까운 이웃에 더 많은 영향력: `weight = 1/distance` 또는 `exp(-distance)`. 불균일 밀도에서 성능 향상.

### 차원의 저주

고차원에서 모든 점이 서로 거의 등거리가 됨 → 최근접 이웃 무의미. 해결: 차원 축소(PCA) 후 KNN 적용.

### 가속 구조

**KD-트리**: 공간을 이진 파티션으로 나눔. 많은 가지치기로 저차원(<20)에서 로그 검색. 고차원에서는 브루트포스로 퇴화.

## 빌드하기

```python
class KNN:
    def __init__(self, k=5, distance='l2', weighted=True):
        self.k, self.weighted = k, weighted
        self.dist_fn = {'l1': lambda a,b: np.sum(np.abs(a-b)),
                        'l2': lambda a,b: np.sqrt(np.sum((a-b)**2)),
                        'cosine': lambda a,b: 1 - np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b))}[distance]

    def fit(self, X, y):
        self.X_train, self.y_train = X, y

    def predict(self, X):
        preds = []
        for x in X:
            dists = np.array([self.dist_fn(x, xt) for xt in self.X_train])
            knn_idx = np.argsort(dists)[:self.k]
            if self.weighted:
                weights = 1/(dists[knn_idx] + 1e-8)
                vote = np.bincount(self.y_train[knn_idx], weights=weights)
            else:
                vote = np.bincount(self.y_train[knn_idx])
            preds.append(np.argmax(vote))
        return np.array(preds)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| KNN | 최근접 K개 이웃 — 저장 후 투표 |
| 게으른 학습 | 학습 단계 없음 — 모든 계산이 예측 시 |
| 차원의 저주 | 고차원 = 모든 거리가 같아짐 |
| KD-트리 | 공간 분할 — 저차원에서 빠른 검색 |