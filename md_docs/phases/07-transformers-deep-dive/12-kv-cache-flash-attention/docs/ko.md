# KV Cache, Flash Attention & 추론 최적화

> 교육은 병렬이고 FLOP가 제한한다. 추론은 직렬이고 메모리가 제한한다. 다른 병목, 다른 트릭.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 02 (Self-Attention), Phase 7 · 05 (Full Transformer), Phase 7 · 07 (GPT)
**소요 시간:** ~75분

## 문제

순진한 autoregressive decoder는 N개의 토큰을 생성하기 위해 O(N²) 작업을 수행한다: 각 단계에서 전체 접두사에 대해 attention을 다시 계산한다. 4K 토큰 응답에 대해 16M attention 작업, 그 대부분이 중복된다. 접두사 토큰의 모든 숨겨진 상태는 한 번 계산되면 결정론적이다 — 이전 모든 것의 캐시된 키와 값에 대해 새로운 토큰 쿼리만 실행하면 된다.

그 위에, attention 자체가 많은 데이터를 이동한다. 표준 attention은 N×N 점수 행렬, N×d softmax 출력, N×d 최종 출력을 구체화한다 — HBM에 너무 많은 읽기/쓰기. N≥2K에서 attention은 FLOP 제한보다 먼저 메모리 제한이 된다. 클래식 attention 커널은 현대 GPU를 4–10× 미사용한다.

Dao et al.의 두 가지 최적화가 프론티어 추론을 "느림"에서 "빠름"으로 밀어붙였다:

