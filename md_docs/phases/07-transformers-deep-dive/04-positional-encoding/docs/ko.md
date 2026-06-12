# 위치 인코딩 — Sinusoidal, RoPE, ALiBi

> Attention은 순열 불변이다. "The cat sat on the mat"와 "mat the on sat cat the"는 위치 신호 없으면 동일한 출력을 생성한다. 세 가지 알고리즘이 이를 해결한다 — 각각 "위치"가 무엇을 의미하는지에 대해 다른 내기를 걸고 있다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 02 (Self-Attention), Phase 7 · 03 (Multi-Head Attention)
**소요 시간:** ~45분

## 문제

Scaled dot-product attention은 순서를 인식하지 못한다. Attention 행렬 `softmax(Q K^T / √d) V`는 쌍별 유사도에서 계산된다. `X`의 행을 섞으면, 출력의 행도 동일한 방식으로 섞인다. Attention 내부에는 위치에 신경 쓰는 것이 없다.

那是 bag-of-words 모델에서는 버그가 아니다. 언어, 코드, 오디오, 비디오 — 순서가 의미를 갖는 모든 것 — 에는 치명적이다.

수정 방법: 어떤 식으로든 임베딩에 위치를 주입한다. 세 가지 시대의 답:

1. **절대 sinusoidal** (Vaswani 2017). 위치에 `sin/cos`를 임베딩에 더한다. 간단하고, 학습 불필요, 학습된 길이를 벗어나면 외삽이 잘 안 된다.
2. **RoPE — Rotary Position Embeddings** (Su 2021). 위치에 비례하는 각도로 Q와 K 벡터를 회전시킨다. 내적에 *상대* 위치를 직접 인코딩한다. 2026년 지배적.
3. **ALiBi — Attention with Linear Biases** (Press 2022). 임베딩을 완전히 건너뛰고, 거리 기반으로 attention 점수에 head당 선형 페널티를 추가한다. 훌륭한 길이 외삽.

2026년 현재, 사실상 모든 프론티어 오픈 모델이 RoPE를 사용한다: Llama 2/3/4, Qwen 2/3, Mistral, Mixtral, DeepSeek-V3, Kimi. 소수의 긴 컨텍스트 모델이 ALiBi 또는 변형을 사용한다. 절대 sinusoidal는 역사적이다.

## 개념

![Sinusoidal 절대 vs RoPE 회전 vs ALiBi 거리 바이어스](../assets/positional-encoding.svg)

### 절대 sinusoidal

Shape `(max_len, d_model)`인 고정 행렬 `PE`를 미리 계산한다:

```
PE[pos, 2i]   = sin(pos / 10000^(2i / d_model))
PE[pos, 2i+1] = cos(pos / 10000^(2i / d_model))
```

그런 다음 attention 전에 `X' = X + PE[:N]`. 각 차원은 다른 주파수의 정현파이다. 모델이 위상을 패턴에서 읽는 방법을 학습한다. `max_len`을 초과하면 실패: 모델이 0–2047 위치만 보았을 때 2048 위치에서 무슨 일이 일어나는지 아무것도 알려주지 않는다.

### RoPE

Q와 K 벡터 (임베딩이 아닌)에 회전을 적용한다. 차원 쌍 `(2i, 2i+1)`에 대해:

```
[q'_2i    ]   [ cos(pos·θ_i)  -sin(pos·θ_i) ] [q_2i   ]
[q'_2i+1  ] = [ sin(pos·θ_i)   cos(pos·θ_i) ] [q_2i+1 ]

θ_i = base^(-2i / d_head),  base = 10000 기본값
```

位置 `pos_k`의 키에도 동일한 회전을 적용한다. 내적 `q'_m · k'_n`은 (m - n)의 함수가 된다. 즉: **attention 점수는 상대 거리에만 의존한다**, 회전이 절대 위치에서 키워졌더라도. 아름다운 트릭.

RoPE 확장: 재교육 없이 더 긴 컨텍스트로 외삽하려면 `base`를 스케일링할 수 있다 (NTK-aware, YaRN, LongRoPE). Llama 3이 이렇게 8K에서 128K 컨텍스트로 확장했다.

### ALiBi

임베딩 트릭을 건너뛴다. 직접 attention 점수를 바이어스한다:

