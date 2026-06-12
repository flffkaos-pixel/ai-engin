# GPT — Causal Language Modeling

> BERT는 양쪽을 본다. GPT는 과거만 본다. 삼각형 마스크가 현대 AI에서 가장 영향력 있는 단일 코드 라인이다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 02 (Self-Attention), Phase 7 · 05 (Full Transformer), Phase 7 · 06 (BERT)
**소요 시간:** ~75분

## 문제

언어 모델은 하나의 질문에 답한다: 첫 번째 `t-1` 토큰이 주어지면, 토큰 `t`에 대한 확률 분포는 무엇인가? 이 신호 — 다음 토큰 예측 — 로 종단 간 교육하면 한 번에 하나의 토큰씩 임의의 텍스트를 생성할 수 있는 모델을 얻는다.

시퀀스 전체에서 병렬로 종단 간 교육하려면 각 위치의 예측이 이전 위치에만 의존해야 한다. 그렇지 않으면 모델이 답을 봐서trivial하게 cheating한다.

Causal mask가 이것을 수행한다. 그것은 softmax 전 attention 점수에 추가되는 `-inf` 값의 단일 상삼각 행렬이다. Softmax 후, 해당 위치는 0이 된다. 각 위치는 자신과 이전 위치에만 attend할 수 있다. 그리고 전체 시퀀스에 한 번 적용하기 때문에, 하나의 forward 통과에서 N개의 병렬 다음 토큰 예측을 얻는다.

GPT-1 (2018), GPT-2 (2019), GPT-3 (2020), GPT-4 (2023), GPT-5 (2024), Claude, Llama, Qwen, Mistral, DeepSeek, Kimi — 그들 모두 동일한 핵심 루프를 가진 decoder-only causal transformer이다. 只是更大、更好的数据、更好的RLHF。

## 개념

![Causal mask가 삼각형 attention 행렬을 생성](../assets/causal-attention.svg)

### 마스크

길이 `N`의 시퀀스가 주어지면, `N × N` 행렬을 구축한다:

```
M[i, j] = 0       if j <= i
M[i, j] = -inf    if j > i
```

Softmax 전에 raw attention 점수에 `M`을 더한다. `exp(-inf) = 0`, 그래서 마스킹된 위치는 0의 가중치를 기여한다. Attention 행렬의 각 행은 이전 위치에 대한 확률 분포이다.

구현 비용: 하나의 `torch.tril()` 호출. 계산 시간: 나노초. 현장에 대한 영향: 모든 것.

### 병렬 교육, 직렬 추론

교육: 전체 `(N, d_model)` 시퀀스를 한 번에 forward-pass하고, N개의 cross-entropy 손실 (위치당 하나)을 계산하고, 합산하고, backprop. 시퀀스를 따라 병렬. 이것이 GPT 교육이 확장되는 이유 — 하나의 GPU 통과에서 1M 토큰을 처리한다.

추론: 토큰별로 생성한다. `[t1, t2, t3]`를 입력하고 `t4`를 얻는다. `[t1, t2, t3, t4]`를 입력하고 `t5`를 얻는다. `[t1, t2, t3, t4, t5]`를 입력하고 `t6`를 얻는다. KV cache (Lesson 12)는 각 단계에서 다시 계산하지 않도록 `t1…tn`의 숨겨진 상태를 저장한다. 그러나 추론 시 직렬 깊이 = 출력 길이. 그것이 모든 LLM의 지연 시간 병목 현상인 autoregressive 세금이다.

### 손실 — 하나씩 시프트

토큰 `[t1, t2, t3, t4]`가 주어지면:

- 입력: `[t1, t2, t3]`
- 타겟: `[t2, t3, t4]`

모든 위치 `i`에 대해 `-log P(target_i | inputs[:i+1])`를 계산한다. 합산. 이것이 전체 시퀀스에 대한 cross-entropy이다.

들어본 모든 transformer LM이 이 손실에서 교육된다. 사전 교육, fine-tuning, SFT — 동일한 손실, 다른 데이터.

### 디코딩 전략

교육 후, 샘플링 선택이人们가 생각하는 것보다更重要하다.

| 방법 | 무엇을 하는가 | 언제 사용 |
|--------|--------------|-------------|
| Greedy | 매단계 argmax | 결정론적 작업, 코드 완성 |
| Temperature | 로짓을 T로 나눈다, 샘플 | 창작 작업, T 높을수록 더 큰 다양성 |
| Top-k | 상위 k 토큰에서만 샘플 | 低확률 꼬리를 죽인다 |
| Top-p (nucleus) | 누적 확률 ≥ p인 가장 작은 세트에서 샘플 | 2020+ 기본값; 분포 형태에 적응 |
| Min-p | `p > min_p * max_p`인 토큰 유지 | 2024+; top-p보다 긴 꼬리拒绝에 더 baik |
| Speculative decoding | Draft 모델이 N 토큰 제안, 큰 모델이 검증 | 동일한 품질에서 2–3× 지연 감소 |

2026년에서 min-p + temperature 0.7은 오픈 웨이트 모델에 대한 합리적인 기본값이다. Speculative decoding은 모든 production 추론 스택의table stakes이다.

### "GPT 레시피"가 작동한 이유

