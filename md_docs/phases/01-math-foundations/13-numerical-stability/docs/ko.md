# 수치적 안정성

> 부동소수점은 새는 추상화입니다. 훈련 중에 당신을 물 것이고, 당신은 그것이 오는 것을 보지 못할 것입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lessons 01-04
**시간:** ~120분

## 학습 목표

- 최댓값 빼기 트릭으로 수치적으로 안정적인 소프트맥스와 로그-합-지수 구현하기
- 부동소수점 계산에서 오버플로, 언더플로, 파국적 소거 식별하기
- 중심 유한 차분을 사용하여 해석적 기울기를 수치적 기울기와 비교 검증하기
- 학습에 float16보다 bfloat16이 선호되는 이유와 loss scaling이 기울기 언더플로를 방지하는 방법 설명하기

## 문제

세 시간 훈련 후 loss가 NaN이 됩니다. 9,000단계에서 로짓은 괜찮았습니다. 9,001단계에서 `inf`가 됩니다. 9,002단계에서는 모든 기울기가 `nan`이고 훈련이 죽습니다.

또는: 모델이 완료까지 훈련되지만 정확도가 논문보다 2% 낮습니다. float16을 올바른 스케일링 없이 사용해서 32비트의 누적 반올림 오차가 정확도를 조용히 깎아먹었습니다.

수치적 안정성은 이론적 관심사가 아닙니다. 성공하는 훈련과 조용히 실패하는 훈련의 차이입니다.

## 개념

### IEEE 754: 컴퓨터가 실수를 저장하는 방법

| 형식 | 비트 | 지수 | 가수 | 십진 자릿수 | 범위 |
|------|------|------|------|-----------|------|
| float64 | 64 | 11 | 52 | ~15-16 | ±1.8e308 |
| float32 | 32 | 8 | 23 | ~7-8 | ±3.4e38 |
| float16 | 16 | 5 | 10 | ~3-4 | ±65,504 |
| bfloat16 | 16 | 8 | 7 | ~2-3 | ±3.4e38 |

bfloat16은 Google의 해결책: float32와 동일한 지수(동일 범위)를 갖지만 더 적은 정밀도. 신경망 훈련에서는 정밀도보다 범위가 더 중요하므로 bfloat16이 보통 승리합니다.

### 왜 0.1 + 0.2 != 0.3인가

0.1은 이진 부동소수점으로 정확히 표현할 수 없습니다:
```python
>>> 0.1 + 0.2
0.30000000000000004
>>> 0.1 + 0.2 == 0.3
False
```

ML에서 중요한 이유: loss 비교, 수천 단계에 걸친 기울기 누적, `==`를 사용한 체크섬이 실패합니다.

### 세 가지 치명적 실패 모드

**오버플로**: `exp(100)` > 3.4e38 → inf
**언더플로**: `exp(-100)` → 0, 기울기 0이 되어 학습 중단
**파국적 소거**: 비슷한 두 수를 빼면 모든 유효 숫자가 소거됨

### 로그-합-지수 트릭

```python
# 불안정: exp 오버플로
def unstable_logsumexp(x):
    return math.log(sum(math.exp(xi) for xi in x))

# 안정: 최댓값 빼기
def stable_logsumexp(x):
    m = max(x)
    return m + math.log(sum(math.exp(xi - m) for xi in x))
```

### 안정적인 소프트맥스

```python
def stable_softmax(logits):
    m = max(logits)
    exp_vals = [math.exp(x - m) for x in logits]
    total = sum(exp_vals)
    return [v / total for v in exp_vals]
```

### Loss Scaling (혼합 정밀도 훈련용)

float16에서 작은 기울기가 언더플로할 때: forward/backward를 float16으로 실행, loss에 scale_factor(예: 1024) 곱하기, backward로 확대된 기울기 생성, optimizer step 전에 기울기를 다시 축소.

### 기울기 검사

```python
def gradient_check(f, grad_f, x, h=1e-5):
    numerical = (f(x + h) - f(x - h)) / (2 * h)
    analytical = grad_f(x)
    diff = abs(numerical - analytical)
    return diff < 1e-4  # 또는 상대 오차 사용
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 오버플로 | 표현 가능한 최댓값 초과 → inf |
| 언더플로 | 표현 가능한 최솟값 미만 → 0 |
| 파국적 소거 | 비슷한 값 뺄셈 시 유효 숫자 손실 |
| 로그-합-지수 | softmax/log-sum-exp의 표준 안정화 트릭 |
| Loss scaling | 혼합 정밀도에서 기울기 언더플로 방지 |
| bfloat16 | float32 범위 + float16 크기 — 훈련에 최적화됨 |