```
attn_score[i, j] = (q_i · k_j) / √d  -  m_h · |i - j|
```

여기서 `m_h`는 head별 기울기이다 (예: `1 / 2^(8·h/H)`). 더 가까운 토큰이 부스트되고; 먼 토큰은 페널티를 받는다. 교육 비용 없음. 논문은 길이 외삽이 sinusoidal보다 우수하고 원래 학습된 길이에서 RoPE와 일치함을 보여준다.

### 2026년 무엇을 선택해야 하는가

| 변형 | 외삽 | 교육 비용 | 사용처 |
|---------|---------------|---------------|---------|
| 절대 sinusoidal | poor | free | 원래 transformer, 초기 BERT |
| 학습된 절대 | none | tiny | GPT-2, GPT-3 |
| RoPE | 스케일링으로 good | free | Llama 2/3/4, Qwen 2/3, Mistral, DeepSeek-V3, Kimi |
| RoPE + YaRN | excellent | fine-tune 단계 | Qwen2-1M, Llama 3.1 128K |
| ALiBi | excellent | free | BLOOM, MPT, Baichuan |

RoPE가 이긴 이유는 attention 아키텍처를 변경하지 않고 들어가고, 상대 위치를 인코딩하며, `base` 하이퍼파라미터가 긴 컨텍스트 fine-tuning을 위한 명쾌한 손잡이를 제공하기 때문이다.

## 실습

### Step 1: sinusoidal 인코딩

`code/main.py`를 참조. 4줄 계산:

```python
def sinusoidal(N, d):
    pe = [[0.0] * d for _ in range(N)]
    for pos in range(N):
        for i in range(d // 2):
            theta = pos / (10000 ** (2 * i / d))
            pe[pos][2 * i]     = math.sin(theta)
            pe[pos][2 * i + 1] = math.cos(theta)
    return pe
```

첫 번째 attention 레이어 전에 임베딩 행렬에 이것을 더한다.

### Step 2: Q, K에 적용된 RoPE

RoPE는 Q와 K에서 in-place로 작동한다. 각 차원 쌍에 대해:

```python
def apply_rope(x, pos, base=10000):
    d = len(x)
    out = list(x)
    for i in range(d // 2):
        theta = pos / (base ** (2 * i / d))
        c, s = math.cos(theta), math.sin(theta)
        a, b = x[2 * i], x[2 * i + 1]
        out[2 * i]     = a * c - b * s
        out[2 * i + 1] = a * s + b * c
    return out
```

중요: 위치 `m`의 Q과 위치 `n`의 K에 동일한 함수를 적용한다. Their 내적은 모든 좌표 쌍에서 `cos((m-n)·θ_i)` 요소를 얻는다. Attention은 무료로 상대 위치를 학습한다.

### Step 3: ALiBi 기울기와 바이어스

```python
def alibi_bias(n_heads, seq_len):
    # slope_h = 2 ** (-8 * h / n_heads) for h = 1..n_heads
    slopes = [2 ** (-8 * (h + 1) / n_heads) for h in range(n_heads)]
    bias = []
    for m in slopes:
        row = [[-m * abs(i - j) for j in range(seq_len)] for i in range(seq_len)]
        bias.append(row)
    return bias  # softmax 전에 attention 점수에 더한다
```

Head `h`의 `(seq_len, seq_len)` attention 점수 행렬에 `bias[h]`를 더한 후 softmax.

### Step 4: RoPE의 상대 거리 속성 확인

두 개의 무작위 벡터 `a, b`를 선택한다. `(pos_a, pos_b)`로 회전한다. 그런 다음 `(pos_a + k, pos_b + k)`로 회전한다. 두 내적 모두 부동 소수점 오차 범위 내에서 일치해야 한다. 그 속성이 RoPE의 전부이다 — 절대 오프셋은 상관없고, 상대적 갭만이 중요하다.

## 활용

PyTorch 2.5+는 `torch.nn.functional`에서 RoPE 유틸리티를 제공한다. 대부분의 production 코드는 `flash_attn` 또는 `xformers`를 사용하는데, RoPE는 attention 커널 내부에 적용된다.

```python
from transformers import AutoModel
model = AutoModel.from_pretrained("meta-llama/Llama-3.2-3B")
# model.config.rope_scaling → {"type": "yarn", "factor": 32.0, "original_max_position_embeddings": 8192}
```

