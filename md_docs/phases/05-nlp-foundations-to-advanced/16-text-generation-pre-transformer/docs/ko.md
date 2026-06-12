# 텍스트 생성 (Transformer 이전)

> Markov 체인 → RNN 언어 모델 → GPT로 가는 길.

**유형:** 빌드 | **언어:** Python | **시간:** ~60min

## 개념
- N-gram: P(w|이전 N-1개 단어) — 희소성 문제
- RNN LM: 은닉 상태로 무제한 문맥 — 기울기 소실
- Temperature: 높음=다양성, 낮음=결정적
- Top-k/Top-p: 확률 기반 샘플링 제어