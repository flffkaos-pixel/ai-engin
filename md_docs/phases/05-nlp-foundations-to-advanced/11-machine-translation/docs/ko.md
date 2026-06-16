# 기계 번역

> 번역은 30년 동안 NLP 연구에 자금을 댄 작업이며 지금도 계속되고 있다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 10 (Attention Mechanism), Phase 5 · 04 (GloVe, FastText, Subword)
**Time:** ~75분

## 문제

모델이 한 언어의 문장을 읽고 다른 언어의 문장을 생성한다. 길이가 다르다. 어순이 다르다. 일부 소스 단어는 여러 대상 단어에 매핑되고 그 반대도 마찬가지다. 관용구는 일대일 매핑을 거부한다.

기계 번역은 NLP가 인코더-디코더, 어텐션, 트랜스포머, 그리고 결국 전체 LLM 패러다임을 발명하도록 강제한 작업이다. 모든 진전은 번역 품질이 측정 가능했고 인간과 기계의 격차가 고집스러웠기 때문에 이루어졌다.

## 개념

현대 MT는 병렬 텍스트로 학습된 트랜스포머 인코더-디코더다. 인코더는 소스를 해당 언어의 토큰화로 읽는다. 디코더는 교차 어텐션을 사용하여 인코더의 출력에서 한 서브워드씩 대상을 생성한다. 디코딩은 빔 탐색을 사용한다. 출력은 디토큰화되고 점수가 계산된다.

## 직접 구현하기

## 사용하기

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_id = "facebook/nllb-200-distilled-600M"
tok = AutoTokenizer.from_pretrained(model_id, src_lang="eng_Latn")
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

src = "The cats are running."
inputs = tok(src, return_tensors="pt")
out = model.generate(**inputs, forced_bos_token_id=tok.convert_tokens_to_ids("fra_Latn"), num_beams=5)
print(tok.batch_decode(out, skip_special_tokens=True)[0])
```

## 최종 결과물

`outputs/skill-mt-evaluator.md`로 저장:

```markdown
---
name: mt-evaluator
description: 기계 번역 출력을 평가하여 배포 준비 상태를 확인한다.
version: 1.0.0
phase: 5
lesson: 11
tags: [nlp, translation, evaluation]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| BLEU | 번역 점수. N-그램 정밀도 + brevity 패널티. [0, 100]. |
| chrF | 문자 F-점수. 형태론적으로 풍부한 언어에 더 민감. |
| NMT | 신경망 기계 번역. |
| NLLB | No Language Left Behind, Meta의 200언어 MT 모델군. |
| Constrained decoding | 제약 디코딩. 출력에 특정 토큰 강제. |
| Hallucination | 환각. 소스에 없는 내용 생성. |

## 추가 자료

- [Costa-jussà et al. (2022). No Language Left Behind](https://arxiv.org/abs/2207.04672)
- [Post (2018). A Call for Clarity in Reporting BLEU Scores](https://aclanthology.org/W18-6319/)
- [Popović (2015). chrF](https://aclanthology.org/W15-3049/)
- [Hugging Face MT guide](https://huggingface.co/docs/transformers/tasks/translation)
