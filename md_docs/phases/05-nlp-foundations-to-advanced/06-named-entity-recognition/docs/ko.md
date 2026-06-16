# 개체명 인식

> 이름을 추출하라. 모호한 경계, 중첩 개체, 도메인 전문 용어를 다루기 전까지는 쉬워 보인다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 02 (BoW + TF-IDF), Phase 5 · 03 (Word Embeddings)
**Time:** ~75분

## 문제

"Apple sued Google over its iPhone search deal in the US." 다섯 개체: Apple (ORG), Google (ORG), iPhone (PRODUCT), search deal (maybe), US (GPE). 좋은 NER 시스템은 이 모두를 올바른 유형으로 추출한다. 나쁜 시스템은 iPhone을 놓치고, Apple을 과일과 회사로 혼동하며, "US"를 PERSON으로 레이블링한다.

NER은 모든 구조화 추출 파이프라인의 핵심이다. 이력서 파싱, 규정 준수 로그 스캐닝, 의료 기록 익명화, 검색 쿼리 이해, 챗봇 응답 접지, 법률 계약 추출. 눈에 띄지 않지만 항상 의존한다.

## 개념

**BIO 태깅**(또는 BILOU)은 개체 추출을 시퀀스 레이블링 문제로 변환한다. 각 토큰에 `B-TYPE`(개체 시작), `I-TYPE`(개체 내부), `O`(개체 외부) 레이블을 붙인다.

아키텍처 발전:
- **규칙 기반.** 정규식 + 사전 조회. 알려진 개체는 높은 정밀도, 새 개체는 적용 범위 0.
- **HMM.** 은닉 마르코프 모델. Viterbi 디코딩.
- **CRF.** 조건부 확률장. 판별적, 임의 특징 혼합 가능.
- **BiLSTM-CRF.** 신경망 특징. LSTM이 양방향으로 문장을 읽고 CRF가 태그 시퀀스 일관성 강제.
- **트랜스포머 기반.** BERT 미세 조정. 최고 정확도, 최대 계산량.

## 직접 구현하기

## 사용하기

spaCy가 프로덕션 등급 NER을 제공한다.

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("Apple sued Google over its iPhone search deal in the US.")
for ent in doc.ents:
    print(f"{ent.text:20s} {ent.label_}")
```

## 최종 결과물

`outputs/skill-ner-picker.md`로 저장:

```markdown
---
name: ner-picker
description: 주어진 추출 작업에 적합한 NER 접근 방식을 선택한다.
version: 1.0.0
phase: 5
lesson: 06
tags: [nlp, ner, extraction]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| NER | 개체명 인식 |
| BIO | 태깅 체계: B-X 시작, I-X 계속, O 외부 |
| BILOU | 개선된 BIO: L-X 마지막, U-X 단일 |
| CRF | 구조화 분류기, 레이블 간 전이 모델링 |
| Nested NER | 중첩 개체, BIO로 표현 불가 |
| Entity-level F1 | 예측된 범위가 실제 범위와 정확히 일치해야 함 |

## 추가 자료

- [Lample et al. (2016). Neural Architectures for Named Entity Recognition](https://arxiv.org/abs/1603.01360)
- [Devlin et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers](https://arxiv.org/abs/1810.04805)
- [spaCy linguistic features](https://spacy.io/usage/linguistic-features#named-entities)
- [seqeval](https://github.com/chakki-works/seqeval)
