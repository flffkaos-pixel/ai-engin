# 벡터, 행렬 & 연산

> 모든 신경망은 추가 단계가 있는 행렬 곱셈일 뿐입니다.

**유형:** 빌드
**언어:** Python, Julia
**선수 과목:** Phase 1, Lesson 01 (선형대수학 직관)
**시간:** ~60분

## 학습 목표

- 요소별 연산, 행렬 곱셈, 전치, 행렬식, 역행렬을 갖춘 Matrix 클래스 구축하기
- 요소별 곱셈과 행렬 곱셈을 구분하고 각각이 언제 적용되는지 설명하기
- from-scratch Matrix 클래스만 사용하여 단일 밀집 신경망 레이어(`relu(W @ x + b)`) 구현하기
- 브로드캐스팅 규칙과 신경망 프레임워크에서 편향 추가가 작동하는 방식 설명하기

## 문제

이 코드를 봅니다:

```
output = activation(weights @ input + bias)
```

`@`는 행렬 곱셈입니다. `weights`는 행렬, `input`은 벡터입니다. 이 연산들이 무엇을 하는지 모르면 이 줄은 마법입니다. 안다면 세 번의 연산으로 레이어의 전체 순전파입니다.

## 개념

### 벡터: 순서 있는 숫자 목록

```python
v = [3, 4]        # 2D 벡터
w = [1, 0, -2]    # 3D 벡터
```

### 행렬: 숫자 격자

m x n 행렬: m행, n열. 신경망에서 가중치 행렬은 입력 벡터를 출력 벡터로 변환합니다. 784개 입력과 128개 출력을 가진 레이어는 128x784 가중치 행렬을 사용합니다.

### 형태가 중요한 이유

행렬 곱셈의 규칙: `(m x n) @ (n x p) = (m x p)`. 내부 차원이 일치해야 합니다.

```
(128 x 784) @ (784 x 1) = (128 x 1)
  가중치       입력        출력
```

PyTorch에서 형태 불일치 오류가 발생하면 이 때문입니다.

### 연산 맵

| 연산 | 하는 일 | 신경망 사용 |
|------|--------|-----------|
| 덧셈 | 요소별 결합 | 출력에 편향 추가 |
| 스칼라 곱 | 모든 요소 크기 조정 | 학습률 * 기울기 |
| 행렬 곱 | 벡터 변환 | 레이어 순전파 |
| 전치 | 행과 열 뒤집기 | 역전파 |
| 행렬식 | 단일 숫자 요약 | 가역성 확인 |
| 역행렬 | 변환 되돌리기 | 선형 시스템 풀기 |

### 요소별 vs 행렬 곱셈

요소별: 일치하는 위치끼리 곱함. 두 행렬이 같은 형태여야 함.

행렬 곱셈: 행과 열의 내적. 내부 차원이 일치해야 함. 다른 연산, 다른 결과, 다른 규칙.

### 브로드캐스팅

편향 벡터를 출력 행렬에 더할 때 형태가 일치하지 않습니다. 브로드캐스팅이 작은 배열을 늘려 맞춥니다.

## 빌드하기

### Matrix 클래스 (주요 부분)

```python
class Matrix:
    def __init__(self, data):
        self.data = [list(row) for row in data]
        self.rows, self.cols = len(self.data), len(self.data[0])
        self.shape = (self.rows, self.cols)

    def __add__(self, other):
        return Matrix([[self.data[i][j] + other.data[i][j]
                        for j in range(self.cols)] for i in range(self.rows)])

    def matmul(self, other):
        return Matrix([[sum(self.data[i][k] * other.data[k][j]
                        for k in range(self.cols))
                        for j in range(other.cols)] for i in range(self.rows)])

    def transpose(self):
        return Matrix([[self.data[j][i] for j in range(self.rows)]
                        for i in range(self.cols)])
```

### 신경망 레이어 연결

```python
inputs = Matrix([[0.5], [0.8], [0.2]])
weights = Matrix([[random.uniform(-1, 1) for _ in range(3)] for _ in range(2)])
bias = Matrix([[0.1], [0.1]])

def relu_matrix(m):
    return Matrix([[max(0, val) for val in row] for row in m.data])

pre_activation = weights.matmul(inputs) + bias
output = relu_matrix(pre_activation)
# output = relu(W @ x + b) — 단일 밀집 레이어
```

## 활용하기 (NumPy)

```python
import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

print("A * B (요소별):\n", A * B)
print("A @ B (행렬 곱):\n", A @ B)
print("A^T:\n", A.T)
print("det(A):", np.linalg.det(A))
print("A^-1:\n", np.linalg.inv(A))

# 신경망 레이어
inputs = np.random.randn(3, 1)
weights = np.random.randn(2, 3)
bias = np.array([[0.1], [0.1]])
output = np.maximum(0, weights @ inputs + bias)
```

NumPy의 `@` 연산자는 C와 Fortran으로 작성된 최적화된 BLAS 루틴을 사용합니다. 같은 수학, 100배 더 빠름.

## 연습 문제

1. **역행렬 검증.** `A @ A.inverse_2x2()`를 곱해 단위 행렬이 나오는지 확인. 행렬식이 0이면 어떻게 되나?
2. **3x3 역행렬 구현.** 여인수 방법을 사용하여 Matrix 클래스 확장. NumPy의 `np.linalg.inv`와 비교 테스트.
3. **2층 네트워크 구축.** Matrix 클래스만 사용(No NumPy): 입력(3) → 은닉(4) → 출력(2). 랜덤 가중치 초기화, 순전파 실행, 모든 형태 확인.

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 벡터 | 순서 있는 숫자 목록. AI: 고차원 공간의 점 |
| 행렬 | 선형 변환. 한 공간에서 다른 공간으로 벡터 매핑 |
| 행렬 곱 | 첫 번째 행렬의 모든 행과 두 번째 행렬의 모든 열 간 내적. 순서가 중요 |
| 전치 | 행과 열 교환. m x n → n x m. 역전파에서 중요 |
| 행렬식 | 행렬이 면적(2D)이나 부피(3D)를 얼마나 조정하는지 측정. 0이면 변환이 차원을 소멸시킴 |
| 브로드캐스팅 | 누락된 차원을 따라 반복하여 작은 배열을 큰 배열에 맞게 늘리기 |