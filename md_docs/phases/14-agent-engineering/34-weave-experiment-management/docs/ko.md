# Weave: 실험 관리

> Weave는 평가(레슨 30)를 실험 관리(레슨 34)와 통합한다. Weave는 LLM 앱에서 실행되는 모든 평가를 추적한다. 프롬프트 변경 사항은 실험 로그에 캡처된다. 이 통합이 없다면 평가는 프로덕션 추적에서 분리된다.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 30 (Custom Evaluation), Phase 14 · 31 (Modular Prompts)
**Time:** ~90분

## 학습 목표

- 실험 관리가 평가와 추적을 통합하는 이유를 설명한다.
- Weave의 네 가지 기본 요소를 명명한다: OpRef, 평가기, 데이터 세트, 모델.
- Weave를 관찰 가능성 시스템과 통합하기 위한 기본 구조를 구현한다.
- Tracer, 데이터 세트, 평가기, 모델이 함께 작동하는 방식의 예를 추적한다.

## 문제

평가 점수는 프롬프트 또는 모델이 변경될 때에만 의미가 있다. 실험 관리는 이 연결을 공식화한다 — 프롬프트 버전 A가 평가 점수 X를 갖고, 프롬프트 버전 B가 평가 점수 Y를 갖는다. Weave는 이 두 가지를 연결하는 계층이다.

## 개념

### Weave (Weights & Biases)

- 실험 추적을 위한 오픈소스 Python 패키지.
- 네 가지 기본 요소:
  1. **OpRef.** 함수에 대한 참조. "어떤 프롬프트를 사용했는가?"를 트레이스에 연결.
  2. **평가기.** 점수를 생성하는 함수. 스코어 카드.
  3. **데이터 세트.** 평가 입력. 골든 세트.
  4. **모델.** 평가 중인 LLM 구성. 프롬프트 + 공급자.

### 실험 관리란 무엇인가

실험 관리는 프롬프트 템플릿(레슨 31)과 평가(레슨 30)를 연결한다. Weave 없이는 "무엇이 변경되었는가?"라고 물을 수 없다. Weave를 사용하면 프롬프트 템플릿(OpRef)을 교체하고 평가기를 다시 실행하여 비교를 확인할 수 있다.

Weave는 MLflow(레슨 25) 및 Langfuse(레슨 24)와 유사한 공간을 차지하지만, 실험 관리(프롬프트 템플릿 + 평가)에 특화되어 있다. MLflow는 더 넓은 MLOps에 중점을 둔다. Langfuse는 프로덕션 관찰 가능성에 중점을 둔다. Weave는 실험 계층에 중점을 둔다.

### Weave 작동 방식

1. 트레이서가 LLM 호출을 래핑 → OpRef가 평가기에서 사용된 프롬프트 템플릿에 연결.
2. 평가기가 스코어 카드를 생성 → 점수가 데이터 세트에 기록됨.
3. 데이터 세트가 추적과 평가를 연결 → Weave UI가 "프롬프트 A가 프롬프트 B보다 더 나은 성능"을 보여줌.
4. Flux(레슨 35)가 프로덕션 배포를 위해 Weave에서 평가 상태를 내보냄 → Weave를 배포 파이프라인(레슨 35)에 연결.

### 사용 사례

| 사용 | Weave 제공 |
|------|-----------|
| 프롬프트 엔지니어링 | 프롬프트 템플릿 A가 골든 세트 B에서 어떤 점수를 받는가? |
| 모델 비교 | gpt-4o 대비 claude-4에서 동일한 프롬프트는 어떤가? |
| 회귀 감지 | 프롬프트 변경이 성능을 떨어뜨리는가? |

### 이 패턴이 잘못되는 경우

- **데이터 세트가 없음.** 평가기를 실행했지만 데이터 세트(골든)가 없어 점수의 의미를 알 수 없음.
- **OpRef 없음.** 평가 점수가 있지만 어떤 프롬프트를 참조하는지 알 수 없음.
- **프로덕션과 연결되지 않음.** Weave가 평가를 추적하지만 프로덕션 추적(레슨 23)이 점수와 연결되지 않음.

## 직접 구현하기

`code/main.py`는 Weave 스타일 실험 관리 시스템을 구현:

- 함수 트레이스용 `Tracer`: OpRef로 평가기에 연결.
- 질문 + 골든 답변이 포함된 `Dataset`.
- 점수를 생성하는 `Evaluator`: 골든 세트에 대한 LLM-as-judge.
- 작업에 대한 프롬프트 템플릿을 캡처하는 `Model`.
- 데모: 프롬프트 템플릿 2개를 동시에 실행하고 평가 점수 비교.

실행:

```
python3 code/main.py
```

출력: 프롬프트 템플릿별 평가 점수, Weave 스타일 "무엇이 변경되었는가?" 분석.

## 활용하기

- **Weave** for prompt experimentation + evaluation tracking.
- **Flux** output for production deployment (레슨 35).
- **MLflow** for wider MLOps needs.
- **Langfuse** for production observability (레슨 24).

## 배포하기

`outputs/skill-weave-experiments.md` scaffolds a Weave-style experiment system with tracer, dataset, evaluator, and model.

## 연습 문제

1. Weave 데이터 세트를 더 많은 질문으로 확장. 데이터 세트가 클 때 평가 점수가 어떻게 변하는가?
2. 두 번째 평가기 추가: "정확도" + "간결함". 다중 메트릭 점수 카드는 어떻게 보이는가?
3. OpRef를 프롬프트 템플릿에 연결: 참조가 어떻게 다른 실험을 가능하게 하는가?
4. 평가 점수를 관찰 가능성(레슨 23)으로 내보내기: 추적이 점수를 소비하는 방법.
5. Flux(레슨 35)를 위한 평가 상태 내보내기 형식을 정의: 프로덕션이 "승인된" 실험 상태를 사용하는 방법.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Weave | "ML 실험 관리" | 프롬프트 템플릿과 평가 점수 연결 |
| OpRef | "함수에 대한 참조" | 평가기에서 사용된 프롬프트 템플릿 참조 |
| Evaluator | "점수 생성기" | 데이터 세트(골든)에 대한 점수를 생성하는 함수 |
| Dataset | "평가 입력" | 질문 + 골든 답변 |
| Model | "LLM 구성" | 공급자가 있는 프롬프트 템플릿 |

## 추가 자료

- [Weights & Biases, Weave docs](https://weave-docs.wandb.ai/) — experiment management for LLMs
- [MLflow, Experiments](https://mlflow.org/docs/latest/experiments.html) — wider MLOps experiment tracking
- [Langfuse, Prompt Experiments](https://langfuse.com/docs/prompts/experiments) — experiment management in Langfuse
