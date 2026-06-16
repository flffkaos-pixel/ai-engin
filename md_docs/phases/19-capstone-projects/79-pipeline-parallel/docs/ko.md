# 파이프라인 병렬 처리

> 파이프라인 병렬 처리는 모델을 여러 GPU에 걸쳐 레이어로 분할합니다. 각 GPU는 연속적인 레이어 세트를 보유합니다. 입력은 GPU 체인을 통해 전달됩니다. 이 레슨은 마이크로배치로 파이프라인을 채워 GPU 활용도를 높이는 1F1B(하나의 순전파, 하나의 역전파) 파이프라인 스케줄링을 구현합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 76-77
**Time:** ~90 minutes

## Learning Objectives

- 모델을 레이어 경계에서 GPU 전체에 분할하는 파이프라인 병렬 래퍼를 구현합니다.
- 1F1B 파이프라인 스케줄링을 구현합니다.

## The Problem

매우 큰 모델(> 10B 파라미터)은 단일 GPU에 맞지 않습니다. 파이프라인 병렬 처리는 모델을 레이어로 분할합니다. 각 GPU는 연속적인 레이어 세트를 보유합니다. 입력은 GPU를 통해 전달됩니다. 1F1B 스케줄링은 마이크로배치로 파이프라인을 채워 GPU 활용도를 높입니다.

## The Concept

### Pipeline parallel

모델은 레이어 경계에서 분할됩니다. GPU 0은 레이어 1-4를 보유합니다. GPU 1은 레이어 5-8을 보유합니다. 등등. 입력은 GPU 체인을 통해 전달됩니다: GPU 0 → GPU 1 → ... → GPU N-1.

### 1F1B scheduling

1F1B(하나의 순전파, 하나의 역전파) 스케줄링은 마이크로배치로 파이프라인을 채웁니다. 각 GPU는 순전파와 역전파를 번갈아 실행합니다. 기존 순차적 파이프라인(워터필링)과 비교하여 GPU 활용도를 높입니다.

## Build It

`code/main.py` implements:

- `PipelineParallelWrapper` - 레이어 경계에서 GPU 전체에 모델을 분할합니다.
- `PipelineSchedule1F1B` - 1F1B 파이프라인 스케줄링을 구현합니다: 마이크로배치로 파이프라인을 채웁니다.

파일 하단의 데모는 여러 GPU(스레드)에서 파이프라인 병렬 훈련을 시뮬레이션합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 GPU당 손실을 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 파이프라인 병렬 처리로 확장합니다.

**Microbatch sizing.** 마이크로배치 크기는 GPU 활용도에 영향을 미칩니다. 마이크로배치가 너무 크면 GPU가 유휴 상태가 됩니다. 마이크로배치가 너무 작으면 통신 오버헤드가 증가합니다.

**Pipeline bubble.** 파이프라인 병렬 처리는 필연적으로 파이프라인 버블(일부 GPU가 유휴 상태)을 생성합니다. 1F1B는 순차적 파이프라인(워터필링)에 비해 버블을 줄입니다.

**Hybrid parallelism with DDP/ZeRO.** 파이프라인 병렬 처리는 종종 DDP(데이터 병렬) 또는 ZeRO와 결합됩니다(레슨 81).

## Use It

프로덕션 패턴:

- **Pipeline parallel for very large models.** 파이프라인 병렬 처리는 모델이 단일 GPU에 맞지 않을 때 필요합니다.

## Ship It

`outputs/skill-pipeline-parallel.md`는 실제 프로젝트에서 사용할 GPU 수와 마이크로배치 크기를 설명합니다. 이 레슨은 엔진을 제공합니다.

## Exercises

1. 마이크로배치 크기를 제어하는 `--microbatch-size` CLI 플래그를 추가합니다.
2. 파이프라인 버블 비율을 측정하는 벤치마크 모드를 추가합니다.
3. 순차적(워터필링) 파이프라인과 1F1B를 비교하는 비교 모드를 추가합니다.
4. 그라디언트 누적(레슨 46)과의 통합을 추가합니다.
5. Hybrdd 병렬 처리(파이프라인 + DDP)를 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Pipeline parallel | "Layer-wise model sharding" | 레이어 경계에서 GPU 전체에 모델 분할 |
| 1F1B | "One forward, one backward" | 파이프라인 스케줄링: 순전파와 역전파를 번갈아 실행 |
| Pipeline bubble | "Idle GPU time" | 일부 GPU가 작업을 기다리는 유휴 시간 |
| Microbatch | "Mini-batch" | 파이프라인을 채우는 데 사용되는 입력 배치의 하위 분할 |

## Further Reading

- [Huang et al., GPipe: Efficient Training of Giant Neural Networks using Pipeline Parallelism (NeurIPS 2019)](https://arxiv.org/abs/1811.06965) - 파이프라인 병렬 처리의 원본 논문
- [Narayanan et al., Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM (SC 2021)](https://arxiv.org/abs/2104.04473) - 1F1B 스케줄링 및 하이브리드 병렬 처리
- Phase 19 · 76 - 집단 통신(파이프라인 통신의 기반)
- Phase 19 · 77 - 데이터 병렬 DDP(파이프라인과 결합 가능)
- Phase 19 · 78 - ZeRO 파라미터 샤딩(파이프라인과 결합 가능)
- Phase 19 · 81 - 엔드-투-엔드 분산 훈련(파이프라인 + DDP + ZeRO 통합)
