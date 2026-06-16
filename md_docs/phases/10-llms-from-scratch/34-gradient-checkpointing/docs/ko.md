# 그래디언트 체크포인팅과 활성화 재계산

> 역전파는 모든 중간 활성화를 유지합니다. 70B 파라미터와 128K 컨텍스트에서 랭크당 3TB의 활성화입니다. 체크포인팅은 FLOPs와 메모리를 교환합니다: 저장 대신 재계산합니다. 문제는 어떤 세그먼트를 버릴 것인지이며, 답은 "전부"가 아닙니다.

**유형:** 구축
**언어:** Python (numpy 사용, 선택적으로 torch)
**사전 필요과목:** 10단계 04과 (미니-GPT 사전학습), 10단계 05과 (스케일링 및 분산)
**시간:** ~70분

## 문제

트랜스포머 학습은 각 층에 대해 역전파에서 미분되는 모든 연산에 대한 입력을 저장합니다: 어텐션 입력, Q/K/V 투영, 소프트맥스 출력, FFN 입력, 정규화 출력, 잔차 스트림. 은닉 크기 `d`, 시퀀스 길이 `L`, 배치 `B`를 가진 층에 대해 이는 층당 약 `12 * B * L * d` float입니다.

`d=8192, L=8192, B=1`의 경우 BF16에서 층당 800MB입니다. 64층 모델은 51GB의 활성화입니다 — 그리고 이는 마이크로배치 크기를 곱하기 전, 어텐션-소프트맥스 중간값(`L^2`/헤드)을 추가하기 전, 텐서-병렬 부분 복사본을 고려하기 전입니다.

양면 청구서: BF16 가중치 + 옵티마이저 상태는 80GB에 맞을 수 있지만, 활성화가 한계를 넘게 만듭니다. 그래디언트 체크포인팅(일명 활성화 재계산)이 표준 수정입니다. 대부분의 활성화를 버리고, 역전파 중에 순전파를 다시 실행하여 다시 얻습니다. 비용: 추가 FLOPs. 이점: 체크포인트 세그먼트 대 전체 층의 비율만큼 메모리가 감소합니다.

순진하게 수행하면 체크포인팅은 단계당 약 33% 더 많은 순전파 FLOPs 비용이 듭니다. 잘 수행하면(Korthikanti et al.의 "스마트 선택"에 따른 선택적 체크포인팅) 5% 미만의 FLOP 오버헤드로 5배 메모리를 절약합니다. 그리고 FP8 행렬곱, FSDP 오프로드, expert-parallel MoE에서 이것이 정말 중요합니다: 메모리나 낭비되는 연산 중 어느 것도 감당할 수 없습니다.

## 개념

### 역전파가 실제로 필요한 것

`output = layer(input)`. 역전파는 `grad_input`과 `grad_params`를 원합니다. 이를 계산하려면 다음이 필요합니다:

- `input` (선형 층의 `grad_params = input.T @ grad_output` 계산용)
- 일부 활성화 도함수 중간값 (ReLU/GELU/softmax의 도함수는 활성화 값에 의존)

순전파는 이를 자동으로 autograd 그래프에 저장합니다. 모든 `tensor.retain_grad()`와 입력이 필요한 모든 연산이 참조를 유지합니다.

### 순진한 전체 체크포인팅

네트워크를 `N`개의 세그먼트로 분할합니다. 순전파 중에는 각 세그먼트의 *입력*만 저장합니다. 역전파가 중간값을 필요로 할 때, 세그먼트의 순전파를 다시 실행하여 중간값을 구체화한 후 미분합니다.

예: 32층 트랜스포머를 각각 1층짜리 32개 세그먼트로 분할.

- 메모리: 32개 층-입력(작음) 대 32 * (층당 활성화 볼륨)(거대).
- 추가 연산: 세그먼트당 1회 추가 순전파, 즉 총 약 33% 더 많은 순전파 FLOPs (역전파가 2배 순전파이므로, 전체 단계는 1 + 2 = 3 단위 대신 1 + 1 + 2 = 4 단위가 됨).

이것이 원래 Chen et al. 2016 레시피입니다: 메모리와 연산의 균형을 맞추기 위해 `sqrt(L)`개 층마다 하나의 체크포인트. L=64의 경우 8개 체크포인트.

### 선택적 체크포인팅 (Korthikanti 2022)

모든 활성화 비용이 같은 것은 아닙니다. 어텐션 소프트맥스 출력은 `B*L*L*heads`이며 시퀀스 길이에 따라 *이차*로 증가합니다. FFN 은닉 활성화는 `B*L*4d`이며 선형으로 증가합니다. 긴 시퀀스의 경우 소프트맥스가 지배적입니다.

