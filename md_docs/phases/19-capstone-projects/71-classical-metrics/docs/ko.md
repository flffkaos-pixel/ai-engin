# 고전 메트릭

> LLM 평가의 고전 메트릭은 perplexity와 정확히 일치입니다. Perplexity는 언어 모델링 손실의 지수입니다. 정확히 일치는 생성된 답변과 참조 답변 간의 엄격한 문자열 일치입니다. 이 레슨은 처리를 위해 토크나이저를 사용하여 perplexity를 구현하고 규칙 기반 정규화를 포함한 정확히 일치를 구현합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 30-37, 49
**Time:** ~60 minutes

## Learning Objectives

- 주어진 토큰에 대한 언어 모델의 perplexity를 계산합니다.
- 규칙 기반 정규화(대소문자, 구두점)를 포함한 정확히 일치 메트릭을 계산합니다.

## The Problem

Perplexity와 정확히 일치는 LLM 평가의 기본 메트릭입니다. Perplexity는 모델이 텍스트에 얼마나 잘 맞는지 측정합니다. 정확히 일치는 모델 출력이 참조와 일치하는지 확인합니다.

## The Concept

### Perplexity

Perplexity(PPL)는 언어 모델링 손실의 지수입니다: `PPL = exp(mean(loss_per_token))`. 토크나이저는 텍스트를 모델로 전달하기 위해 토큰화합니다. Perplexity는 모델이 텍스트를 생성할 확률이 얼마나 되는지 측정합니다(PPL이 낮을수록 좋음).

### Exact match

정확히 일치는 생성된 답변이 참조 답변과 정확히 일치하는지 확인합니다. 규칙 기반 정규화(대소문자 무시, 구두점 제거, 공백 정규화)가 비교 전에 특수 토큰(예: `<eos>`)을 처리하기 위해 적용됩니다.

## Build It

`code/main.py` implements:

- `PerplexityCalculator` - 토크나이저를 사용하여 주어진 텍스트에 대한 언어 모델의 perplexity를 계산합니다.
- `ExactMatchCalculator` - 규칙 기반 정규화를 사용하여 정확히 일치를 계산합니다.

파일 하단의 데모는 작은 언어 모델과 토크나이저를 시뮬레이션하고, perplexity와 정확히 일치를 계산하고, 메트릭을 출력합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 perplexity와 정확히 일치 점수를 출력합니다.

## Production Patterns

두 가지 패턴이 이 레슨을 프로덕션 평가로 확장합니다.

**Perplexity on a fixed test set.** Perplexity는 고정된 테스트 세트에서 계산되어야 합니다. Perplexity가 시간이 지남에 따라 어떻게 진화하는지 측정할 수 있기 때문입니다.

**Exact match with relaxed criteria.** 정확히 일치는 까다로울 수 있습니다. 정규화에는 종종 공백, 구두점 및 대소문자 처리가 포함됩니다. 특수 토큰은 정규화되거나 제거되어야 합니다.

## Use It

프로덕션 패턴:

- **Perplexity as a diagnostic, not a goal.** Perplexity는 훈련 목표와 상관관계가 있지만 작업 성능과는 완벽하게 상관되지 않습니다. Perplexity는 진단으로 사용하고, 작업 메트릭(정확히 일치)으로 모델을 선택하십시오.

## Ship It

`outputs/skill-classical-metrics.md`는 실제 프로젝트에서 사용할 perplexity 테스트 세트와 정확히 일치 정규화 규칙을 설명합니다. 이 레슨은 엔진을 제공합니다.

## Exercises

1. perplexity 계산의 정확성을 확인하는 단위 테스트를 추가합니다.
2. 정확히 일치에 대한 정규화 규칙(예: 구두점 제거, 대소문자 무시, 공백 정규화)을 추가합니다.
3. 특수 토큰(예: `<eos>`) 처리를 추가합니다.
4. perplexity 계산에서 평균 손실을 반환하는 `--per-token` 플래그를 추가합니다.
5. 여러 유형의 정규화가 있는 여러 참조 답변을 비교하는 `--multi-ref` 플래그를 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Perplexity | "PPL" | 언어 모델링 손실의 지수, 모델이 텍스트에 얼마나 잘 맞는지 측정 |
| Exact match | "EM" | 생성된 답변과 참조 답변 간의 엄격한 문자열 일치 |
| Normalization | "Cleaning" | 비교 전에 문자열에 적용되는 규칙(대소문자, 구두점) |
| Special token | "EOS, BOS" | perplexity 계산에서 처리되어야 하는 토크나이저 특수 토큰 |

## Further Reading

- [Jelinek et al., Perplexity — a measure of the difficulty of speech recognition tasks](https://www.isca-speech.org/archive/jelinek_1977.html) - PPL의 원본 논문
- Phase 19 · 49 - LM 평가 하네스(이 메트릭 사용)
- Phase 19 · 71 - 코드 실행 메트릭(정확히 일치의 대안)
