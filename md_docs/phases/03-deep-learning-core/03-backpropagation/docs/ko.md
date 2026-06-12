# 처음부터 구현하는 역전파

> 역전파는 학습을 가능하게 하는 알고리즘입니다. 없으면 신경망은 비싼 난수 생성기일 뿐입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Lesson 03.02
**시간:** ~120분

## 학습 목표

- 계산 그래프를 구축하고 위상 정렬로 기울기를 계산하는 Value 기반 autograd 엔진 구현
- 연쇄 법칙으로 덧셈, 곱셈, 시그모이드의 역방향 전파 유도
- 자체 구현 역전파 엔진만으로 XOR 및 원 분류에서 다층 네트워크 훈련
- 깊은 시그모이드 네트워크의 기울기 소실 문제 식별, 기울기가 지수적으로 축소되는 이유 설명

## 개념

### 역전파 = 연쇄 법칙의 체계적 적용

1. **순전파**: 계산 수행, 그래프 구축, 출력/손실 계산
2. **역전파**: 위상 정렬로 각 노드 방문, ∂loss/∂node 계산

### 주요 연산의 지역적 기울기

- **덧셈**: 기울기를 양쪽에 1:1 전파
- **곱셈**: `a*b` → a의 기울기 = b*upstream, b의 기울기 = a*upstream
- **시그모이드**: σ'(x) = σ(x)(1-σ(x))

### 기울기 소실

깊은 시그모이드 네트워크에서: 각 레이어에서 σ'(x) ≤ 0.25 곱해짐 → 10레이어 후 기울기 ≤ 0.25¹⁰ ≈ 10⁻⁶. 초기 레이어가 거의 학습되지 않음 → ReLU/잔차 연결의 동기.

## 빌드하기

```python
class Value:
    def __init__(self, data, _children=(), _op=''):
        self.data = data; self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)

    def __add__(self, other):
        out = Value(self.data + other.data, (self, other), '+')
        def _backward():
            self.grad += out.grad; other.grad += out.grad
        out._backward = _backward; return out

    def __mul__(self, other):
        out = Value(self.data * other.data, (self, other), '*')
        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward; return out

    def backward(self):
        topo = []; visited = set()
        def build(v):
            if v not in visited:
                visited.add(v)
                for c in v._prev: build(c)
                topo.append(v)
        build(self); self.grad = 1.0
        for v in reversed(topo): v._backward()
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| Autograd | 자동 미분 — 연산 기록, 기울기 계산 |
| 위상 정렬 | 의존성 순서 — 출력에서 입력으로 |
| 연쇄 법칙 | ∂L/∂x = ∂L/∂y · ∂y/∂x |
| 기울기 소실 | 시그모이드 포화 → 깊은 네트워크 학습 불가 |