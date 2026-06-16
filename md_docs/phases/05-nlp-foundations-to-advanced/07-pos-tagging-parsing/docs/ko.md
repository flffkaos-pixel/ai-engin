# 품사 태깅 및 구문 분석

> 문법은 한동안 유행에서 밀려났다. 그러다 모든 LLM 파이프라인이 구조화 추출을 검증해야 하게 되면서 돌아왔다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 01 (Text Processing), Phase 2 · 14 (Naive Bayes)
**Time:** ~45분

## 문제

레슨 01은 표제어 추출이 품사 태그가 필요하다고 약속했다. `running`이 동사라는 것을 모르면 표제어 추출기가 `run`으로 줄일 수 없다. `better`가 형용사임을 모르면 `good`으로 줄일 수 없다.

품사 태깅은 문법 범주를 할당한다. 구문 분석은 문장의 트리 구조를 복원한다: 어떤 단어가 어떤 단어를 수식하는지, 어떤 동사가 어떤 인수를 지배하는지.

알아둘 가치가 있다. 이 레슨은 태그셋, 기준선, 그리고 spaCy를 호출하는 지점을 소개한다.

## 개념

**POS 태깅**은 각 토큰에 문법 범주를 레이블링한다. **Penn Treebank (PTB)** 태그셋이 영어 기본값이다. 36개 태그. **Universal Dependencies (UD)** 태그셋은 더 거칠고(17개 태그) 언어에 구애받지 않는다.

**구문 분석**은 트리를 생성한다. 두 가지 주요 스타일:
- **구성소 분석.** 명사구, 동사구, 전치사구가 서로 중첩.
- **의존 구문 분석.** 각 단어는 의존하는 하나의 헤드 단어가 있음.

## 직접 구현하기

## 사용하기

모든 프로덕션 NLP 라이브러리는 표준 파이프라인의 일부로 POS 및 의존 구문 분석기를 제공한다.

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("The cats were running at 3pm.")
for token in doc:
    print(f"{token.text:10s} tag={token.tag_:5s} pos={token.pos_:6s} dep={token.dep_:10s} head={token.head.text}")
```

## 최종 결과물

`outputs/skill-grammar-pipeline.md`로 저장:

```markdown
---
name: grammar-pipeline
description: 다운스트림 NLP 작업을 위한 고전적 POS + 의존 파이프라인을 설계한다.
version: 1.0.0
phase: 5
lesson: 07
tags: [nlp, pos, parsing]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| POS tag | 단어의 유형. PTB 36개, UD 17개. |
| Penn Treebank | 표준 태그셋. 영어 특화. |
| Universal Dependencies | 다국어 태그셋. 언어 중립. |
| Dependency parse | 문장 트리. 각 단어는 하나의 헤드. |
| Viterbi | 동적 프로그래밍, 최고 확률 태그 시퀀스 탐색. |

## 추가 자료

- [Jurafsky and Martin — Speech and Language Processing](https://web.stanford.edu/~jurafsky/slp3/)
- [Universal Dependencies project](https://universaldependencies.org/)
- [spaCy linguistic features](https://spacy.io/usage/linguistic-features)
- [Chen and Manning (2014). A Fast and Accurate Dependency Parser](https://nlp.stanford.edu/pubs/emnlp2014-depparser.pdf)
