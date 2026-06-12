# 개체명 인식 (NER)

> 텍스트에서 사람, 장소, 조직 등 찾기.

**유형:** 빌드 | **언어:** Python | **시간:** ~75분

## 개념
- 시퀀스 레이블링: BIO 태깅 (Begin/Inside/Outside)
- CRF: 전이 확률로 일관성 유지
- BERT 기반: 최고 정확도

## 빌드
```python
from transformers import pipeline
ner = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03")
ner("Steve Jobs founded Apple in Cupertino.")
```