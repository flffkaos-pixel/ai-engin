# 결과 평가자

> 실험 결과는 연구 질문에 답합니다. 원시 메트릭은 질문에 답하지 않습니다; 답변을 추출하려면 컨텍스트가 필요합니다. 결과 평가자는 이 컨텍스트를 제공합니다: 가설과 실험 결과를 비교하고, 실험이 가설을 확인 또는 반증하는지 평가하고, 업데이트된 가설에 대한 추천을 생성합니다. 이 레슨은 가설-메트릭 비교기, 가설 확인/반증 평가자 및 업데이트된 가설 추천을 구축합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 30-37
**Time:** ~90 minutes

## Learning Objectives

- 가설과 실험 메트릭을 비교하고 일치도 점수를 계산하는 가설-메트릭 비교기를 구현합니다.
- 확인 임계값을 충족하거나 충족하지 못하는 메트릭을 기반으로 가설을 "확인됨" 또는 "반증됨"으로 평가합니다.
- 반증된 가설을 리팩터링하거나 확인된 가설을 확장하는 업데이트된 가설 생성기를 구축합니다.

## The Problem

실험이 완료되면 원시 메트릭(예: 정확도 72.3%)이 생성됩니다. 연구 질문(예: "데이터 증강이 추론 정확도를 개선합니까?")은 메트릭에 의해 직접 답변되지 않습니다. 실험 전에 합의된 확인 임계값(예: 70% 기준에 비해 정확도가 5% 포인트 이상 개선됨)으로 해석이 필요합니다.

결과 평가자는 이 해석을 자동화합니다: 메트릭을 가져와서 가설의 예측과 비교하고, 가설의 상태(확인됨 또는 반증됨)를 평가합니다.

## The Concept

```mermaid
flowchart TD
  Metrics[Experiment metrics] --> Comparator[Hypothesis-metric comparator]
  Hypothesis[Original hypothesis] --> Comparator
  Comparator --> Score[Match score]
  Score --> Evaluator[Confirm/falsify evaluator]
  Evaluator --> Status["Confirmed" | "Falsified"]
  Status --> Updater[Hypothesis updater]
  Updater --> Updated[Updated hypothesis]
```

### Hypothesis-metric comparator

비교기는 가설 예측과 실험 메트릭을 비교합니다. 두 가지 유형의 예측이 있습니다:

- **정량적 예측** - 특정 메트릭 값(예: "정확도는 기준에 비해 5% 포인트 이상 개선됨 = 75% 정확도"). 비교기는 메트릭이 예측 범위 내에 있는지 계산합니다.
- **정성적 예측** - 특정 동작(예: "모델은 더 적은 훈련 예제로 일반화됨"). 비교기는 이 기준에 대해 메트릭을 평가하기 위해 LLM을 사용합니다.

비교기는 0에서 1 사이의 일치도 점수를 출력합니다.

### Confirm/falsify evaluator

평가자는 일치도 점수를 가져와서 확인 임계값과 비교합니다. 일치도 점수가 확인 임계값 이상이면 가설이 "확인됨"으로 표시됩니다(또는 예비 실험의 경우 "부분 확인"). 일치도 점수가 확인 임계값 미만이면 가설이 "반증됨"으로 표시됩니다.

### Hypothesis updater

반증된 가설에 대해 업데이터는 원래 가설, 메트릭 및 실험 설정을 사용하여 업데이트된 가설을 생성합니다. 업데이트된 가설은 원래 가설을 확장하거나(원래 가설이 부분적으로 확인된 경우) 대체합니다(원래 가설이 완전히 반증된 경우). 각 업데이트된 가설에는 근거가 포함됩니다.

## Build It

`code/main.py` implements:

- `HypothesisMetricComparator` - 가설 예측과 실험 메트릭을 비교합니다. 정량적 및 정성적 예측을 지원합니다.
- `Evaluator` - 비교기에서 일치도 점수를 가져오고 확인 임계값에 대해 평가합니다.
- `HypothesisUpdater` - 반증된 가설에 대해 업데이트된 가설을 생성합니다. 이전 가설, 메트릭 및 실험 설정으로 프롬프트되는 LLM을 사용합니다.

파일 하단의 데모는 두 가지 가설(하나는 확인, 하나는 반증)을 시작합니다. 각각에 대해 실험 메트릭이 생성됩니다. 비교기가 일치도 점수를 계산합니다. 평가자가 가설을 확인 또는 반증으로 레이블링합니다. 업데이터가 반증된 가설에 대한 업데이트된 가설을 생성합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 각 가설에 대한 평가 및 업데이트된 가설을 출력합니다.

