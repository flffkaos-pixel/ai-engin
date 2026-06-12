# 분리된 Prefill/Decode — NVIDIA Dynamo 및 llm-d

> Prefill은 계산 바운드입니다; decode는 메모리 바운드입니다. 둘 다 같은 GPU에서 실행하면 한 가지 리소스가浪费됩니다. 분리는它们를 별도의 풀로 분할하고 NIXL (RDMA/InfiniBand 또는 TCP 폴백)을 통해 KV 캐시를 它们 사이에서 전송합니다. NVIDIA Dynamo (GTC 2025 발표, 1.0 GA)는 vLLM/SGLang/TRT-LLM 위에 있습니다 — Planner Profiler + SLA Planner가 SLO를 충족하기 위해 prefill:decode 비율을 자동 조정합니다. NVIDIA는 이 범위에서 처리량 이득을 게시합니다 — developer.nvidia.com (2025-06)는 GB200 NVL72 + Dynamo에서 DeepSeek-R1 MoE에 대해 중간 지연 시간 체제에서 ~6x 개선을 보여줍니다, 그리고 Dynamo 제품 페이지 (developer.nvidia.com, 날짜 없음)는 GB300 NVL72 + Dynamo에서 Hopper 대비 최대 50x MoE 처리량을 광고합니다. "30x" 수치는 전체 스택 Blackwell + Dynamo + DeepSeek-R1 보고서에 대한 커뮤니티 집계입니다; 30x를 정확히陈述하는 단일 기본 소스를 찾지 못했으므로 방향성 주장으로 취급하세요. llm-d (Red Hat + AWS)는 Kubernetes 네이티브입니다: prefill / decode / 라우터를 역할별 HPA가 있는 독립적인 Services로. llm-d 0.5는 계층적 KV 오프로딩, 캐시 인식 LoRA 라우팅, UCCL 네트워킹, scale-to-zero를 추가합니다. 경제학: 복수 고객 공개의 내부 롤업은 $2M 클래스 추론 지출에서collocated 서비스에서 Dynamo로의 전환 시 동등한 SLA에서 30-40% 절감 ($600-800K/年)을 제안합니다; 특정 $2M→$600-800K 수치는 단일 게시 사례 연구가 아닌 내부 복합입니다 — 참조 인용이 아닌 크기 순서锚として 사용하세요. 짧은 프롬프트 (<512 토큰, 짧은 출력)는 전송 비용을 정당화하지 않습니다.

**유형:** 학습
**언어:** Python (stdlib, toy 분리 대 배치 시뮬레이터)
**선수 과목:** Phase 17 · 04 (vLLM Serving Internals), Phase 17 · 08 (Inference Metrics)
**소요 시간:** ~75분

## 학습 목표

- prefill과 decode가 다른 최적 GPU 할당을 가지는 이유를 설명하고 배치에서 낭비를 정량화합니다.
- 분리된 아키텍처를 다이어그램으로 그립니다: prefill 풀, decode 풀, NIXL를 통한 KV 전송, 라우터.
- 분리가 payoff하지 않는 조건을 이름 짓습니다 (짧은 프롬프트, 짧은 출력).
- NVIDIA Dynamo (스택 위)와 llm-d (Kubernetes 네이티브)를区別하고 각각을 운영 맥락과 매칭합니다.

## 문제

8개의 H100에서 Llama 3.3 70B을 실행합니다. 혼합 작업 (긴 프롬프트 + 짧은 출력)에서 GPU가 decode 중에 유휴 상태입니다 — 대부분의 계산이 prefill에 spent되었기 때문입니다. 다른 작업 (짧은 프롬프트 + 긴 출력)에서 반대가 발생합니다. 배치 prefill + decode는 둘 다 과잉 프로비저닝을 의미합니다.

예산 영향: GPU 시간의 20-40%가 잘못된 리소스에서浪费됩니다. 메모리 바운드 decode를 실행하기 위해 H100 컴퓨트를 사거나, 계산 바운드 prefill을 실행하기 위해 H100 HBM 대역폭을 사는 것입니다. 둘 다 expensive浪费.

분리는 prefill과 decode를 각자의 병목에 맞춰 크기가 조정된 별도의 풀로 분할합니다. KV 캐시가 고대역폭 상호 연결을 통해 prefill 풀에서 decode 풀트로 전송됩니다.

## 개념

### 병목이 다른 이유

**Prefill** — 전체 입력 프롬프트에서 하나의 포워드로 트랜스포머를 실행합니다. 행렬 곱셈이 지배합니다; 계산 바운드. H100 FP8은 ~2000 TFLOPS의 유용한 처리량을 제공합니다. 배치 효율성이 좋습니다 — 하나의 포워드가 많은 토큰을 처리합니다.

**Decode** — 각 반복에서 전체 가중치를 읽으면서 한 번에 하나의 토큰을 생성합니다. 메모리 대역폭 바운드. HBM3는 ~3 TB/s를 제공합니다. 배치 효율성은 높은 동시성에서만 좋습니다 — 가중치 읽기가 배치 전반에 상각됩니다.

