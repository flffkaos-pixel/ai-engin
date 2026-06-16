# 서브워드 토큰화 — BPE, WordPiece, Unigram, SentencePiece

> 단어 토크나이저는 본 적 없는 단어에 질식한다. 문자 토크나이저는 시퀀스 길이를 폭발시킨다. 서브워드 토크나이저는 그 중간을 택한다. 모든 현대 LLM은 그 위에서 배송된다.

**Type:** Learn
**Languages:** Python
**Prerequisites:** Phase 5 · 01 (Text Processing), Phase 5 · 04 (GloVe / FastText / Subword)
**Time:** ~60분

## 문제

어휘에 50,000개의 단어가 있다. 사용자가 "untokenizable"을 입력한다. 토크나이저가 `[UNK]`를 반환한다. 모델은 이제 단어에 대한 신호가 없다.

서브워드 토크나이저는 이것을 해결한다. 흔한 단어는 단일 토큰으로 남는다. 드문 단어는 의미 있는 조각으로 분해된다: `untokenizable` → `un`, `token`, `izable`.

## 개념

**BPE (Byte-Pair Encoding).** 문자 수준 어휘로 시작. 모든 인접 쌍을 카운트. 가장 빈번한 쌍을 새 토큰으로 병합. 반복.

**Byte-level BPE.** 유니코드 대신 원시 바이트(256개 기본 토큰)에 동일한 알고리즘 적용.

**Unigram.** 거대한 어휘로 시작. 각 토큰에 unigram 확률 할당. 제거 시 말뭉치 로그 우도 감소가 가장 작은 토큰을 반복적으로 제거.

**WordPiece.** 원시 빈도 대신 학습 말뭉치의 우도를 최대화하는 쌍 병합.

## 직접 구현하기

## 사용하기

```python
import tiktoken
enc = tiktoken.get_encoding("o200k_base")
print(enc.encode("untokenizable"))
print(len(enc.encode("Hello, world!")))
```

## 최종 결과물

`outputs/skill-bpe-vs-wordpiece.md`로 저장:

```markdown
---
name: tokenizer-picker
description: 주어진 말뭉치와 배포 대상에 대한 토크나이저 알고리즘, 어휘 크기, 라이브러리를 선택한다.
version: 1.0.0
phase: 5
lesson: 19
tags: [nlp, tokenization]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| BPE | Byte-Pair Encoding. 가장 빈번한 문자 쌍의 탐욕적 병합. |
| Byte-level BPE | 원시 256바이트에 대한 BPE. |
| Unigram | 대규모 후보 집합에서 로그 우도로 가지치기. |
| SentencePiece | 공백을 `▁`로 인코딩하는 라이브러리. |
| tiktoken | OpenAI의 Rust 기반 BPE 인코더. |
| Character coverage | 토크나이저가 커버해야 하는 문자 비율. |

## 추가 자료

- [Sennrich, Haddow, Birch (2015). Neural MT of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909)
- [Kudo (2018). Subword Regularization](https://arxiv.org/abs/1804.10959)
- [Kudo, Richardson (2018). SentencePiece](https://arxiv.org/abs/1808.06226)
- [Hugging Face — Tokenizer summary](https://huggingface.co/docs/transformers/tokenizer_summary)
- [OpenAI tiktoken](https://github.com/openai/tiktoken)
