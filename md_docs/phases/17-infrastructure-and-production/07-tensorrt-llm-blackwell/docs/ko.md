# Blackwell에서 TensorRT-LLM 및 FP8 및 NVFP4

> TensorRT-LLM은 NVIDIA 전용이지만 Blackwell에서 이깁니다. GB200 NVL72 + Dynamo 오케스트레이션에서 SemiAnalysis InferenceX는 2026년 Q1-Q2에 120B 모델에서 백만 토큰당 $0.012를 측정했으며, H100 + vLLM에서 $0.09/M과 비교하여 — 7x 경제 격차. 스택은 세 가지 부동 소수점 체제가 복합된 것입니다: FP8은 KV 캐시와 어텐션 커널에 필요한 동적 범위를 가지므로 여전히 중요합니다; NVFP4 (4비트 마이크로스케일링)는 가중치와 activations를 처리합니다; 멀티 토큰 예측 (MTP) 및 분리된 prefill/decode가 그 위에 2-3배를 더합니다. Day-0 모델 지원은 사후 훈련 변환 없이 FP4 가중치를 직접 로드합니다. 2026년 엔지니어링 팀을 위한 단점: TRT-LLM은 닫힌 NVIDIA 스택이므로 채택하면 이식성을 처리량과 교환합니다. 커밋하기 전에 모델과 하드웨어의 조합에 대해 수학을 실행하세요.

**유형:** 학습
**언어:** Python (stdlib, toy FP8/NVFP4 메모리 및 비용 계산기)
**선수 과목:** Phase 17 · 04 (vLLM Serving Internals), Phase 10 · 13 (Quantization)
**소요 시간:** ~75분

## 학습 목표

- 가중치가 NVFP4에 있을 때에도 KV 캐시와 어텐션에 FP8이 여전히 중요한 이유를 설명합니다.
- BF16, FP8, NVFP4에서 프론티어 모델의 HBM 공간을 계산하고 절감이 어디서 오는지 추론합니다.
- TRT-LLM이 활용하는 Blackwell 특정 기능 (day-0 FP4, MTP, 분리된 서비스, all-to-all 프리미티브)의 이름을 붙입니다.
- TRT-LLM의 NVIDIA 잠금이 H100에서 vLLM 대비 7x 비용 격차보다 가치가 있는 때를 결정합니다.

## 문제

2026년 추론 경제학의 프론티어는 "토큰당 얼마"입니다. 답은 네 가지 쌓인 선택에 달려 있습니다: 하드웨어 세대 (Hopper H100/H200 대 Blackwell B200/GB200), 정밀도 (BF16 → FP8 → NVFP4), 서비스 엔진 (vLLM 대 SGLang 대 TRT-LLM), 오케스트레이션 (평면 대 분리 대 Dynamo).

Hopper에서 vLLM으로 120B MoE가 ~$0.09 백만 토큰당 실행됩니다. Blackwell에서 TRT-LLM + Dynamo로 같은 모델이 ~$0.012 — 7x 더 저렴합니다. 그 격차의 일부는 하드웨어입니다 (Blackwell은 Hopper 대비 GPU당 LLM 처리량이 11-15배). 일부는 스택입니다: FP4 가중치, MTP draft, 분리된 prefill/decode, MoE 전문가 통신을 위한 NVLink 5 all-to-all.

NVIDIA 스택 외부에서 이것을 복제할 수 없습니다. 그것이 tradeoffs입니다 — 이식성을 위한 경제학. 어떤 스택 선택이 격차의 어느 부분에 해당하는지 이해하는 것이 이 레슨의 요점입니다.

## 개념

### KV 캐시에 FP8이 여전히 바닥인 이유

2026년의 일반적인 실수: NVFP4가 모든 곳에 적용된다고 가정하는 것. 그렇지 않습니다. KV 캐시에는 FP8 (8비트 부동 소수점)이 필요합니다, 왜냐하면 광범위한 동적 범위를跨越하는 어텐션 키와 값을 저장하기 때문입니다. KV를 FP4로 양자화하면 catastrophic 정확도 손실이 발생합니다 — 분포의 꼬리가 사라지고 어텐션 점수가崩溃합니다. FP8의 지수 비트가 KV 캐시에 필요한 범위를 제공합니다.

