# 추측적 디코딩과 EAGLE

> 프런티어 LLM이 하나의 토큰을 생성하려면 수십억 개의 파라미터에 대한 전체 순전파가 필요합니다. 그 순전파는 엄청나게 과잉 공급됩니다: 대부분의 경우 훨씬 더 작은 모델이 다음 3-5개 토큰을 올바르게 추측할 수 있으며, 큰 모델은 추측을 *검증*만 하면 됩니다. 추측이 맞다면 하나의 비용으로 5개의 토큰을 얻습니다. 추측적 디코딩 (Leviathan et al. 2023)은 이를 정확하게 만들었고, EAGLE-3 (2025)는 수락률을 검증당 약 4.5개 토큰으로 밀어 올렸습니다 — 일치하는 출력 분포에서 4-5배 속도 향상.

**유형:** 구축
**언어:** Python (numpy 사용)
**사전 필요과목:** 10단계 12과 (추론 최적화), 10단계 04과 (미니-GPT 사전학습)
**시간:** ~75분

## 학습 목표

- 표준 추측적 디코딩 루프(초안 K개 토큰, 검증, 수락/기각 규칙, 보너스 토큰)를 설명할 수 있다
- Leviathan 기각 규칙이 검증기의 분포를 정확히 보존함을 증명할 수 있다
- 초안 수락률 `α`와 초안 길이 `K`가 주어졌을 때 기대 속도 향상을 계산할 수 있다
- numpy로 2-모델 추측적 디코딩 루프를 구현하고 경험적 분포 일치를 검증할 수 있다
- EAGLE-스타일 트리 초안 작성 및 특징 재사용이 표준 추측적 디코딩을 개선하는 방법을 설명할 수 있다

## 문제

H100에서 70B급 모델의 디코드 처리량은 일반적으로 초당 40-80 토큰입니다. 각 토큰은 HBM에서 모든 모델 가중치를 읽는 전체 순전파가 필요합니다. 출력을 변경하지 않고 모델을 더 작게 만들 수 없습니다. 메모리 이상으로 배치 크기를 늘릴 수 없습니다. 막혔습니다 — 순전파당 모델이 하나 이상의 토큰을 출력하도록 할 수 없다면 말입니다.

자기회귀 생성은 본질적으로 직렬처럼 보입니다: `x_{t+1} = sample(p(· | x_{1:t}))`. 하지만 동시성 기회가 있습니다. "다음 4개 토큰은 아마 [a, b, c, d]일 것이다"라고 말하는 저렴한 예측자가 있다면, **큰 모델의 단일 순전파**로 5개 위치를 모두 검증하고 가장 긴 일치 프리픽스를 수락할 수 있습니다.

Leviathan, Kalai, Matias (2023, "Fast Inference from Transformers via Speculative Decoding")는 목표 모델의 샘플링 분포를 보존하는 영리한 수락/기각 규칙을 통해 이를 정확하게 만들었습니다. 동일한 출력 분포, 2-4배 빠름.

## 개념

### 두-모델 설정

- **목표 모델** `M_p`: 크고, 느리고, 고품질인, 실제로 샘플을 원하는 모델. 분포: `p(x)`.
- **초안 모델** `M_q`: 작고, 빠르고, 저품질인 모델. 분포: `q(x)`. 5-30배 더 작음.

단계당:

1. 초안 모델이 `K`개의 토큰을 자기회귀적으로 제안: `x_1, x_2, ..., x_K ~ q`.
2. 목표 모델이 모든 `K+1`개 위치에 대해 하나의 순전파를 병렬로 실행하여 각 제안된 토큰에 대해 `p(x_k)`를 생성.
3. 아래의 수정된 기각 샘플링 규칙을 통해 각 토큰을 왼쪽에서 오른쪽으로 수락/기각. 가장 긴 일치 프리픽스를 수락.
4. 어떤 토큰이든 기각되면 수정된 분포에서 대체품을 샘플링하고 중단. 그렇지 않으면 `p(· | x_1...x_K)`에서 보너스 토큰 하나를 샘플링.

초안이 목표와 완벽하게 일치하면 목표-순전파당 K+1개 토큰을 얻습니다. 초안이 위치 1에서 틀리면 1개 토큰만 얻습니다.

### 정확성 규칙

추측적 디코딩은 **분포적으로 p에서 샘플링하는 것과 증명 가능하게 동등**합니다. 기각 규칙:

