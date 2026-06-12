# Speculative Decoding — Draft, Verify, Repeat

> Autoregressive 디코딩은 직렬이다. 각 토큰이 이전 토큰을 기다린다. Speculative decoding이 체인을 끊는다: 저렴한 모델이 N 토큰을 draft하고, 비싼 모델이 하나의 forward pass로 모든 N을 검증한다. Draft가 맞으면 N 생성을 위해 1번의 큰 forward를 지불했다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 07 (GPT Causal LM), Phase 7 · 12 (KV Cache & Flash Attention)
**소요 시간:** ~60분

## 문제

70B LLM이 하나의 토큰을 샘플링하는 데 H100에서 ~30ms가 걸린다. 3B draft 모델은 ~3ms가 걸린다. 3B draft를 5 토큰 앞서게 하고 70B를 실행하여 모든 5를 한 번에 검증하면, 총계는 승인된 최대 5개의 토큰에 대해 `5×3 + 30 = 45ms` — straight-line 생성의 경우 `5×30 = 150ms`와 대조적이다. 이것이 완전한 speculative-decodingpitch이다: 소량의 추가 GPU 메모리 (draft 모델)를 2–4× 더 낮은 디코드 지연 시간과 trade한다.

트릭은 분포를 보존해야 한다. Leviathan et al. (2023)과 Chen et al.가 동시에 도입한 speculative sampling은 출력 시퀀스가big 모델이 단독으로 생성했을 것과 **동일하게 분포**됨을 보장한다. 품질 tradeoff 없음. 그냥 더 빠르다.

2026년 추론의 네 가지 draft-verifier 쌍이 지배한다:

1. **Vanilla speculative (Leviathan 2023).** 별도의 draft 모델 (예: Llama 3 1B) + verifier (예: Llama 3 70B).
2. **Medusa (Cai 2024).** Verifier의 여러 디코딩 heads가 병렬로 위치 `t+1..t+k`를 예측. 별도의 draft 모델 없음.
3. **EAGLE family (Li 2024, 2025).** Verifier의 숨겨진 상태를 재사용하는 경량 draft; vanilla보다 가까운 수락율; 일반적인 3–4×.
4. **Lookahead decoding (Fu 2024).** Jacobi 반복; draft 모델이 전혀 필요하지 않다. Self-speculation. 틈새 시장이지만 의존성 없음.

2026년 모든 production 추론 스택이 기본적으로 speculative decoding을 제공한다. vLLM, TensorRT-LLM, SGLang 및 llama.cpp는 모두 최소 vanilla + EAGLE-2를 지원한다.

## 개념

### 핵심 알고리즘

Verifier `M_q`와 더 저렴한 draft `M_p`가 주어지면:

1. `x_1..x_k`를 이미 디코딩된 접두사로 한다.
2. **Draft**: `M_p`를 사용하여 draft 확률 `p_1..p_N`로 `d_{k+1}, d_{k+2}, ..., d_{k+N}`를 autoregressive하게 제안한다.
3. **병렬로 검증**: `x_1..x_k, d_{k+1}, ..., d_{k+N}`에 대해 `M_q`를 한 번 실행하여 위치 `k+1..k+N+1`에 대한 verifier 확률 `q_1..q_{N+1}`를 얻는다.
4. **각 draft 토큰을 좌에서 우로 수락/거부**: 각 `i`에 대해 확률 `min(1, q_i(d_i) / p_i(d_i))`로 수락.
5. 위치 `j`에서 첫 번째 거부 시: 잔여 분포 `(q_j - p_j)_+`에서 `t_j`를 샘플링. `j` 이후의 모든 draft는 폐기.
6. 모든 N을 승인 시: `q_{N+1}`에서 보너스 토큰 `t_{N+1}`를 샘플링.

잔여 분포 트릭이big 모델이 처음부터 샘플링했을 분포와 정확히 동일하게 출력을 유지하는 수학적 통찰력이다.

