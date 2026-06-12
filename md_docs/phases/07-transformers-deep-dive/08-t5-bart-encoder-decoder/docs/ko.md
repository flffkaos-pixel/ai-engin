# T5, BART — Encoder-Decoder 모델

> Encoder는 이해한다. Decoder는 생성한다. 다시 합치면 입력 → 출력 작업용 모델이 된다: 번역, 요약, 재작성, 전사.

**유형:** 학습
**언어:** Python
**선수 과목:** Phase 7 · 05 (Full Transformer), Phase 7 · 06 (BERT), Phase 7 · 07 (GPT)
**소요 시간:** ~45분

## 문제

Decoder-only GPT와 encoder-only BERT는 각각 다른 목표를 위해 2017년 아키텍처를 떼어낸다. 그러나 많은 작업은 자연스럽게 입력-출력이다:

- 번역: 영어 → 프랑스어.
- 요약: 5,000토큰 기사 → 200토큰 요약.
- 음성 인식: 오디오 토큰 → 텍스트 토큰.
- 구조화된 추출: 산문 → JSON.

对这些来说，encoder-decoder是最干净的。Encoder产生源的密集表示。Decoder在每个步骤都cross-attending到该表示， autoregressive地生成输出。输出端的training是 shift-by-one。与GPT相同的loss，只是以encoder输出为条件。

두 논문이 현대 플레이북을 정의했다:

1. **T5** (Raffel et al. 2019). "Text-to-Text Transfer Transformer." 모든 NLP 작업을 text-in, text-out으로 재구성. 단일 아키텍처, 단일 어휘, 단일 손실. 마스킹된 스팬 예측으로 사전 교육 (입력의 손상된 스팬, 출력에서 디코딩).

2. **BART** (Lewis et al. 2019). "Bidirectional and Auto-Regressive Transformer." Denoising autoencoder: 다양한 방식으로 입력 손상 (shuffle, mask, delete, rotate), decoder에게 원본을 재구성하도록 요청.

2026년 encoder-decoder 형식은 입력이 구조화된 경우 계속 존재한다:

- Whisper (음성 → 텍스트).
- Google's 번역 스택.
- 명확한 context 및 edit 구조를 가진 일부 코드 완성/수정 모델.
- 구조화된 추론 작업을 위한 Flan-T5 및 변형.

Decoder-only가 발광을 얻었지만, encoder-decoder는 사라지지 않았다.

## 개념

![Cross-attention이 있는 Encoder-decoder](../assets/encoder-decoder.svg)

### Forward 루프

```
source tokens ─▶ encoder ─▶ (N_src, d_model)  ──┐
                                                 │
target tokens ─▶ decoder block                    │
                 ├─▶ masked self-attention       │
                 ├─▶ cross-attention ◀───────────┘
                 └─▶ FFN
                ↓
              next-token logits
```

결정적으로, encoder는 입력당 한 번 실행된다. Decoder는 각 단계에서 동일한 encoder 출력에 cross-attending하면서 autoregressive하게 실행된다. Encoder 출력 캐싱은 긴 입력에 대한 무료 속도 향상이다.

### T5 사전 교육 — 스팬 손상

입력의 무작위 스팬을 선택한다 (평균 길이 3 토큰, 총 15%). 각 스팬을 고유한 sentinel으로 대체: `<extra_id_0>`, `<extra_id_1>`, 등. Decoder는 손상된 스팬을 해당 sentinel 접두사와 함께 출력한다:

```
source: The quick <extra_id_0> fox jumps <extra_id_1> dog
target: <extra_id_0> brown <extra_id_1> over the lazy
```

전체 시퀀스를 예측하는 것보다 저렴한 신호. T5论文的消融实验中与MLM（BERT）和prefix-LM（UniLM）竞争。

### BART 사전 교육 — 다중 노이즈 denoising

BART는五种noising 함수를 시도한다:

1. 토큰 마스킹.
2. 토큰 삭제.
3. 텍스트 채우기 (스팬을 마스킹하고, decoder가 올바른 길이를 삽입).
4. 문장 순열.
5. 문서 회전.

텍스트 채우기 + 문장 순열 조합이 최고의 하류 수치를 생성했다. Decoder는 항상 원본을 재구성한다. BART의 출력은 손상된 스팬이 아니라 전체 시퀀스이다 — 所以预训练计算比T5高。

### 추론

GPT와 동일한 autoregressive 생성. Greedy / beam / top-p 샘플링이 적용된다. Beam search (너비 4-5)는 번역과 요약에 표준이다 — 출력 분포가 채팅보다 좁기 때문이다.

### 2026년 각 변형을 언제 선택하는가

| 작업 | Encoder-decoder? | 이유 |
|------|------------------|-----|
| 번역 | Yes, usually | 명확한 소스 시퀀스; 고정 출력 분포; beam search 작동 |
| 음성-텍스트 | Yes (Whisper) | 입력 양식도가 출력과 다름; encoder가 오디오 특징을 형성 |
| 채팅 / 추론 | No, decoder-only | 지속적인 "입력" 없음 — 대화가 시퀀스이다 |
| 코드 완성 | Usually no | 긴 컨텍스트로 decoder-only가 이김; Qwen 2.5 Coder와 같은 코드 모델은 decoder-only |
| 요약 | Either works | BART, PEGASUS가 이전 decoder-only baseline을 이김; 현대 decoder-only LLM이 它们를 matches |
| 구조화된 추출 | Either | T5는 "text → text"가 모든 출력 형식을 흡수하기 때문에 깔끔함 |

