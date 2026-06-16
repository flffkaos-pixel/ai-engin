# 상호참조 해결

> "그녀가 그를 불렀다. 그는 응답하지 않았다. 의사는 점심 중이었다." 두 사람에 대한 세 개의 참조, 아무도 이름이 없다. 상호참조 해결이 누가 누군지 알아낸다.

**Type:** Learn
**Languages:** Python
**Prerequisites:** Phase 5 · 06 (NER), Phase 5 · 07 (POS & Parsing)
**Time:** ~60분

## 문제

300단어 기사에서 Apple Inc.에 대한 모든 언급을 추출하라. 기사가 "Apple"이라고 말할 때는 쉽다. "the company", "they", "Cupertino's technology giant", "Jobs's firm"이라고 말할 때는 어렵다.

상호참조 해결은 동일한 실제 개체를 가리키는 모든 표현을 하나의 클러스터로 연결한다.

## 개념

**작업.** 입력: 문서. 출력: 각 클러스터가 하나의 개체를 가리키는 언급(범위)의 클러스터링.

**언급 유형.** 개체명, 명사구, 대명사, 동격.

**아키텍처.** 규칙 기반 → 언급-쌍 분류기 → 언급 순위 → 범위 기반 종단간 → 생성형.

## 직접 구현하기

## 사용하기

```python
import spacy
nlp = spacy.load("en_coreference_web_trf")
doc = nlp("Apple announced new products. The company said they would ship soon.")
for cluster in doc._.coref_clusters:
    print(cluster, "->", [m.text for m in cluster])
```

## 최종 결과물

`outputs/skill-coref-picker.md`로 저장:

```markdown
---
name: coref-picker
description: 상호참조 접근법, 평가 계획 및 통합 전략을 선택한다.
version: 1.0.0
phase: 5
lesson: 24
tags: [nlp, coref, information-extraction]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Mention | 개체를 가리키는 텍스트 범위. |
| Antecedent | "그것"이 가리키는 것. |
| Cluster | 동일한 실제 개체를 가리키는 모든 언급 집합. |
| Anaphora | 뒤쪽 참조. |
| Cataphora | 앞쪽 참조. |
| Bridging | 암시적 참조. |
| CoNLL F1 | MUC, B³, CEAF-φ4 F1 점수의 평균. |

## 추가 자료

- [Jurafsky & Martin, SLP3 Ch. 26](https://web.stanford.edu/~jurafsky/slp3/26.pdf)
- [Lee et al. (2017). End-to-end Neural Coreference](https://arxiv.org/abs/1707.07045)
- [Joshi et al. (2020). SpanBERT](https://arxiv.org/abs/1907.10529)
- [Pradhan et al. (2012). CoNLL-2012 Shared Task](https://aclanthology.org/W12-4501/)
- [Hobbs (1978). Resolving Pronoun References](https://www.sciencedirect.com/science/article/pii/0024384178900064)