### 무엇이 속도를 결정하는가

`α` = 토큰당 예상 수락율. `c` = draft-to-verifier 비용 비율. 단계당:

- Naive 생성은 토큰당 1번의 큰 모델 호출.
- Speculative는 `α`가 높을 때 1/(1-α) 토큰당 1번의 큰 모델 호출.

`α = 0.75`와 `N = 5`의 일반적인 경험적 규칙: 큰 모델 호출이 3× 적음. Draft 비용은 5× 저렴. 총 벽시계가 ~2.5× 감소.

**α는 다음에 의존:**
- Draft가 verifier를 얼마나 잘 근사하는가. 동일한 패밀리 / 동일한 교육 데이터가 α를 크게 높임.
- 디코딩 전략. Greedy draft 대 greedy verifier: 높은 α. Temperature 샘플링: 일치하기更难; 수용 감소.
- 작업 유형. 코드 및 구조화된 출력은 더 많이 수락 (예측 가능); 자유 형식 창작 글은 더 적게 수락.

### Medusa — draft 없는 draft

Medusa는 draft 모델을 verifier의 추가 출력 heads로 대체한다. 위치 `t`에서:

```
shared trunk → hidden h_t
    ├── head_0: t+1의 토큰 예측 (표준 LM head)
    ├── head_1: t+2 예측
    ├── head_2: t+3 예측
    ├── head_3: t+4 예측
```

각 head는 고유한 로짓을 출력한다. 추론 시 각 head에서 샘플링하여 후보 시퀀스를 얻고, tree-attention 체계로 모든 후보 연속을 한 번에 고려하여 하나의 forward pass로 검증한다.

장점: 두 번째 모델 없음. 단점: 학습 가능한 매개변수 추가; 감독된 fine-tuning 단계 (~1B 토큰) 필요; 수락율이 vanilla speculative보다 약간 낮음.

### EAGLE — 숨겨진 상태를 재사용하여 더 나은 draft

EAGLE-1/2/3 (Li et al., 2024–2025)은 tiny transformer draft를 만들어 verifier의 마지막 레이어 숨겨진 상태를 수집한다. Draft가 verifier의 feature representation을 보기 때문에 예측이 verifier의 출력 분포와 강하게 상관된다. 수락율이 ~0.6 (vanilla)에서 0.85+로 상승한다.

EAGLE-3 (2025)은 후보 연속에 대한 tree search를 추가했다. vLLM과 SGLang은 Llama 3/4 및 Qwen 3의 기본 spec 경로로 EAGLE-2/3을 제공한다.

### KV cache dance

검증은 하나의 forward pass에서 `N` draft 토큰을 verifier에 공급한다. 이것은 verifier의 KV cache를 `N` 항목만큼 확장한다. 일부 draft가 거부되면 수락된 접두사 길이로 cache를 롤백해야 한다.

Production 구현 (vLLM의 `--speculative-model`, TensorRT-LLM의 LookaheadDecoder)은 scratch KV 버퍼로 처리한다. 먼저 쓰고 수락 시 커밋. 개념적으로 어렵지 않지만 fiddly하다.

## 실습

`code/main.py`를 참조. 핵심 speculative-sampling 알고리즘 (거부 단계 + 잔여 분포)을 다음으로 구현:

- 수락 수학을 분석적으로 검증할 수 있도록 손코딩된 분포에 대한 결정론적 softmax인 "큰 모델".
- 큰 모델의 섭동인 "draft 모델".
- 직접 샘플링과 동일한 한계 분포를 산출하는 수락/거부 루프.

### Step 1: 거부 단계

```python
def accept_or_reject(q_prob, p_prob, draft_token, u):
    ratio = q_prob / p_prob if p_prob > 0 else float("inf")
    return u < min(1.0, ratio)
```