**2026년 긴 컨텍스트 트릭:**

- **NTK-aware interpolation.** 4K에서 16K+로 확장할 때 `base`를 `base * (scale_factor)^(d/(d-2))`로 리스케일한다.
- **YaRN.** 긴 컨텍스트에서 attention 엔트로피를 보존하는 더 스마트한 interpolation. Llama 3.1 128K가 사용.
- **LongRoPE.** 각 차원별 scale factor를 선택하기 위해 진화적 검색을 사용하는 Microsoft의 2024년 방법. Phi-3-Long이 사용하고 활용 섹션에서 인용.
- **Position interpolation + fine-tuning.** 확장 계수로 위치를 수축하고 1–5B 토큰에 대해 fine-tune한다. 놀랍도록 효과적.

## 결과물

`outputs/skill-positional-encoding-picker.md`를 참조. 이 skill은 대상 컨텍스트 길이, 외삽 필요성, 교육 예산을 고려하여 새 모델에 대한 인코딩 전략을 선택한다.

## 연습 문제

1. **쉬움.** `max_len=512, d=128`에 대해 sinusoidal `PE` 행렬을 히트맵으로 플롯한다. "차원 인덱스가 증가함에 따라 줄무늬가 넓어지는" 패턴을 확인한다.
2. **보통.** NTK-aware RoPE 스케일링을 구현한다. 길이 256 시퀀스로 작은 LM을 교육한 다음 스케일링 유무로 길이 1024에서 테스트한다. Perplexity를 측정한다.
3. **어려움.** 동일한 attention 모듈에서 ALiBi와 RoPE를 모두 구현한다. 길이 512 시퀀스로 4층 transformer를 복사 작업에 교육한다. 테스트 시 2048로 외삽한다. 저하를 비교한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Positional encoding | "attention에 순서를 알려준다" | 임베딩이나 attention에 추가되어 위치를 인코딩하는 모든 신호. |
| Sinusoidal | "원래 것" | 기하학적 주파수의 `sin/cos`를 임베딩에 더함; 외삽 안 됨. |
| RoPE | "회전 임베딩" | Q, K를 위치 의존 각도로 회전; 내적이 상대 거리를 인코딩. |
| ALiBi | "선형 바이어스 트릭" | attention 점수에 `-m·|i-j|`를 더함; 임베딩 불필요, 뛰어난 외삽. |
| base | "RoPE의 손잡이" | RoPE의 주파수 스케일러; 추론 시 컨텍스트 확장을 위해 증가. |
| NTK-aware | "RoPE 스케일링 트릭" | 컨텍스트가 확장될 때 고주파수 차원이 압축되지 않도록 `base`를 리스케일. |
| YaRN | "야심 찬 것" | attention 엔트로피를 보존하는 차원별 interpolation+외삽. |
| Extrapolation | "학습된 길이를 넘어 작동" | 위치 체계가 교육에서 본 `max_len` 이후에도 올바른 출력을 제공할 수 있는가? |

## 추가 자료

- [Vaswani et al. (2017). Attention Is All You Need §3.5](https://arxiv.org/abs/1706.03762) — 원래 sinusoidal.
- [Su et al. (2021). RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864) — RoPE 논문.
- [Press, Smith, Lewis (2021). Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation](https://arxiv.org/abs/2108.12409) — ALiBi.
- [Peng et al. (2023). YaRN: Efficient Context Window Extension of Large Language Models](https://arxiv.org/abs/2309.00071) — RoPE 스케일링의 최첨단.
- [Chen et al. (2023). Extending Context Window of Large Language Models via Positional Interpolation](https://arxiv.org/abs/2306.15595) — Meta의 Llama 2 긴 컨텍스트 논문.
- [Ding et al. (2024). LongRoPE: Extending LLM Context Window Beyond 2 Million Tokens](https://arxiv.org/abs/2402.13753) — Microsoft 방법론으로 Phi-3-Long이 사용하고 활용 섹션에서 인용.
- [HuggingFace Transformers — `modeling_rope_utils.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/modeling_rope_utils.py) — 모든 RoPE 스케일링 체계 (기본, 선형, 동적, YaRN, LongRoPE, Llama-3)의 production-grade 구현.