선택적 체크포인팅은 저장 비용이 저렴한 활성화(선형 투영, 잔차)를 유지하고 비용이 많이 드는 것(어텐션)만 재계산합니다. 재계산에 최소한의 FLOPs를 지불하지만 O(L^2) 메모리를 절약합니다.

Megatron-Core는 이를 "선택적" 활성화 재계산으로 구현합니다. 대부분의 2024+ 프런티어 학습 실행에서 사용됩니다.

### 오프로드

재계산의 대안: 순전파와 역전파 사이에 활성화를 CPU RAM으로 전송합니다. PCIe 대역폭이 필요합니다; 유휴 대역폭이 재구성 비용을 초과할 때 유용합니다. 혼합 전략이 일반적입니다: 일부 층은 체크포인팅, 다른 층은 오프로드.

FSDP2는 오프로드를 일급 옵션으로 제공합니다. 오프로드는 GPU가 메모리에서 병목이지만 CPU-GPU 전송에 여유가 있을 때 빛납니다.

### 재계산 비용 모델

`L`개 층 중 `k`개 층마다 순진한 체크포인팅을 사용한 단계당 FLOPs:

```
flops_fwd_normal = L * f_layer
flops_bwd_normal = 2 * L * f_layer
flops_total_normal = 3 * L * f_layer

flops_fwd_ckpt = L * f_layer
flops_recompute = L * f_layer  # 세그먼트 내 층당 1회 추가 순전파
flops_bwd_ckpt = 2 * L * f_layer
flops_total_ckpt = 4 * L * f_layer
overhead = 4 / 3 - 1 = 0.33 = 33%
```

선택적 체크포인팅으로 전체 층이 아닌 어텐션 커널만 재계산:

```
flops_recompute_selective = L * f_attention ~= L * f_layer * 0.15
overhead_selective = (3 + 0.15) / 3 - 1 = 0.05 = 5%
```

### 메모리 절약 모델

층당 활성화 볼륨: `A`. `L`개 층의 경우 총 활성화 메모리: `L * A`.

전체 체크포인트 (세그먼트 크기 1): `L * input_volume`만 저장 (~표준 트랜스포머의 `L * 1/10 A`). 약 `9 * L * A * 1/10` 절약.

`k`개 층마다 체크포인트: `L/k * A` + 활성 세그먼트 내 `k-1`개 층 분량 저장.

`k = sqrt(L)`에서 메모리와 재계산 비용 모두 `sqrt(L)`로 스케일링 — 균일 비용 층에 대한 최적 트레이드오프.

### 체크포인팅하지 말아야 할 때

- 이미 진행 중인 파이프라인 스테이지의 가장 안쪽 층. 어차피 완료되어야 합니다.
- 스테이지의 연산을 지배하는 첫 번째와 마지막 층 (트랜스포머에서는 드뭄).
- 이미 FlashAttention을 사용하는 어텐션 커널 — Flash는 이미 소프트맥스를 빠르게 재계산하므로, 추가 층-수준 체크포인팅이 거의 추가되지 않음.

### 구현 패턴

1. **함수 래퍼:** `torch.utils.checkpoint.checkpoint(fn, input)`으로 세그먼트를 래핑. PyTorch는 `input`만 저장하고, 역전파에서 나머지를 재계산.

2. **데코레이터 기반:** 층을 체크포인트 가능으로 표시; 트레이너가 설정 시간에 어떤 세그먼트를 래핑할지 결정.

3. **수동 명시적 재계산:** 직접 역전파를 작성하고, 저장된 입력으로 순전파를 복제하는 사용자 정의 `recompute_forward` 호출.

세 가지 모두 동일한 기능적 결과를 제공합니다. 래퍼가 표준 관용구입니다.

### TP / PP / FP8과의 상호작용

- **텐서 병렬:** 체크포인트 입력은 재계산 시 gather 또는 rescatter되어야 함; 통신 비용 처리.
- **파이프라인 병렬:** 일반적인 패턴은 각 파이프라인-스테이지의 순전파를 체크포인트하여 역순서 마이크로배치가 활성화 메모리를 재사용할 수 있도록 함.
- **FP8 재계산:** 재계산 중 업데이트된 amax 이력이 원래 순전파와 일치해야 함, 그렇지 않으면 FP8 스케일이 표류함. 대부분의 프레임워크가 스케일을 스냅샷함.

## 직접 구현하기

### 1단계: 세그먼트가 있는 장난감 모델

