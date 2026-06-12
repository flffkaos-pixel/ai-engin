# 텐서 연산

> 텐서는 데이터와 딥러닝 사이의 공통 언어입니다. 모든 이미지, 모든 문장, 모든 기울기가 텐서를 통해 흐릅니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lessons 01-02
**시간:** ~90분

## 학습 목표

- 형태, 스트라이드, 재구성, 전치, 요소별 연산을 갖춘 텐서 클래스를 처음부터 구현하기
- 데이터를 복사하지 않고 다른 형태의 텐서를 연산하기 위해 브로드캐스팅 규칙 적용하기
- 내적, 행렬 곱, 외적, 배치 연산을 위한 einsum 표현식 작성하기
- 다중 헤드 어텐션의 모든 단계를 통해 정확한 텐서 형태 추적하기

## 문제

트랜스포머를 구축합니다. 순전파가 깔끔해 보입니다. 실행하면: `RuntimeError: mat1 and mat2 shapes cannot be multiplied (32x768 and 512x768)`. 전치를 시도합니다. 이제 `Expected 4D input (got 3D input)`. unsqueeze 추가. 다른 것이 깨집니다.

형태 오류는 딥러닝 코드에서 가장 흔한 버그입니다. 개념적으로 어렵지 않지만 빠르게 증식합니다. 트랜스포머는 수십 개의 reshape, transpose, broadcast가 연결되어 있습니다. 한 축이 잘못되면 오류가 연쇄됩니다. 더 나쁜 것은 일부 형태 실수는 오류를 발생시키지 않고 잘못된 차원으로 브로드캐스팅하거나 잘못된 축을 합산하여 조용히 쓰레기를 생성합니다.

## 개념

### 텐서란

텐서는 균일한 데이터 타입의 다차원 숫자 배열입니다:
- 스칼라: 랭크 0, 형태 ()
- 벡터: 랭크 1, 형태 (n,)
- 행렬: 랭크 2, 형태 (m,n)
- 3D 텐서: 랭크 3, 형태 (b,m,n)
- 4D 텐서: 랭크 4, 형태 (B,C,H,W)

### 딥러닝에서의 텐서 형태

| 도메인 | 형태 | 예시 |
|--------|------|------|
| 비전 (NCHW) | (B, C, H, W) | (32, 3, 224, 224) |
| NLP | (B, T, D) | (16, 128, 768) |
| 어텐션 | (B, H, T, D) | (16, 12, 128, 64) |
| 가중치 | 선형: (out, in) | Conv2D: (out_c, in_c, kH, kW) |

### 메모리 레이아웃

**스트라이드**: 각 축을 따라 한 걸음 이동할 때 건너뛸 요소 수.
- 행 우선 (C 순서): strides (cols, 1)
- 열 우선 (F 순서): strides (1, rows)

**Transpose는 데이터를 이동시키지 않습니다.** 스트라이드만 교환합니다. 결과 텐서는 비연속적입니다.

### 브로드캐스팅 규칙

1. 뒤에서부터 차원 정렬
2. 크기가 같거나 하나가 1이면 호환 가능
3. 크기 1인 차원은 더 큰 차원과 일치하도록 확장

```
(3, 1) + (1, 4) → (3, 4)    # 확장
(3, 4) + (4,)   → (3, 4)    # 묵시적 선행 차원 추가
```

### Einsum (아인슈타인 합)

```python
import numpy as np

# 내적: 'i,i->'
np.einsum('i,i->', a, b)

# 행렬 곱: 'ik,kj->ij'
np.einsum('ik,kj->ij', A, B)

# 배치 행렬 곱: 'bik,bkj->bij'
np.einsum('bik,bkj->bij', A_batch, B_batch)

# 다중 헤드 어텐션: 'bhtd,bhsd->bhts'
scores = np.einsum('bhtd,bhsd->bhts', Q, K)
```

### 다중 헤드 어텐션의 형태 추적

```python
# 입력
Q: (batch, heads, seq_len, head_dim)  # (B, H, T, D)

# 어텐션 점수
scores = Q @ K.transpose(-2, -1)  # (B, H, T, D) @ (B, H, D, S) → (B, H, T, S)
scores = scores / sqrt(head_dim)  # 스케일링
attn = softmax(scores, dim=-1)    # 마지막 축 따라 정규화

# 출력
out = attn @ V                     # (B, H, T, S) @ (B, H, S, D) → (B, H, T, D)
out = out.transpose(1, 2).reshape(B, T, H*D)  # 헤드 결합
final = out @ W_o                              # (B, T, H*D) @ (H*D, D_out)
```

## 빌드하기

```python
class Tensor:
    def __init__(self, data, shape=None):
        self.data = list(self._flatten(data))
        self.shape = tuple(shape) if shape else self._infer_shape(data)

    def reshape(self, *new_shape):
        # 자동 차원 추론: -1
        total = 1
        inferred_idx = -1
        for i, dim in enumerate(new_shape):
            if dim == -1:
                inferred_idx = i
            else:
                total *= dim
        if inferred_idx >= 0:
            inferred = len(self.data) // total
            new_shape = list(new_shape)
            new_shape[inferred_idx] = inferred
        return Tensor(self.data, tuple(new_shape))

    def transpose(self, dim0, dim1):
        new_shape = list(self.shape)
        new_shape[dim0], new_shape[dim1] = new_shape[dim1], new_shape[dim0]
        # 스트라이드 기반 재정렬 (구현 생략)
        return Tensor(new_data, tuple(new_shape))
```

## 연습 문제

1. `(2,3,4)` 텐서를 `(4,6)`으로 재구성. 어떤 조건에서 작동하나?
2. `(32,1,128)`과 `(1,64,128)`을 `+`로 브로드캐스팅. 최종 형태는?
3. 다중 헤드 어텐션에서 `(B,H,T,D)` Q,K,V의 einsum 연산 작성

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 랭크 | 텐서의 차원 수 |
| 형태 | 각 축의 크기 튜플 |
| 스트라이드 | 각 축을 따라 한 걸음 이동할 때 건너뛸 요소 수 |
| 브로드캐스팅 | 크기 1 차원을 더 큰 크기에 맞게 확장 (데이터 복사 없이) |
| Einsum | 아인슈타인 합 표기법 — 임의의 텐서 축소를 위한 간결한 DSL |