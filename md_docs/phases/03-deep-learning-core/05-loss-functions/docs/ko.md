# 손실 함수

> 손실 함수는 모델에게 "틀렸다"는 의미를 알려줍니다. 잘못된 것을 최적화하면 완벽하게 잘못된 모델을 얻습니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Lesson 03.03
**시간:** ~75분

## 개념

### 회귀 손실

- **MSE**: (1/n)Σ(ŷ-y)² — 큰 오차에 민감, 미분 가능
- **MAE**: (1/n)Σ|ŷ-y| — 이상치에 강건, 0에서 미분 불가
- **Huber**: MSE+MAE 하이브리드 — 작은 오차=MSE, 큰 오차=MAE

### 분류 손실

- **이진 교차 엔트로피**: `-[y log(p)+(1-y)log(1-p)]` — 로지스틱 회귀 표준
- **범주형 교차 엔트로피**: `-Σ y_k log(p_k)` — 다중 클래스 표준
- **힌지**: `max(0,1-y·ŷ)` — SVM, 마진 최대화

### 선택 가이드

| 문제 | 손실 함수 |
|------|----------|
| 회귀 (이상치 적음) | MSE |
| 회귀 (이상치 많음) | Huber |
| 이진 분류 | 이진 교차 엔트로피 |
| 다중 클래스 | 범주형 교차 엔트로피 |

## 빌드하기

```python
def mse(y_true, y_pred): return np.mean((y_pred - y_true)**2)
def mae(y_true, y_pred): return np.mean(np.abs(y_pred - y_true))
def bce(y_true, y_pred):
    eps = 1e-15
    return -np.mean(y_true*np.log(y_pred+eps) + (1-y_true)*np.log(1-y_pred+eps))
def cce(y_true, y_pred):
    return -np.mean(np.sum(y_true * np.log(y_pred + 1e-15), axis=1))
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| MSE | 제곱 오차 — 큰 오차 페널티 |
| 교차 엔트로피 | 확률 분포 차이 — 분류 표준 |
| Huber | MSE+MAE — 이상치 강건 |