```
각 초안 토큰 x_t에 대해:
    r ~ Uniform(0, 1)
    if r < p(x_t) / q(x_t):
        x_t 수락
    else:
        잔차에서 대체품 샘플링: (p - q)+ / ||(p - q)+||_1
        중단
```

여기서 `(p - q)+`는 점별 차이의 양의 부분을 나타냅니다. 초안과 목표가 일치하면(`p ≈ q`) 수락이 거의 1입니다. 일치하지 않으면, 전체 샘플이 여전히 정확히 `p`가 되도록 잔차 분포가 구성됩니다.

**탐욕적 경우.** temperature=0 샘플링의 경우 `argmax(p) == x_t`만 확인합니다. 맞으면 수락; 아니면 `argmax(p)`를 출력하고 중단.

### 기대 속도 향상

초안 모델의 토큰-수준 수락률이 `α`이면, 목표-순전파당 기대 생성 토큰 수는:

```
E[tokens] = (1 - α^{K+1}) / (1 - α)        # K = 초안 길이, α in [0, 1]
```

`α = 0.8, K = 4`: `(1 - 0.8^5)/(1 - 0.8) = 3.36` 토큰/순전파. 단일 목표 순전파는 대략 `cost_q * K + cost_p` 비용 (K번의 초안 단계 + 한 번의 목표 검증). `cost_p >> cost_q * K`이면 속도 향상 비율은 처리량 기준 `3.36× / 1 = 3.36×`입니다.

유일한 실제 파라미터는 `α`이며, 이는 전적으로 초안-목표 정렬에 달려 있습니다. 좋은 초안이 전부입니다.

### 초안 학습: 증류

무작위 작은 모델은 좋은 초안이 아닙니다. 표준 레시피는 목표에서 증류하는 것입니다:

1. 작은 아키텍처 선택 (70B 목표에 ~1B, 7B 목표에 ~500M).
2. 대규모 텍스트 코퍼스에서 목표 모델 실행; 다음-토큰 분포 저장.
3. 목표의 분포에 대한 KL 발산으로 초안 학습 (정답 토큰이 아닌).

결과: `α`는 코딩에서 일반적으로 0.6-0.8, 자연어 채팅에서 0.7-0.85. 프로덕션에서 2-3배 속도 향상.

### EAGLE: 트리 초안 작성 + 특징 재사용

Li, Wei, Zhang, Zhang (2024, "EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty")는 표준 추측적 디코딩에서 두 가지 비효율성을 관찰했습니다:

1. 초안이 K번의 직렬 단계를 수행하며, 각각 전체 스택입니다. 하지만 초안은 가장 최근 검증의 목표 특징(은닉 상태)을 재사용할 수 있습니다 — 목표는 이미 초안이 처음부터 다시 유도하고 있는 풍부한 표현을 계산했습니다.
2. 초안이 선형 사슬을 출력합니다. 초안이 후보의 *트리*를 출력할 수 있다면(각 노드가 여러 추측), 목표의 단일 순전파가 트리 어텐션 마스크를 통해 여러 후보 경로를 병렬로 검증하고 가장 긴 수락된 가지를 선택할 수 있습니다.

EAGLE-1 변경:
- 초안 입력 = 위치 t에서 목표의 최종 은닉 상태, 원시 토큰이 아님.
- 초안 아키텍처 = 1개 트랜스포머 디코더 층 (별도의 작은 모델이 아님).
- 출력 = 깊이당 K = 4-8개 후보의 트리, 깊이 4-6.

EAGLE-2 (2024)는 동적 트리 토폴로지를 추가합니다: 초안이 불확실한 곳에서 트리가 더 넓어지고, 확신하는 곳에서 좁게 유지됩니다. 검증 비용을 증가시키지 않고 `α_effective`를 높입니다.

EAGLE-3 (Li et al. 2025, "EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test")는 고정된 최상위 층 특징 의존성을 제거하고 새로운 "테스트-시간 시뮬레이션" 손실로 초안을 학습시킵니다 — 초안은 교사 강제 학습 분포가 아닌 목표의 테스트-시간 분포와 일치하는 출력에서 학습됩니다. 수락률이 0.75(EAGLE-2)에서 0.82(EAGLE-3)로 상승하고, 평균 토큰/검증이 3.0에서 4.5로 증가합니다.

### 트리 어텐션 검증

초안이 트리를 출력할 때, 목표 모델은 **트리 어텐션 마스크**를 사용하여 단일 순전파로 검증합니다 — 순수한 선 대신 트리 토폴로지를 인코딩하는 인과 마스크. 각 토큰은 트리에서 자신의 조상에만 주목합니다. 검증 패스는 여전히 하나의 순전파, 하나의 행렬곱입니다; 토폴로지 마스크는 몇 개의 추가 KV 항목만 필요로 합니다.