~2022년以来的趋势: decoder-only占领了encoder-decoder曾经拥有的任务，因为(a)指令调整decoder-only LLM通过提示泛化到任何事情，(b)一个架构比两个更容易扩展，(c) RLHF假设一个decoder。Encoder-decoder在输入模态不同的情况下（语音、图像）或beam search质量很重要的情况下仍然存在。

## 실습

`code/main.py`를 참조. 토이 코퍼스에 대한 T5 스타일 스팬 손상을 구현한다 — 이 수업에서 가장有用的单个 piece因为它出现在每个encoder-decoder预训练配方中。

### Step 1: 스팬 손상

```python
def corrupt_spans(tokens, mask_rate=0.15, mean_span=3.0, rng=None):
    """~mask_rate의 토큰을 합산하는 스팬을 선택. (손상된 입력, 대상)을 반환."""
    n = len(tokens)
    n_mask = max(1, int(n * mask_rate))
    n_spans = max(1, int(round(n_mask / mean_span)))
    ...
```

대상 형식은 T5 규칙이다: `<sent0> span0 <sent1> span1 ...`. 손상된 입력은 스팬 위치의 sentinel 토큰과 변경되지 않은 토큰을 interleaves한다.

### Step 2: 라운드 트립 확인

손상된 입력과 대상이 주어지면 원본 문장을 재구성한다. 손상 것이可逆하면 forward pass是 well-defined。这是健全性检查 — 真正的训练从不这样做，但测试便宜，可以捕获跨度簿记中的 off-by-one 错误。

### Step 3: BART 노이징

5개 함수: `token_mask`, `token_delete`, `text_infill`, `sentence_permute`, `document_rotate`. 그 중 두 개를 구성하고 결과를 보여준다.

## 활용

HuggingFace 참조:

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer
tok = T5Tokenizer.from_pretrained("google/flan-t5-base")
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-base")

inputs = tok("translate English to French: Attention is all you need.", return_tensors="pt")
out = model.generate(**inputs, max_new_tokens=32)
print(tok.decode(out[0], skip_special_tokens=True))
```

T5 트릭: 작업 이름이 입력 텍스트로 간다. 동일한 모델이数十개 작업을 처리한다因为每个任务是 text-in, text-out。2026年这个模式已被指令调整decoder-only模型推广，但T5首先将其编纂。

## 결과물

`outputs/skill-seq2seq-picker.md`를 참조. 이 skill는 입력-출력 구조, 지연 시간 및 품질 목표를 고려하여 새 작업에 대한 encoder-decoder와 decoder-only 사이를 선택한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하고 30토큰 문장에 스팬 손상을 적용하고, non-sentinel 소스 토큰과 디코딩된 대상 스팬을 연결하여 원본을 재현하는지 확인한다.
2. **보통.** BART의 `text_infill` 노이즈를 구현: 무작위 스팬을 단일 `<mask>` 토큰으로 대체하고, decoder는 올바른 스팬 길이와 내용을推断해야 한다. 하나의 예를 보여준다.
3. **어려움.** 동일한 데이터에서 동일한 계산으로 `Llama-3.2-1B`를 fine-tune하는 것과 비교하여 tiny English → pig-Latin 코퍼스 (200쌍)에서 `flan-t5-small`를 fine-tune한다. 유지된 50쌍 세트에서 BLEU를 측정한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Encoder-decoder | "Seq2seq transformer" | 두 스택: 입력용 양방향 encoder, 출력용 cross-attention이 있는 causal decoder. |
| Cross-attention | "소스가 대상과 대화하는 곳" | Decoder의 Q × encoder의 K/V. Encoder 정보가 decoder에 들어오는 유일한 곳. |
| Span corruption | "T5의 사전 교육 트릭" | 무작위 스팬을 sentinel 토큰으로 대체; decoder가 스팬을 출력. |
| Denoising objective | "BART의 게임" | 입력에 노이즈 기능을 적용하고, decoder가 클린 시퀀스를 재구성하도록 교육. |
| Sentinel token | "`_<extra_id_N>` 플레이스홀더" | 소스의 손상된 스팬을 태깅하고 대상에서 다시 태깅하는 특수 토큰. |
| Flan | "Instruction-tuned T5" | >1,800 작업에서 fine-tune된 T5; 명령 추종에서 encoder-decoder를 경쟁력 있게 만들었다. |
| Beam search | "디코딩 전략" | 각 단계에서 상위 k 부분 시퀀스를 유지; 번역/요약에 표준. |
| Teacher forcing | "교육 시간 입력" | 교육 중 실제 이전 출력 토큰을 decoder에 공급하고, 샘플링된 것이 아닌. |

## 추가 자료

- [Raffel et al. (2019). Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer](https://arxiv.org/abs/1910.10683) — T5.
- [Lewis et al. (2019). BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension](https://arxiv.org/abs/1910.13461) — BART.
- [Chung et al. (2022). Scaling Instruction-Finetuned Language Models](https://arxiv.org/abs/2210.11416) — Flan-T5.
- [Radford et al. (2022). Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — Whisper, 표준 2026 encoder-decoder.
- [HuggingFace `modeling_t5.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/t5/modeling_t5.py) — 참조 구현.