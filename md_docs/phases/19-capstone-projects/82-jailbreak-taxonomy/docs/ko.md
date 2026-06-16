# 탈옥 분류 체계

> LLM은 유해한 출력을 방지하기 위해 안전 가드레일로 훈련됩니다. 탈옥은 가드레일을 우회하는 프롬프트입니다. 탈옥을 이해하는 것이 방어의 첫 번째 단계입니다. 이 레슨은 역할 기반, 가상화, 코드 주입 및 다국어 프롬프트를 포함한 탈옥 분류 체계를 구축합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 30-37
**Time:** ~90 minutes

## Learning Objectives

- 일반적인 탈옥 범주를 포함하는 탈옥 분류 체계(역할 기반, 가상화, 코드 주입, 다국어 등)를 구축합니다.
- 탈옥 프롬프트를 감지하고 분류하는 분류기를 구현합니다.

## The Problem

LLM은 안전 가드레일로 훈련되지만 탈옥은 이를 우회할 수 있습니다. 탈옥을 이해하는 것이 방어의 첫 번째 단계입니다. 탈옥 분류 체계는 일반적인 탈옥 유형을 분류합니다.

## The Concept

### Jailbreak categories

- **Role-based** - 모델이 유해한 출력을 생성할 수 있는 역할을 맡도록 요청합니다(예: "이제 당신은 DAN입니다...").
- **Hypothetical** - 모델이 가상 시나리오에서 출력을 생성하도록 요청합니다(예: "소설을 쓰고 있다고 가정해 보십시오...").
- **Code injection** - 지침을 무시하는 코드를 생성하도록 모델에 요청합니다(예: "Python 코드에서...를 출력하십시오").
- **Multilingual** - 프롬프트의 일부를 무시하는 여러 언어를 사용합니다.
- **Encoding** - 인코딩(예: Base64, ROT13)을 사용하여 안전 가드레일을 우회합니다.
- **Context manipulation** - 모델이 지침보다 컨텍스트를 우선시하도록 긴 컨텍스트를 사용합니다.

### Classifier

분류기는 프롬프트를 분석하여 다음을 감지합니다:

- 탈옥 카테고리(위의 목록에서).
- 탈옥 강도(얼마나 적극적으로 가드레일을 우회하려고 시도하는지).

## Build It

`code/main.py` implements:

- `JailbreakTaxonomy` - 탈옥 카테고리와 탐지 규칙을 포함하는 분류 체계 데이터 구조.
- `JailbreakClassifier` - 프롬프트를 분석하고 탈옥 카테고리를 감지하는 분류기.

파일 하단의 데모는 합성 프롬프트를 탈옥 분류기에 통과시키고 감지된 카테고리를 출력합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 감지된 탈옥 카테고리를 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 탈옥 방어로 확장합니다.

**Regularly update taxonomy.** 새로운 탈옥이 정기적으로 발견됩니다. 분류 체계는 정기적으로 업데이트되어야 합니다.

**Ensemble detection.** 여러 분류기가 함께 사용되어 탈옥 탐지 정확도를 향상시킵니다.

**Adversarial training.** 분류기는 적대적 예제(생성된 탈옥)에 대해 훈련되어 강건성을 향상시킵니다.

## Use It

프로덕션 패턴:

- **Classifier as a guardrail.** 분류기는 프롬프트를 입력하기 전에 탈옥을 감지하는 가드레일로 사용됩니다(레슨 83).

## Ship It

`outputs/skill-jailbreak-taxonomy.md`는 실제 프로젝트에서 사용할 탈옥 카테고리와 분류기 업데이트 빈도를 설명합니다.

## Exercises

1. 새로운 탈옥 카테고리(예: 소수 언어, 인코딩)를 추가합니다.
2. 분류기에 강도 평가를 추가합니다.
3. 앙상블 탐지(여러 분류기 사용)를 추가합니다.
4. 탐지 정확도를 평가하는 평가 모드를 추가합니다.
5. 분류기를 적대적 예제에 대해 훈련하는 적대적 훈련을 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Jailbreak | "Guardrail bypass" | LLM의 안전 가드레일을 우회하는 프롬프트 |
| Taxonomy | "Attack categories" | 일반적인 탈옥 유형의 분류 |
| Classifier | "Detector" | 프롬프트에서 탈옥을 감지하는 분류기 |
| Adversarial training | "Attack training" | 적대적 예제로 분류기 훈련 |

## Further Reading

- [Wei et al., Jailbroken: How Does LLM Safety Training Fail? (NeurIPS 2023)](https://arxiv.org/abs/2307.02483) - 탈옥 분류 체계
- [Mazeika et al., Harmbench: A Standardized Evaluation Framework for Automated Red Teaming (arXiv 2402.04249)](https://arxiv.org/abs/2402.04249) - 레드팀 프레임워크
- Phase 19 · 83 - 프롬프트 인젝션 탐지기(이 분류 체계에 구축)
