# GloVe, fastText & 서브워드

> GloVe: 전역 통계 활용. fastText: 문자 n-gram → OOV 처리.

**유형:** 빌드 | **언어:** Python | **시간:** ~60분

## 개념
- GloVe: 동시발생 행렬 분해 → Word2Vec보다 전역 정보 활용
- fastText: 단어를 문자 n-gram의 합으로 표현 → 오타/신조어도 처리
- Byte-Pair Encoding: 가장 흔한 문자 쌍 병합 → 서브워드 분할