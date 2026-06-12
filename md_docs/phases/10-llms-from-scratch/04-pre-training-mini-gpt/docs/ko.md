# 사전훈련 — Mini-GPT

> GPT 아키텍처 처음부터 구현. 작은 규모로 훈련.

**유형:** 빌드 | **시간:** ~150min

## 구현
- Transformer 디코더: masked self-attention+FFN
- 토큰 임베딩+위치 임베딩
- LayerNorm+잔차 연결
- 작은 말뭉치로 훈련 테스트
- Andrej Karpathy의 nanoGPT 참고