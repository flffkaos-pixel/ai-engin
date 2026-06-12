# 완전한 Transformer — Encoder + Decoder

> Attention이 스타다. 나머지 — residual, normalization, feed-forward, cross-attention — 는 그것을 깊이 쌓을 수 있게 하는 발판이다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 02 (Self-Attention), Phase 7 · 03 (Multi-Head Attention), Phase 7 · 04 (Positional Encoding)
**소요 시간:** ~75분

## 문제

단일 attention 레이어는 특징 추출기이지 모델이 아니다. 레이어당 하나의 matmul은 언어에 충분한 용량이 아니다. 깊이가 필요하다 — 그리고 올바른 배선 없이는 깊이가 깨진다.

2017년 Vaswani 논문은 하나의 attention 레이어를 스택 가능한 블록으로 변환한 여섯 가지 설계 결정을 패키지화했다. 그 이후 모든 transformer — encoder-only (BERT), decoder-only (GPT), encoder-decoder (T5) — 가 동일한 뼈대를 상속한다. 2026년 블록은 개선되었다 (RMSNorm, SwiGLU, pre-norm, RoPE) 하지만 뼈대는 동일하다.

이 수업은 뼈대이다. 다음 수업을 통해 specialized한다 — 06은 encoder, 07은 decoder, 08은 encoder-decoder.

## 개념

![Encoder와 decoder 블록 내부, 배선됨](../assets/full-transformer.svg)

### 여섯 가지 구성 요소

1. **임베딩 + 위치 신호.** 토큰 → 벡터. RoPE (현대) 또는 sinusoidal (고전)으로 위치 주입.
2. **Self-attention.** 모든 위치가 다른 모든 위치에 attend. Decoder에서 masked.
3. **Feed-forward network (FFN).** 위치별 2층 MLP: `W_2 · activation(W_1 · x)`. 기본 확장 비율 4×.
4. **Residual connection.** `x + sublayer(x)`. 없으면 gradient가 ~6 레이어 이후에 사라진다.
5. **Layer normalization.** `LayerNorm` 또는 `RMSNorm` (현대). Residual stream을 안정화.
6. **Cross-attention (decoder만).** Query는 decoder에서 오고, key와 value는 encoder 출력에서 온다.

벡터가 하나의 블록을 통과하는 것을 지켜보자: attention이 위치를 따라 mixed하고, residual이 그것을 전달하고, FFN가 그것을 변환하고, norm이 stream을 안정적으로 유지한다.

```figure
transformer-block
```

### Encoder 블록 (BERT, T5 encoder에서 사용)

```
x → LN → MHA(self) → + → LN → FFN → + → out
                     ^              ^
                     |              |
                     └── residual ──┘
```

Encoder는 양방향이다. 마스킹 없음. 모든 위치가 모든 위치를 본다.

### Decoder 블록 (GPT, T5 decoder에서 사용)

```
x → LN → MHA(masked self) → + → LN → MHA(cross to encoder) → + → LN → FFN → + → out
```

Decoder는 블록당 세 개의 하위 레이어를 갖는다. 중간 것 — cross-attention — 은 encoder에서 decoder로 정보가 흐르는 유일한 곳이다. Pure decoder-only 아키텍처 (GPT)에서는 cross-attention이 생략되고 masked self-attention + FFN만 있다.

### Pre-norm vs post-norm

원래 논문: `x + sublayer(LN(x))` vs `LN(x + sublayer(x))`. Post-norm은 2019년경 인기를 잃었다 — 신중한 warmup 없이는 깊게 훈련하기 어렵다. Pre-norm (`LN` *이전* 하위 레이어)은 2026년 기본값이다: Llama, Qwen, GPT-3+, Mistral 모두 사용한다.

### 2026년 현대화된 블록

Vaswani 2017은 LayerNorm + ReLU를 탑재했다. 현대 스택은 둘 다 교체했다. Production 블록이 실제로 어떻게 보이는지:

