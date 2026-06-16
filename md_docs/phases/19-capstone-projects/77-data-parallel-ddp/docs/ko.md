# 데이터 병렬 DDP

> 데이터 병렬 처리는 분산 훈련의 가장 간단한 형태입니다. 분산 데이터 병렬(DDP)은 각 GPU가 전체 모델 사본을 유지하고 그라디언트에서 all-reduce를 실행합니다. 이 레슨은 레슨 76의 all-reduce 프리미티브를 사용하여 DDP를 처음부터 구현합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 76
**Time:** ~90 minutes

## Learning Objectives

- 레슨 76의 all-reduce를 사용하여 데이터 병렬 DDP 래퍼를 처음부터 구현합니다.
- 각 GPU가 다른 데이터 배치를 처리하고, 역전파 후 그라디언트가 동기화되는지 확인합니다.

## The Problem

DDP는 분산 훈련의 진입점입니다. 각 GPU는 전체 모델 사본을 유지하고 다른 데이터를 처리합니다. 역전파 후 그라디언트는 all-reduce(레슨 76)를 사용하여 동기화됩니다. 모든 GPU가 동일한 그라디언트를 가지면 동일한 옵티마이저 단계를 적용합니다.

## The Concept

### DDP forward pass

각 GPU는 전체 모델 사본을 유지합니다. 순전파는 단일 GPU 순전파와 동일합니다: 입력이 모델을 통과하고 손실이 계산됩니다.

### DDP backward pass

역전파 중에 각 GPU는 자체 그라디언트를 계산합니다. 역전파 후 DDP는 레슨 76의 all-reduce를 호출하여 모든 GPU에서 그라디언트를 합산하고 평균을 계산합니다. 모든 GPU가 동일한 그라디언트를 가지면 동일한 옵티마이저 단계를 적용합니다.

## Build It

`code/main.py` implements:

- `DDPWrapper` - 각 GPU가 전체 모델 사본을 유지하고 all-reduce(레슨 76)로 그라디언트를 동기화하는 데이터 병렬 래퍼.
- `DistributedSampler` - 데이터셋을 GPU 전체에 분할하는 분산 샘플러.

파일 하단의 데모는 여러 GPU(스레드)에서 DDP 훈련을 시뮬레이션합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 GPU당 손실을 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 DDP로 확장합니다.

**Gradient bucket all-reduce.** DDP는 그라디언트를 버킷으로 그룹화하고 버킷 단위로 all-reduce하여 통신 오버헤드를 줄입니다.

**Async all-reduce.** 그라디언트는 역전파와 동시에 all-reduce되어 통신을 계산과 오버랩할 수 있습니다.

**Mixed precision with DDP.** AMP(레슨 45)는 DDP와 호환됩니다. 각 GPU는 언스케일링 후 자체 그라디언트를 all-reduce합니다.

## Use It

프로덕션 패턴:

- **DDP for small models.** 모델이 단일 GPU에 맞으면 DDP가 선호되는 분산 전략입니다.

## Ship It

`outputs/skill-data-parallel-ddp.md`는 실제 프로젝트에서 사용할 GPU 수, 배치 크기 및 all-reduce 백엔드(NCCL)를 설명합니다.

## Exercises

1. 그라디언트 버킷 all-reduce를 추가합니다.
2. 비동기 all-reduce를 추가합니다.
3. AMP(레슨 45)와의 통합을 추가합니다.
4. DDP를 단일 GPU와 비교하는 벤치마크 모드를 추가합니다.
5. DDP에 대한 그라디언트 누적(레슨 46)을 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| DDP | "Data parallel" | 각 GPU가 전체 모델을 유지하고 all-reduce로 그라디언트를 동기화 |
| Gradient bucket | "Grad group" | all-reduce를 위해 그라디언트를 그룹화 |
| Async all-reduce | "Async grad sync" | 역전파와 동시에 all-reduce하여 통신을 계산과 오버랩 |
| Distributed sampler | "Data sharding" | GPU 간에 데이터셋 분할 |

## Further Reading

- [PyTorch DDP documentation](https://pytorch.org/docs/stable/notes/ddp.html) - PyTorch의 DDP 구현
- Phase 19 · 76 - 집단 통신(all-reduce, 이 레슨의 기반)
- Phase 19 · 78 - ZeRO 파라미터 샤딩(DDP 확장, 더 많은 메모리 효율성)
