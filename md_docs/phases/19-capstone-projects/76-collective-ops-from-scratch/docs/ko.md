# 처음부터 집단 통신 구현

> 분산 훈련은 all-reduce, all-gather, reduce-scatter 및 broadcast와 같은 집단 통신 프리미티브에 의존합니다. 이러한 프리미티브는 PyTorch의 분산 패키지(레슨 48)의 기초입니다. 이 레슨은 기본적인 집단 프리미티브를 처음부터 구현합니다: all-reduce(all-gather + reduce-scatter로 분해됨), broadcast 및 all-gather. 이러한 프리미티브는 레슨 77-81에서 분산 훈련을 구축하는 데 사용됩니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 01-10
**Time:** ~90 minutes

## Learning Objectives

- All-reduce(all-gather + reduce-scatter로 분해됨)를 처음부터 구현합니다.
- Broadcast(all-gather로 분해됨)를 처음부터 구현합니다.
- All-gather를 처음부터 구현합니다.

## The Problem

분산 훈련(레슨 48, 77-81)은 집단 통신 프리미티브에 의존합니다. 이러한 프리미티브를 이해하는 것은 분산 훈련이 어떻게 작동하는지 이해하는 데 중요합니다.

## The Concept

### Ring all-reduce

링 all-reduce는 링 토폴로지를 사용합니다. 각 노드는 이웃과 통신합니다. All-reduce는 두 단계로 나뉩니다: reduce-scatter(각 노드가 합계의 청크를 가짐)와 all-gather(각 노드가 전체 합계를 가짐).

### Broadcast

Broadcast는 한 노드(루트)에서 다른 모든 노드로 데이터를 보냅니다. All-gather를 사용하여 구현됩니다: 각 노드가 데이터의 일부를 가지고 있고 all-gather가 모든 부분을 수집합니다.

### All-gather

All-gather는 각 노드의 데이터를 수집하여 모든 노드가 전체 데이터를 가지도록 합니다. 링 토폴로지를 사용하여 구현됩니다.

## Build It

`code/main.py` implements:

- `RingAllReduce` - 링 토폴로지를 사용한 all-reduce(ring reduce-scatter + ring all-gather로 분해됨).
- `Broadcast` - all-gather를 사용한 broadcast(선택적으로 링 기반 또는 단순 나무 기반).
- `AllGather` - 링 토폴로지를 사용한 all-gather.
- `CollectiveDemo` - 프로세스(스레드) 풀을 시작하고 집단 통신을 실행하는 데모.

파일 하단의 데모는 여러 워커(스레드)에서 집단 통신을 시뮬레이션합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 집단 통신 결과를 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 집단 통신으로 확장합니다.

**NCCL backend.** 프로덕션 분산 훈련은 CPU 기반 프리미티브가 아닌 NCCL(GPU 최적화)을 사용합니다.

**Fault-tolerant collectives.** 프로덕션 집단 통신은 노드 장애를 처리해야 합니다.

**Bandwidth-optimal algorithms.** 링 all-reduce는 대역폭 최적이지만 위성으로 분리된 노드에는 최적이 아닙니다.

## Use It

프로덕션 패턴:

- **PyTorch's distributed API for production.** 프로덕션 분산 훈련은 PyTorch의 `torch.distributed` API(레슨 48, 77-78)를 사용해야 합니다.

## Ship It

`outputs/skill-collective-ops.md`는 실제 프로젝트에서 사용할 집단 통신 백엔드(NCCL)와 노드 수를 설명합니다.

## Exercises

1. 대역폭을 측정하는 all-reduce 벤치마크를 추가합니다.
2. 장애 허용 집단 통신을 추가합니다.
3. 노드 장애를 시뮬레이션하는 테스트를 추가합니다.
4. 나무 기반 broadcast(all-gather 대신)를 추가합니다.
5. 링 all-reduce의 대역폭을 2-트리 all-reduce와 비교합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| All-reduce | "Sum across nodes" | 모든 노드에서 값을 합산하고 결과를 모든 노드에 브로드캐스트 |
| Reduce-scatter | "Sum and shard" | 값을 합산하고 각 노드에 합계의 일부를 남김 |
| All-gather | "Collect full tensor" | 각 노드의 부분을 수집하여 모든 노드가 전체 텐서를 가지도록 함 |
| Ring topology | "Circular communication" | 각 노드가 정확히 두 이웃과 통신하는 링 |

## Further Reading

- [Thakur et al., Optimization of Collective Communication Operations in MPICH (IJHPCA 2005)](https://journals.sagepub.com/doi/10.1177/1094342005051521) - 집단 통신 최적화
- [NVIDIA NCCL documentation](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/index.html) - 프로덕션 집단 통신
- Phase 19 · 48 - 분산 훈련 FSDP 및 DDP(이 집단 통신 사용)
- Phase 19 · 77 - 데이터 병렬 DDP(이 집단 통신 사용)
- Phase 19 · 78 - ZeRO 파라미터 샤딩(이 집단 통신 사용)