| 구성 요소 | 2017 | 2026 |
|-----------|------|------|
| Normalization | LayerNorm | RMSNorm |
| FFN activation | ReLU | SwiGLU |
| FFN expansion | 4× | 2.6× (SwiGLU는 세 개의 행렬을 사용, 총 매개변수 일치) |
| Position | Sinusoidal absolute | RoPE |
| Attention | Full MHA | GQA (or MLA) |
| Bias terms | Yes | No |

RMSNorm은 LayerNorm의 평균 중심화를 제거한다 (하나의 빼기 감소), 이는 연산을 절약하고 경험적으로 최소한 동등하게 안정적이다. SwiGLU (`Swish(W1 x) ⊙ W3 x`)는 Llama, PaLM 및 Qwen 논문에서 ReLU/GELU FFN보다 ~0.5점 ppl 항상 우수하다.

### 매개변수 수

`d_model = d`이고 FFN 확장 `r`인 하나의 블록에 대해:

- MHA: `4 · d²` (Q, K, V, O projection)
- FFN (SwiGLU): `3 · d · (r · d)` ≈ `3rd²`
- Norm: 미미

`d = 4096, r = 2.6, layers = 32` (대략 Llama 3 8B)에서 총계: `32 · (4·4096² + 3·2.6·4096²) ≈ 32 · (16 + 32) M = ~1.5B 매개변수/레이어 × 32 ≈ 7B` (임베딩과 head plus). 게시된 수와 일치.

## 실습

### Step 1: 빌딩 블록

Lesson 03의 작은 `Matrix` 클래스를 사용 (독립성을 위해 이 파일로 복사):

- `layer_norm(x, eps=1e-5)` — 평균을 빼고 std로 나눈다.
- `rms_norm(x, eps=1e-6)` — RMS로 나눈다. 평균 빼기 없음.
- `gelu(x)` and `silu(x) * W3 x` (SwiGLU).
- `ffn_swiglu(x, W1, W2, W3)`.
- `encoder_block(x, params)` and `decoder_block(x, enc_out, params)`.

전체 배선은 `code/main.py`를 참조.

### Step 2: 2층 encoder와 2-layer decoder 배선

它们를 쌓는다. Encoder 출력을 모든 decoder cross-attention에 전달한다. 출력 projection 전에 최종 LN을 추가한다.

```python
def encode(tokens, params):
    x = embed(tokens, params.emb) + sinusoidal(len(tokens), params.d)
    for block in params.encoder_blocks:
        x = encoder_block(x, block)
    return x

def decode(target_tokens, encoder_out, params):
    x = embed(target_tokens, params.emb) + sinusoidal(len(target_tokens), params.d)
    for block in params.decoder_blocks:
        x = decoder_block(x, encoder_out, block)
    return x
```

### Step 3: 토이 예제에서 forward 실행

6토큰 소스와 5토큰 대상을 통과시킨다. 출력 shape이 `(5, vocab)`인지 확인한다. 교육 없음 — 이 수업은 아키텍처에 관한 것이지 손실에 관한 것이 아니다.

### Step 4: RMSNorm + SwiGLU로 교체

LayerNorm과 ReLU-FFN을 RMSNorm과 SwiGLU로 교체한다. Shape이 여전히 일치하는지 확인한다. 이것은 하나의 함수 치환으로 2026년 현대화이다.

## 활용

PyTorch/TF 참조 구현: `nn.TransformerEncoderLayer`, `nn.TransformerDecoderLayer`. 그러나 2026년 대부분의 production 코드는 자체 블록을 만든다 because:

- Flash Attention은 `nn.MultiheadAttention`을 통하지 않고 attention 내부에서 호출된다.
- GQA / MLA는 stdlib 참조에 없다.
- RoPE, RMSNorm, SwiGLU는 PyTorch 기본값이 아니다.

HF `transformers`에는 읽어야 할 깔끔한 참조 블록이 있다: `modeling_llama.py`는 표준 2026 decoder-only 블록이다. ~500줄이며 한 번 훑어볼 가치 있다.