```
        root
       /    \
      a      b
     / \    / \
    c  d   e   f
```

`a, b`가 경쟁하는 첫-토큰 후보이고 `c, d, e, f`가 두 번째-토큰 후보이면, 6개 위치 모두 하나의 순전파에서 검증됩니다. 출력은 어떤 수락된 경로를 따라 가장 긴 프리픽스입니다.

### 언제 이기고, 언제 지는가

**이기는 경우:**
- 예측 가능한 텍스트(코드, 일반 영어, 구조화된 출력)가 있는 채팅/완성. `α`가 높습니다.
- 디코드 중 사용되지 않은 GPU 연산이 있는 설정(메모리-바운드 단계). 트리 초안 작성은 사용 가능한 FLOPs를 사용합니다.

**지는 경우 / 이점 없음:**
- 매우 높은 확률적 출력(높은 온도에서 창의적 글쓰기). `α`가 `1/|vocab|` 쪽으로 떨어집니다.
- 매우 높은 동시성을 가진 배치 서빙 — 배치가 이미 FLOPs를 채우며, 트리 검증을 위한 여지가 거의 없습니다.
- 초안이 훨씬 작지 않은 매우 작은 목표 모델.

프로덕션 샵은 일반적으로 채팅에서 2-3배, 코드 생성에서 3-5배, 창의적 글쓰기에서 거의 0에 가까운 벽시계 속도 향상을 보고합니다.

## 직접 구현하기

`code/main.py`:

- 정확한 기각 규칙을 구현하고 목표의 분포를 보존함을 검증하는 참조 `speculative_decode(target, draft, prompt, K, temperature)` (경험적 KL < 0.01 대 일반 목표 샘플링).
- top-p 분기로 깊이-K 트리를 구축하는 EAGLE-스타일 트리 초안자.
- 검증기를 위한 올바른 인과 패턴을 생성하는 트리 어텐션 마스크 구축자.
- 작은 LM에서 둘 다 실행하는 수락률 하네스 (GPT-2-medium 목표에서 GPT-2-small 증류).

```python
def speculative_step(p_target, q_draft, K, temperature=1.0):
    """추측적 디코딩의 한 라운드. 수락된 토큰 리스트 반환."""
    # 1. K개 토큰 초안 작성
    draft_tokens = []
    q_probs = []
    state = draft_state_init()
    for _ in range(K):
        probs = softmax(q_draft(state) / temperature)
        t = np.random.choice(len(probs), p=probs)
        draft_tokens.append(t)
        q_probs.append(probs[t])
        state = draft_step(state, t)

    # 2. 목표가 모든 초안 위치 + 1개 추가에서 p 계산
    p_probs_all = target_forward_batched(p_target, draft_tokens, temperature)

    # 3. 왼쪽에서 오른쪽으로 수락/기각
    accepted = []
    for k, tok in enumerate(draft_tokens):
        r = np.random.uniform()
        if r < p_probs_all[k][tok] / q_probs[k]:
            accepted.append(tok)
        else:
            residual = np.maximum(p_probs_all[k] - q_probs[k], 0)
            residual /= residual.sum()
            accepted.append(np.random.choice(len(residual), p=residual))
            return accepted
    # 4. 모든 K개 수락 → 목표에서 보너스 토큰 샘플링
    accepted.append(np.random.choice(len(p_probs_all[-1]), p=p_probs_all[-1]))
    return accepted
```

## 활용하기

- **vLLM**과 **SGLang**은 일급 추측적 디코딩을 제공합니다. 플래그: `--speculative_model`, `--num_speculative_tokens`. EAGLE-2/3 지원은 `--spec_decoding_algorithm eagle` 플래그를 통해.
- **NVIDIA TensorRT-LLM**은 Medusa와 EAGLE 트리를 네이티브로 지원합니다.
- **참조 초안 모델**: `Qwen/Qwen3-0.6B-spec` (Qwen3-32B용 초안), `meta-llama/Llama-3.2-1B-Instruct-spec` (70B용 초안).
- **Medusa 헤드** (Cai et al. 2024, "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads"): 초안 모델 대신 목표 자체에 K개의 병렬 예측 헤드를 추가합니다. 배포가 더 간단하고, EAGLE보다 약간 낮은 수락률.

## 배포하기

