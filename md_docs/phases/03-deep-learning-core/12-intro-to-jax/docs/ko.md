# JAX 입문

> 함수형 딥러닝의 다른 패러다임.

**유형:** 빌드
**언어:** Python
**선수 과목:** Lesson 03.10
**시간:** ~90분

## 개념

### JAX = NumPy + Autograd + JIT + vectorize

```python
import jax.numpy as jnp
from jax import grad, jit, vmap

# 자동 미분
def loss(w, x, y):
    return jnp.mean((x @ w - y)**2)
grad_loss = grad(loss)

# JIT 컴파일
fast_fn = jit(loss)

# 자동 벡터화
batched = vmap(fn, in_axes=(0, None))
```

### Flax/Haiku (NN 라이브러리)

JAX 자체는 순수 함수형 — 상태 관리 없음. Flax/Haiku가 PyTorch 유사 API 제공.

### PyTorch vs JAX

| 특성 | PyTorch | JAX |
|------|---------|-----|
| 스타일 | 객체 지향 | 함수형 |
| 난수 | 전역 상태 | 명시적 키 |
| 루프 | Python for | jax.lax.scan |
| 속도 | eager 우수 | JIT 우수 |
| 사용처 | 연구/프로덕션 | Google/DeepMind |

## 빌드하기

```python
import jax; import jax.numpy as jnp

def mlp(params, x):
    for w, b in params:
        x = jax.nn.relu(x @ w + b)
    return x

def loss(params, x, y):
    return jnp.mean((mlp(params, x) - y)**2)

grad_fn = jax.grad(loss)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| jit | XLA 컴파일 → 수십 배 가속 |
| vmap | 자동 벡터화 — 배치 차원 처리 |
| pmap | 자동 병렬화 — 멀티 GPU |