**Encoder vs decoder vs encoder-decoder — 언제 선택:**

| 필요 | 선택 | 예시 |
|------|------|---------|
| 텍스트에 대한 분류, 임베딩, QA | Encoder-only | BERT, DeBERTa, ModernBERT |
| 텍스트 생성, 채팅, 코드, 추론 | Decoder-only | GPT, Llama, Claude, Qwen |
| 구조화된 입력 → 구조화된 출력 (번역, 요약) | Encoder-decoder | T5, BART, Whisper |

Decoder-only는 언어에서 이겼는데 확장성이 가장 깨끗하고 comprehension과 generation을 모두 처리하기 때문이다. Encoder-decoder는 입력이明確な "소스 시퀀스" 정체성을 갖을 때 (번역, 음성 인식, 구조화된 작업) 여전히 최상이다.

## 결과물

`outputs/skill-transformer-block-reviewer.md`를 참조. 이 skill은 2026년 기본값에 대한 새로운 transformer 블록 구현을 검토하고 누락된 pieces (pre-norm, RoPE, RMSNorm, GQA, FFN 확장 비율)를 플래그한다.

## 연습 문제

1. **쉬움.** `d_model=512, n_heads=8, ffn_expansion=4, swiglu=True`에서 encoder_block의 매개변수를 센다. 블록을 구현하고 `sum(p.numel() for p in block.parameters())`를 사용하여 검증한다.
2. **보통.** Post-norm에서 pre-norm으로 전환한다. 둘 다 초기화하고 무작위 입력에서 12개 쌓인 레이어 후 activation norm을 측정한다. Post-norm의 activation은 폭발해야 한다; pre-norm의 activation은 제한된 상태를 유지해야 한다.
3. **어려움.** 토이 복사 작업 (x를 뒤집어서 복사)에 4층 encoder-decoder를 구현한다. 100단계 교육. 손실을 보고한다. RMSNorm + SwiGLU + RoPE로 교체 — 손실이 떨어지는가?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Block | "하나의 transformer 레이어" | norm + attention + norm + FFN의 스택으로, residual connection으로 감싸진다. |
| Residual | "스킵 연결" | `x + f(x)` 출력; 깊은 스택을 통해 gradient 흐름을 가능하게 한다. |
| Pre-norm | "이전, 이후가 아닌 정상화" | 현대: `x + sublayer(LN(x))`. Warmup 조작 없이 더 깊게 훈련. |
| RMSNorm | "평균 없는 LayerNorm" | RMS로 나눈다; 하나의 op가 적고 동일한 경험적 안정성. |
| SwiGLU | "모두가 전환한 FFN" | `Swish(W1 x) ⊙ W3 x → W2`. LM ppl에서 ReLU/GELU를 능가. |
| Cross-attention | "Decoder가 encoder를 보는 방법" | Q는 decoder에서, K/V는 encoder 출력에서 오는 MHA. |
| FFN expansion | "중간 MLP가 얼마나 넓은가" | hidden-size 대 d_model 비율, 대개 4 (LayerNorm) 또는 2.6 (SwiGLU). |
| Bias-free | "+b 항 삭제" | 현대 스택은 선형 레이어에서 바이어스를 생략; 약간의 ppl 개선, 더 작은 모델. |

## 추가 자료

- [Vaswani et al. (2017). Attention Is All You Need](https://arxiv.org/abs/1706.03762) — 원래 블록 사양.
- [Xiong et al. (2020). On Layer Normalization in the Transformer Architecture](https://arxiv.org/abs/2002.04745) — 왜 pre-norm이 deep하게 post-norm을 이기는지.
- [Zhang, Sennrich (2019). Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467) — RMSNorm.
- [Shazeer (2020). GLU Variants Improve Transformer](https://arxiv.org/abs/2002.05202) — SwiGLU 논문.
- [HuggingFace `modeling_llama.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py) — 표준 2026 decoder-only 블록.