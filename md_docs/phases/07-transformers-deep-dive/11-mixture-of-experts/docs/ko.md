# Mixture of Experts (MoE)

> Dense 70B transformer는 모든 토큰에 대해 모든 매개변수를 활성화한다. 671B MoE는 토큰당 37B만 활성화하며 모든 벤치마크에서 이를 이긴다. 희소성은 이 10년간 가장 중요한 스케일링 아이디어이다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 05 (Full Transformer), Phase 7 · 07 (GPT)
**소요 시간:** ~45분

## 문제

추론 시 dense transformer의 FLOP는 매개변수 수와 같다 (forward pass에 2배). Dense 모델을 스케일업하면 모든 토큰이 전액을 지불한다. 2024년까지 프론티어는 계산 벽에 부딪혔다: 의미 있게 더 똑똑해지려면 토큰당 기하급수적으로 더 많은 FLOP가 필요했다.

Mixture of Experts는 이 링크를 끊는다. 각 FFN을 `E`개의 독립적인 experts + 토큰당 `k` experts를 선택하는 router로 대체한다. 총 매개변수 = `E × FFN_size`. 토큰당 활성 매개변수 = `k × FFN_size`. Typical 2026 구성: `E=256`, `k=8`. 스토리지는 `E`와 함께 스케일, 계산은 `k`와 함께 스케일.

2026년 프론티어는 거의 전적으로 MoE이다: DeepSeek-V3 (671B 총 / 37B 활성), Mixtral 8×22B, Qwen2.5-MoE, Llama 4, Kimi K2, gpt-oss. Artificial Analysis의 독립 리더보드에서 상위 10개 오픈소스 모델은 모두 MoE이다.

## 개념

![MoE 레이어: router가 토큰당 E개의 experts 중 k개를 선택](../assets/moe.svg)

### FFN 스왑

Dense transformer 블록:

```
h = x + attn(norm(x))
h = h + FFN(norm(h))
```

MoE 블록:

```
h = x + attn(norm(x))
scores = router(norm(h))              # (N_tokens, E)
top_k = argmax_k(scores)              # 토큰당 E 중 k 선택
h = h + sum_{e in top_k}(
        gate(scores[e]) * Expert_e(norm(h))
    )
```

모든 expert는 독립적인 FFN이다 (일반적으로 SwiGLU). Router는 단일 선형 레이어이다. 각 토큰은 자체 `k` experts를 선택하고 그 출력의 게이트된 mixture를 얻는다.

### 로드 밸런싱 문제

Router가 experts 3을 통해 토큰의 90%를 보내면, 다른 experts는 굶주린다. 세 가지 해결책이 시도되었다:

1. **Auxiliary load-balancing loss** (Switch Transformer, Mixtral). Expert 사용량의 분산에 비례하는 페널티를 추가한다. 작동하지만 하이퍼파라미터와 두 번째 gradient 신호를 추가한다.
2. **Expert capacity + token dropping** (early Switch). 각 expert는 최대 `C × N/E` 토큰을 처리한다; 오버플로 토큰은 레이어를 건너뛴다. 품질을 해친다.
3. **Auxiliary-loss-free balancing** (DeepSeek-V3). Router의 top-k 선택을 이동시키는 학습된 per-expert bias를 추가한다. Bias는 교육 손실 외부에서 업데이트된다. 주요 목표에 페널티 없음. 2024년의 큰解锁.

DeepSeek-V3의 접근 방식: 각 교육 단계 후, 모든 expert에 대해 사용량이 목표 이상인지 이하인지 확인한다. Bias를 `±γ`만큼 조정한다. 선택은 `scores + bias`를 사용한다. Gating에 사용되는 expert 확률은 변경되지 않은 원본 `scores`이다. Routing을 표현에서 분리한다.

### 공유 experts

DeepSeek-V2/V3는 또한 experts를 *공유*와 *라우팅됨*으로 나눈다. 모든 토큰은 모든 공유 expert를 통과한다. 라우팅된 experts는 top-k를 통해 선택된다. 공유 experts는 공통 지식을 포착; 라우팅된 experts는 전문화한다. V3는 256개의 라우팅된 중 top-8 plus 1개의 공유 expert를 실행한다.

