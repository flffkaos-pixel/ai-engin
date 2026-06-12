# 가중치 초기화

> 무작위로 시작하되, 똑똑하게 무작위여야 합니다. 잘못된 초기화는 훈련 시작 전에 죽입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Lesson 03.03
**시간:** ~60분

## 개념

### 문제: 잘못된 초기화

- **너무 큼**: 활성화 포화 → 기울기 0 → 학습 안 됨
- **너무 작음**: 신호 소실 → 기울기 0 → 학습 안 됨
- **0**: 대칭 파괴 안 됨 — 모든 뉴런이 동일하게 학습

### Xavier/Glorot (tanh/sigmoid용)

`W ~ N(0, 2/(fan_in + fan_out))`

순전파와 역전파의 분산 보존.

### He/Kaiming (ReLU용)

`W ~ N(0, 2/fan_in)`

ReLU가 출력의 절반을 죽이므로 분산 2배.

### LeCun (SELU용)

`W ~ N(0, 1/fan_in)`

## 빌드하기

```python
def init_weights(shape, method='he'):
    fan_in = shape[0] if len(shape) == 2 else np.prod(shape[1:])
    if method == 'he':
        std = np.sqrt(2.0 / fan_in)
    elif method == 'xavier':
        fan_out = shape[1] if len(shape) > 1 else 1
        std = np.sqrt(2.0 / (fan_in + fan_out))
    elif method == 'lecun':
        std = np.sqrt(1.0 / fan_in)
    return np.random.randn(*shape) * std
```

## 주요 용어

| 용어 | 활성화 | 초기화 |
|------|--------|--------|
| He/Kaiming | ReLU | √(2/fan_in) |
| Xavier/Glorot | Tanh/Sigmoid | √(2/(fan_in+fan_out)) |
| LeCun | SELU | √(1/fan_in) |

편향은 보통 0으로 초기화 (ReLU의 경우 작은 양수도 가능).