# Attention 변형 — Sliding Window, Sparse, Differential

> 완전한 attention은 원이다. 모든 토큰이 모든 토큰을 보고, 메모리가 그 대가를 지불한다. 네 가지 변형이 원의 모양을 구부리고 비용의 절반을 회복한다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 02 (Self-Attention), Phase 7 · 03 (Multi-Head), Phase 7 · 12 (KV Cache / Flash Attention)
**소요 시간:** ~60분

## 문제

완전한 attention은 시퀀스 길이에서 `O(N²)` 메모리와 `O(N²)` 계산을 costing한다. 128K-컨텍스트 Llama 3 70B의 경우 레이어당 160억 attention 항목, 80 레이어 곱하기. Flash Attention (Lesson 12)은 `O(N²)` 활성화 메모리를 숨기지만 산술 비용을 변경하지 않는다 — 모든 토큰이 여전히 다른 모든 토큰에 attend한다.

세 가지 클래스의 변형이 attention 행렬 자체의 위ولوج리를 변경한다:

1. **Sliding window attention (SWA).** 각 토큰이 전체 접두사가 아닌 고정 윈도우의 이웃에만 attend한다. 메모리와 계산이 `O(N · W)`로 떨어진다. 여기서 `W`는 윈도우. Gemma 2/3, Mistral 7B의 첫 번째 레이어, Phi-3-Long.
2. **Sparse / block attention.** 선택된 쌍 `(i, j)`만 스코어링된다; 나머지는 0 가중치로 강제된다. Longformer, BigBird, OpenAI sparse transformer.
3. **Differential attention.** 별도의 Q/K projection으로 두 개의 attention 행렬을 계산하고, 하나를 다른 것에서 뺀다. 첫 번째 몇 토큰에 가중치를 흐르는 "attention sink"를 죽인다. Microsoft's DIFF Transformer (2024).

これらは共存한다。2026년 프론티어 모델은 종종它们를混合한다: 대부분의 레이어는 SWA-1024, 5번째마다全局 전체 attention, 그리고 검색을 정리하는 differential heads가 소수 있다. Gemma 3의 5:1 SWA-to-global 비율이 현재 교과서 기본값이다.

## 개념

### Sliding Window Attention (SWA)

위치 `i`의 각 query는 `[i - W, i]` (causal SWA) 또는 `[i - W/2, i + W/2]` (양방향)의 위치에만 attend한다. 윈도우 밖의 토큰은 점수 행렬에서 `-inf`를 얻는다.

```
full causal:           sliding window (W=4):
positions 0-7          positions 0-7, W=4
    0 1 2 3 4 5 6 7        0 1 2 3 4 5 6 7
0 | x                0 |  x
1 | x x              1 |  x x
2 | x x x            2 |  x x x
3 | x x x x          3 |  x x x x
4 | x x x x x        4 |    x x x x
5 | x x x x x x      5 |      x x x x
6 | x x x x x x x    6 |        x x x x
7 | x x x x x x x x  7 |          x x x x
```

`N = 8192`와 `W = 1024`의 경우, 점수 행렬은预期적으로 1024 × 8192개의 非ゼロ 행을 갖는다 — 8× 감소.

**KV cache는 SWA와 함께 축소된다.** 레이어당 K와 V의 마지막 `W` 토큰만 유지하면 된다. Gemma-3-ish 구성 (1024 윈도우, 128K 컨텍스트)의 경우, KV cache가 128× 감소한다.

**품질 비용.** SWA 전용 transformer는 장기 검색에 어려움을 겪는다. 수정: SWA 레이어와 全注意力 레이어를 interleaving한다. Gemma 3은 5:1 SWA:global을 사용한다. Mistral 7B는 정보가 overlapping 윈도우를 통해 "forward로 흐르는" causal-SWA 스택을 사용했다 — 각 레이어가 유효 수용 필드를 `W`만큼 확장하고, `L` 레이어 후 모델은 `L × W` 토큰만큼 뒤로 attend할 수 있다.

### Sparse / Block Attention

미리 `N × N` 희소 패턴을 선택한다. 세 가지 표준 모양:

- **Local + strided (OpenAI sparse transformer).** 마지막 `W` 토큰 plus 그 이전의 모든 `stride`번째 토큰에 attend. `O(N · sqrt(N))` 계산으로 지역과 장거리 모두를 포착.
- **Longformer / BigBird.** 로컬 윈도우 + 모두에게 attend하고 모두에게 attend되는 소수의 全역 토큰 (예: `[CLS]`) + 무작위 희소 링크. 2× 컨텍스트에서 품질 일치. 
- **Native Sparse Attention (DeepSeek, 2025).** `(Q, K)`의 어떤 블록이 중요한지 학습; 커널 수준에서 제로 블록을 건너뛴다. FlashAttention 호환.

희소 attention은 커널 엔지니어링 이야기이다. 수학은 단순하다 (점수 행렬을 마스킹); 승리는 SRAM에 제로 항목을 로드하지 않음에서 온다. FlashAttention-3과 2026년 FlexAttention API는 사용자 정의 희소 패턴을 PyTorch에서 first-class로 만든다.