`u`는 균일 무작위 수이다. `q_prob`는 draft된 토큰에 대한 verifier의 확률이다. `p_prob`는 draft 모델의 확률이다. Leviathan 정리에 따르면 이 Bernoulli 결정, followed by rejection에서 잔여 분포로부터 샘플링, verifier의 분포를 정확히 보존한다.

### Step 2: 잔여 분포

```python
def residual_dist(q, p):
    raw = [max(0.0, qi - pi) for qi, pi in zip(q, p)]
    s = sum(raw)
    return [r / s for r in raw]
```

요소별로 `q`에서 `p`를 빼고, 음수 값을 0으로 고정하고, 재정규화. 거부 시 여기서 샘플.

### Step 3: 하나의 speculative 단계

```python
def spec_step(prefix, q_model, p_model, N, rng):
    drafts = []
    p_probs = []
    ctx = list(prefix)
    for _ in range(N):
        p_dist = p_model(ctx)
        d = sample(p_dist, rng)
        drafts.append(d)
        p_probs.append(p_dist[d])
        ctx.append(d)

    q_dists = [q_model(prefix + drafts[:i]) for i in range(N + 1)]

    for i, d in enumerate(drafts):
        u = rng.random()
        q_prob = q_dists[i][d]
        p_prob = p_probs[i]
        if u < min(1.0, q_prob / p_prob if p_prob > 0 else float("inf")):
            prefix = prefix + [d]
        else:
            res = residual_dist(q_dists[i], p_model(prefix))
            prefix = prefix + [sample(res, rng)]
            return prefix
    prefix = prefix + [sample(q_dists[N], rng)]
    return prefix
```

5개 승인 → 1개의 보너스 → 하나의 verifier pass에서 6개의 토큰 생성.

### Step 4: 수락율 측정

다양한 draft 품질 수준에서 10,000개의 speculative 단계를 실행한다. 수락율 대 draft와 verifier 분포 간 KL 발산을 플롯한다. 깨끗한 단조 관계가 표시되어야 한다.

### Step 5: 분포 등가성 검증

실제로: speculative 루프가 생성한 토큰의 히스토그램이 verifier에서 직접 샘플링하여 생성된 히스토그램과 일치해야 한다. 이것이 실전의 Leviathan 정리이다. Chi-square 테스트가 샘플링 오류 내에서確認한다.

## 활용

Production:

```bash
# vLLM with EAGLE
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --speculative-model /models/llama-3.1-eagle-70b \
    --speculative-draft-tensor-parallel-size 1 \
    --num-speculative-tokens 5

# vLLM with vanilla draft model
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --speculative-model meta-llama/Llama-3.2-1B-Instruct \
    --num-speculative-tokens 5
```

TensorRT-LLM은 2026년 중반 현재 가장 빠른 Medusa 경로를 갖는다. `faster-whisper`가 작은 draft로 Whisper-large에 대한 speculative decoding을 래핑한다.

**Draft 선택:**

| 전략 | 선택하는 경우 | 스피드업 |
|----------|--------------|---------|
| Vanilla draft (1B/3B Llama 패밀리) | 빠른 프로토타입, 교육 없음 | 1.8–2.3× |
| Medusa heads | verifier를 fine-tune할 수 있음 | 2–3× |
| EAGLE-2 / 3 | Production, 최대 속도 | 3–4× |
| Lookahead | draft 없음, 교육 없음, 추가 매개변수 없음 | 1.3–1.6× |

**spec-decode를 하지 않는 경우:**

- 1–5 토큰의 단일 시퀀스 생성. 오버헤드가 지배.
- 자유 창작 / 고온도 샘플링 (α 감소).
- 메모리 제약 배포 (draft 모델이 VRAM 추가).

## 결과물

