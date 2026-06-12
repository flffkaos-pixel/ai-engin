# BERT — Masked Language Modeling

> GPT는 다음 단어를 예측한다. BERT는 누락된 단어를 예측한다. 한 문장의 차이가 — 반평생에 걸친 모든 임베딩 형태의 것들을 만들어냈다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 05 (Full Transformer), Phase 5 · 02 (Text Representation)
**소요 시간:** ~45분

## 문제

2018년에 모든 NLP 작업 — 감성, NER, QA, 내포 — 은 자체 레이블된 데이터에서 처음부터 자체 모델을 교육했다. Fine-tune할 수 있는 사전 훈련된 "영어 이해" 체크포인트가 없었다. ELMo (2018)는 양방향 LSTM으로 문맥 임베딩을 사전 훈련할 수 있음을 보여주었다; 그것은 도움이 됐지만 일반화하지 못했다.

BERT (Devlin et al. 2018)가 물었다: transformer encoder를 가져와서 인터넷의 모든 문장으로 교육하고, 양쪽에서上下文로부터 누락된 단어를 예측하도록 강제하면 어떻게 될까? 그런 다음下游 작업에 하나의 head만 fine-tune한다. 매개변수 효율성은 혁신적이었다.

결과: 18개월 내에 BERT와 그 변형 (RoBERTa, ALBERT, ELECTRA)은 존재하는 모든 NLP 리더보드를 지배했다. 2020년까지 지구상의 모든 검색 엔진, 콘텐츠 moderation 파이프라인 및 의미론적 검색 시스템에 BERT가 들어 있었다.

2026년 encoder-only 모델은 여전히 분류, 검색 및 구조화된 추출에 적합한 도구이다 — 토큰당 decoder보다 5–10× 빠르며 임베딩은 모든 현대 검색 스택의 백본이다. ModernBERT (2024년 12월)는 Flash Attention + RoPE + GeGLU로 아키텍처를 8K 컨텍스트로 확장했다.

## 개념

![Masked language modeling: 토큰 선택, 마스킹, 원본 예측](../assets/bert-mlm.svg)

### 교육 신호

문장을 가져온다: `the quick brown fox jumps over the lazy dog`.

15%의 토큰을 무작위로 마스킹한다:

```
input:  the [MASK] brown fox jumps [MASK] the lazy dog
target: the  quick brown fox jumps  over  the lazy dog
```

마스킹된 위치에서 원본 토큰을 예측하도록 모델을 교육한다. Encoder가 양방향이기 때문에, 위치 1에서 `[MASK]`를 예측할 때 위치 2+의 `brown fox jumps`를 사용할 수 있다. 이것이 GPT가 할 수 없는 것이다.

### BERT 마스킹 규칙

예측을 위해 선택된 15%의 토큰 중:

- 80%는 `[MASK]`로 대체된다.
- 10%는 무작위 토큰으로 대체된다.
- 10%는 변경되지 않고 그대로 둔다.

왜 항상 `[MASK]`가 아닌가? porque `[MASK]`는 추론 시점에 나타나지 않는다. 마스킹된 위치의 100%에서 `[MASK]`를 기대하도록 모델을 교육하면 사전 교육과 fine-tuning 사이에 분포 불일치가 발생한다. 10% 무작위 + 10% 변경 없음은 모델을 정직하게 유지한다.

### Next Sentence Prediction (NSP) — 그리고 왜 폐기되었는가

원래 BERT는 NSP에서도 교육했다: 두 문장 A와 B가 주어지면, B가 A 다음에 오는지 예측한다. RoBERTa (2019)는 그것을 없애고 NSP가 도움이 되는 것이 아니라 해로움을 보여주었다. Modern encoder는 그것을 건너뛴다.

### 2026년 무엇이 변경되었나: ModernBERT

2024년 ModernBERT 논문은 2026년 primitives로 블록을 재건했다:

| 구성 요소 | 원래 BERT (2018) | ModernBERT (2024) |
|-----------|----------------------|-------------------|
| Position | Learned absolute | RoPE |
| Activation | GELU | GeGLU |
| Normalization | LayerNorm | Pre-norm RMSNorm |
| Attention | Full dense | Alternating local (128) + global |
| Context length | 512 | 8192 |
| Tokenizer | WordPiece | BPE |

그리고 2018 스택과 달리, Flash-Attention-native이다. 시퀀스 길이 8K에서 DeBERTa-v3보다 GLUE 점수가 더 좋으면서 추론이 2–3× 빠르다.

### 2026년，仍然选择 encoder를 사용하는 사용 사례

| 작업 | Encoder가 decoder를 이기는 이유 |
|------|---------------------------|
| 검색 / 의미론적 검색 임베딩 | 양방향 컨텍스트 = 토큰당 더 나은 임베딩 품질 |
| 분류 (감성, 의도, 유해성) | 하나의 forward 통과; 생성 오버헤드 없음 |
| NER / 토큰 라벨링 | 위치별 출력, nativo 양방향 |
| 제로샷 내포 (NLI) | Encoder 위의 분류기 head |
| RAG용 리랭커 | Cross-encoder 스코어링, LLM 리랭커보다 10x 빠름 |

## 실습

### Step 1: 마스킹 로직

`code/main.py`를 참조. 함수 `create_mlm_batch`는 토큰 ID 목록, 어휘 크기, 마스킹 확률을 받는다. 입력 ID (마스킹 적용됨)와 레이블 (마스킹된 위치에서만, 나머지는 -100 — PyTorch의 ignore 인덱스 규칙)를 반환한다.

