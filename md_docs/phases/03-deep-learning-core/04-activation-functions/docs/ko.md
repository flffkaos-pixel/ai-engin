# 활성화 함수

> 비선형성이 없으면 100층 네트워크도 fancy 행렬 곱일 뿐입니다. 활성화 함수는 신경망이 곡선으로 생각하게 하는 게이트입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Lesson 03.03
**시간:** ~75분

## 학습 목표

- 시그모이드, tanh, ReLU, Leaky ReLU, GELU, Swish, 소프트맥스와 미분을 처음부터 구현
- 다양한 활성화 함수로 10개 이상 레이어에서 활성화 크기 측정, 기울기 소실 진단
- ReLU 네트워크의 죽은 뉴런 감지, GELU가 이 실패 모드를 피하는 이유 설명
- 주어진 아키텍처(트랜스포머, CNN, RNN, 출력 레이어)에 적합한 활성화 함수 선택

## 개념

### 주요 활성화 함수

| 함수 | 공식 | 미분 | 용도 |
|------|------|------|------|
| Sigmoid | 1/(1+e⁻ˣ) | σ(1-σ) | 이진 출력, 게이트 |
| Tanh | (eˣ-e⁻ˣ)/(eˣ+e⁻ˣ) | 1-tanh² | RNN 은닉 상태 |
| ReLU | max(0,x) | 0 if x<0 else 1 | CNN, MLP 기본값 |
| Leaky ReLU | max(0.01x, x) | 0.01 if x<0 else 1 | 죽은 ReLU 방지 |
| GELU | x·Φ(x) | 복잡 | Transformer (GPT, BERT) |
| Swish | x·σ(x) | 복잡 | EfficientNet |
| Softmax | eˣ/Σeˣ | 복잡 | 다중 클래스 출력 |

### 죽은 ReLU 문제

ReLU: x<0 → 출력 0, 기울기 0. 음수 영역에 빠진 뉴런 = 영원히 0. Leaky ReLU와 GELU가 음수 영역에서 작은 기울기 허용 → 방지.

### 아키텍처별 선택

| 아키텍처 | 은닉층 | 출력층 |
|---------|--------|--------|
| MLP/CNN | ReLU | Softmax/Sigmoid |
| Transformer | GELU | Softmax |
| RNN/LSTM | Tanh | Softmax |
| 회귀 | ReLU | Linear |

## 빌드하기

```python
def relu(x): return np.maximum(0, x)
def relu_deriv(x): return (x > 0).astype(float)

def sigmoid(x):
    s = 1/(1+np.exp(-np.clip(x, -500, 500)))
    return s
def sigmoid_deriv(x):
    s = sigmoid(x); return s * (1 - s)

def softmax(x):
    e = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| ReLU | 단순/빠름 — 죽은 뉴런 위험 |
| GELU | 부드러운 ReLU — Transformer 표준 |
| 죽은 ReLU | 영원히 0 출력 — Leaky/GELU로 해결 |
| 소프트맥스 | 로짓 → 확률 — 분류 출력 |