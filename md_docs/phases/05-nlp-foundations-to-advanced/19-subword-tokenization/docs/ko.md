# 서브워드 토큰화

> BPE, WordPiece, Unigram. OOV 없는 토큰화.

**유형:** 빌드 | **언어:** Python | **시간:** ~75min

## 개념
- BPE: 가장 흔한 문자 쌍 반복 병합
- WordPiece: BPE + 확률 기반 선택
- SentencePiece: 언어 독립적 — 공백도 토큰
- Unigram: 확률적 LM으로 서브워드 선택