## Production Patterns

세 가지 패턴이 결과 평가자를 프로덕션 과학 도구로 확장합니다.

**Multiple confirmation thresholds.** "확인됨"은 한 가지 종류의 결과가 아닙니다. 여러 임계값이 서로 다른 수준의 증거를 포착합니다: "약한 확인"(낮은 임계값), "확인"(보통 임계값) 및 "강한 확인"(높은 임계값). 각 임계값은 실험의 통계적 검정력에 해당합니다.

**Updating hypotheses, not discarding.** 반증된 가설은 폐기되지 않고 확장됩니다. 업데이트된 가설은 원래 가설 ID에 연결됩니다. 가설의 계보가 추적됩니다. 연구자들은 가설이 실험에 의해 어떻게 수정되었는지 검토할 수 있습니다.

**Statistical significance check.** 평가자는 메트릭 변경이 통계적으로 유의한지 확인해야 합니다. 기준과 실험 메트릭 간의 차이가 신뢰 구간 외부에 있는지 확인합니다. 유의하지 않은 변경은 확인으로 표시되지 않습니다.

## Use It

프로덕션 패턴:

- **Hypothesis ID tracks lineage.** 각 가설에는 원래 가설에 다시 연결되는 계보 ID가 있습니다. 반증된 가설이 업데이트되면 업데이트된 가설은 원래 가설 ID를 계보 필드에 상속합니다. 연구자들은 실험에 의해 가설이 어떻게 수정되었는지 확인할 수 있습니다.
- **Human approval before new experiment.** 업데이트된 가설은 새 실험을 생성하기 전에 인간의 승인이 필요합니다. 인간의 개입은 업데이트된 가설이 실행되기 전에 검토되도록 보장합니다.
- **Confidence intervals on metric deltas.** "정확도가 5% 포인트 개선됨"은 "정확도가 3%-7% 포인트 개선됨"과 다릅니다. 평가자는 메트릭 델타의 신뢰 구간을 확인 임계값과 비교해야 합니다.

## Ship It

`outputs/skill-result-evaluator.md`는 실제 프로젝트에서 사용되는 확인 임계값, 반증된 가설의 계보가 추적되는 방법 및 인간의 승인이 필요한 시점을 설명합니다. 이 레슨은 엔진을 제공합니다.

## Exercises

1. 여러 확인 임계값(약한, 중간, 강한)을 추가하고 적절한 레이블을 생성합니다.
2. 각 가설에 대한 계보 추적을 추가합니다. 업데이트된 가설은 원래 가설의 계보 ID를 상속합니다.
3. 메트릭 델타의 신뢰 구간을 계산하고 확인 임계값과 비교하는 통계적 유의성 검사를 추가합니다.
4. 업데이트된 가설이 실행되기 전에 인간의 승인이 필요하도록 `--require-human-approval` 플래그를 추가합니다.
5. 평가 결과를 JSON 파일에 저장하고 가설 상태를 기록합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Hypothesis evaluation | "Did it work?" | 확인 임계값에 대해 가설의 예측과 실험 메트릭 비교 |
| Confirmation threshold | "Success criteria" | 가설이 "확인됨"으로 레이블링되기 위해 일치도 점수가 충족해야 하는 임계값 |
| Falsification | "It didn't work" | 가설이 확인 임계값을 충족하지 못함 |
| Hypothesis lineage | "Hypothesis tree" | 실험에 의해 가설이 어떻게 확장되었는지 추적하는 계보 ID |
| Match score | "How close?" | 0에서 1 사이의 점수로 가설 예측과 실험 메트릭이 얼마나 일치하는지 측정 |

## Further Reading

- [Popper, The Logic of Scientific Discovery (1934/1959)](https://en.wikipedia.org/wiki/The_Logic_of_Scientific_Discovery) - 반증 가능성의 철학
- [Neyman-Pearson lemma](https://en.wikipedia.org/wiki/Neyman–Pearson_lemma) - 가설 검정의 통계적 기초
- [Open Science Framework](https://osf.io/) - 사전 등록 및 확인 임계값의 투명성
- Phase 19 · 50 - 가설 생성기, 이 평가자가 평가하는 가설 생성
- Phase 19 · 52 - 실험 러너, 이 평가자가 평가하는 메트릭 생성
- Phase 19 · 54 - 논문 작성기, 이 평가자의 결과로 논문 업데이트
