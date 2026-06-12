# 어텐션 변형

> Multi-Query, Grouped-Query, Sliding Window.

**유형:** 학습 | **시간:** ~45min

## 개념
- MQA: 모든 헤드가 하나의 K,V 공유 → KV 캐시 감소
- GQA: MHA와 MQA 사이 — 그룹별 K,V 공유
- Sliding Window: 지역적 Attention — 긴 시퀀스용