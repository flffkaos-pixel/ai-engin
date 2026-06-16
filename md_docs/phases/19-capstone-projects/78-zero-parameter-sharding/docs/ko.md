# ZeRO 파라미터 샤딩

> ZeRO(Zero Redundancy Optimizer)는 모델 파라미터, 그라디언트 및 옵티마이저 상태를 GPU 전체에 분할하여 메모리 사용량을 줄입니다. ZeRO-1은 옵티마이저 상태를 샤딩합니다. ZeRO-2는 옵티마이저 상태 + 그라디언트를 샤딩합니다. ZeRO-3(FSDP, 레슨 48)는 옵티마이저 상태 + 그라디언트 + 파라미터를 샤딩합니다. 이 레슨은 ZeRO-1(옵티마이저 상태 샤딩)과 ZeRO-2(옵티마이저 상태 + 그라디언트 샤딩)를 처음부터 구현합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 76-77
**Time:** ~90 minutes

## Learning Objectives

- 레슨 76의 all-gather 및 reduce-scatter 프리미티브를 사용하여 ZeRO-1(옵티마이저 상태 샤딩)을 처음부터 구현합니다.
- ZeRO-2(옵티마이저 상태 + 그라디언트 샤딩)를 구현합니다.
- DDP(레슨 77)와 비교하여 ZeRO의 메모리 절약을 확인합니다.

## The Problem

DDP는 각 GPU에 전체 옵티마이저 상태를 저장합니다. 7B 모델의 경우 AdamW 상태(2개의 실행 평균)는 GPU당 56GB입니다. ZeRO는 옵티마이저 상태를 GPU 전체에 분할하여 GPU당 비용을 `1 / world_size`로 줄입니다.

## The Concept

### ZeRO-1: Optimizer state sharding

ZeRO-1은 옵티마이저 상태를 GPU 전체에 분할합니다. 각 GPU는 옵티마이저 상태의 `1 / world_size`만 저장합니다. 역전파 후 all-gather(레슨 76)가 전체 그라디언트를 재구성합니다. 옵티마이저 단계는 그라디언트의 로컬 샤드에서 실행됩니다.

### ZeRO-2: Optimizer state + gradient sharding

ZeRO-2는 그라디언트도 분할합니다. 각 GPU는 그라디언트의 `1 / world_size`만 저장합니다. Reduce-scatter(레슨 76)가 역전파 후 그라디언트를 분할합니다. 옵티마이저 단계는 그라디언트 샤드에서 실행됩니다.

## Build It

`code/main.py` implements:

- `Zero1Wrapper` - 레슨 76의 all-gather를 사용하여 옵티마이저 상태를 샤딩하는 ZeRO-1 구현.
- `Zero2Wrapper` - 레슨 76의 reduce-scatter를 사용하여 옵티마이저 상태 + 그라디언트를 샤딩하는 ZeRO-2 구현.

파일 하단의 데모는 여러 GPU(스레드)에서 ZeRO-1 및 ZeRO-2를 DDP와 메모리 사용량을 비교합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 DDP, ZeRO-1 및 ZeRO-2의 GPU당 메모리 사용량을 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 ZeRO로 확장합니다.

**ZeRO stages are configurable.** 훈련 설정은 ZeRO 단계(0=DDP 없음, 1=ZeRO-1, 2=ZeRO-2, 3=ZeRO-3/FSDP)를 지정해야 합니다.

**ZeRO with gradient accumulation.** ZeRO는 그라디언트 누적(레슨 46)과 호환됩니다.

**ZeRO with activation checkpointing.** ZeRO는 활성화 체크포인팅과 결합되어 GPU 메모리 사용량을 더욱 줄일 수 있습니다.

## Use It

프로덕션 패턴:

- **ZeRO-2 is often sufficient.** ZeRO-3(FSDP, 레슨 48)는 파라미터 통신을 추가하여 오버헤드가 더 높습니다. ZeRO-2는 종종 메모리 효율성과 통신 오버헤드 사이의 좋은 균형을 제공합니다.

## Ship It

`outputs/skill-zero-sharding.md`는 실제 프로젝트에서 사용할 ZeRO 단계와 GPU 수를 설명합니다.

## Exercises

1. ZeRO 단계를 제어하는 `--zero-stage` CLI 플래그를 추가합니다.
2. ZeRO에 대한 그라디언트 누적(레슨 46)을 추가합니다.
3. ZeRO-1, ZeRO-2 및 DDP의 처리량을 비교하는 벤치마크 모드를 추가합니다.
4. ZeRO-1 및 ZeRO-2에서 올바른 메모리 절약을 확인하는 메모리 프로파일러를 추가합니다.
5. ZeRO-3(FSDP, 레슨 48)와의 통합을 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| ZeRO-1 | "Optimizer state sharding" | 옵티마이저 상태를 GPU 전체에 분할 |
| ZeRO-2 | "Optimizer state + gradient sharding" | 옵티마이저 상태 + 그라디언트를 GPU 전체에 분할 |
| ZeRO-3 | "FSDP" | 옵티마이저 상태 + 그라디언트 + 파라미터를 GPU 전체에 분할 |
| Reduce-scatter | "Sum and shard" | 그라디언트를 합산하고 각 GPU에 합계의 샤드를 남김 |

## Further Reading

- [Rajbhandari et al., ZeRO: Memory Optimizations Toward Training Trillion Parameter Models (SC 2020)](https://arxiv.org/abs/1910.02054) - ZeRO의 원본 논문
- [PyTorch FSDP documentation](https://pytorch.org/docs/stable/fsdp.html) - ZeRO-3 구현
- Phase 19 · 76 - 집단 통신(all-gather, reduce-scatter)
- Phase 19 · 77 - 데이터 병렬 DDP(ZeRO의 기반)
- Phase 19 · 48 - FSDP(ZeRO의 전체 구현)