1. **KV cache.** 모든 접두사 토큰의 K와 V 벡터를 저장한다. 각 새 토큰의 attention은 캐시된 키에 대한 하나의 쿼리이다. 추론이 생성 단계당 O(N²)에서 O(N으로 감소.
2. **Flash Attention.** 전체 N×N 행렬이 HBM에 도달하지 않도록 attention 계산을 타일링한다. 모든 softmax + matmul이 SRAM에서 발생. A100에서 2–4× 벽시계 속도 향상; H100에서 FP8으로 5–10×.

2026년까지 둘 다 보편적이다. 모든 production 추론 스택 (vLLM, TensorRT-LLM, SGLang, llama.cpp)이它们를 가정한다. 모든 프론티어 모델이 Flash Attention을 활성화한 상태로 제공한다.

## 개념

![KV cache 성장과 Flash Attention 타일링](../assets/kv-cache-flash-attn.svg)

### KV cache 수학

decoder 레이어당, 토큰당, head당:

```
bytes_per_token_per_layer = 2 * d_head * dtype_size
                           ^
                           K and V
```

32 레이어, 32 heads, d_head=128, fp16가 있는 7B 모델의 경우:

```
레이어당 토큰당 = 2 * 128 * 2 = 512 bytes
토큰당 (32 레이어) = 16 KB
32K 컨텍스트당 = 512 MB
```

80 레이어, d_head=128, 8 KV heads의 GQA가 있는 Llama 3 70B의 경우:

```
레이어당 토큰당 = 2 * 8 * 128 * 2 = 4096 bytes (4 KB)
32K 컨텍스트당 = 10.4 GB
```

그 10 GB가 Llama 3 70B가 128K 컨텍스트에서 배치 크기 1에서 KV cache에만 40 GB A100의 대부분이 필요한 이유이다.

**GQA가 KV-cache 승리이다.** 64 heads의 MHA는 32 GB가 된다. MLA는 더 압축한다.

차원을 드래그하고 캐시 크기가 어떻게 이동하는지 지켜본다. 시퀀스 길이나 배치를 올리면 단일 GPU를 얼마나 빨리 초과하는지 본다:

```figure
kv-cache-sizer
```

### Flash Attention — 타일링 트릭

표준 attention:

```
S = Q @ K^T          (HBM 읽기, N×N, HBM 쓰기)
P = softmax(S)       (HBM 읽기, HBM 쓰기)
O = P @ V            (HBM 읽기, HBM 쓰기)
```

세 번의 HBM 라운드 트립. H100에서 HBM 대역폭은 3 TB/s; SRAM은 30 TB/s. 모든 HBM 트립은 온칩에 모든 것을 유지하는 것 대비 10배의 속도 저하이다.

Flash Attention:

```
각 Q 블록에 대해 (타일 크기 ~128 × 128):
    Q_tile를 SRAM로 로드
    각 K, V 블록에 대해:
        K_tile, V_tile를 SRAM로 로드
        S_tile = Q_tile @ K_tile^T     (SRAM)
        실행 중인 softmax 집계             (SRAM)
        O_tile로 누적                  (SRAM)
    O_tile를 HBM로 쓰기
```

타일당 1번의 HBM 트립. 총 메모리 풋프린트가 O(N²)에서 O(N으로 감소. 역방향 pass는 저장하는 대신 전방향 pass의 일부 값을 다시 계산한다 — 또 다른 메모리 승리.

**수치 트릭.** 실행 중인 softmax는 최종 정규화가 정확하도록 타일 전반에 `(max, sum)`을 유지한다. 근사가 아니다 — Flash Attention은 표준 attention과 비트 단위로 동일한 출력을 계산한다 (fp16 비결합성 modulo).

**버전 진화:**

| 버전 | 연도 | 주요 변경 | 기준 하드웨어의 스피드업 |
|---------|------|-----------|-------------------------------|
| Flash 1 | 2022 | 타일형 SRAM 커널 | A100에서 2× |
| Flash 2 | 2023 | 더 나은 병렬 처리, causal-first 순서 | A100에서 3× |
| Flash 3 | 2024 | Hopper 비동기, FP8 | H100에서 ~1.5–2× (~740 TFLOPs FP16) |
| Flash 4 | 2026 | Blackwell 5단계 파이프라인, software exp2 | 추론 우선 (초기에는 forward만) |

Flash 4는 출시 시 forward-pass 전용이다. 교육은 여전히 Flash 3을 사용한다. Flash 4에 대한 GQA 및 varlen 지원은 보류 중 (2026년 중반).

### Speculative decoding — 또 다른 지연 시간 승리

저렴한 모델이 N 토큰을 제안한다. 큰 모델이 모두 병렬로 N을 검증한다. 검증이 k 토큰을 수락하면 k 생성을 위해 1번의 큰 모델 forward pass를 지불했다. 코드와 산문에서 일반적인 k=3–5.

2026년 기본값:
- **EAGLE 2 / Medusa.** 검증자의 숨겨진 상태를 공유하는 통합 draft heads. 품질 손실 없이 2–3× 스피드업.
- **초안 모델이 있는 투술적 디코딩.** 소비자 하드웨어에서 2–4× 스피드업.
- **예측 디코딩.** Jacobi 반복; draft 모델 필요 없음. 틈새 시장이지만 무료.

### 연속 배칭

클래식 배칭 추론: 가장 느린 시퀀스가 완료될 때까지 기다린 다음 새 배치를 시작한다. 짧은 응답이 일찍 완료되면 GPU가 낭비된다.

연속 배칭 (Orca에서 처음 제공, 이제 vLLM, TensorRT-LLM, SGLang):旧的完成하면すぐに新しいリクエストをバッチに插入する。典型的なチャットワークロードで5-10×のスループット向上。

### PagedAttention — 가상 메모리로서의 KV cache

vLLM의 주요 기능. KV cache는 16토큰 블록으로 할당된다; 페이지 테이블이 논리적 위치를 물리적 블록에 매핑한다. 병렬 샘플 (beam search, 병렬 샘플링) 간 KV 공유, 프롬프트 캐싱용 핫 스왑, 메모리 단편화를 방지할 수 있다. 순진한 연속 할당보다 4× 동시 처리 향상.

## 실습

`code/main.py`를 참조. 구현:

1. 순진한 O(N²) 증분 decoder.
2. O(N) KV-cached decoder.
3. Flash Attention의 실행 중 최대 알고리즘을 시뮬레이션하는 타일형 softmax.

### Step 1: KV cache

```python
class KVCache:
    def __init__(self, n_layers, n_heads, d_head):
        self.K = [[[] for _ in range(n_heads)] for _ in range(n_layers)]
        self.V = [[[] for _ in range(n_heads)] for _ in range(n_layers)]

    def append(self, layer, head, k, v):
        self.K[layer][head].append(k)
        self.V[layer][head].append(v)

    def read(self, layer, head):
        return self.K[layer][head], self.V[layer][head]
```

단순함: per-layer, per-head 리스트에서 토큰당 K, V 벡터를 계속 증가시킨다.

### Step 2: 타일형 softmax

```python
def tiled_softmax_dot(q, K, V, tile=4):
    """실행 중 max/sum이 있는 Flash-attention 스타일 softmax(qK^T)V."""
    m = float("-inf")
    s = 0.0
    out = [0.0] * len(V[0])
    for start in range(0, len(K), tile):
        k_block = K[start:start + tile]
        v_block = V[start:start + tile]
        scores = [sum(qi * ki for qi, ki in zip(q, k)) for k in k_block]
        new_m = max(m, *scores)
        exp_old = math.exp(m - new_m) if m != float("-inf") else 0.0
        exp_new = [math.exp(sc - new_m) for sc in scores]
        s = s * exp_old + sum(exp_new)
        for j in range(len(out)):
            out[j] = out[j] * exp_old + sum(e * v[j] for e, v in zip(exp_new, v_block))
        m = new_m
    return [o / s for o in out]
```

작업 중 작업 세트가 전체 `N × d_head`가 아닌 `tile × d_head` 블록이지만, 한 번에 `softmax(qK) V`와 비트 단위로 동일한 출력.

### Step 3: 100토큰 생성에서 순진 vs 캐시 디코딩 비교

Attention 작업 수를 센다. 순진: O(N²) = 5050. 캐시: O(N) = 100. 코드가 둘 다 인쇄한다.

## 활용

```python
# HuggingFace transformers는 decoder-only generate()에서 KV cache를 자동으로 활성화한다.
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B",
    attn_implementation="flash_attention_2",  # Hopper면 FA3 사용
    torch_dtype="bfloat16",
)
# generate()는 자동으로 KV cache를 사용한다
```

vLLM production:

```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --tensor-parallel-size 4 \
    --max-model-len 32768 \
    --enable-prefix-caching \
    --kv-cache-dtype fp8
```

요청 간 접두사 캐싱은 2026년 큰 승리이다 — 동일한 시스템 프롬프트, few-shot 예제 또는 긴 컨텍스트 문서가 호출 간 KV를 재사용한다. 반복되는 도구 프롬프트가 있는 에이전트 워크로드의 경우, 접두사 캐싱은 일반적으로 5× 동시 처리 승리이다.

## 결과물

`outputs/skill-inference-optimizer.md`를 참조. 이 skill는 새 추론 배포에 대한 attention 구현, KV cache 전략, 양자화 및 투술적 디코딩을 선택한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행한다. 순진하고 캐시된 decoder가 동일한 출력을 생성하는지 확인; 작업 수 차이를 note.
2. **보통.** 접두사 캐싱을 구현: 프롬프트 P와 여러 완료가 주어지면, P에 대해 하나의 forward pass를 실행하여 KV cache를 채우고, 완료당 분기한다. 각 완료에 대해 P를 다시 인코딩하는 것과 비교하여 속도 향상을 측정한다.
3. **어려움.** 토이 PagedAttention을 구현: 고정 16토큰 블록의 KV cache와 free-list가 있는 것. 시퀀스가 완료되면 블록을 풀에 반환한다. 다양한 길이의 1,000 채팅 완료를 시뮬레이션한다. 연속 할당 대비 메모리 단편화를 비교한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| KV cache | "디코딩을 빠르게 만드는 트릭" | 모든 접두사 토큰의 저장된 K와 V; 새 쿼리가 다시 계산하는 대신它们를 attend한다. |
| HBM | "GPU 메인 메모리" | High Bandwidth Memory; H100에서 80 GB, B200에서 192 GB. ~3 TB/s 대역폭. |
| SRAM | "온칩 메모리" | SM당 빠른 메모리, H100에서 ~256 KB/SM. ~30 TB/s 대역폭. |
| Flash Attention | "타일형 attention 커널" | N×N을 HBM에 구체화하지 않고 attention을 계산. |
| Continuous batching | "대기 없는 배칭" | 시퀀스가 완료되면排出し、新的ものを待たずに batch に参加させる. |
| PagedAttention | "vLLM의 주요 기능" | KV cache가 고정 블록과 페이지 테이블로 할당됨; 단편화를 없앤다. |
| Prefix caching | "긴 프롬프트 재사용" | 요청 간 공유 접두사에 대한 KV 캐시; 에이전트에게 주요 비용 절감. |
| Speculative decoding | "Draft + 확인" | 저렴한 draft 모델이 토큰을 제안; 큰 모델이 한 번에 k를 확인. |

## 추가 자료

- [Dao et al. (2022). FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) — Flash 1.
- [Dao (2023). FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691) — Flash 2.
- [Shah et al. (2024). FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](https://arxiv.org/abs/2407.08608) — Flash 3.
- [FlashAttention-4 release notes (Dao-AILab, 2026)](https://github.com/Dao-AILab/flash-attention) — Blackwell 5단계 파이프라인 및 software-exp2 트릭; 이 수업이 언급하는 forward 전용 출시caveats에 대해서는 repo README를 읽는다.
- [Kwon et al. (2023). Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) — vLLM 논문.
- [Leviathan et al. (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — spec 디코딩.
- [Li et al. (2024). EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077) — 수업이 인용하는 통합 draft 접근법의 EAGLE-1/2 논문.
- [Cai et al. (2024). Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774) — EAGLE와 함께 언급된 Medusa 접근법.
- [vLLM docs — PagedAttention](https://docs.vllm.ai/en/latest/design/kernel/paged_attention.html) — 16토큰 블록 및 페이지 테이블 설계에 대한 표준 심층 분석.