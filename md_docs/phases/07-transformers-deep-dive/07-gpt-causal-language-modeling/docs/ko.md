# GPT & 인과적 언어 모델링

> 자기회귀: 이전 토큰 → 다음 토큰 예측. 생성의 기초.

**유형:** 빌드 | **언어:** Python | **시간:** ~90min

## 개념
- CLM: P(tokenₙ | token₀...tokenₙ₋₁)
- Masked Self-Attention: 미래 토큰 차단
- 확장 법칙: 더 큰 모델+데이터 = 더 좋은 성능
- GPT-1 → GPT-4: 스케일링의 승리