### 세분화된 experts

클래식 MoE (GShard, Switch): 각 expert는 전체 FFN만큼 넓다. `E`는 작다 (8–64), `k`는 작다 (1–2).

현대 세분화된 MoE (DeepSeek-V3, Qwen-MoE): 각 expert가 더 좁다 (FFN 크기의 1/8). `E`가 크다 (256+), `k`가 더 크다 (8+). 총 매개변수 동일하지만 조합이 훨씬 더 빠르게 스케일. 토큰당 가능한 "experts" `C(256, 8) = 400조`. 품질이 올라가고 지연 시간은 평평하게 유지된다.

### 비용 프로파일

토큰당, 레이어당:

| 구성 | 토큰당 활성 매개변수 | 총 매개변수 |
|--------|-----------------------|--------------|
| Mixtral 8×22B | ~39B | 141B |
| Llama 3 70B (dense) | 70B | 70B |
| DeepSeek-V3 | 37B | 671B |
| Kimi K2 (MoE) | ~32B | 1T |

DeepSeek-V3는 토큰당 **더 적은 활성 FLOP**로 Llama 3 70B (dense)를 거의 모든 벤치마크에서 이긴다. 더 많은 매개변수 = 더 많은 지식. 더 많은 활성 FLOP = 토큰당 더 많은 계산. MoE는它们를 분리한다.

### 단점: 메모리

활성 여부와 관계없이 모든 experts가 GPU에 있다. 671B 모델은 fp16 가중치에 ~1.3 TB의 VRAM이 필요하다. 프론티어 MoE 배포에는 expert 병렬 처리가 필요하다 — experts를 GPU에 분산시키고, 토큰을 네트워크를 통해 라우팅한다. 지연 시간은 matmul이 아니라 all-to-all 통신에 의해 지배된다.

## 실습

`code/main.py`를 참조. Pure stdlib의 컴팩트한 MoE 레이어:

- `n_experts=8` SwiGLU-ish experts (설명을 위해 각각 하나의 선형)
- top-k=2 라우팅
- softmax 정규화된 게이팅 가중치
- per-expert bias를 통한 auxiliary-loss-free balancing

### Step 1: router

```python
def route(hidden, W_router, top_k, bias):
    scores = [sum(h * w for h, w in zip(hidden, W_router[e])) for e in range(len(W_router))]
    biased = [s + b for s, b in zip(scores, bias)]
    top_idx = sorted(range(len(biased)), key=lambda i: -biased[i])[:top_k]
    # 선택된 experts의 ORIGINAL 점수에 대해 softmax
    chosen = [scores[i] for i in top_idx]
    m = max(chosen)
    exps = [math.exp(c - m) for c in chosen]
    s = sum(exps)
    gates = [e / s for e in exps]
    return top_idx, gates
```

Bias가 게이트 가중치가 아닌 선택에 영향을 미친다. 그것이 DeepSeek-V3 트릭이다 — bias는 모델의 예측을 조종하지 않고 로드 불균형을 교정한다.

### Step 2: 100개 토큰을 router를 통해 실행

어떤 experts가 얼마나 자주 활성화되는지 추적한다. bias 없으면 사용량이 왜곡된다. bias 업데이트 루프가 있으면 (`-γ` 오버사용 experts, `+γ` 언더사용), 사용량이 몇 iterations에서 균일한 분포로 수렴한다.

### Step 3: 매개변수 수 비교

MoE 구성의 "dense 등가"를 인쇄한다. DeepSeek-V3 형태: 256 라우팅 + 1 공유, 8 활성, d_model=7168. 총 매개변수 수는 눈물 나는 수치이다. 활성 수는 dense Llama 3 70B의 7분의 1이다.

## 활용