배치它们: 둘 모두에 최적화된 GPU를 삽입합니다. H100은 둘 다에서 좋지만 어느 쪽이든 같은 비용입니다. 규모에서 prefill 풀은 H100 / 컴퓨트 무거운 것에, decode 풀은 H200 / 메모리 무거운 것, 또는 공격적 양자화와 함께 wanting합니다.

### 아키텍처

```
            ┌──────────────┐
  Request → │    Router    │ ───────────────────────┐
            └──────┬───────┘                        │
                   │                                │
                   ▼ (prompt only)                  │
            ┌──────────────┐    KV cache    ┌───────▼──────┐
            │ Prefill pool │ ─── NIXL ────► │ Decode pool  │
            │  (compute)   │                │  (memory)    │
            └──────────────┘                └──────┬───────┘
                                                    │ tokens
                                                    ▼
                                                  Client
```

NIXL은 NVIDIA의 노드 간 전송입니다. 사용 가능한 경우 RDMA/InfiniBand, 그렇지 않으면 TCP 폴백을 사용합니다. 전송 지연이 실제입니다 — 일반적으로 70B FP8에서 4K 토큰 프롬프트의 KV에 대해 20-80 ms입니다. 이것이 짧은 프롬프트가 분리를 정당화하지 않는 이유입니다: 전송 세금이 이득을 능가합니다.

### Dynamo 대 llm-d

**NVIDIA Dynamo** (GTC 2025 발표, 1.0 GA):
- vLLM, SGLang, TRT-LLM 위의 오케스트레이터로 앉습니다.
- Planner Profiler가 작업량을 측정하고, SLA Planner가 풀 비율을 자동 구성합니다.
- Rust 핵심, Python 확장성.
- 처리량 이득: NVIDIA는 GB200 NVL72 + Dynamo에서 DeepSeek-R1 MoE에 대해 중간 지연 시간 체제에서 6x를 보고합니다 (developer.nvidia.com, 2025-06); 전체 Blackwell + Dynamo + DeepSeek-R1 스택에서 "최대 30x"에 대한 커뮤니티 보고서는 단일 기본 소스가 없으며 방향으로 취급되어야 합니다.
- GB300 NVL72 + Dynamo: Hopper 대비 최대 50x MoE 처리량 (Dynamo 제품 페이지, 날짜 없음).

**llm-d** (Red Hat + AWS, Kubernetes 네이티브):
- prefill / decode / 라우터를 독립적인 Kubernetes Services로.
- 역할별 HPA가 있는 큐 깊이 (prefill) / KV 利用률 (decode) 신호.
- `topologyConstraint packDomain: rack`는 고대역폭 KV 전송을 위해 prefill+decode 클리크를 같은 랙에 패킹합니다.
- llm-d 0.5 (2026): 계층적 KV 오프로딩, 캐시 인식 LoRA 라우팅, UCCL 네트워킹, scale-to-zero.

Dynamo가 관리되는 스택 위 오케스트레이터를 원하면 사용하세요. Kubernetes 네이티브 프리미티브를 원하고 CNCF 에코시스템에 헌신적이면 llm-d를 사용하세요.

### 경제학

내부 복합 (단일 게시 사례 연구가 아닌 — 크기 순서锚):
-collocated 서비스에서 연간 $2M 지출.
- Dynamo로 분리된 것으로 전환.
- 동일한 요청 볼륨, 동일한 P99 지연 시간 SLA.
- 보고된 절감: $600K–$800K/年 (30–40% 감소).
- 새 하드웨어 없음.

이 수치를 단일 인용 가능한 사례 연구가 아닌 복수 고객 공개에서 합성합니다; 가장 가까운 게시된 데이터 포인트는 Baseten의 Dynamo KV 라우팅으로 2배 더 빠른 TTFT / 61% 더 높은 처리량 (baseten.co, 2025-10)과 VAST + CoreWeave의 40-60% KV 적중률에서 tokens/$ 60-130% 더 많은 투영 (vastdata.com, 2025-12)입니다. 절감은 각 풀을 올바르게 크기 조정하여 comes; 8K+ 접두사가 있는 RAG (prefill 무거운)가 균형 잡힌 것보다 더 benefit합니다.

### 분리를 하지 말 때

- 프롬프트 < 512 토큰 및 출력 < 200 토큰: 전송 세금이 이득을 지배합니다.
- 작은 클러스터 (< 4 GPU): 풀 다양성이 충분하지 않습니다.
- 팀이 역할별 확장이 있는 두 개의 GPU 풀을 운영할 수 없습니다: Dynamo가 도움이 되지만 trivial하지 않습니다.
- RDMA 패브릭 없음: TCP 전송 세금이 더 무겁습니다.

### 라우터는 Phase 17 · 11와 통합됩니다

