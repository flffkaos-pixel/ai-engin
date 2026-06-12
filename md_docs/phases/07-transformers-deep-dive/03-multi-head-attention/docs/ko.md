# Multi-Head Attention

> 하나의 attention head는 한 번에 하나의 관계를 학습한다. 여덟 개의 head는 여덟 가지를 학습한다. Head는 무료다. 더 많이 가져가라.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 02 (Self-Attention from Scratch)
**소요 시간:** ~75분

## 문제

단일 self-attention head는 하나의 attention 행렬을 계산한다. 그 행렬은 한 가지 종류의 관계만 포착한다 - 대개 훈련 신호에서 손실을 최소화하는 것이다. 데이터에 주어-동사 일치, 공기참조, 장기 담론, 구문 청킹이 얽혀 있다면, 단일 head는 그것들을 하나의 부드러운 max 분포로 뭉개어 절반의 신호를 잃는다.

2017년 Vaswani 논문의 해결책: 여러 attention 함수를 병렬로 실행하고, 각각 고유한 Q, K, V projection을 가지며, 출력을 연결한다. 각 head는 `d_model / n_heads` 차원의 더 작은 부분 공간에서 작동한다. 총 매개변수 수는 동일하다. 표현력이 향상된다.

Multi-head attention은 2026년 모든 transformer가 기본으로 탑재한다.唯一的争论是关于*有多少*个head，以及keys和values是否共享projection（Grouped-Query Attention, Multi-Query Attention, Multi-head Latent Attention）。

## 개념

![Multi-head attention 분할, attend, 연결](../assets/multi-head-attention.svg)

**분할.** shape `(N, d_model)`인 `X`를 가져온다. Q, K, V를 각각 shape `(N, d_model)`로 projection한다. `d_head = d_model / n_heads`인 `(N, n_heads, d_head)`로 reshape한다. Transpose하여 `(n_heads, N, d_head)`로 만든다.

**병렬로 attend.** 각 head 내에서 scaled dot-product attention을 실행한다. 각 head는 `(N, d_head)`를 생성한다. Head는 임베딩의 서로 다른 부분 공간에서 작동하며, attention 계산 중에 서로 직접 통신하지 않는다.

**연결하고 projection.** Head를 다시 `(N, d_model)`로 스택하고 학습된 출력 행렬 `W_o` of shape `(d_model, d_model)`를 곱한다. `W_o`는 head가 혼합되는 곳이다.

**작동 원리.** 각 head는 표현 예산을 두고 서로 경쟁하지 않고 전문화할 수 있다. 2019-2024년의 probing 연구는 Distinct head 역할을 보여준다: 위치 head, 이전 토큰에 attend하는 head, 복사 head, 개체명 head, induction head (in-context learning의 근간).

**2026년 변형 계열:**

| 변형 | Q heads | K/V heads | 사용처 |
|---------|---------|-----------|---------|
| Multi-head (MHA) | N | N | GPT-2, BERT, T5 |
| Multi-query (MQA) | N | 1 | PaLM, Falcon |
| Grouped-query (GQA) | N | G (예: N/8) | Llama 2 70B, Llama 3+, Qwen 2+, Mistral |
| Multi-head latent (MLA) | N | 저차원으로 압축 | DeepSeek-V2, V3 |

GQA가 현대의 기본값인 이유는 KV-cache 메모리를 `N/G` 요인으로 줄이면서 거의 완벽한 품질을 유지하기 때문이다. MLA는更进一步，将K/V压缩到潜在空间，然后在计算时投影回来——消耗FLOP，但节省更多内存。

## 실습

### Step 1: 우리가 이미 가진 단일 head attention에서 head 분할

Lesson 02의 `SelfAttention`을 가져와서 split/concat 쌍으로 감싼다. NumPy 구현은 `code/main.py`를 참조; 로직은 다음과 같다:

```python
def split_heads(X, n_heads):
    n, d = X.shape
    d_head = d // n_heads
    return X.reshape(n, n_heads, d_head).transpose(1, 0, 2)  # (heads, n, d_head)

def combine_heads(H):
    h, n, d_head = H.shape
    return H.transpose(1, 0, 2).reshape(n, h * d_head)
```

하나의 reshape와 하나의 transpose. 루프 없음. 이것이 PyTorch가 `nn.MultiheadAttention`에서 실제로 하는 것이다.

### Step 2: Head당 scaled-dot-product attention 실행

각 head는 Q, K, V의 고유한 조각을 얻는다. Attention은 batched matmul이 된다:

```python
def mha_forward(X, W_q, W_k, W_v, W_o, n_heads):
    Q = X @ W_q
    K = X @ W_k
    V = X @ W_v
    Qh = split_heads(Q, n_heads)         # (heads, n, d_head)
    Kh = split_heads(K, n_heads)
    Vh = split_heads(V, n_heads)
    scores = Qh @ Kh.transpose(0, 2, 1) / np.sqrt(Qh.shape[-1])
    weights = softmax(scores, axis=-1)
    out = weights @ Vh                    # (heads, n, d_head)
    concat = combine_heads(out)
    return concat @ W_o, weights
```

실제 하드웨어에서 `Qh @ Kh.transpose(...)`는 하나의 `bmm`이다. GPU는 shape `(heads, N, d_head) × (heads, d_head, N) -> (heads, N, N)`의 단일 batched matmul을 본다. Head를 추가하는 것은 무료다.

### Step 3: Grouped-Query Attention 변형

Key와 value projection만 변경된다. Q는 `n_heads` 그룹을 얻고, K와 V는 `n_kv_heads < n_heads` 그룹을 얻어 매칭하도록 반복된다:

