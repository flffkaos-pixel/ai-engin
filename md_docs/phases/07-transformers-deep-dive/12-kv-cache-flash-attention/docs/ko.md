# KV 캐시 & Flash Attention

> 더 빠른 추론, 더 적은 메모리.

**유형:** 빌드 | **시간:** ~75min

## 개념
- KV 캐시: 이전 토큰의 Key/Value 저장 → 재계산 방지
- Flash Attention: 타일링 + 재계산 → 메모리 접근 최적화
- Page Attention: KV 캐시를 페이지로 관리 → 긴 시퀀스 효율적