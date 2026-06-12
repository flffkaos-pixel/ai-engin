# 기계 번역

> Seq2Seq + Attention. BLEU 점수로 평가.

**유형:** 빌드 | **언어:** Python | **시간:** ~90분

## 개념
- 병렬 코퍼스: 쌍을 이룬 번역문
- BPE 토크나이저: 희귀 단어 처리
- BLEU: n-gram 정밀도 기반 — 참조와의 유사도

## 빌드
```python
from transformers import MarianMTModel, MarianTokenizer
model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-ko-en")
```