```python
import numpy as np


def linear_forward(x, w, b):
    return x @ w + b


def relu(x):
    return np.maximum(x, 0)


def layer_forward(x, w1, b1, w2, b2):
    h = relu(linear_forward(x, w1, b1))
    return linear_forward(h, w2, b2)


def model_forward(x, params):
    activations = [x]
    h = x
    for w1, b1, w2, b2 in params:
        h = layer_forward(h, w1, b1, w2, b2)
        activations.append(h)
    return h, activations
```

### 2단계: 모든 활성화가 필요한 순진한 역전파

```python
def model_backward(grad_output, activations, params):
    grads = [None] * len(params)
    g = grad_output
    for i in range(len(params) - 1, -1, -1):
        w1, b1, w2, b2 = params[i]
        x_in = activations[i]
        h_pre = linear_forward(x_in, w1, b1)
        h = relu(h_pre)
        gh = g @ w2.T
        gw2 = h.T @ g
        gb2 = g.sum(axis=0)
        g_pre = gh * (h_pre > 0)
        gx = g_pre @ w1.T
        gw1 = x_in.T @ g_pre
        gb1 = g_pre.sum(axis=0)
        grads[i] = (gw1, gb1, gw2, gb2)
        g = gx
    return g, grads
```

### 3단계: k개마다 체크포인트하는 메모리

```python
def model_forward_checkpointed(x, params, k=4):
    saved_inputs = [x]
    h = x
    for i, (w1, b1, w2, b2) in enumerate(params):
        h = layer_forward(h, w1, b1, w2, b2)
        if (i + 1) % k == 0:
            saved_inputs.append(h)
    return h, saved_inputs


def model_backward_checkpointed(grad_output, saved_inputs, params, k=4):
    grads = [None] * len(params)
    g = grad_output
    segments = [(j * k, min((j + 1) * k, len(params))) for j in range(len(saved_inputs))]
    for seg_idx in range(len(saved_inputs) - 1, -1, -1):
        start, end = segments[seg_idx]
        if start >= end:
            continue
        x_in = saved_inputs[seg_idx]
        _, seg_acts = model_forward(x_in, params[start:end])
        g, seg_grads = model_backward(g, seg_acts, params[start:end])
        for j, gr in enumerate(seg_grads):
            grads[start + j] = gr
    return g, grads
```

### 4단계: 비용 모델

```python
def checkpoint_cost(n_layers, segment_size, flops_per_layer=1.0):
    fwd = n_layers * flops_per_layer
    recompute = n_layers * flops_per_layer
    bwd = 2 * n_layers * flops_per_layer
    return {
        "fwd": fwd,
        "recompute": recompute,
        "bwd": bwd,
        "total": fwd + recompute + bwd,
        "overhead_vs_no_ckpt": (fwd + recompute + bwd) / (fwd + bwd) - 1.0,
    }


def selective_checkpoint_cost(n_layers, attention_fraction=0.15,
                              flops_per_layer=1.0):
    fwd = n_layers * flops_per_layer
    recompute = n_layers * attention_fraction * flops_per_layer
    bwd = 2 * n_layers * flops_per_layer
    return {
        "fwd": fwd,
        "recompute": recompute,
        "bwd": bwd,
        "total": fwd + recompute + bwd,
        "overhead_vs_no_ckpt": (fwd + recompute + bwd) / (fwd + bwd) - 1.0,
    }
```

### 5단계: 메모리 추정기

```python
def activation_memory_mb(n_layers, hidden=8192, seq=8192,
                        batch=1, bytes_per_value=2):
    per_layer = 12 * batch * seq * hidden * bytes_per_value
    return n_layers * per_layer / 1e6


def memory_after_checkpoint(n_layers, segment_size, hidden=8192,
                           seq=8192, batch=1, bytes_per_value=2):
    n_seg = max(1, n_layers // segment_size)
    saved = (n_seg + segment_size) * 1 * batch * seq * hidden * bytes_per_value
    return saved / 1e6
```

### 6단계: 최적 세그먼트 크기

```python
def optimal_segment(n_layers):
    return int(round(np.sqrt(n_layers)))
```

### 7단계: 선택적 체크포인트 결정

```python
def should_recompute(layer_type, activation_bytes, recompute_flops_ratio):
    if layer_type == "attention" and activation_bytes > 100 * 1e6:
        return True
    if layer_type == "ffn" and activation_bytes > 500 * 1e6:
        return recompute_flops_ratio < 0.1
    return False
```

## 활용하기

- **torch.utils.checkpoint**: `from torch.utils.checkpoint import checkpoint` — PyTorch의 표준 래퍼. 함수를 래핑; 입력만 저장, 역전파에서 재계산.
- **Megatron-Core 활성화 재계산**: `selective`, `full`, `block` 모드 지원. 2024+ 프런티어 학습의 표준.
- **FSDP2 오프로드**: `module.to_empty(device="cpu")` + FSDP2의 `offload_policy`로 활성화를 재계산 대신 CPU로 샤딩.
- **DeepSpeed ZeRO-Offload**: 옵티마이저 상태 및 활성화의 CPU 오프로드, 체크포인팅을 보완.

