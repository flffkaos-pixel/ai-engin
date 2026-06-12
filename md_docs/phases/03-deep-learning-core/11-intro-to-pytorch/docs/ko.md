# PyTorch 입문

> 자체 프레임워크를 만든 후, 프로들이 사용하는 것을 이해하세요.

**유형:** 빌드
**언어:** Python
**선수 과목:** Lesson 03.10
**시간:** ~90분

## 개념

### Tensor = ndarray + autograd

```python
x = torch.tensor([1.0, 2.0], requires_grad=True)
w = torch.randn(2, requires_grad=True)
y = torch.dot(w, x)
y.backward()
print(w.grad)  # = x
```

### 기본 패턴

```python
# 1. 모델 정의
model = nn.Sequential(
    nn.Linear(784, 128), nn.ReLU(),
    nn.Linear(128, 10)
)

# 2. 손실 + 옵티마이저
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 3. 훈련 루프
for epoch in range(epochs):
    for X, y in dataloader:
        optimizer.zero_grad()
        loss = criterion(model(X), y)
        loss.backward()
        optimizer.step()
```

### 주요 모듈

- `nn.Linear`, `nn.Conv2d`, `nn.LSTM`, `nn.Transformer`
- `nn.ReLU`, `nn.Dropout`, `nn.BatchNorm`
- `F.cross_entropy`, `F.mse_loss`
- `optim.SGD`, `optim.Adam`, `optim.AdamW`
- `DataLoader`, `Dataset`

### 디바이스 관리

```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
X, y = X.to(device), y.to(device)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| Tensor | GPU 지원 다차원 배열 + autograd |
| nn.Module | 모든 모델의 기본 클래스 |
| DataLoader | 배치 + 셔플 + 병렬 로딩 |
| to(device) | CPU ↔ GPU 전송 |