# Kubernetes에서 GPU 자동 스케일링 — Karpenter, KAI Scheduler, Gang Scheduling

> 세 가지 레이어, 하나가 아닙니다. Karpenter는 노드를 동적으로 프로비저닝합니다 (1분 미만, Cluster Autoscaler보다 40% 빠름). KAI Scheduler는 gang 스케줄링, 토폴로지 인식, 계층적 큐를 처리합니다 — 7-of-8 부분 할당 함정, 일곱 개의 노드가 하나의 누락된 GPU에서 기다리고 소모하는 것을 방지합니다. 애플리케이션 수준 자동 스케일러 (NVIDIA Dynamo Planner, llm-d Workload Variant Autoscaler)는 CPU/DCGM duty cycle이 아닌 추론 특정 신호 — 큐 깊이, KV 캐시 利用률 — 에서 스케일합니다. 클래식 HPA 함정은 `DCGM_FI_DEV_GPU_UTIL`가 duty cycle 측정이라는 것입니다: 100%는 10개의 요청 또는 100개일 수 있습니다. vLLM은 KV 캐시 메모리를 사전 할당하므로 메모리가 스케일 다운을 트리거하지 않습니다. 이 레슨은 세 가지 레이어를 구성하고 실행 중인 GPU 작업을 중간 추론에서 종료하는 기본 Karpenter `WhenEmptyOrUnderutilized` 정책을 피하도록 가르칩니다.

**유형:** 학습
**언어:** Python (stdlib, toy queue-depth 자동 스케일러 시뮬레이터)
**선수 과목:** Phase 17 · 02 (Inference Platform Economics), Phase 17 · 04 (vLLM Serving Internals)
**소요 시간:** ~75분

## 학습 목표

- 세 가지 자동 스케일링 레이어 (노드 프로비저닝, gang 스케줄링, 애플리케이션 수준)를 다이어그램으로 그리고 각 레이어에서 사용되는 도구의 이름을 붙입니다.
- `DCGM_FI_DEV_GPU_UTIL`가 vLLM에 대한 잘못된 HPA 신호인 이유를 설명하고 두 가지 대체재를 이름 짓습니다 (큐 깊이, KV 캐시 利用률).
- Gang 스케줄링과 KAI Scheduler가 방지하는 부분 할당 실패 모드 (7개의 GPU 유휴, 1개 분산)를 설명합니다.
- 실행 중인 GPU 작업을 종료하는 Karpenter 통합 정책 (`WhenEmptyOrUnderutilized`)의 이름을 말하고 2026년 안전한 대안을 설명합니다.

## 문제

팀이 Kubernetes에서 LLM提供服务하고 있습니다. `DCGM_FI_DEV_GPU_UTIL`를 신호로 HPA를 설정합니다. 서비스가 영업 시간에 100% 利用률에 고정됩니다. HPA는 스케일 업하지 않습니다 — 이미 가득 차 있다고 생각합니다. 수동으로 복제본을 추가합니다; TTFT가 떨어집니다. HPA는 여전히 스케일하지 않습니다. 신호가 거짓말을 하고 있습니다.

따로 떨어져서, Cluster Autoscaler를 노드에 사용합니다. 2시에 1M 토큰 프롬프트가 도착합니다; 클러스터가 노드를 프로비저닝하는 데 3분이 걸리고 요청이 시간 초과됩니다.

또 따로 떨어져서, 8개 GPU가 2개 노드에 걸쳐 필요한 70B 모델을 배포합니다. 클러스터에 7개의 사용 가능한 GPU와 3개 노드에 분산된 1개가 있습니다. Cluster Autoscaler가 1개의 누락된 GPU를 위해 노드를 프로비저닝합니다. Kubernetes가 마지막 GPU를 가동하는 동안 7개 노드가 4분 동안 돈을焚烧하며 기다립니다.

세 가지 레이어, 세 가지 다른 실패 모드. 2026년 GPU 인식 자동 스케일링은 "HPA를 켭니다"가 아닙니다. 노드 프로비저닝, gang 스케줄링, 애플리케이션 신호 자동 스케일링을 구성하는 것입니다.

## 개념

### 레이어 1 — 노드 프로비저닝 (Karpenter)

Karpenter는 보류 중인 포드를監視하고 ~45-60초 내에 노드를 프로비저닝합니다 (Cluster Autoscaler는 일반적으로 GPU 노드에 90-120초가 걸립니다). `NodePool` 제약 조건에 따라 instance 유형을 동적으로 선택합니다 — 포드에 8개의 H100이 필요하고 클러스터에 일치하는 노드가 없으면, Karpenter 기존 그룹을 스케일링而非而是直接 프로비저닝합니다.