1. **Decoder-only.** Encoder 오버헤드 없음. 레이어당 attention + FFN的一次 통과.
2. **스케일링.** 124M → 1.5B → 175B → 조. Chinchilla 스케일링 법칙 (Lesson 13)은 계산량을 사용하는 방법을 알려준다.
3. **In-context learning.** ~6B–13B에서 출현. 모델은 fine-tuning 없이 few-shot 예제를 따를 수 있다.
4. **RLHF.** 인간 선호도에 대한 사후 교육은 원시 사전 교육 텍스트를 채팅 어시스턴트로 변환했다.
5. **Pre-norm + RoPE + SwiGLU.** 규모에서 안정적인 교육.

핵심 아키텍처는 GPT-2 이후 많이 변경되지 않았다. 모든 흥미로운 일은 데이터, 규모 및 사후 교육에서 발생했다.

## 실습

### Step 1: causal mask

`code/main.py`를 참조. 한 줄:

```python
def causal_mask(n):
    return [[0.0 if j <= i else float("-inf") for j in range(n)] for i in range(n)]
```

Softmax 전에 attention 점수에 추가한다. 이것이 전체 메커니즘이다.

### Step 2: 2층 GPT-ish 모델

두 개의 decoder 블록을 쌓는다 (masked self-attention + FFN, cross-attention 없음). 토큰 임베딩, 위치 인코딩, 언임베딩 (토큰 임베딩 행렬에 바이어스됨 — GPT-2 이후 표준 트릭)을 추가한다.

### Step 3: 다음 토큰 예측, 종단 간

20토큰 토이 어휘에서 모든 위치에서 로짓을 생성한다. 시프트 바이 원 타겟에 대해 cross-entropy 손실을 계산한다. Gradient 없음 — 이것은 forward-pass 정합성 검사이다.

### Step 4: 샘플링

Greedy, temperature, top-k, top-p, min-p를 구현한다. 각각을 고정 프롬프트에서 실행하고 출력을 비교한다. 샘플링 함수는 10줄이다.

## 활용

PyTorch, 2026 관용구:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")
tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")

prompt = "Attention is all you need because"
inputs = tok(prompt, return_tensors="pt")
out = model.generate(
    **inputs,
    max_new_tokens=64,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
)
print(tok.decode(out[0]))
```

내부에서 `generate()`는 forward 통과를 실행하고, 최종 위치 로짓을 가져오고, 다음 토큰을 샘플링하고, 그것을 추가하고, 반복한다. 모든 production LLM 추론 스택 (vLLM, TensorRT-LLM, llama.cpp, Ollama, MLX)은 batched prefill, continuous batching, KV cache paging, speculative decoding로 무거운 최적화와 함께 동일한 루프를 구현한다.

**GPT vs BERT, 한 줄씩:** GPT는 `P(x_t | x_{<t})`를 예측한다. BERT는 `P(x_masked | x_unmasked)`를 예측한다. 손실은 모델이 생성할 수 있는지 여부를 결정한다.

## 결과물

`outputs/skill-sampling-tuner.md`를 참조. 이 skill는 새 생성 작업에 대한 샘플링 매개변수를 선택하고 결정론적 디코딩이 필요할 때 플래그한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하고 softmax 후 causal attention 행렬이 하삼각형인지 확인한다. Spot-check: 행 3은 열 0–3에서만 가중치를 가져야 한다.
2. **보통.** 너비 4의 beam search를 구현한다. 10개의 짧은 프롬프트에서 beam-4와 greedy의 순열도를 비교한다. Beam이 항상 이기는가? (힌트: 보통 번역에는, 열린 채팅에는 아니다.)
3. **어려움.** Speculative decoding을 구현: 작은 2층 모델을 draft로, 6층 모델을 verifier로 사용한다. 길이 64의 100개 완성에서 벽시계 속도 향상을 측정한다. 출력이 verifier의 greedy와 일치하는지 확인한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Causal mask | "삼각형" | Attention 점수에 추가되는 상삼각 `-inf` 행렬으로, 위치 `i`가 위치 `≤ i`만 볼 수 있도록 한다. |
| Next-token prediction | "손실" | 모든 위치에서 모델 분포에 대한 진짜 다음 토큰의 cross-entropy. |
| Autoregressive | "한 번에 하나씩 생성" | 출력을 입력에 다시 공급; 교육 중에는 병렬, 생성 중에는 아님. |
| Logits | "softmax 전 점수" | softmax 전 LM head의 원시 출력; 샘플링은 이것에서 발생. |
| Temperature | "창작성 손잡이" | 로짓을 T로 나눈다; T→0 = greedy, T→∞ = 균일. |
| Top-p | "핵ucleus 샘플링" | 누적 ≥p인 가장 작은 세트로 분포를 자른다; 나머지에서 샘플. |
| Min-p | "top-p보다 나은" | `p ≥ min_p × max_p`인 토큰 유지; 분포 날카로움에 맞게 컷오프 적응. |
| Speculative decoding | "Draft + 확인" | 저렴한 모델이 N 토큰 제안; 큰 모델이 병렬로 확인. |
| Teacher forcing | "교육 트릭" | 교육 중 실제 이전 토큰을 공급하고, 모델의 예측이 아닌. 모든 seq2seq LM의 표준. |

## 추가 자료

- [Radford et al. (2018). Improving Language Understanding by Generative Pre-Training](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf) — GPT-1.
- [Radford et al. (2019). Language Models are Unsupervised Multitask Learners](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) — GPT-2.
- [Brown et al. (2020). Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165) — GPT-3 및 in-context learning.
- [Leviathan, Kalman, Matias (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — spec 디코딩 논문.
- [HuggingFace `modeling_llama.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py) — 표준 causal-LM 참조 코드.