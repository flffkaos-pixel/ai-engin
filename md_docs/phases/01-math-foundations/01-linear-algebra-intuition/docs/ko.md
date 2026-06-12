# 선형대수학 직관

> 모든 AI 모델은 그저 멋진 모자를 쓴 행렬 수학일 뿐입니다.

**유형:** 학습
**언어:** Python, Julia
**선수 과목:** Phase 0
**시간:** ~60분

## 학습 목표

- Python에서 벡터와 행렬 연산(덧셈, 내적, 행렬 곱)을 처음부터 구현하기
- 내적, 사영, Gram-Schmidt 과정이 무엇을 하는지 기하학적으로 설명하기
- 행 축소를 사용하여 벡터 집합의 선형 독립성, 랭크, 기저 결정하기
- 선형대수 개념을 AI 응용과 연결하기: 임베딩, 어텐션 점수, LoRA

## 문제

ML 논문을 아무거나 열어보세요. 첫 페이지에 벡터, 행렬, 내적, 변환이 나옵니다. 선형대수 직관 없이는 이것들은 그저 기호일 뿐입니다. 직관이 있다면 신경망이 실제로 무엇을 하는지 볼 수 있습니다 — 공간에서 점들을 이동시키는 것입니다.

수학자가 될 필요는 없습니다. 이러한 연산이 기하학적으로 무엇을 의미하는지 보고, 직접 코딩하면 됩니다.

## 개념

### 벡터는 점(그리고 방향)입니다

벡터는 그저 숫자 목록입니다. 하지만 그 숫자들은 의미가 있습니다 — 공간에서의 좌표입니다.

2D 벡터 [3, 2]: 원점 (0,0)에서 평면상의 (3, 2)를 가리킵니다. 크기는 sqrt(13)입니다.

AI에서 벡터는 모든 것을 표현합니다:
- 단어 → 768개 숫자의 벡터 (임베딩 공간에서의 "의미")
- 이미지 → 수백만 픽셀 값의 벡터
- 사용자 → 선호도의 벡터

### 행렬은 변환입니다

행렬은 한 벡터를 다른 벡터로 변환합니다. 회전, 크기 조정, 늘이기, 사영할 수 있습니다.

AI에서 행렬이 바로 모델입니다:
- 신경망 가중치 → 입력을 출력으로 변환하는 행렬
- 어텐션 점수 → 무엇에 집중할지 결정하는 행렬
- 임베딩 → 단어를 벡터로 매핑하는 행렬

### 내적은 유사도를 측정합니다

두 벡터의 내적은 그것들이 얼마나 유사한지 알려줍니다.

```
a · b > 0: 같은 방향 (유사함)
a · b = 0: 수직 (무관함)
a · b < 0: 반대 방향 (비유사함)
```

이것이 검색 엔진, 추천 시스템, RAG가 작동하는 방식입니다 — 높은 내적을 가진 벡터 찾기.

### 선형 독립성

어떤 벡터도 다른 벡터들의 조합으로 표현될 수 없을 때 선형 독립입니다.

AI에서 중요한 이유: 특성 행렬은 선형 독립 열을 가져야 합니다. 두 특성이 완벽하게 상관관계(선형 종속)이면 모델이 그 효과를 구분할 수 없습니다 — 다중공선성 발생.

### 기저와 랭크

기저는 전체 공간을 생성하는 최소한의 선형 독립 벡터 집합입니다. 랭크 = 선형 독립 열의 수.

| 상황 | 랭크 | ML에 의미하는 것 |
|------|------|-----------------|
| 완전 랭크 | 최대 | 고유 최소제곱 해 존재. 모델이 잘 조건화됨 |
| 랭크 부족 | 최대 미만 | 특성이 중복됨. 무한히 많은 가중치 해. 정규화 필요 |

### 사영

벡터 a를 벡터 b에 사영하면 b 방향의 a 성분을 얻습니다. 잔차는 b에 수직입니다.

사영은 ML 어디에나 있습니다:
- 선형 회귀 → 관측값에서 열 공간으로의 사영
- PCA → 최대 분산 방향으로 데이터 사영
- 트랜스포머의 어텐션 → 쿼리를 키에 사영

### Gram-Schmidt 과정

독립 벡터 집합을 정규직교 기저로 변환합니다. QR 분해의 내부 작동 방식입니다.

## 빌드하기

### 1단계: 처음부터 Vector 클래스 (Python)