**통합 함정**: Karpenter의 기본 `consolidationPolicy: WhenEmptyOrUnderutilized`는 GPU 풀에危险합니다. 실행 중인 GPU 노드를 종료하여 포드를 더 저렴한 적절히 크기 조정된 인스턴스로 마이그레이션합니다. 추론 작업의 경우 실행 중인 요청을 제거하고 70B 모델을 새 노드에서 다시 로드하는 것을 의미합니다. 손실은 수 분의 용량 plus 요청 실패입니다.

GPU 풀의 안전한 설정:

```yaml
disruption:
  consolidationPolicy: WhenEmpty
  consolidateAfter: 1h
```

Karpenter가 실제로 빈 노드를 한 시간 후 통합하지만 실행 중인 작업은 절대 제거하지 않습니다.

### 레이어 2 — gang 스케줄링 (KAI Scheduler)

KAI Scheduler (프로젝트 "Karp" 후 이름 변경)는 기본 kube-scheduler가 처리하지 않는 것을 처리합니다:

**Gang 스케줄링** — 전체 또는 전무. 8개 GPU가 필요한 분산 추론 포드는 8개가 모두 함께 시작하거나 아무도 시작하지 않습니다. 이것이 없으면 부분 할당 함정에 빠집니다: 8개 중 7개가 시작하고 무한히 기다리며 돈을焚烧합니다.

**토폴로지 인식** — 어떤 GPU가 NVLink를 공유하는지, 같은 랙에 있는지, 그들 사이에 InfiniBand가 있는지 압니다. 그에 따라 포드를 배치합니다. DeepSeek-V3 67B tensor-parallel 작업은 하나의 NVLink 도메인에 머물러야 합니다; KAI Scheduler가 그것을 존중합니다.

**계층적 큐** — 여러 팀이 우선순위 및 할당량으로 같은 GPU 풀을 경쟁합니다. 팀 A의 프로덕션 압박은 우선순위 규칙이 허용하는 경우에만 팀 B의 훈련 작업에 선점됩니다.

KAI는 kube-scheduler Alongside에 secondary 스케줄러로 배포됩니다; 포드에 그것을 사용하도록 주석을 지정합니다. Ray 및 vLLM production-stack 모두 통합합니다.

### 레이어 3 — 애플리케이션 수준 신호

**HPA 함정**: `DCGM_FI_DEV_GPU_UTIL`는 duty cycle 메트릭입니다 — 각 샘플링 간격에서 GPU가 작업을 수행했는지 측정합니다. 100% 利用률은 10개의 동시 요청 또는 100개를 의미할 수 있습니다; GPU는 두 경우 모두 바빴습니다. Duty cycle에서 스케일하면 눈을 Blind하게 스케일하는 것입니다.

더 나쁘게, vLLM 및 유사한 엔진은 KV 캐시 메모리를 사전 할당합니다 (`--gpu-memory-utilization`까지). 메모리 사용량은 하나의 요청에서도 90% 근처에 있습니다. 메모리 기반 HPA는 스케일 다운하지 않습니다.

**2026년 대체 신호**:

- 큐 깊이 (prefill을 기다리는 요청 수).
- KV 캐시 利用률 (활성 시퀀스에 할당된 블록 비율).
- 복제당 P99 TTFT (SLA 신호).
- Goodput (초당 모든 SLO를 충족하는 요청).

NVIDIA Dynamo Planner 및 llm-d Workload Variant Autoscaler는 이러한 신호를 소비하고 복제본을 스케일합니다. LLM 제공을 위해 HPA를 완전히 대체합니다.

### 언제 무엇을 사용するか

| 스케일 결정 | 도구 |
|----------------|------|
| 노드 추가/제거 | Karpenter |
| 멀티 GPU 작업 스케줄 | KAI Scheduler |
| 복제본 추가/제거 | Dynamo Planner / llm-d WVA (또는 큐 깊이의 사용자 정의 HPA) |
| GPU 유형 선택 | Karpenter NodePool |
| 낮은 우선순위 선점 | KAI Scheduler 큐 |

### 분리된 prefill/decode가 모든 것을 복잡하게 합니다

분리된 prefill/decode (Phase 17 · 17)를 실행하는 경우, 두 개의 포드 클래스가 다른 스케일 트리거를 가집니다: prefill 포드는 큐 깊이에서 스케일하고, decode 포드는 KV 캐시 압력에서 스케일합니다. llm-d는 它们를 별도의 `Services`로 노출하여 역할별 HPA를 제공합니다. 둘 다 앞에 단일 HPA를 놓으려고 하지 마세요.

### 콜드 스타트도 여기서 중요합니다

콜드 스타트 완화 (Phase 17 · 10)는 노드 프로비저닝 시간이 사용자에게可視化する 곳입니다. Karpenter의 45-60초 워밍업 plus 20GB 모델 로드 plus 엔진 초기화는零からの请求에 2-5분이 걸립니다. SLO 중요한 경로에 대해 따뜻한 풀을 유지하세요 (`min_workers=1`), 또는 애플리케이션 레이어에서 Modal 스타일 체크포인팅을 사용하세요.

