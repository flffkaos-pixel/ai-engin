# 관계 추출 및 지식 그래프 구축

> NER이 개체를 찾았다. 개체 연결이 고정했다. 관계 추출이 개체 간의 엣지를 찾는다. 지식 그래프는 노드, 엣지 및 출처의 합이다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 06 (NER), Phase 5 · 25 (Entity Linking)
**Time:** ~60분

## 문제

분석가가 "Tim Cook became CEO of Apple in 2011"을 읽는다. 네 가지 사실:

- `(Tim Cook, role, CEO)`
- `(Tim Cook, employer, Apple)`
- `(Tim Cook, start_date, 2011)`
- `(Apple, type, Organization)`

관계 추출(RE)은 자유 텍스트를 구조화된 트리플 `(subject, relation, object)`로 변환한다.

## 개념

**트리플 형식.** `(주어_개체, 관계_유형, 목적어_개체)`.

**세 가지 추출 접근법.**

1. **규칙/패턴 기반.** Hearst 패턴 등.
2. **지도 분류기.** 고정 집합에서 관계 예측.
3. **생성형 LLM.** 트리플을 방출하도록 프롬프트.

## 직접 구현하기

## 사용하기

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tok = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")

text = "Tim Cook was born in Alabama. He later became CEO of Apple."
encoded = tok(text, return_tensors="pt", truncation=True)
output = model.generate(**encoded, max_length=200)
triples = tok.batch_decode(output, skip_special_tokens=False)
```

## 최종 결과물

`outputs/skill-re-designer.md`로 저장:

```markdown
---
name: re-designer
description: 출처 및 정규화를 포함한 관계 추출 파이프라인을 설계한다.
version: 1.0.0
phase: 5
lesson: 26
tags: [nlp, relation-extraction, knowledge-graph]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Triple | (s, r, o) 튜플. KG의 원자 단위. |
| Open IE | 개방 어휘 관계 구문. 높은 재현율, 낮은 정밀도. |
| Closed ontology | 고정 스키마. 제한된 관계 유형 집합. |
| Canonicalization | 표면 이름/관계를 정규 ID로 매핑. |
| AEVS | 근거 추출 파이프라인. |
| Provenance | 각 트리플이 소스에 대한 문서 ID + 문자 범위를 가짐. |

## 추가 자료

- [Mintz et al. (2009). Distant supervision for RE](https://www.aclweb.org/anthology/P09-1113.pdf)
- [Huguet Cabot, Navigli (2021). REBEL](https://aclanthology.org/2021.findings-emnlp.204.pdf)
- [Wadden et al. (2019). DyGIE++](https://arxiv.org/abs/1909.03546)
- [Wikidata SPARQL tutorial](https://www.wikidata.org/wiki/Wikidata:SPARQL_tutorial)