### Differential Attention (DIFF Transformer, 2024)

일반 attention에는 "attention sink" 문제가 있다: softmax는 모든 행이 1이 되도록 강제하므로, 특별한 것에 attend하고 싶지 않은 토큰은 첫 번째 토큰 (또는 처음 몇 개)에 가중치를 덤프한다. 이는 실제 콘텐츠로 갔어야 할 용량을 훔친다.

Differential attention은 **두 개의** attention 행렬을 계산하고 빼서修正한다:

```
A1 = softmax(Q1 K1^T / √d)
A2 = softmax(Q2 K2^T / √d)
DiffAttn = (A1 - λ · A2) V
```

여기서 `λ`는 학습된 스칼라 (typically 0.5–0.8). A1은 실제 콘텐츠 가중치를 포착; A2는 sink를 포착. 빼기가 sink를 상쇄하고 가중치를 관련 토큰에 재할당한다.

보고된 결과 (Microsoft 2024): perplexity 5–10% 낮춤, 동일한 교육 길이에서 1.5–2× 더 긴 유효 컨텍스트, 더 날카로운 바늘-건초반 검색.

### 변형 비교

| 변형 | 계산 | KV cache | 품질 vs 전체 | Production 사용 |
|---------|---------|----------|-----------------|----------------|
| 전체 attention | O(N²) | O(N) per layer | baseline | 모든 모델의 기본 레이어 |
| SWA (윈도우 1024) | O(N·W) | O(W) per layer | -0.1 ppl, global 레이어와 함께 양호 | Gemma 2/3, Phi-3-Long |
| Local + strided sparse | O(N·√N) | mixed | SWA와 유사 | OpenAI sparse transformer, Longformer |
| BigBird (local + global + random) | O(N) 근사 | mixed | 2× 컨텍스트에서 전체와 일치 | 초기 장기 컨텍스트 BERT |
| Native Sparse (DeepSeek-V3.2) | O(N · active fraction) | O(N) | 0.05 ppl 이내 | DeepSeek-V3.2, 2025 |
| Differential | O(2·N²) | O(2N) | -5 ~ -10% ppl | DIFF Transformer, 2026년 초기 모델 |

## 실습

`code/main.py`를 참조. 토이 시퀀스에서 전체, SWA, local+strided 및 differential attention을 나란히 보여주는 causal mask 비교자를 구현한다.

### Step 1: 전체 causal mask (baseline)

```python
def causal_mask(n):
    return [[0.0 if j <= i else float("-inf") for j in range(n)] for i in range(n)]
```

Lesson 07의 기준. 하삼각; 대각선 위에는 0 가중치.

### Step 2: sliding window causal mask

```python
def swa_mask(n, window):
    M = [[float("-inf")] * n for _ in range(n)]
    for i in range(n):
        lo = max(0, i - window + 1)
        for j in range(lo, i + 1):
            M[i][j] = 0.0
    return M
```

하나의 매개변수 — `window`. `window >= n`에 대해 전체 causal attention을 recover한다. `window = 1`에 대해 각 토큰은 자신에게만 attend한다.

### Step 3: local + strided sparse mask

```python
def strided_mask(n, window, stride):
    M = [[float("-inf")] * n for _ in range(n)]
    for i in range(n):
        lo = max(0, i - window + 1)
        for j in range(lo, i + 1):
            M[i][j] = 0.0
        for j in range(0, i + 1, stride):
            M[i][j] = 0.0
    return M
```

모든 `stride`번째 토큰까지의 시퀀스 시작에 더한 조밀한 로컬 윈도우 plus. 추가 레이어로 수용 필드가 로그 단계로 성장한다.

### Step 4: differential attention

```python
def diff_attention(Q1, K1, Q2, K2, V, lam):
    A1 = softmax_causal(Q1 @ K1.T / sqrt_d)
    A2 = softmax_causal(Q2 @ K2.T / sqrt_d)
    return (A1 - lam * A2) @ V
```

두 번의 attention 통과, 학습된 혼합 계수로 빼기. 코드에서 단일 vs 차등의 attention-sink 히트맵을 비교하고 sink가崩溃하는 것을 본다.

### Step 5: KV cache 크기

각 변형에 대해 `N = 131072`에서 레이어당 캐시 크기를 인쇄한다. SWA와 희소 변형이 10–100× 감소한다. Differential은 두 배. 의식적으로 메모리 빚을 지다.

## 활용

2026년 production 패턴:

```python
from transformers import AutoModelForCausalLM
# Gemma 3은 SWA (윈도우=1024)와 全局 레이어를 5:1로混合한다.
model = AutoModelForCausalLM.from_pretrained("google/gemma-3-27b-it")
# print(model.config.sliding_window, model.config.layer_types)
```

PyTorch 2.5+의 FlexAttention이 mask 함수를accepts한다:

