# 퍼셉트론

> 퍼셉트론은 신경망의 원자입니다. 쪼개보면 가중치, 편향, 결정이 나옵니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1
**시간:** ~60분

## 학습 목표

- 가중치 업데이트 규칙과 계단 활성화 함수로 퍼셉트론을 Python에서 처음부터 구현
- 단일 퍼셉트론이 선형 분리 가능 문제만 해결 가능한 이유 설명, XOR 실패 케이스 시연
- OR, NAND, AND 게이트를 구성하여 다층 퍼셉트론으로 XOR 해결
- 시그모이드 활성화와 역전파로 2층 네트워크 훈련하여 XOR 자동 학습

## 개념

### 모델

`output = step(w·x + b)`, step(x) = 1 if x≥0 else 0.

선형 결정 경계 그리기. AND, OR은 선형 분리 가능 → 해결 가능. XOR은 비선형 → 단일 퍼셉트론으로 불가능.

### XOR 해결

계층 조합으로: input → (NAND, OR) → AND → output. 은닉층이 비선형 결정 경계 생성.

### 훈련

```
w ← w + lr * (y_true - y_pred) * x
b ← b + lr * (y_true - y_pred)
```

오분류 시에만 업데이트. 선형 분리 가능 데이터에서 수렴 보장.

## 빌드하기

```python
class Perceptron:
    def __init__(self, n_features, lr=0.1):
        self.w = np.zeros(n_features)
        self.b = 0.0
        self.lr = lr

    def predict(self, X):
        return np.where(X @ self.w + self.b >= 0, 1, 0)

    def fit(self, X, y, epochs=100):
        for _ in range(epochs):
            for xi, yi in zip(X, y):
                pred = self.predict(xi.reshape(1, -1))[0]
                error = yi - pred
                self.w += self.lr * error * xi
                self.b += self.lr * error
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 퍼셉트론 | 단일 뉴런 — 가중합 + 계단 함수 |
| 선형 분리 | 직선으로 클래스 분리 가능 |
| XOR 문제 | 단일 퍼셉트론 실패 — MLP의 동기 |