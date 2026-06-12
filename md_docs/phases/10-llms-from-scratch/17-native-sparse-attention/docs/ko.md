# Native Sparse Attention

> 전체 Attention 대신 중요한 토큰만. 긴 시퀀스에 효율적.

**유형:** 학습 | **시간:** ~45min

## 개념
- Sparse Attention: 모든 토큰 간 Attention X
- Sliding Window + 선택적 전역 토큰
- 계산량 O(n²)→O(n·window) 감소