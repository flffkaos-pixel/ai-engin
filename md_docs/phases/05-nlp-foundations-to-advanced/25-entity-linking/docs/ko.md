# 개체 연결 및 명확화

> NER이 "Paris"를 찾았다. 개체 연결이 결정한다: Paris, France? Paris Hilton? Paris, Texas? Paris (트로이 왕자)? 연결 없이는 지식 그래프가 모호하게 남는다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 06 (NER), Phase 5 · 24 (Coreference Resolution)
**Time:** ~60분

## 문제

문장이 "Jordan beat the press"라고 말한다. NER이 "Jordan"을 PERSON으로 태그한다. 좋다. 하지만 *어떤* Jordan인가?

개체 연결(EL)은 각 언급을 지식 베이스의 고유 항목으로 해결한다. 두 가지 하위 작업:

1. **후보 생성.** "Jordan"이 주어지면 어떤 KB 항목이 그럴듯한가?
2. **명확화.** 컨텍스트가 주어지면 어떤 후보가 올바른가?

## 개념

**후보 생성.** 언급 표면 형태("Jordan")가 주어지면 별칭 색인에서 후보를 조회한다.

**명확화: 세 가지 접근법.**

1. **사전 + 컨텍스트 (Milne & Witten, 2008).**
2. **임베딩 기반 (ESS / REL / Blink).**
3. **생성형 (GENRE, 2021; LLM 기반, 2023+).**

## 직접 구현하기

## 사용하기

```python
from sentence_transformers import SentenceTransformer

encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_mention(text, mention_span):
    start, end = mention_span
    marked = f"{text[:start]} [MENTION] {text[start:end]} [/MENTION] {text[end:]}"
    return encoder.encode([marked], normalize_embeddings=True)[0]

def embed_entity(entity_id, description):
    return encoder.encode([f"{entity_id}: {description}"], normalize_embeddings=True)[0]
```

## 최종 결과물

`outputs/skill-entity-linker.md`로 저장:

```markdown
---
name: entity-linker
description: 개체 연결 파이프라인을 설계한다 — KB, 후보 생성기, 명확화, 평가.
version: 1.0.0
phase: 5
lesson: 25
tags: [nlp, entity-linking, knowledge-graph]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Entity linking (EL) | 언급을 고유한 KB 항목에 매핑. |
| Candidate generation | 언급에 대한 그럴듯한 KB 항목의 후보 목록 반환. |
| Disambiguation | 컨텍스트를 사용하여 후보 점수 계산, 승자 선택. |
| Alias index | 표면 형태 → 후보 개체 매핑. |
| NIL | KB에 없음. |
| KB | 지식 베이스. |
| AIDA-CoNLL | 표준 EL 벤치마크. |

## 추가 자료

- [Milne, Witten (2008). Learning to Link with Wikipedia](https://www.cs.waikato.ac.nz/~ihw/papers/08-DM-IHW-LearningToLinkWithWikipedia.pdf)
- [Wu et al. (2020). Zero-shot Entity Linking (BLINK)](https://arxiv.org/abs/1911.03814)
- [De Cao et al. (2021). Autoregressive Entity Retrieval (GENRE)](https://arxiv.org/abs/2010.00904)
- [Hoffart et al. (2011). Robust Disambiguation (AIDA)](https://www.aclweb.org/anthology/D11-1072.pdf)
- [REL: An Entity Linker (2020)](https://arxiv.org/abs/2006.01969)
