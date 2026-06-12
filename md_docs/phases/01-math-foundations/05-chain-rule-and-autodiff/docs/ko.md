# 연쇄 법칙 & 자동 미분

> 연쇄 법칙은 학습하는 모든 신경망 뒤에 있는 엔진입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lesson 04 (도함수 & 기울기)
**시간:** ~90분

## 학습 목표

- 연산을 기록하고 역방향 자동 미분으로 기울기를 계산하는 최소한의 autograd 엔진(Value 클래스) 구축하기
- 위상 정렬을 사용하여 계산 그래프를 통한 순전파와 역전파 구현하기
- from-scratch autograd 엔진만 사용하여 XOR에 대한 다층 퍼셉트론 구성 및 훈련하기
- 수치적 유한 차분에 대한 기울기 검사로 autograd 정확성 검증하기

## 문제

간단한 함수의 도함수는 계산할 수 있습니다. 하지만 신경망은 간단한 함수가 아닙니다. 수백 개의 함수가 합성된 것입니다: 행렬 곱, 편향 추가, 활성화 적용, 다시 행렬 곱, 소프트맥스, 교차 엔트로피 손실.

수백만 개의 파라미터에 대해 수동으로 도함수를 계산하는 것은 불가능합니다. 수치적으로(유한 차분) 계산하는 것은 너무 느립니다.

연쇄 법칙이 수학을 제공합니다. 자동 미분이 알고리즘을 제공합니다. 함께 사용하면 임의의 함수 합성을 통해 단일 순전파에 비례하는 시간으로 정확한 기울기를 계산할 수 있습니다.

## 개념

### 연쇄 법칙

y = f(g(x))일 때: dy/dx = f'(g(x)) * g'(x)

더 깊은 합성: y = f(g(h(x))) → dy/dx = f'(g(h(x))) * g'(h(x)) * h'(x)

신경망의 모든 레이어가 이 연쇄의 한 연결고리입니다.

### 계산 그래프

순전파: x1=2, x2=3 → 곱하기 → a=6 → 더하기(+b=1) → c=7 → relu → y=7
역전파: dy/dy=1 → dy/dc=1 → dy/da=1, dy/db=1 → dy/dx1=3, dy/dx2=2

역전파는 각 노드에서 연쇄 법칙을 적용하여 출력에서 입력으로 기울기를 전파합니다.

### 순방향 vs 역방향 모드

- **순방향 모드**: 입력에서 시작하여 도함수를 앞으로 밀어냄. 입력이 적고 출력이 많을 때 좋음
- **역방향 모드**: 출력에서 시작하여 기울기를 뒤로 당김. 입력이 많고 출력이 적을 때 좋음

신경망은 수백만 개의 입력(가중치)과 하나의 출력(손실)을 가집니다. 역방향 모드가 한 번의 역전파로 모든 기울기를 계산합니다. 이것이 역전파가 역방향 모드를 사용하는 이유입니다.

## 빌드하기

### Value 클래스 (미니 autograd)

```python
class Value:
    def __init__(self, data, _children=(), _op=''):
        self.data = data
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)
        self._op = _op

    def __add__(self, other):
        out = Value(self.data + other.data, (self, other), '+')
        def _backward():
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        out = Value(self.data * other.data, (self, other), '*')
        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def relu(self):
        out = Value(self.data if self.data > 0 else 0, (self,), 'ReLU')
        def _backward():
            self.grad += (out.data > 0) * out.grad
        out._backward = _backward
        return out
```

### 위상 정렬 역전파

```python
def backward(self):
    topo = []
    visited = set()
    def build_topo(v):
        if v not in visited:
            visited.add(v)
            for child in v._prev:
                build_topo(child)
            topo.append(v)
    build_topo(self)
    self.grad = 1.0
    for v in reversed(topo):
        v._backward()
```

### XOR에 대한 MLP 훈련

```python
# from-scratch Value만 사용하여 2-4-1 MLP 훈련
model = MLP(2, [4, 1])
for epoch in range(100):
    total_loss = 0
    for x, y in xor_data:
        pred = model(x)
        loss = (pred - y) ** 2
        total_loss += loss.data
        loss.backward()
        for p in model.parameters():
            p.data -= 0.1 * p.grad
            p.grad = 0.0
```

이것이 PyTorch, TensorFlow, JAX의 작동 방식입니다. 방금 미니어처 버전을 구축했습니다.

## 연습 문제

1. Value 클래스에 `tanh` 연산 추가 (도함수: 1 - tanh²(x))
2. 위상 정렬에 순환이 감지되면 오류를 발생시키도록 구현 (순환 그래프 방지)
3. from-scratch autograd MLP를 PyTorch로 구현한 동일한 네트워크와 수렴 속도 비교

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 연쇄 법칙 | 합성 함수 미분: dy/dx = dy/du * du/dx |
| Autograd | 자동 미분: 코드가 연산을 추적하고 자동으로 기울기 계산 |
| 계산 그래프 | 연산을 노드로 표현하는 방향 그래프 |
| 순방향 모드 | 입력 → 출력 방향 기울기. 쌍대수로 구현 |
| 역방향 모드 | 출력 → 입력 방향 기울기. 역전파에 사용 |
| 위상 정렬 | 모든 의존성이 처리된 후 노드를 처리하는 그래프 순서 |