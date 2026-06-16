# 샤딩된 체크포인트 저장 및 재개

> 분산 훈련은 각 GPU가 저장하는 체크포인트가 다릅니다(ZeRO/FSDP 샤드). 분산 체크포인트는 각 GPU가 자체 파라미터 샤드를 저장하도록 요구합니다. 재개 시 GPU는 자체 샤드만 로드합니다. 이 레슨은 ZeRO/FSDP 체크포인트에 대한 샤딩된 체크포인트 저장 및 로드를 구현합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 47, 76-78
**Time:** ~90 minutes

## Learning Objectives

- ZeRO/FSDP 샤드에 대한 분산 체크포인트 저장(reduce-scatter 또는 단일 작성자 사용)을 구현합니다.
- 분산 체크포인트 로드(each rank loads its shard from the global checkpoint)를 구현합니다.

## The Problem

분산 훈련에서 각 GPU는 파라미터의 다른 샤드를 보유합니다(ZeRO/FSDP를 통해, 레슨 78). 체크포인트를 저장하려면 각 GPU가 자체 샤드를 저장해야 합니다. 재개 시 각 GPU는 자체 샤드만 로드합니다.

## The Concept

### Distributed checkpoint save

분산 체크포인트 저장에는 두 가지 접근 방식이 있습니다:

1. **Reduce-scatter save** - 각 GPU가 자체 파라미터 샤드를 파일에 저장합니다. 체크포인트는 GPU 전체에 분산된 파일 세트입니다.
2. **Single-writer save** - 한 GPU(rank 0)가 모든 GPU로부터 파라미터 샤드를 수집하고 단일 파일에 씁니다.

### Distributed checkpoint load

재개 시 각 GPU는 분산 체크포인트에서 자체 샤드만 로드합니다.

## Build It

`code/main.py` implements:

- `DistributedCheckpointSaver` - ZeRO/FSDP 샤드에 대한 분산 체크포인트 저장을 구현합니다.
- `DistributedCheckpointLoader` - ZeRO/FSDP 샤드에 대한 분산 체크포인트 로드를 구현합니다.

파일 하단의 데모는 분산 훈련(여러 GPU/스레드)을 시뮬레이션하고, 분산 체크포인트로 저장하고, 분산 체크포인트에서 로드합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 분산 체크포인트 저장 및 로드 작업을 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 분산 체크포인트로 확장합니다.

**Checkpoint on rank 0 only.** 단일 작성자 접근 방식은 rank 0가 모든 GPU로부터 수집하고 저장합니다. 저장 중 rank 0가 실패하면 체크포인트가 손실되지만 단순합니다.

**Consistent hashing for shard mapping.** 샤드 ID를 체크포인트 파일에 매핑하는 것은 재현 가능해야 합니다(GPU 수가 변경되는 경우에도). 일관된 해싱은 안정적인 매핑을 보장합니다.

**Checkpoint format migration.** GPU 수가 변경되면 체크포인트 형식이 변경될 수 있습니다. 형식 마이그레이션 도구가 필요합니다.

## Use It

프로덕션 패턴:

- **Checkpoint every N steps.** 분산 체크포인트는 N단계마다 저장되어야 합니다.
- **Verify checkpoint after saving.** 체크포인트 저장 후 각 GPU는 저장된 샤드의 sha256(레슨 47)을 확인해야 합니다.

## Ship It

`outputs/skill-sharded-checkpoint.md`는 실제 프로젝트에서 사용할 체크포인트 저장 전략(reduce-scatter vs single-writer)과 체크포인트 빈도를 설명합니다.

## Exercises

1. 체크포인트 저장 전략(reduce-scatter vs single-writer)을 제어하는 `--save-strategy` CLI 플래그를 추가합니다.
2. 저장된 체크포인트의 sha256 검증(레슨 47)을 추가합니다.
3. GPU 수 변경을 처리하는 체크포인트 마이그레이션 도구를 추가합니다.
4. 분산 체크포인트 저장의 스루풋을 단일 GPU 체크포인트(레슨 47)와 비교하는 벤치마크를 추가합니다.
5. 분산 체크포인트에 대한 체크포인트 정리(레슨 47)를 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Distributed checkpoint | "Sharded save" | ZeRO/FSDP 샤드를 저장하는 분산 체크포인트 |
| Reduce-scatter save | "Each rank saves its shard" | 각 GPU가 자체 파라미터 샤드를 저장 |
| Single-writer save | "Rank 0 saves" | Rank 0가 모든 GPU로부터 수집하고 단일 체크포인트 파일에 저장 |
| Checkpoint migration | "Format conversion" | GPU 수가 변경될 때 체크포인트 형식 변경 |

## Further Reading

- [PyTorch Distributed Checkpoint documentation](https://pytorch.org/docs/stable/distributed.checkpoint.html) - 분산 체크포인트 API
- Phase 19 · 47 - 체크포인트 저장(단일 GPU 체크포인트의 기반)
- Phase 19 · 76 - 집단 통신(분산 체크포인트 통신의 기반)
- Phase 19 · 77 - 데이터 병렬 DDP(분산 체크포인트의 기반)
- Phase 19 · 78 - ZeRO 파라미터 샤딩(분산 체크포인트의 기반)
- Phase 19 · 81 - 엔드-투-엔드 분산 훈련(분산 체크포인트 통합)