NVFP4 (2025-2026)는 가중치와 activations에 적용됩니다. 마이크로스케일링: 가중치의 각 블록에는 자체 스케일 인자가 있으므로 작은 블록이 텐서별 스케일 손실 없이 다양한 동적 범위를跨越할 수 있습니다. Activations의 경우 FP4가 유지됩니다, 왜냐하면 activations는 레이어 내에서 작은 범위이기 때문입니다.

일반적인 Blackwell 구성:

- 가중치: NVFP4 (4비트 마이크로스케일링).
- Activations: NVFP4.
- KV 캐시: FP8.
- 어텐션 어큐뮬레이터: FP32 (softmax 안정성).

### TRT-LLM이 사용하는 Blackwell 특정 프리미티브

- **Day-0 FP4 가중치**: 모델 제공자가 FP4 가중치를 직접 배송합니다; TRT-LLM은 사후 훈련 변환 없이 로드합니다. FP4에 대한 AWQ / GPTQ 단계 없음.
- **멀티 토큰 예측 (MTP)**: EAGLE (Phase 17 · 05)과 동일한 아이디어이지만 TRT-LLM 빌드에 통합되었습니다.
- **분리된 서비스**: 별도의 GPU 풀에서 prefill 및 decode, NVLink 또는 InfiniBand를 통해 전송되는 KV 캐시. Dynamo (Phase 17 · 20)와 동일한 아이디어.
- **All-to-all 통신 프리미티브**: NVLink 5가 MoE 전문가 통신 지연 시간을 Hopper 대비 3x 줄였습니다. TRT-LLM의 MoE 커널은 이것에 맞게 조정되었습니다.
- **NVFP4 + MXFP8 마이크로스케일링**: Blackwell Tensor Cores에서 하드웨어 가속 스케일 인자 처리.

### 외워야 할 숫자

- HGX B200, TRT-LLM을 통한 GPT-OSS-120B에서 토큰당 $0.02.
- GB200 NVL72, Dynamo (TRT-LLM 오케스트레이션)를 통해 토큰당 $0.012.
- H100 + vLLM ≈ 동등한 작업에서 토큰당 $0.09.
- 2026년 3개월 동안 TRT-LLM 업데이트의 처리량 이득 2.8x.
- GPU당 LLM 처리량, Blackwell 대 Hopper 11-15x.
- MLPerf Inference v6.0 (2026년 4월): Blackwell이 제출된 모든 작업에서 지배합니다.

### FP4의 실제 품질 비용

NVFP4는 공격적입니다. 추론 무거운 작업 (사슬-의-사고, 수학, 긴 컨텍스트가 있는 코드 생성)에서 FP4 가중치가可视적으로 저하됩니다. 블록별 캘리브레이션이 완화하지만eliminate하지 않습니다. 추론 모델을 배송하는 팀은 종종 절충으로 FP8 가중치 + FP4 activations를 사용하거나 FP8 전반에 걸쳐 H200에 붙습니다.

규칙: NVFP4 가중치로 커밋하기 전에 항상 평가 집합에서 작업 품질을 검증하세요.

### 이것이 NVIDIA 잠금 결정인 이유

TRT-LLM은 C++ + CUDA + closed-source 커널입니다. 모델을 특정 GPU SKU에 대해 컴파일해야 합니다. AMD 없음, Intel 없음, ARM 없음. 인프라 전략이 멀티 벤더인 경우 TRT-LLM은 TRT-LLM 제공 계층에 대해 시작점이 아닙니다 — 여전히 혼합 하드웨어에서 vLLM에서 제공할 수 있습니다. NVIDIA 전용인 경우 7x 격차가 잠금 비용을 지불합니다.

### 2026년 실용적 레시피

연간 추론 청구서가 $100M 이상인 경우 Hopper + vLLM에서 실행하면 7-10배를 tables에 남깁니다. 비용 지배 작업을 Blackwell + TRT-LLM + Dynamo로 마이그레이션합니다. 모델 반복 속도를 위해 실험 계층을 H100 + vLLM으로 유지합니다. 프로덕션 전 각 NVFP4 변환 모델에서 품질을 검증합니다.

### 분리의 보너스

TRT-LLM의 분리된 서비스 (별도의 prefill 및 decode 풀)은 Phase 17 · 20에서 깊이 다루었습니다. Blackwell에서 승수는 쌓입니다: FP4 가중치 × MTP 스피드업 × 분리된 배치 × 캐시 인식 라우팅. 7x 숫자는 이 전체 스택을 가정합니다.

