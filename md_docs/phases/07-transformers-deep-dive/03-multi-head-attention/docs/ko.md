# 멀티헤드 어텐션

> 하나의 어텐션 = 하나의 관점. 여러 개 = 풍부한 표현.

**유형:** 빌드 | **언어:** Python | **시간:** ~60min

## 개념
- 여러 Attention 헤드를 병렬로 → 각각 다른 관계 학습
- 헤드별로 Q,K,V를 저차원으로 투영 → 계산 효율적
- 출력 연결 → 선형 변환

## 빌드
```python
# 각 헤드: d_model → d_k, 별도 Attention → 연결 → d_model
heads = [attention(Q_i, K_i, V_i) for 8 heads]
output = concat(heads) @ W_o
```