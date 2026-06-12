# Self-Attention 처음부터 구현

> Q·K^T/√d → softmax → × V. 시퀀스 내 토큰 관계 계산.

**유형:** 빌드 | **언어:** Python | **시간:** ~90min

## 개념
- Q, K, V: 모두 입력의 선형 변환
- Attention 맵: 각 토큰이 다른 토큰에 주는 가중치
- √d 스케일링: 큰 차원에서 softmax 포화 방지

## 빌드
```python
def self_attention(Q, K, V):
    d_k = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)
    weights = softmax(scores, axis=-1)
    return weights @ V
```