## 활용

`code/main.py`는 세 가지 스택에서 모델의 HBM 공간, decode 처리량 (메모리 바운드 체제), $/M-tokens를 계산합니다: H100 + BF16 + vLLM, H100 + FP8 + vLLM, B200 + NVFP4/FP8 + TRT-LLM. 각 변경이 기여하는 격차의複合 효과와 몫을 확인하기 위해 실행하세요.

## 결과물

이 레슨은 `outputs/skill-trtllm-blackwell-advisor.md`를 산출합니다. 작업, 모델 크기, 연간 토큰 볼륨이 주어지면 Blackwell + TRT-LLM 스택이 NVIDIA 잠금 비용보다 가치가 있는지를 결정합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 30% 활성 매개변수가 있는 120B MoE에서 H100 BF16, H100 FP8, B200 NVFP4/FP8에서 메모리 대역폭 제한 decode 처리량을 계산하세요. 가장 큰 점프가 어디서 오는지?
2. 고객이 H100 + vLLM에 연간 $2M을 지출합니다. 12개월 내에 TRT-LLM으로 마이그레이션 상환을 위해 구매해야 하는 Blackwell GPU의 균형 수는 얼마입니까? 7x 경제 격차를 감안할 때?
3. NVFP4 가중치 변환 후 MATH에서 정확도가 3포인트 떨어지는 것을 saw습니다. 두 가지 복구 경로의 이름을 붙이세요: 하나는 품질 우선 (FP8 가중치 유지), 하나는 비용 우선 (도메인 데이터로 캘리브레이션).
4. MLPerf v6.0 추론 결과를 읽으세요. 어떤 작업이 가장 작은 Blackwell-over-Hopper 격차를 가지며 왜?
5. 128k 컨텍스트에서 NVFP4 가중치 + FP8 KV 캐시로 405B 모델에 필요한 HBM을 계산하세요. 단일 GB200 NVL72 노드에 맞습니까?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| FP8 | "8비트 부동 소수점" | KV 캐시와 어텐션에 사용되는 8비트 부동 소수점; 필요한 동적 범위 때문 |
| NVFP4 | "4비트 마이크로" | NVIDIA의 4비트 마이크로스케일링 FP 형식; Blackwell에서 가중치와 activations |
| MXFP8 | "MX 8" | Blackwell Tensor Cores에서 하드웨어 가속되는 마이크로스케일링 FP8 변형 |
| Day-0 FP4 | "FP4 가중치 배송" | 모델 제공자가 이미 FP4로 가중치를 릴리스합니다; 사후 훈련 변환 단계 없음 |
| MTP | "멀티 토큰 예측" | TRT-LLM의 통합 스펙큘러티브 디코딩 draft (Phase 17 · 05) |
| 분리된 서비스 | "분리된 prefill/decode" | 별도의 GPU 풀에서 prefill과 decode; KV가 NVLink/IB를 통해 전송됨 |
| All-to-all | "MoE 전문가 통신" | 전문가 GPU로 토큰을 라우팅하는 통신 패턴; NVLink 5가 3x 절감 |
| InferenceX | "SemiAnalysis 추론 벤치마크" | 2026년 업계公认 비용-토큰 벤치마크 |

## 추가 자료

- [NVIDIA — Blackwell Ultra MLPerf Inference v6.0](https://developer.nvidia.com/blog/nvidia-blackwell-ultra-sets-new-inference-records-in-mlperf-debut/) — 2026년 4월 MLPerf 결과.
- [NVIDIA — Blackwell에서 MoE 추론](https://developer.nvidia.com/blog/delivering-massive-performance-leaps-for-mixture-of-experts-inference-on-nvidia-blackwell/) — NVLink 5 all-to-all 및 MoE 커널.
- [TensorRT-LLM 개요](https://nvidia.github.io/TensorRT-LLM/overview.html) — 공식 엔진 문서.
- [NVIDIA — Dynamo 소개](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/) — TRT-LLM 위의 분리된 오케스트레이션.
- [MLPerf Inference](https://mlcommons.org/benchmarks/inference-datacenter/) — Blackwell 숫자를 게시하는 벤치마크 제품군.