```python
from torch.nn.attention.flex_attention import flex_attention, create_block_mask

def swa_pattern(b, h, q_idx, kv_idx):
    return (q_idx - kv_idx < 1024) & (q_idx >= kv_idx)

mask = create_block_mask(swa_pattern, B=batch, H=heads, Q_LEN=n, KV_LEN=n)
out = flex_attention(q, k, v, block_mask=mask)
```

이것은 사용자 정의 Triton 커널로 컴파일된다. 일반적인 패턴에서 FlashAttention-3 속도의 10% 이내, mask 함수는 Python callable이다.

**각각을 선택하는 경우:**

- **순수 전체 attention** — ~16K 컨텍스트까지 모든 레이어, 또는 검색 품질이 가장 중요한 경우.
- **SWA + global mix** — 장기 컨텍스트 (>32K), 교육 및 추론 메모리 제한. 32K 이상에서 2026년 기본값.
- **Sparse block attention** — 사용자 정의 커널, 사용자 정의 패턴. 전문화된 워크로드 (검색, 오디오)용.
- **Differential attention** — attention-sink 오염이 해로운 모든 워크로드 (장기 컨텍스트 RAG, 바늘-건초반).

## 결과물

`outputs/skill-attention-variant-picker.md`를 참조. 이 skill는 대상 컨텍스트 길이, 검색 요구 사항 및 교육/추론 계산 프로파일을 고려하여 새 모델에 대한 attention 위OLOG 선택한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행한다. `window=4`의 SWA가 각 행의 마지막 4 토큰 밖의 모든 것을 0으로 만드는지 확인한다. `window=n`이 전체 causal attention과 비트 단위로 동일하게 재현되는지 확인.
2. **보통.** Lesson 07 최종 프로젝트 위에 `window=1024`로 causal SWA를 구현한다. tinyshakespeare에서 1,000단계 교육. Val 손실이 전체 attention보다 얼마나 회귀하는가? Peak 메모리가 얼마나 감소하는가?
3. **어려움.** 최종 프로젝트 모델에서 Gemma-3 스타일 5:1 레이어 혼합 (5 SWA, 1 global)을 구현한다. 일치하는 매개변수에서 pure-SWA 및 pure-global 기준과 비교한다.
4. **어려움.** Head당 학습된 `λ`로 differential attention을 구현한다. 합성 검색 작업 (하나의 바늘, 2,000개의 방해물)에서 교육. 일치하는 매개변수에서 단일 attention 기준과 검색 정확도를 비교.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Sliding window attention (SWA) | "로컬 attention" | 각 query가 마지막 `W` 토큰에 attend; KV cache가 `O(W)`로 축소. |
| Effective receptive field | "모델이 얼마나 멀리 보는가" | 창 `W`가 있는 `L`-레이어 SWA 스택에서 최대 `L × W` 토큰. |
| Longformer / BigBird | "Local + global + random" | 항상 attend하는 소수의 全역 토큰이 있는 희소 패턴; 초기 장기 컨텍스트 접근법. |
| Native Sparse Attention | "DeepSeek의 커널 트릭" | 블록 수준 희소성을 학습; 품질을 유지하면서 커널 수준에서 제로 블록을 건너뛴다. |
| Differential attention | "두 맵, 하나가 빼기" | DIFF Transformer: 첫 번째에서 두 번째 attention 맵의 학습된 `λ` 배를 빼서 attention sink를 상쇄. |
| Attention sink | "가중치가 토큰 0으로 새는" | Softmax 정규화가 행 합계를 1로 강제; 정보 없는 query가 위치 0에 가중치를 덤프. |
| FlexAttention | "Mask-as-Python" | PyTorch 2.5+ API that compiles arbitrary mask functions into FlashAttention-shape kernels. |
| Layer type mix | "5:1 SWA-to-global" | 더 낮은 메모리에서 품질을 유지하기 위해 스택에서 희소와 全注意力 레이어를 interleaving. |

## 추가 자료

- [Beltagy, Peters, Cohan (2020). Longformer: The Long-Document Transformer](https://arxiv.org/abs/2004.05150) — 표준 sliding-window + global-token 논문.
- [Zaheer et al. (2020). Big Bird: Transformers for Longer Sequences](https://arxiv.org/abs/2007.14062) — local + global + random.
- [Child et al. (2019). Generating Long Sequences with Sparse Transformers](https://arxiv.org/abs/1904.10509) — OpenAI의 local+strided 패턴.
- [Gemma Team (2024). Gemma 2: Improving Open Language Models at a Practical Size](https://arxiv.org/abs/2408.00118) — 1:1 SWA:global 혼합.
- [Gemma Team (2025). Gemma 3 technical report](https://arxiv.org/abs/2503.19786) — 이제 교과서 기본값인 window=1024의 5:1 혼합.
- [Ye et al. (2024). Differential Transformer](https://arxiv.org/abs/2410.05258) — DIFF Transformer 논문.
- [Yuan et al. (2025). Native Sparse Attention](https://arxiv.org/abs/2502.11089) — DeepSeek-V3.2의 학습된 희소성 attention.
- [PyTorch — FlexAttention blog and docs](https://pytorch.org/blog/flexattention/) — Use It의 mask-as-callable 패턴에 대한 API 참조.