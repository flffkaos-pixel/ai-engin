# 완전한 트랜스포머

> Attention + FFN + 잔차 + LayerNorm. 인코더/디코더 조합.

**유형:** 빌드 | **언어:** Python | **시간:** ~120min

## 아키텍처
- 인코더: Self-Attention + FFN (양방향)
- 디코더: Masked Self-Attention + Cross-Attention + FFN (자기회귀)
- 잔차 연결 + LayerNorm: 안정적 훈련
- 인코더 전용: BERT / 디코더 전용: GPT