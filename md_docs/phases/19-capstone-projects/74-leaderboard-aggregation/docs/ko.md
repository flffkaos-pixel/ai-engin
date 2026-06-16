# 리더보드 집계

> 리더보드는 여러 작업과 메트릭에 걸쳐 모델 성능을 집계합니다. 단일 메트릭(평균 정확도)은 순위를 생성합니다. 이 레슨은 작업 점수를 정규화하고, 가중 평균으로 집계하고, 순위 보고를 생성하는 리더보드 집계기를 구현합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 30-37, 49
**Time:** ~60 minutes

## Learning Objectives

- 작업 점수를 정규화하여 비교 가능하게 만듭니다.
- 가중 평균으로 작업 점수를 집계합니다.
- 순위 보고서를 생성합니다.

## The Problem

리더보드는 여러 작업에 걸쳐 모델을 비교합니다. 각 작업은 다른 메트릭(정확도, F1, ROUGE-L)을 가집니다. 이러한 메트릭은 직접 비교할 수 없습니다. 리더보드 집계기는 메트릭을 정규화하고, 가중 평균을 계산하고, 순위를 생성합니다.

## The Concept

### Score normalization

작업 점수는 공통 척도로 정규화됩니다(일반적으로 0-100). Min-max 정규화가 일반적입니다: `normalized = (score - min_score) / (max_score - min_score) * 100`.

### Weighted average aggregation

정규화된 점수는 가중 평균을 통해 집계됩니다. 각 작업에는 집계에 대한 중요도를 반영하는 가중치가 있습니다. 가중치는 균등하거나(모든 작업이 동일하게 중요) 작업별(일부 작업이 더 중요)일 수 있습니다.

### Ranking

집계된 점수에 따라 모델의 순위가 매겨집니다. 순위 보고서에는 순위, 모델 이름, 집계 점수 및 작업별 점수가 포함됩니다.

## Build It

`code/main.py` implements:

- `ScoreNormalizer` - min-max 정규화로 작업 점수를 정규화합니다.
- `ScoreAggregator` - 가중 평균으로 점수를 집계합니다.
- `LeaderboardRanker` - 집계된 점수로 모델의 순위를 매기고 순위 보고서를 생성합니다.

파일 하단의 데모는 합성 모델 점수를 생성하고, 정규화하고, 집계하고, 순위 보고서를 출력합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 순위 보고서를 출력합니다.

## Production Patterns

두 가지 패턴이 이 레슨을 프로덕션 리더보드로 확장합니다.

**Dynamic task weighting.** 작업 가중치는 동적일 수 있습니다. 새로운 작업이 리더보드에 추가되거나 제거됨에 따라 조정됩니다.

**Confidence intervals on rankings.** 순위는 신뢰 구간과 함께 보고되어야 합니다. 값이 겹치면 순위 차이가 유의하지 않습니다.

## Use It

프로덕션 패턴:

- **Submit results via task spec.** 모델 결과는 작업 사양(레슨 70)을 통해 리더보드에 제출됩니다. 작업 사양에는 메트릭과 점수가 포함됩니다.

## Ship It

`outputs/skill-leaderboard.md`는 실제 프로젝트에서 사용할 작업 가중치, 정규화 방법 및 순위 보고서가 생성되는 빈도를 설명합니다. 이 레슨은 엔진을 제공합니다.

## Exercises

1. 정규화 방법(예: z-점수)을 제어하는 `--normalization` 플래그를 추가합니다.
2. 작업 가중치를 제어하는 `--weights` 플래그를 추가합니다.
3. 작업 사양(레슨 70)을 통해 결과를 리더보드에 제출합니다.
4. 순위에 대한 신뢰 구간을 추가합니다.
5. 다이나믹 작업 가중치를 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Score normalization | "Scale scores" | 비교를 위해 메트릭을 공통 척도로 변환 |
| Weighted average | "Task importance" | 작업별 가중치가 있는 집계 |
| Leaderboard ranking | "Model ranking" | 집계된 점수로 모델 순위 매기기 |
| Confidence interval | "Ranking uncertainty" | 순위 불확실성을 측정하는 순위별 신뢰 구간 |

## Further Reading

- [Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard) - 널리 사용되는 리더보드의 예
- Phase 19 · 70 - 작업 사양 형식(리더보드 제출에 사용)
- Phase 19 · 71 - 고전 메트릭(리더보드에 사용)
- Phase 19 · 72 - 코드 실행 메트릭(리더보드에 사용)
- Phase 19 · 73 - Perplexity 교정(리더보드에 사용)
- Phase 19 · 75 - 엔드-투-엔드 평가 러너(리더보드에 연결)
