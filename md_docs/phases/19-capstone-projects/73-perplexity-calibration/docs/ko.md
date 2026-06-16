# Perplexity 교정

> Perplexity는 언어 모델의 교정된 불확실성 추정치를 제공해야 합니다: perplexity가 10인 모델은 10-way 동등하게 가능한 대안을 고려하고 있다는 의미여야 합니다. 실제로 LLM의 perplexity는 교정되지 않습니다: 모델이 한 답변에 높은 확신을 가지지만 perplexity는 여전히 높습니다. 이 레슨은 perplexity 교정을 구현합니다: perplexity를 기대 정확도와 비교하고(교정 곡선), 교정 오차(ECE)를 계산하고, 온도 스케일링으로 perplexity를 교정합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 30-37, 71
**Time:** ~60 minutes

## Learning Objectives

- Perplexity를 기대 정확도와 비교하여 교정 곡선을 계산합니다.
- ECE(기대 교정 오차)를 계산합니다.
- perplexity를 교정하기 위해 온도 스케일링을 적용합니다.

## The Problem

Perplexity는 교정되어야 합니다: perplexity가 10인 모델은 선택이 10-way 균등하다는 의미여야 합니다. 실제로는 그렇지 않습니다. 교정은 이러한 불일치를 측정하고 수정합니다.

## The Concept

### Calibration curve

교정 곡선은 perplexity를 기대 정확도와 비교합니다. 완벽하게 교정된 모델의 경우 곡선은 대각선입니다. perplexity 빈(예: [0-5), [5-10), [10-20))에 대해 각 빈의 평균 정확도를 계산하고 교정 곡선에 플롯합니다.

### Expected Calibration Error (ECE)

ECE는 perplexity-정확도 쌍과 완벽한 교정(대각선) 사이의 가중 평균 절대 차이입니다. ECE가 낮을수록 교정이 더 좋습니다.

### Temperature scaling

온도 스케일링은 로짓에 단일 스칼라 온도 파라미터 `T`를 적용합니다: `logits / T`. 온도 `T`는 교정 곡선이 대각선에 가까워지도록 검증 세트에서 학습됩니다. `T > 1`은 분포를 평탄화하고(덜 확신), `T < 1`은 분포를 날카롭게 합니다(더 확신).

## Build It

`code/main.py` implements:

- `CalibrationCurveCalculator` - perplexity 빈에 걸쳐 교정 곡선을 계산합니다.
- `ECECalculator` - ECE(기대 교정 오차)를 계산합니다.
- `TemperatureScaler` - 검증 세트에서 온도 파라미터를 학습하고 perplexity에 적용합니다.

파일 하단의 데모는 교정되지 않은 모델을 시뮬레이션하고, 교정 곡선을 계산하고, ECE를 계산하고, 온도 스케일링을 적용하고, 교정된 및 교정되지 않은 perplexity를 출력합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 교정 곡선 데이터, ECE 및 교정된 및 교정되지 않은 perplexity를 출력합니다.

## Production Patterns

두 가지 패턴이 이 레슨을 프로덕션 교정으로 확장합니다.

**Calibration on held-out set.** 교정은 홀드아웃 검증 세트에서 수행되어야 합니다.

**Per-bucket calibration analysis.** ECE는 세분화된 진단을 제공하지 않습니다. 빈별 정확도 분석은 특정 perplexity 범위에서 교정이 실패하는 위치를 보여줍니다.

## Use It

프로덕션 패턴:

- **Temperature scaling is fast.** 온도 스케일링은 단일 파라미터를 학습하므로 교정이 빠릅니다.
- **Calibration-aware evaluation.** perplexity 교정이 좋지 않으면 perplexity 기반 평가 메트릭이 신뢰할 수 없음을 의미합니다.

## Ship It

`outputs/skill-perplexity-calibration.md`는 실제 프로젝트에서 사용할 교정 검증 세트와 학습된 온도 파라미터를 설명합니다. 이 레슨은 엔진을 제공합니다.

## Exercises

1. perplexity 빈을 제어하는 `--num-bins` 플래그를 추가합니다.
2. 플롯 교정 곡선을 추가합니다.
3. 온도 스케일링을 위해 음의 로그 우도(NLL) 손실을 추가합니다.
4. ECE 계산에서 가중치가 적용되지 않은(균등 가중) ECE를 추가합니다.
5. 교정 곡선 데이터를 보기 위한 `--calibration-curve-plot` 플래그를 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Calibration curve | "Reliability diagram" | Perplexity를 기대 정확도와 비교하여 교정 품질 측정 |
| ECE | "Expected Calibration Error" | perplexity-정확도 차이의 가중 평균, 낮을수록 좋음 |
| Temperature scaling | "Logit scaling" | perplexity를 교정하기 위해 온도 파라미터로 로짓을 스케일링 |

## Further Reading

- [Guo et al., On Calibration of Modern Neural Networks (ICML 2017)](https://arxiv.org/abs/1706.04599) - 신경망 교정의 원본
- Phase 19 · 71 - 고전 메트릭(perplexity, 이 레슨의 기반)
- Phase 19 · 75 - 엔드-투-엔드 평가 러너(이 교정 통합)