## 배포하기

이 과는 `outputs/prompt-activation-recompute-policy.md`를 생성합니다 — 모델 설정(층, 은닉, 시퀀스, 배치)과 사용 가능한 GPU 메모리를 받아 층별 재계산 정책(없음 / 선택적 / 전체 / 오프로드)을 출력하는 프롬프트.

## 연습 문제

1. 정확성을 검증하십시오. `model_forward` + `model_backward` (전체 활성화)와 `model_forward_checkpointed` + `model_backward_checkpointed` (세그먼트)를 실행하십시오. 파라미터 그래디언트가 기계 정밀도까지 동일해야 합니다.

2. 세그먼트 크기 `k`를 1부터 `L`까지 스윕하십시오. FLOP 오버헤드와 메모리를 플로팅하십시오. 곡선의 무릎을 찾으십시오.

3. 선택적 체크포인팅을 구현하십시오: 어텐션-모듈 입력은 저장하지만 중간값은 저장하지 않습니다. seq=8192에서 32층 모델의 FLOP 오버헤드를 전체-층 체크포인팅과 비교하여 측정하십시오.

4. 오프로드를 추가하십시오. 세그먼트 입력을 시뮬레이션된 "CPU 버퍼"(별도 리스트)에 저장하십시오. "PCIe 대역폭"을 바이트/시간으로 측정하고 오프로드와 재계산 사이의 손익분기점을 찾으십시오.

5. 실제 PyTorch 트랜스포머를 `torch.utils.checkpoint`를 사용할 때와 사용하지 않을 때 벤치마킹하십시오. 메모리(`torch.cuda.max_memory_allocated` 통해)와 단계 시간을 측정하십시오.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| 그래디언트 체크포인팅 | "순전파를 다시 실행하여 메모리 절약" | 세그먼트 입력만 저장; 역전파 중 그래디언트 지원 텐서를 얻기 위해 중간값 재계산 |
| 활성화 재계산 | "체크포인팅과 동일" | 동일한 기술의 HPC-풍 이름 |
| 세그먼트 크기 (k) | "체크포인트당 층 수" | 중간값이 함께 버려지고 재구성되는 층 수 |
| 선택적 체크포인팅 | "Korthikanti의 비결" | 저장 비용이 많이 드는 활성화(어텐션 소프트맥스)만 재계산; 저렴한 것은 유지 |
| 전체 체크포인팅 | "순진한 버전" | 모든 세그먼트에서 모든 층의 중간값 재계산 |
| 블록 체크포인팅 | "조립" | 전체 트랜스포머 블록 체크포인트; 가장 큰 세분화 |
| FLOP 오버헤드 | "연산 세금" | 단계당 추가 FLOPs = (재계산 FLOPs) / (fwd + bwd FLOPs); 순진 33%, 선택적 5% |
| 활성화 오프로드 | "CPU로 전송" | 순전파->역전파 사이에 활성화를 CPU RAM으로 이동; 재계산의 대안 |
| sqrt-L 규칙 | "고전적 최적점" | 균일 비용 층의 경우, 최적 체크포인트 간격은 sqrt(L)개 층 |
| 어텐션-소프트맥스 볼륨 | "O(L^2) 문제" | L^2 * 헤드 * 배치 float; 긴 컨텍스트에서 활성화 메모리를 지배 |

## 추가 자료

- [Chen et al., 2016 -- "Training Deep Nets with Sublinear Memory Cost"](https://arxiv.org/abs/1604.06174) -- 그래디언트 체크포인팅을 공식화한 원본 논문
- [Korthikanti et al., 2022 -- "Reducing Activation Recomputation in Large Transformer Models"](https://arxiv.org/abs/2205.05198) -- 선택적 활성화 재계산 및 공식 비용 분석
- [Pudipeddi et al., 2020 -- "Training Large Neural Networks with Constant Memory using a New Execution Algorithm"](https://arxiv.org/abs/2002.05645) -- 역방향 모드 재구성을 통한 일정 메모리 접근법 대안
- [Ren et al., 2021 -- "ZeRO-Offload: Democratizing Billion-Scale Model Training"](https://arxiv.org/abs/2101.06840) -- 대규모 활성화 오프로드
- [PyTorch torch.utils.checkpoint 문서](https://pytorch.org/docs/stable/checkpoint.html) -- 표준 API
- [Megatron-Core 활성화 재계산 문서](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/features/memory_optimizations.html) -- 선택적, 전체, 블록 모드
