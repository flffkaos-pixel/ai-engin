# 토크나이저 구축

> BPE 처음부터 구현. 어휘 병합.

**유형:** 빌드 | **시간:** ~90min

## 빌드
- 말뭉치 전처리→바이트 시퀀스
- 가장 흔한 쌍 반복 병합
- 어휘 사전 구축→인코딩/디코딩

## 핵심
```python
while len(vocab) < target:
    pair = most_frequent_pair(tokens)
    tokens = merge(tokens, pair)
```