```python
def create_mlm_batch(tokens, vocab_size, mask_prob=0.15, rng=None):
    input_ids = list(tokens)
    labels = [-100] * len(tokens)
    for i, t in enumerate(tokens):
        if rng.random() < mask_prob:
            labels[i] = t
            r = rng.random()
            if r < 0.8:
                input_ids[i] = MASK_ID
            elif r < 0.9:
                input_ids[i] = rng.randrange(vocab_size)
            # else: 원본 유지
    return input_ids, labels
```

### Step 2: 작은 코퍼스에서 MLM 예측 실행

20개 단어 어휘, 200개 문장에서 2층 encoder + MLM head를 교육한다. Gradient 없음 — 우리는 forward-pass 정합성 검사를 한다. 완전한 교육에는 PyTorch가 필요하다.

### Step 3: 마스크 유형 비교

세 가지 방식 규칙이 `[MASK]` 없이도 모델을 사용 가능하게 유지하는 방법을 보여준다. 마스킹되지 않은 문장과 마스킹된 문장 모두에서 예측한다. 둘 다 합리적인 토큰 분포를 생성해야 한다 — 모델이 교육에서 두 패턴을 모두 보았기 때문이다.

### Step 4: head fine-tune

MLM head를 토이 감성 데이터 세트에서 분류 head로 교체한다. Head만 교육; encoder는 동결된다. 이것이 모든 BERT 애플리케이션이 따르는 패턴이다.

## 활용

```python
from transformers import AutoModel, AutoTokenizer

tok = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")
model = AutoModel.from_pretrained("answerdotai/ModernBERT-base")

text = "Attention is all you need."
inputs = tok(text, return_tensors="pt")
out = model(**inputs).last_hidden_state   # (1, N, 768)
```

**임베딩 모델은 fine-tuned BERT이다.** `all-MiniLM-L6-v2`와 같은 `sentence-transformers` 모델은 대조 손실로 훈련된 BERT이다. Encoder는 동일하다. 손실이 변경되었다.

**Cross-encoder 리랭커도 fine-tuned BERT이다.** `[CLS] query [SEP] doc [SEP]`에서 쌍 분류. Query와 doc 사이의 양방향 attention은 cross-encoder에 품질 에지를 주는 것이다 biencoders보다.

**2026년 BERT를 선택하지 말아야 할 때.** 생성적인 것은 무엇이든. Encoder는 자기회귀적으로 토큰을 생성할 방법이 없다. 또한: 작은 decoder가 더 나은 유연성으로 품질을 맞출 수 있는 1B 매개변수 미만 (Phi-3-Mini, Qwen2-1.5B).

## 결과물

`outputs/skill-bert-finetuner.md`를 참조. 이 skill은 새 분류 또는 추출 작업에 대한 BERT fine-tune (백본 선택, head 사양, 데이터, 평가, 중지)을 범위화한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하고 10,000개 토큰에서 마스킹 분포를 인쇄한다. ~15%가 선택되고, 그 중 ~80%가 `[MASK]`가 되는지 확인한다.
2. **보통.** Whole-word masking 구현: 단어가 하위 단어로 토큰화되는 경우, 모든 하위 단어를 함께 마스킹하거나 마스킹하지 않는다. 이것이 500문장 코퍼스에서 MLM 정확도를 개선하는지 측정한다.
3. **어려움.** 공개 데이터 세트의 10,000개 문장에서 작은 (2층, d=64) BERT를 교육한다. SST-2 감성을 위해 `[CLS]` 토큰을 fine-tune한다. 매칭된 매개변수에서 decoder-only baseline과 비교 — 어느 것이 이기는가?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| MLM | "Masked language modeling" | 교육 신호: 토큰의 15%를 무작위로 `[MASK]`로 대체하고, 원본을 예측. |
| Bidirectional | "양쪽을 본다" | Encoder attention에는 causal mask가 없다 — 모든 위치가 다른 모든 위치를 본다. |
| `[CLS]` | "The pooler token" | 모든 시퀀스에 앞에 추가되는 특수 토큰; 최종 임베딩이 문장 수준 표현으로 사용된다. |
| `[SEP]` | "Segment separator" | 쌍으로 된 시퀀스를 분리 (예: query/doc, 문장 A/B). |
| NSP | "Next sentence prediction" | BERT의 두 번째 사전 교육 작업; RoBERTa에서 유용하지 않음이 밝혀지고 2019년 이후 폐기. |
| Fine-tuning | "작업에 적응" | encoder를 대부분 동결;下游 작업에 위에 작은 head를 교육. |
| Cross-encoder | "A reranker" | query와 doc을 모두 입력으로 받는 BERT로, relevance 점수를 출력. |
| ModernBERT | "2024년 새로고침" | RoPE, RMSNorm, GeGLU, alternating local/global attention, 8K 컨텍스트로 재건된 Encoder. |

## 추가 자료

- [Devlin et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805) — 원래 논문.
- [Liu et al. (2019). RoBERTa: A Robustly Optimized BERT Pretraining Approach](https://arxiv.org/abs/1907.11692) — BERT를 올바르게 교육하는 방법; NSP 폐기.
- [Clark et al. (2020). ELECTRA: Pre-training Text Encoders as Discriminators Rather Than Generators](https://arxiv.org/abs/2003.10555) — 대체 토큰 탐지가 매칭된 계산에서 MLM을 이긴다.
- [Warner et al. (2024). Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder](https://arxiv.org/abs/2412.13663) — ModernBERT 논문.
- [HuggingFace `modeling_bert.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/bert/modeling_bert.py) — 표준 encoder 참조.