```python
class Vector:
    def __init__(self, components):
        self.components = list(components)
        self.dim = len(self.components)

    def __add__(self, other):
        return Vector([a + b for a, b in zip(self.components, other.components)])

    def dot(self, other):
        return sum(a * b for a, b in zip(self.components, other.components))

    def magnitude(self):
        return sum(x**2 for x in self.components) ** 0.5

    def normalize(self):
        mag = self.magnitude()
        return Vector([x / mag for x in self.components])

    def cosine_similarity(self, other):
        return self.dot(other) / (self.magnitude() * other.magnitude())
```

### 2단계: 처음부터 Matrix 클래스

```python
class Matrix:
    def __init__(self, rows):
        self.rows = [list(row) for row in rows]
        self.shape = (len(self.rows), len(self.rows[0]))

    def __matmul__(self, other):
        # 행렬-벡터 및 행렬-행렬 곱셈
        ...

    def transpose(self):
        return Matrix([[self.rows[j][i] for j in range(self.shape[0])]
                        for i in range(self.shape[1])])
```

### 3단계: 선형 독립성과 사영

```python
def project(a, b):
    scalar = a.dot(b) / b.dot(b)
    return Vector([scalar * x for x in b.components])

def gram_schmidt(vectors):
    orthonormal = []
    for v in vectors:
        w = v
        for u in orthonormal:
            proj = project(w, u)
            w = w - proj
        if w.magnitude() > 1e-10:
            orthonormal.append(w.normalize())
    return orthonormal
```

## 활용하기

NumPy로 실제 사용:

```python
import numpy as np

a = np.array([1, 2, 3], dtype=float)
b = np.array([4, 5, 6], dtype=float)

print(f"내적: {np.dot(a, b)}")
print(f"코사인: {np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)):.4f}")

W = np.random.randn(2, 3) * 0.1
x = np.array([1.0, 0.5, -0.3])
print(f"Wx = {W @ x}")
```

PyTorch — 텐서는 자동 미분이 있는 벡터:

```python
import torch
x = torch.randn(3, requires_grad=True)
y = torch.tensor([1.0, 0.0, 0.0])
similarity = torch.dot(x, y)
similarity.backward()
print(f"기울기: {x.grad}")  # d(dot)/dx = y
```

## 연결

| 개념 | 어디서 나타나는가 |
|------|------------------|
| 내적 | 트랜스포머의 어텐션 점수, RAG의 코사인 유사도 |
| 행렬 곱 | 모든 신경망 레이어, 모든 선형 변환 |
| 랭크 | LoRA(저랭크 적응) |
| 사영 | 선형 회귀, PCA |
| Gram-Schmidt / QR | 수치 솔버, 고윳값 계산 |

LoRA 특별 언급: 4096x4096 가중치 행렬(16M 파라미터) 대신 4096x16과 16x4096(131K 파라미터) 두 행렬로 분해합니다. 이것이 실제로 작동하는 선형대수입니다.

## 연습 문제

1. 두 벡터 사이의 각도를 도 단위로 반환하는 `Vector.angle_between(other)` 구현하기
2. x좌표를 2배, y좌표를 3배 하는 2D 크기 조정 행렬을 만들고 [1, 1]에 적용하기
3. 5개의 랜덤 단어 유사 벡터(차원 50)가 주어졌을 때, 코사인 유사도로 가장 유사한 두 개 찾기
4. Gram-Schmidt 출력이 진정한 정규직교인지 확인: 모든 쌍의 내적이 0이고 모든 벡터 크기가 1인지
5. 랭크 2인 3x3 행렬 만들기. 열이 어떤 기하학적 객체를 생성하는지 설명하기

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 벡터 | "화살표" | n차원 공간의 점이나 방향을 나타내는 숫자 목록 |
| 행렬 | "숫자 표" | 한 공간에서 다른 공간으로 벡터를 매핑하는 변환 |
| 내적 | "곱하고 더하기" | 두 벡터의 정렬도 측정 — 유사도 검색의 핵심 |
| 임베딩 | "AI 마법" | 어떤 것(단어, 이미지, 사용자)의 의미를 나타내는 벡터 |
| 선형 독립 | "겹치지 않는다" | 집합의 어떤 벡터도 다른 벡터들의 조합으로 표현 불가 |
| 랭크 | "차원 수" | 행렬의 선형 독립 열(또는 행)의 수 |
| 사영 | "그림자" | 한 벡터의 다른 벡터 방향 성분 |
| 정규직교 | "수직 단위 벡터" | 서로 수직이고 각각 길이가 1인 벡터들 |