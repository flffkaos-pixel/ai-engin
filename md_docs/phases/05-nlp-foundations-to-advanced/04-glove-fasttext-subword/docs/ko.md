# GloVe, FastText 및 서브워드 임베딩

> Word2Vec은 단어당 하나의 임베딩을 학습했다. GloVe는 동시 발생 행렬을 분해했다. FastText는 조각을 임베딩했다. BPE는 트랜스포머로 연결했다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 03 (Word2Vec from Scratch)
**Time:** ~45분

## 문제

Word2Vec은 두 가지 미해결 질문을 남겼다.

첫째, 온라인 skip-gram 업데이트 대신 동시 발생 행렬을 직접 분해하는 연구 흐름이 있었다(LSA, HAL). Word2Vec의 반복적 접근 방식이 근본적으로 더 나은가, 아니면 차이가 단지 두 방법이 카운트를 처리하는 방식의 차이인가? **GloVe**가 답했다: 신중하게 선택된 손실 함수를 가진 행렬 분해는 Word2Vec과 같거나 더 나은 성능을 내며 학습 비용이 더 적게 든다.

둘째, 어떤 방법도 본 적 없는 단어에 대한 대책이 없었다. **FastText**가 문자 n-그램을 임베딩하여 이 문제를 해결했다: 단어는 그 부분의 합이며, 어휘 외 단어도 의미 있는 벡터를 얻는다.

셋째, 트랜스포머가 도래하면서 질문이 다시 바뀌었다. **BPE(Byte-Pair Encoding)**와 그 변형들이 빈번한 서브워드 단위의 어휘를 학습하여 모든 것을 커버함으로써 이 문제를 해결했다.

## 개념

**GloVe (Global Vectors).** 단어-단어 동시 발생 행렬 `X`를 구축한다. `X[i][j]`는 단어 `i`의 맥락에서 단어 `j`가 등장한 횟수다. `v_i · v_j + b_i + b_j ≈ log(X[i][j])`가 되도록 벡터를 학습시킨다. 빈번한 쌍이 손실을 지배하지 않도록 가중치를 적용한다.

**FastText.** 단어는 문자 n-그램과 단어 자체의 합이다. `where`는 `<wh, whe, her, ere, re>, <where>`가 된다. 단어 벡터는 이러한 구성 요소 벡터의 합이다. Word2Vec처럼 학습시킨다. 장점: 본 적 없는 단어(`whereupon`)도 알려진 n-그램으로 구성된다.

**BPE (Byte-Pair Encoding).** 개별 바이트(또는 문자)의 어휘로 시작한다. 말뭉치의 모든 인접 쌍을 센다. 가장 빈번한 쌍을 새 토큰으로 병합한다. `k`번 반복한다. 결과: `k + 256`개의 토큰으로 구성된 어휘.

## 직접 구현하기

## 사용하기

실제로는 직접 학습시키는 경우가 드물다. 사전 학습된 체크포인트를 로드한다.

```python
import fasttext.util
fasttext.util.download_model("en", if_exists="ignore")
ft = fasttext.load_model("cc.en.300.bin")
print(ft.get_word_vector("whereupon").shape)
```

BPE 스타일 서브워드 토큰화:

```python
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("gpt2")
print(tok.tokenize("unbelievably tokenized"))
```

## 최종 결과물

`outputs/skill-embeddings-picker.md`로 저장:

```markdown
---
name: tokenizer-picker
description: 새 언어 모델 또는 텍스트 파이프라인을 위한 토큰화 방식을 선택한다.
version: 1.0.0
phase: 5
lesson: 04
tags: [nlp, tokenization, embeddings]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Co-occurrence matrix | 단어-단어 빈도 테이블 |
| Subword | 단어의 조각 |
| BPE | Byte-Pair Encoding, 가장 빈번한 인접 쌍의 반복적 병합 |
| OOV | 어휘 외 단어 |
| Byte-level BPE | 원시 바이트에 대한 BPE |

## 추가 자료

- [Pennington, Socher, Manning (2014). GloVe: Global Vectors for Word Representation](https://nlp.stanford.edu/pubs/glove.pdf)
- [Bojanowski et al. (2017). Enriching Word Vectors with Subword Information](https://arxiv.org/abs/1607.04606)
- [Sennrich, Haddow, Birch (2016). Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909)
- [Hugging Face tokenizer summary](https://huggingface.co/docs/transformers/tokenizer_summary)
