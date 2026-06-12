# CNN & RNN을 텍스트에

> CNN: 지역적 패턴 (n-gram). RNN: 순차적 흐름.

**유형:** 빌드 | **언어:** Python | **시간:** ~75분

## 개념
- TextCNN: 1D 합성곱 → n-gram 특징 추출
- LSTM/GRU: 장기 의존성 포착, 기울기 소실 해결
- 양방향 RNN: 왼쪽+오른쪽 문맥

## LSTM vs GRU
| LSTM | 3개 게이트 (입력/망각/출력) |
| GRU | 2개 게이트 (리셋/업데이트) → 더 빠름 |