분리된 라우터는 KV-cache 인식입니다 (Phase 17 · 11). 요청이 해당 접두사를 보유한 decode 풀에_land합니다 — 일치하지 않으면 prefill → decode로 흐릅니다. 적중률과 분리가 결합됩니다 — 캐시 인식 라우터가 새로운 prefill이 필요한지 여부를 결정합니다.

### MoE on Blackwell이 진짜 숫자가 있는 곳입니다

GB300 NVL72 + Dynamo는 Hopper 기준 대비 50x MoE 처리량을 보여줍니다. MoE 전문가 라우팅은 prefill에서 컴퓨트 무겁지만 decode에서 메모리 무겁습니다 (전문가 캐시), 따라서 분리는 이중 wins입니다. 2026년 프론티어 모델 서비스는 MoE 지배적입니다 (DeepSeek-V3, 향후 GPT-5 변형).

### 기억해야 할 숫자

벤치마크 숫자가drift합니다 — NVIDIA와 추론 스택이 분기마다 업데이트된 결과를 게시합니다. 인용하기 전에 다시 확인하세요.

- GB200 NVL72 + Dynamo의 DeepSeek-R1: 중간 지연 시간 체제에서 기준 대비 ~6x 처리량 (developer.nvidia.com, 2025-06); 전체 Blackwell + Dynamo 스택에서 "최대 30x"에 대한 커뮤니티 "주장"은 단일 기본 소스 없이 방향성 집계입니다.
- GB300 NVL72 + Dynamo: Hopper 대비 최대 50x MoE 처리량 (developer.nvidia.com, 날짜 없음).
- 절감 anchor (내부 복합, 단일 사례 연구 아님): 동등한 SLA에서 연간 $2M 지출에서 $600-800K/年 절감.
- 분리 임계값: 프롬프트 >512 토큰 + 출력 >200 토큰.
- NIXL를 통한 KV 전송: 70B FP8에서 4K-프롬프트 KV에 대해 20-80 ms.

## 활용

`code/main.py`는 배치 대 분리된 서비스를 시뮬레이션합니다. 처리량, 요청당 비용, 프롬프트 길이 교차로를 보고합니다.

## 결과물

이 레슨은 `outputs/skill-disaggregation-decider.md`를 산출합니다. 작업 및 클러스터가 주어지면 분할 여부를 결정합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 어느 프롬프트 길이에서 분리가 배치를 이깁니까?
2. P99 접두사 길이 8K, 출력 300이 있는 RAG 서비스에 대한 prefill 풀과 decode 풀을 디자인하세요.
3. Dynamo 대 llm-d: Python 런타임 선호도가 없는 순수 Kubernetes 상점에서 하나를 선택하세요.
4. KV 전송 비용을 계산하세요: 70B FP8에서 4K prefill = ~500 MB KV. RDMA 100 GB/s에서 전송 = 5 ms. TCP 10 GB/s = 50 ms. 어느 것이 SLA에 중요합니까?
5. MoE 전문가 라우팅이 KV 액세스 패턴을 변경합니다. MoE가 토큰마다 다른 전문가를 활성화할 때 분리가 어떻게 작동합니까?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| 분리된 서비스 | "분리된 prefill/decode" | 각 단계에 대한 별도의 GPU 풀 |
| NIXL | "NVIDIA 전송" | Dynamo's 노드 간 KV 전송 (RDMA/TCP) |
| NVIDIA Dynamo | "오케스트레이터" | vLLM/SGLang/TRT-LLM 위의 스택 위 좌표 |
| llm-d | "Kubernetes 네이티브" | Red Hat + AWS K8s 분리 스택 |
| Planner Profiler | "Dynamo 자동 구성" | 작업량을 측정하고 풀 비율을 구성합니다 |
| SLA Planner | "Dynamo 정책" | SLO를 충족하기 위해 prefill:decode를 자동 조정합니다 |
| `packDomain: rack` | "llm-d 토폴로지" | 빠른 KV 전송을 위해 prefill+decode를 같은 랙에 패킹 |
| UCCL | "통합 수집" | scale-to-zero를 위한 llm-d 0.5 네트워킹 레이어 |
| MoE 전문가 라우팅 | "토큰당 전문가" | DeepSeek-V3 패턴; 분리가 도움됩니다 |

## 추가 자료

- [NVIDIA — Dynamo 소개](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/)
- [NVIDIA — Kubernetes에서 분리된 LLM 추론](https://developer.nvidia.com/blog/deploying-disaggregated-llm-inference-workloads-on-kubernetes/)
- [TensorRT-LLM 분리된 서비스 블로그](https://nvidia.github.io/TensorRT-LLM/blogs/tech_blog/blog5_Disaggregated_Serving_in_TensorRT-LLM.html)
- [llm-d GitHub](https://github.com/llm-d/llm-d)
- [llm-d 0.5 릴리스 노트](https://github.com/llm-d/llm-d/releases)