### 기억해야 할 숫자

- Karpenter 노드 프로비저닝: ~45-60초 대 Cluster Autoscaler ~90-120초 (GPU 노드).
- KAI Scheduler는 부분 할당 폐기를 방지합니다 — 7-of-8 함정.
- `DCGM_FI_DEV_GPU_UTIL` HPA 신호로: 고장; 큐 깊이 또는 KV 利用률 사용.
- Karpenter `WhenEmptyOrUnderutilized`: 실행 중인 GPU 작업을 종료합니다. 추론에는 `WhenEmpty + consolidateAfter: 1h`를 사용하세요.

## 활용

`code/main.py`는 버스티 GPU 작업에서 3층 자동 스케일러를 시뮬레이션합니다. 순진한 HPA (duty cycle), 큐 깊이 HPA, KAI-gang 스케줄링 스케일링을 비교합니다. 미충족 요청, 유휴 GPU 분, 복합 점수를 보고합니다.

## 결과물

이 레슨은 `outputs/skill-gpu-autoscaler-plan.md`를 산출합니다. 클러스터 토폴로지, 작업 형태, SLO가 주어지면 3층 자동 스케일링 계획을 디자인합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 버스티 작업에서 순진한 duty-cycle HPA가 큐 깊이 HPA가 잡는 요청을 몇 개 드롭합니까? 차이가 어디서 오는지 설명하세요.
2. H100 SXM5에서 Llama 3.3 70B FP8을 제공하는 클러스터에 대한 Karpenter NodePool을 디자인하세요. `capacity-type`, `disruption.consolidationPolicy`, `consolidateAfter`, 비 GPU 작업을 이러한 노드에서 유지하는 테인트를 指定하세요.
3. 팀이 "GPU 사용 가능하지만 포드가 예약되지 않는다"고 보고합니다. 진단하세요 — Karpenter, kube-scheduler, 아니면 KAI Scheduler입니까? 확인하는 메트릭은 무엇입니까?
4. 분리된 prefill 포드를 자동 스케일링할 신호를 선택하고 decode 포드에 다른 신호를 선택하세요. 둘 다 정당화하세요.
5. P99 TTFT > 10초인 24시간 프로덕션 서비스에서 `WhenEmptyOrUnderutilized` 통합 함정의 비용을 계산하세요 (평균적으로 하루에 60개의 요청 드롭 событий).

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| Karpenter | "노드 프로비저너" | Kubernetes 노드 자동 스케일러; 1분 미만 프로비저닝 |
| Cluster Autoscaler | "이전 스케일러" | Kubernetes 노드 자동 스케일러 선배; 느리고 그룹 기반 |
| KAI Scheduler | "GPU 스케줄러" | gang + 토폴로지 + 큐용 secondary 스케줄러 |
| Gang 스케줄링 | "전체 또는 전무" | N개의 포드를 원자적으로 스케줄하거나 모두 연기 |
| 토폴로지 인식 | "랙 인식" | NVLink/IB/랙 배치를 기반으로 포드 배치 |
| `DCGM_FI_DEV_GPU_UTIL` | "GPU 利用률" | Duty cycle 메트릭; LLM의 스케일 신호가 아님 |
| 큐 깊이 | "대기 요청" | prefill 바운드 스케일링을 위한 올바른 HPA 신호 |
| KV 캐시 利用률 | "메모리 압력" | decode 바운드 스케일링을 위한 올바른 HPA 신호 |
| 통합 | "Karpenter 통합" | 더 저렴한 인스턴스 유형으로 노드 종료 |
| `WhenEmpty + 1h` | "안전한 통합" | 실행 중인 GPU 작업을 제거하지 않는 정책 |

## 추가 자료

- [KAI Scheduler GitHub](https://github.com/kai-scheduler/KAI-Scheduler) — 디자인 문서 및 구성 예.
- [Karpenter Disruption Controls](https://karpenter.sh/docs/concepts/disruption/) — 통합 정책 의미론 및 GPU 안전한 기본값.
- [NVIDIA — Disaggregated LLM Inference on Kubernetes](https://developer.nvidia.com/blog/deploying-disaggregated-llm-inference-workloads-on-kubernetes/) — Dynamo Planner 스케일링 신호.
- [Ray docs — KAI Scheduler for RayClusters](https://docs.ray.io/en/latest/cluster/kubernetes/k8s-ecosystem/kai-scheduler.html) — Ray 통합 패턴.
- [AWS EKS Compute and Autoscaling Best Practices](https://docs.aws.amazon.com/eks/latest/best-practices/aiml-compute.html) — 관리형 Kubernetes 특정 지침.
- [llm-d GitHub](https://github.com/llm-d/llm-d) — Workload Variant Autoscaler 디자인.