```python
def gqa_project(X, W, n_kv_heads, n_heads):
    kv = split_heads(X @ W, n_kv_heads)       # (kv_heads, n, d_head)
    repeat = n_heads // n_kv_heads
    return np.repeat(kv, repeat, axis=0)      # (n_heads, n, d_head)
```

추론 시 이것은 KV cache에 `n_heads` 복사본이 아닌 `n_kv_heads` 복사본만 있으면 되므로 메모리를 절약한다. Llama 3 70B는 64개의 query head와 8개의 KV head를 사용한다 - 8배 캐시 감소.

### Step 4: 각 head가 무엇을 학습했는지 조사

4개의 head로 짧은 문장에 MHA를 실행한다. 각 head마다 `(N, N)` attention 행렬을 출력한다. 무작위 초기화에서도 다른 head가 다른 구조를 선택하는 것을 볼 수 있다 - 그것은 partly signal, partly 부분 공간의 회전 대칭 때문이다.

## 활용

PyTorch에서 한 줄 버전:

```python
import torch.nn as nn

mha = nn.MultiheadAttention(embed_dim=512, num_heads=8, batch_first=True)
```

PyTorch 2.5+에서의 GQA:

```python
from torch.nn.functional import scaled_dot_product_attention

# scaled_dot_product_attention은 CUDA에서 Flash Attention으로 자동 디스패치.
# GQA의 경우 shape (B, n_heads, N, d_head)의 Q와 shape (B, n_kv_heads, N, d_head)의 K,V를 전달.
# PyTorch가 repeat을 처리한다.
out = scaled_dot_product_attention(q, k, v, is_causal=True, enable_gqa=True)
```

**얼마나 많은 head?** 2026년 생산 모델의 경험적 규칙:

| 모델 크기 | d_model | n_heads | d_head |
|------------|---------|---------|--------|
| Small (~125M) | 768 | 12 | 64 |
| Base (~350M) | 1024 | 16 | 64 |
| Large (~1B) | 2048 | 16 | 128 |
| Frontier (~70B) | 8192 | 64 | 128 |

`d_head`는 거의 항상 64 또는 128에 landing된다. 그것은 하나의 head가 "볼 수 있는" 단위이다. 32 아래로 떨어뜨리면 head가 `sqrt(d_head)` 스케일링_factor와 싸우기 시작한다; 256 이상이면 " banyak 작은 전문가" 이점을 잃는다.

## 결과물

`outputs/skill-mha-configurator.md`를 참조. 이 skill은 매개변수 budget, 시퀀스 길이, 배포 대상을 고려하여 새로운 transformer에 대한 head 수, kv-head 수, projection 전략을 권장한다.

## 연습 문제

1. **쉬움.** `code/main.py`의 MHA를 가져와서 `d_model=64`를 고정으로 `n_heads`를 1에서 16으로 변경한다. 합성 복사 작업에서 작은 1층 모델의 손실을 플롯한다. 더 많은 head가 도움이 되는가, 정체되는가, 해로운가?
2. **보통.** MQA (모든 query head에서 공유되는 단일 KV head)를 구현한다. 완전한 MHA 대비 매개변수 수가 얼마나 감소하는지 측정한다. N=2048에서 추론 시 KV-cache 크기가 얼마나 감소하는지 계산한다.
3. **어려움.** Multi-head Latent Attention의 작은 버전을 구현한다: K,V를 rank-`r` 잠재 공간으로 압축하고, KV cache에 잠재를 저장하고, attention 시점에서 decompression한다. 어떤 `r`에서 cache 메모리가 완전한 MHA의 1/8 아래로 내려가고 품질이 검증 ppl의 1비트 이내로 유지되는가?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Head | "단일 attention 회로" | 고유한 attention 행렬이 있는 `d_head = d_model / n_heads` 차원의 하나의 Q/K/V projection. |
| d_head | "Head 차원" | 당 head hidden 너비; production에서 거의 항상 64 또는 128. |
| Split / combine | "Reshape 트릭" | attention 주변의 `(N, d_model) ↔ (n_heads, N, d_head)` reshape+transpose. |
| W_o | "출력 projection" | head 연결 후 적용되는 `(d_model, d_model)` 행렬; head가 혼합되는 곳. |
| MQA | "하나의 KV head" | Multi-Query Attention: 단일 공유 K/V projection. 가장 작은 KV cache, 일부 품질 손실. |
| GQA | "Llama 2 이후 기본" | `n_kv_heads < n_heads`인 Grouped-Query Attention; Q와 매칭하기 위해 반복. |
| MLA | "DeepSeek의 트릭" | Multi-head Latent Attention: K,V가 저차원潜在로 압축되고, attend 시점에서 decompression. |
| Induction head | "In-context learning의 뒤편 회로" | 이전 발생을 감지하고 그 뒤에 있는 것을 복사하는 head 쌍. |

## 추가 자료

- [Vaswani et al. (2017). Attention Is All You Need §3.2.2](https://arxiv.org/abs/1706.03762) — 원래 multi-head 사양.
- [Shazeer (2019). Fast Transformer Decoding: One Write-Head is All You Need](https://arxiv.org/abs/1911.02150) — MQA 논문.
- [Ainslie et al. (2023). GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245) — 교육 후 MHA를 GQA로 변환하는 방법.
- [DeepSeek-AI (2024). DeepSeek-V2 Technical Report](https://arxiv.org/abs/2405.04434) — MLA와 cache 메모리에서 MHA/GQA를 이기는 이유.
- [Olsson et al. (2022). In-context Learning and Induction Heads](https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html) — head가 실제로 무엇을 하는지에 대한 기계적 분석.