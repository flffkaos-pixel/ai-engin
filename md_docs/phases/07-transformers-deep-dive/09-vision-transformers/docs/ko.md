# 비전 트랜스포머 (ViT)

> 이미지를 패치로, Transformer로 처리.

**유형:** 빌드 | **시간:** ~60min

## 개념
- 이미지 → 16x16 패치 → 선형 투영 → 토큰
- CLS 토큰 + 위치 임베딩 → Transformer
- CNN 없는 순수 Attention — 대규모 데이터에서 우수