# 다국어 NLP

> 하나의 모델, 100개 이상의 언어, 대부분에 대해 학습 데이터는 0. 교차 언어 전이는 2020년대의 실용적 기적이다.

**Type:** Learn
**Languages:** Python
**Prerequisites:** Phase 5 · 04 (GloVe, FastText, Subword), Phase 5 · 11 (Machine Translation)
**Time:** ~45분

## 문제

영어에는 수십억 개의 레이블된 예제가 있다. 우르두어에는 수천 개가 있다. 마이틸리어에는 거의 없다. 글로벌 사용자를 서비스하는 실용적인 NLP 시스템은 작업별 학습 데이터가 없는 긴 꼬리 언어에서도 작동해야 한다.

다국어 모델은 많은 언어를 동시에 하나의 모델로 학습시켜 이 문제를 해결한다. 공유 표현을 통해 모델이 고자원 언어에서 학습한 기술을 저자원 언어로 전이할 수 있다.

## 개념

**공유 어휘.** 다국어 모델은 모든 대상 언어의 텍스트로 학습된 SentencePiece 또는 WordPiece 토크나이저를 사용한다.

**공유 표현.** 마스크 언어 모델링으로 사전 학습된 트랜스포머는 의미적으로 유사한 문장이 유사한 은닉 상태를 생성함을 학습한다.

**제로샷 전이.** 한 언어(보통 영어)의 레이블된 데이터로 모델을 미세 조정하고 지원되는 다른 언어에서 실행한다.

**퓨샷 미세 조정.** 대상 언어에 100-500개의 레이블된 예제를 추가한다.

## 직접 구현하기

## 사용하기

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tok = AutoTokenizer.from_pretrained("joeddav/xlm-roberta-large-xnli")
model = AutoModelForSequenceClassification.from_pretrained("joeddav/xlm-roberta-large-xnli")

def classify(text, candidate_labels, hypothesis_template="This text is about {}."):
    scores = {}
    for label in candidate_labels:
        hypothesis = hypothesis_template.format(label)
        inputs = tok(text, hypothesis, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = model(**inputs).logits[0]
        entail_score = torch.softmax(logits, dim=-1)[2].item()
        scores[label] = entail_score
    return dict(sorted(scores.items(), key=lambda x: -x[1]))
```

## 최종 결과물

`outputs/skill-multilingual-picker.md`로 저장:

```markdown
---
name: multilingual-picker
description: 다국어 NLP 작업을 위한 소스 언어, 대상 모델 및 평가 계획을 선택한다.
version: 1.0.0
phase: 5
lesson: 18
tags: [nlp, multilingual, cross-lingual]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Multilingual model | 하나의 모델, 여러 언어. 공유 어휘 및 파라미터. |
| Cross-lingual transfer | 한 언어로 학습, 다른 언어에서 실행. |
| Zero-shot | 대상 언어 레이블 없음. |
| Few-shot | 100-500개의 대상 언어 예제. |
| mBERT | 최초의 다국어 LM. 104개 언어. |
| XLM-R | 표준 교차 언어 기준선. 100개 언어. |
| NLLB | Meta의 200언어 기계 번역. |

## 추가 자료

- [Conneau et al. (2019). XLM-R](https://arxiv.org/abs/1911.02116)
- [Pires, Schlinger, Garrette (2019). How Multilingual is Multilingual BERT?](https://arxiv.org/abs/1906.01502)
- [Costa-jussà et al. (2022). No Language Left Behind](https://arxiv.org/abs/2207.04672)
- [Üstün et al. (2024). Aya Model](https://arxiv.org/abs/2402.07827)
