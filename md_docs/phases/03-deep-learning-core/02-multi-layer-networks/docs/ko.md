# 다층 네트워크와 순전파

> 뉴런 하나는 선을 그립니다. 쌓으면 무엇이든 그릴 수 있습니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lesson 03.01
**시간:** ~90분

## 학습 목표

- Layer와 Network 클래스로 완전한 순전파를 수행하는 다층 네트워크를 처음부터 구축
- 네트워크의 각 레이어를 통한 행렬 차원 추적 및 형태 불일치 식별
- 비선형 활성화 중첩이 네트워크의 곡선 결정 경계 학습을 가능하게 하는 방법 설명
- 2-2-1 아키텍처와 수동 조정된 시그모이드 가중치로 XOR 해결

## 개념

### 네트워크 = 레이어 스택

```
input → Linear(W₁,b₁) → σ → Linear(W₂,b₂) → σ → ... → output

각 레이어: h = σ(Wx + b)
```

W: (output_dim, input_dim), b: (output_dim,)

### 비선형성이 중요한 이유

비선형 활성화 없는 n개 Linear 레이어 = 단일 Linear 레이어. 중간 은닉층이 무의미해짐. 비선형 σ(ReLU, sigmoid 등)가 각 레이어를 다르게 만들어 깊이가 의미 있게 함.

### 형태 추적

```
입력: (batch, 2)
은닉: (batch, 2) @ (2, 4) + (4,) = (batch, 4)
출력: (batch, 4) @ (4, 1) + (1,) = (batch, 1)
```

## 빌드하기

```python
class Layer:
    def __init__(self, in_dim, out_dim, activation='sigmoid'):
        self.W = np.random.randn(out_dim, in_dim) * 0.1
        self.b = np.zeros(out_dim)
        self.activation = activation

    def forward(self, x):
        z = x @ self.W.T + self.b
        return 1/(1+np.exp(-z)) if self.activation == 'sigmoid' else z

class Network:
    def __init__(self, layers):
        self.layers = layers

    def forward(self, x):
        for layer in self.layers:
            x = layer.forward(x)
        return x
```

## 연습 문제

1. 2-4-1 네트워크 구축. XOR에 대한 수동 가중치 찾기
2. 깊이가 늘어날 때 형태 추적 (2→8→16→8→1)
3. 시그모이드 없는 Linear 전용 네트워크로 XOR 시도. 실패 확인

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 순전파 | 입력 → 가중치 → 활성화 → 다음 레이어 |
| 비선형성 | 레이어를 다르게 만듦 — 깊이에 의미 부여 |
| 형태 추적 | 각 레이어의 차원 변환 확인 |