HuggingFace 로딩:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("mistralai/Mixtral-8x22B-v0.1")
```

2026년 production 추론: vLLM은 MoE 라우팅을 네이티브로 지원한다. SGLang이 가장 빠른 expert 병렬 경로가 있다. 둘 다 자동으로 top-k 선택과 expert 병렬 처리를 처리한다.

**MoE를 선택하는 경우:**
- 토큰당 낮은 추론 비용으로 프론티어 품질을 원한다.
- VRAM / expert 병렬 인프라가 있다.
- 워크로드가 토큰 무겁다 (채팅, 코드) 컨텍스트 무겁지 않다 (긴 문서).

**MoE를 선택하지 않는 경우:**
- 에지 배포 — 활성 FLOP에 대해 전체 스토리지 비용을 지불한다.
- 지연 시간에 민감한 단일 사용자 제공 — expert 라우팅이 오버헤드를 추가한다.
- 작은 모델 (<7B) — MoE의 품질 이점은 계산 임계값 (~6B 활성 매개변수) 이상에서만 나타난다.

## 결과물

`outputs/skill-moe-configurator.md`를 참조. 이 skill는 매개변수 예산, 교육 토큰 및 배포 대상을 고려하여 새 MoE에 대한 E, k 및 공유 expert 레이아웃을 선택한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행한다. 50 iterations에서 auxiliary-loss-free bias 업데이트가 expert 사용량을 어떻게 평활하게 하는지 지켜본다.
2. **보통.** 학습된 router를 해시 기반 router로 교체한다 (결정론적, 학습 없음). 품질과 균형을 비교한다. 학습된 router가 더 나은 이유는 무엇인가?
3. **어려움.** GRPO 스타일의 "rollout-matched routing" (DeepSeek-V3.2 트릭)을 구현: 추론 중 어떤 experts가 활성화되는지 로그를 남기고, gradient 계산 중에 동일한 라우팅을 강제한다. 토이 policy-gradient 설정에서 효과를 측정한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Expert | "많은 FFN 중 하나" | 독립적인 feed-forward network; FFN 계산의 희소 슬라이스에 전념한 매개변수. |
| Router | "게이트" | 각 토큰을 각 expert에 대해 스코어하는 작은 선형 레이어; top-k 선택. |
| Top-k routing | "토큰당 k개의 활성 experts" | 각 토큰의 FFN 계산이 정확히 k experts를 통과하고, 게이트로 가중치화됨. |
| Auxiliary loss | "로드 밸런스 페널티" | 왜곡된 expert 사용량을 페널티하는 추가 손실 항. |
| Auxiliary-loss-free | "DeepSeek-V3의 트릭" | Router의 선택에만 per-expert bias를 통한 밸런싱; 추가 gradient 없음. |
| Shared expert | "항상 온" | 모든 토큰이 통과하는 추가 expert; 공통 지식 포착. |
| Expert parallelism | "expert로 분산" | 다른 GPU에 다른 experts를 분산; 네트워크를 통해 토큰 라우팅. |
| Sparsity | "활성 매개변수 < 총 매개변수" | 비율 `k × expert_size / (E × expert_size)`; DeepSeek-V3의 경우 37/671 ≈ 5.5%. |

## 추가 자료

- [Shazeer et al. (2017). Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer](https://arxiv.org/abs/1701.06538) — 아이디어.
- [Fedus, Zoph, Shazeer (2022). Switch Transformer: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961) — Switch, 클래식 MoE.
- [Jiang et al. (2024). Mixtral of Experts](https://arxiv.org/abs/2401.04088) — Mixtral 8×7B.
- [DeepSeek-AI (2024). DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) — MLA + auxiliary-loss-free MoE + MTP.
- [Wang et al. (2024). Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts](https://arxiv.org/abs/2408.15664) — bias 기반 밸런싱 논문.
- [Dai et al. (2024). DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models](https://arxiv.org/abs/2401.06066) — 이 수업의 router가 사용하는 세분화 + 공유 expert 분할.
- [Kim et al. (2022). DeepSpeed-MoE: Advancing Mixture-of-Experts Inference and Training](https://arxiv.org/abs/2201.05596) — 원래 공유 expert 논문.