`outputs/skill-spec-decode-picker.md`를 참조. 이 skill는 새 추론 워크로드를 위해 speculative 디코딩 전략 (vanilla / Medusa / EAGLE / lookahead)과 튜닝 매개변수 (N, draft temperature)를 선택한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행한다. 50,000 토큰에서 speculative 토큰 분포가 chi-square p > 0.05 이내로 verifier의 직접 샘플 분포와 일치하는지 확인.
2. **보통.** `α = 0.5, 0.7, 0.85`에 대해 `N` 함수의 스피드업 (큰 모델 당 토큰 수)을 플롯한다. 각 α에 대한 최적의 `N`을 식별한다. (힌트: 검증 호출당 예상 토큰 = `(1 - α^{N+1}) / (1 - α)`.)
3. **어려움.** 작은 Medusa를 구현: Lesson 14의 최종 프로젝트 GPT를 가져와서 위치 t+2, t+3, t+4를 예측하는 3개의 추가 LM heads를 추가한다. 공동 다중 head 손실로 tinyshakespeare에서 교육. 동일한 모델을 자른 vanilla draft와 수락율을 비교.
4. **어려움.** 롤백을 구현: 10토큰 접두사 KV cache로 시작, 5 draft 토큰을 공급, 위치 3에서 거부를 시뮬레이션. 다음 반복에서 cache 읽기가 "접두사 + 처음 2개의 승인된 draft"와 올바르게 일치하는지 확인.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Draft model | "저렴한 것" | 후보 토큰을 제안하는 더 작은 모델; обычно 10–50× 더 저렴 than the verifier. |
| Verifier | "큰 것" | 분포를 보존하는 대상 모델; speculative 단계당 한 번 실행. |
| Acceptance rate (α) | "draft가 맞는 빈도" | 토큰당 verifier가 draft를 승인할 확률. 0.7–0.9 일반적. |
| Residual distribution | "거부 대체" | `(q - p)_+` 정규화; 거부 시 여기서 샘플링하면 verifier의 분포가 보존됨. |
| Bonus token | "무료 하나" | 모든 N draft가 승인되면 verifier의 다음 단계 분포에서 하나 더 샘플. |
| Medusa | "Draft 없는 speculative" | verifier의 여러 LM heads가 병렬로 위치 t+1..t+k를 예측. |
| EAGLE | "숨겨진 상태 draft" | verifier의 마지막 레이어 숨겨진 상태에 조건화된 tiny transformer draft. |
| Lookahead decoding | "Jacobi 반복" | 고정점 반복을 사용하는 self-speculation; draft 모델 없음. |
| Tree attention | "한 번에 많은 후보 검증" | 여러 draft 연속을 동시에 고려하는 분기 검증. |
| KV rollback | "거부된 draft 취소" | Scratch KV 버퍼; 수락 시 커밋, 거부 시 폐기. |

## 추가 자료

- [Leviathan, Kalman, Matias (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — 핵심 알고리즘과 등가성 정리.
- [Chen et al. (2023). Accelerating Large Language Model Decoding with Speculative Sampling](https://arxiv.org/abs/2302.01318) — 동시 도입; 깨끗한 Bernoulli-거부 증거.
- [Cai et al. (2024). Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774) — Medusa 논문; tree-attention 검증.
- [Li et al. (2024). EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077) — EAGLE-1; 숨겨진 상태 조건 draft.
- [Li et al. (2024). EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees](https://arxiv.org/abs/2406.16858) — EAGLE-2; 동적 트리 깊이.
- [Li et al. (2025). EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test](https://arxiv.org/abs/2503.01840) — EAGLE-3.
- [Fu et al. (2024). Break the Sequential Dependency of LLM Inference Using Lookahead Decoding](https://arxiv.org/abs/2402.02057) — lookahead, no-draft 접근법.
- [vLLM docs — Speculative Decoding](https://docs.vllm.ai/en/latest/features/spec_decode.html) — 네 가지 전략이 모두 연결된 표준 production 참조.
- [SafeAILab / EAGLE reference implementation](https://github.com/SafeAILab/EAGLE) — EAGLE-1/2/3의 참조 코드.