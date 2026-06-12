# 미니 딥러닝 프레임워크

> 지금까지 모든 것을 하나로 통합. 자체 딥러닝 라이브러리.

**유형:** 빌드
**언어:** Python
**선수 과목:** Lesson 03.01~09
**시간:** ~120분

## 개념

### 통합 구성 요소

지금까지 배운 모든 것을 하나의 프레임워크로: Layer, Network, 활성화, 손실, 옵티마이저, 초기화, 스케줄, 드롭아웃, 배치 정규화.

### 최소 API (PyTorch 유사)

```python
net = Sequential([
    Linear(2, 64), ReLU(), Dropout(0.2),
    Linear(64, 32), ReLU(),
    Linear(32, 1), Sigmoid()
])

net.train(X, y, loss='bce', optimizer='adam', lr=0.001, epochs=100)
preds = net.predict(X_test)
```

## 빌드하기

```python
class Sequential:
    def __init__(self, layers):
        self.layers = layers

    def forward(self, x, training=True):
        for layer in self.layers:
            if isinstance(layer, Dropout):
                x = layer.forward(x, training)
            else:
                x = layer.forward(x)
        return x

    def backward(self, grad):
        for layer in reversed(self.layers):
            grad = layer.backward(grad)

    def train(self, X, y, loss='mse', optimizer='sgd', lr=0.01, epochs=100):
        for epoch in range(epochs):
            out = self.forward(X)
            L, dL = compute_loss(out, y, loss)
            self.backward(dL)
            update_params(self.layers, optimizer, lr)
            if epoch % 10 == 0: print(f"Epoch {epoch}: loss {L:.4f}")
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| Sequential | 레이어 체인 → 순차적 순전파/역전파 |
| Module | 모든 레이어의 기본 클래스 |
| 통합 | 모든 컴포넌트를 단일 API로 |