이 과는 `outputs/skill-speculative-tuning.md`를 생성합니다 — 목표 모델의 워크로드를 프로파일링하고 초안 모델, K(초안 길이), 트리 너비, 온도, 일반 디코드로의 폴백 시점을 선택하는 스킬입니다.

## 연습 문제

1. 정확한 기각 규칙을 구현하고 경험적으로 검증하십시오. `speculative_decode`와 일반 목표 샘플링을 통해 10K 샘플을 실행하십시오; 두 출력 분포 간의 TV 거리를 계산하십시오. 0.01 미만이어야 합니다.

2. 속도 향상 공식을 계산하십시오. 고정된 `α`와 `K`가 주어지면 목표-순전파당 기대 토큰을 플로팅하십시오. α ∈ {0.5, 0.7, 0.9}에 대한 최적 K를 찾으십시오.

3. 작은 초안을 학습시키십시오. 124M GPT-2 목표를 가지고 30M GPT-2 초안을 100M 토큰에서 KL 손실로 증류하십시오. 보류 텍스트에서 `α`를 측정하십시오. 예상: 0.6-0.7.

4. EAGLE-스타일 트리 초안 작성을 구현하십시오. 사슬 대신 초안이 각 깊이에서 top-3 분기를 출력하도록 하십시오. 트리 어텐션 마스크를 구축하십시오. 목표가 가장 긴 올바른 가지를 수락하는지 확인하십시오.

5. 실패 모드를 측정하십시오. temperature=1.5(높은 확률성)에서 추측적 디코딩을 실행하십시오. α가 붕괴되고 초안 오버헤드로 인해 알고리즘이 일반 디코딩보다 느려짐을 보이십시오.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| 목표 모델 | "큰 모델" | 느리고 고품질인, 샘플을 원하는 모델 (p 분포) |
| 초안 모델 | "추측자" | 작고 빠른 예측자 (q 분포); 5-30배 더 작음 |
| K / 초안 길이 | "미리보기" | 검증 패스당 추측된 토큰 수 |
| α / 수락률 | "적중률" | 초안의 제안이 수락되는 토큰당 확률 |
| 정확한 기각 규칙 | "수락 테스트" | 목표의 분포를 보존하는 r < p/q 비교 |
| 잔차 분포 | "수정된 p-q" | (p - q)+ / ||(p - q)+||_1, 기각 시 샘플링할 분포 |
| 트리 초안 작성 | "분기 추측" | 초안이 후보 트리를 출력, 트리-구조 어텐션 마스크로 한 번에 검증 |
| 트리 어텐션 마스크 | "토폴로지 마스크" | 각 노드가 자신의 조상에만 주목하도록 트리 토폴로지를 인코딩하는 인과 마스크 |
| Medusa 헤드 | "병렬 헤드" | 목표 자체의 K개 추가 예측 헤드; 별도의 초안 모델 없음 |
| EAGLE 특징 재사용 | "은닉 상태 초안" | 초안 입력이 원시 토큰이 아닌 목표의 마지막 은닉 상태여서 초안 축소 |
| 테스트-시간 시뮬레이션 손실 | "EAGLE-3 학습" | 교사 강제가 아닌 목표의 테스트-시간 분포와 일치하는 출력에서 초안 학습 |

## 추가 자료

- [Leviathan, Kalai, Matias, 2023 — "Fast Inference from Transformers via Speculative Decoding"](https://arxiv.org/abs/2211.17192) -- 정확한 기각 규칙 및 이론적 속도 향상 분석
- [Chen, Borgeaud, Irving et al., 2023 — "Accelerating Large Language Model Decoding with Speculative Sampling"](https://arxiv.org/abs/2302.01318) -- DeepMind의 동시 추측적 샘플링 논문
- [Cai, Li, Geng, Wang, Wang, Zhu, Dao, 2024 — "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads"](https://arxiv.org/abs/2401.10774) -- 초안 모델의 대안인 병렬-헤드
- [Li, Wei, Zhang, Zhang, 2024 — "EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty"](https://arxiv.org/abs/2401.15077) -- 특징 재사용 및 트리 초안 작성
- [Li et al., 2024 — "EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees"](https://arxiv.org/abs/2406.16858) -- 동적 트리 토폴로지
- [Li et al., 2025 — "EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test"](https://arxiv.org/abs/2503.01840) -- 학습-시간 테스트-시간 일치
- [Fu, Haotian, Peng et al., 2024 — "Break the Sequential Dependency of LLM Inference Using Lookahead Decoding"](https://arxiv.org/abs/2402.02057) -- Jacobi/lookahead 디코딩, 초안 없는 대안
