# 평가: LM Eval Harness와 EleutherAI

> lm-eval-harness는 LLM 평가를 위한 업계 표준 도구다. 200개 이상의 작업, 커스텀 작업을 위한 YAML 인터페이스, 몇 줄의 구성으로 벤치마크 간 모델 평가. 2026년에는 에이전트 작업과 프롬프트 소스 포맷을 지원한다.

**Type:** Learn
**Languages:** Python, YAML
**Prerequisites:** Phase 14 · 19-20 (Benchmarks)
**Time:** ~60분

## 학습 목표

- lm-eval-harness의 아키텍처를 설명한다: 작업 → 템플릿 → 모델 → 메트릭.
- 새로운 벤치마크를 위한 커스텀 YAML 작업을 작성한다.
- lm-eval-harness가 에이전트 작업(멀티 턴, 도구 사용)과 프롬프트 소스 포맷(YAML, JSON, 개행)을 지원하는 방식을 설명한다.
- lm-eval-harness를 로컬 모델과 API 모델 모두에 대해 실행한다.

## 문제

에이전트를 출시하기 전에 검증이 필요하다. 벤치마크가 복잡하다. lm-eval-harness는 작업 로딩, 모델 추론, 메트릭 집계를 단일 CLI로 표준화한다. 그러나 프레임워크를 배우는 데 오버헤드가 있으며, 200개 작업이 모두 에이전트에 관련된 것은 아니다.

## 개념

### 아키텍처

CLI (`lm_eval`) → 태스크 매니저 → 모델 → 작업. 작업은 다음을 정의:

- 프롬프트 템플릿 (doc 문자열을 사용한 YAML jinja2).
- 예상 출력 (선택적: 'golden' 정답).
- 메트릭 (exact_match, f1, bleu, perplexity, 또는 커스텀).

모델 어댑터: `--model openai-completions` (API), `--model hf` (로컬 transformers), `--model vllm` (vLLM 서빙), `--model local-completions` (모든 OpenAI 호환 API).

### 작업 형식

작업은 YAML. 간단한 것:

```yaml
task: my_qa
dataset_path: json
doc_to_text: "Q: {{question}}\nA:"
doc_to_target: "{{answer}}"
metric: exact_match
```

### 에이전트 작업

2025-2026 이후 lm-eval-harness는 3가지 에이전트 작업 유형을 지원:

- **멀티 턴.** 메시지 이력을 대화 상태로 설정. - **도구 사용.** `available_tools` 및 `tool_call`을 작업 템플릿에 포함.
- **프롬프트 소스.** YAML, JSON, 개행 분리. 단일 작업에서 여러 프롬프트 소스 포맷.

이러한 확장 없이 멀티 단계 에이전트 작업을 평가하는 것은 각 도구 호출을 수동으로 템플릿화하는 것을 의미한다.

### 특화된 변형

**lm-eval-agent-harness** (EleutherAI의 포크). 작업은 도구 사용, 리소스 파일, 체인드 평가가 있는 복합 에이전트 궤적이다. 나중에 Phase 13 - Phase 14 커리큘럼에서 사용.

**lighteval** (Hugging Face). lm-eval-harness의 컴패니언으로, 더 간단한 작업 템플릿. EleutherAI의 도구와 동일한 기본 LLM 평가 패턴.

### 사용 시기

| 도구 | 사용 시기 | 피해야 할 시기 |
|------|-----------|-----------|
| lm-eval-harness | API/로컬 모델을 200개 작업으로 평가 | 작업당 비싼 도구 실행이 필요한 커스텀 에이전트 평가 |
| lm-eval-agent-harness | 에이전트 작업 평가 (멀티 턴, 도구 사용) | 모델을 원시 벤치마크에 대해서만 테스트 |
| lighteval | Hugging Face 워크플로우; 더 간단한 템플릿 | 메트릭 또는 작업 형식의 전체 제어가 필요한 경우 |

### 이 패턴이 잘못되는 경우

- **벤치마크 행복감.** lm-eval-harness 작업 = 실제 성능을 측정하지 않을 수 있는 작업.
- **YAML 폭발.** 조건부 논리가 많은 작업 → 읽기 어려운 YAML.
- **커스텀 에이전트 작업 간과.** lm-eval-harness가 멀티 턴 도구 사용을 지원하지만 표준 작업이 아닌 경우가 많음.

## 직접 구현하기

`code/main.py`는 lm-eval-harness 스타일 미니 평가기를 구현:

- 작업 레지스트리 및 작업 로더 (YAML 작업 게시).
- 3개의 내장 작업: "simple_qa", "multi_turn_qa", "tool_use_qa".
- "multi_turn_qa"를 위한 간단한 에이전트 루프 + 컨텍스트 관리.
- 학습 가능한 파라미터가 있는 모델로 사용되는 규칙 기반 스코어러.

실행:

```
python3 code/main.py
```

출력: 작업당 결과 JSON, 작업당 평균 점수, 히스토그램.

## 활용하기

- **lm-eval-harness** for benchmarking models against 200+ standard tasks.
- **lm-eval-agent-harness** for agent-specific evals.
- **YAML task definitions** to store task configurations in version control.

## 배포하기

`outputs/skill-evaluation-harness-setup.md` scaffolds a task YAML file and integration with lm-eval-harness.

## 연습 문제

1. 장난감 평가기를 lm-eval-harness로 포팅. 실제 모델에 대한 YAML 작업 정의.
2. `multi_turn_qa` 확장: 3턴으로 실행. 작업 YAML에서 턴당 게이팅을 어떻게 표현하는가?
3. 간단한 경우에 여러 메트릭 추가: exact_match, f1, rouge.
4. 작업을 `doc_to_text`, `doc_to_target`, `metric`처럼 문서화. 작업 문서화가 lm-eval-harness 사용을 어떻게 개선하는가?
5. lm-eval-agent-harness 읽기. 일반 하네스에 비해 어떤 에이전트별 기능이 추가되었는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Task | "평가 예제 집합" | 프롬프트, 예상 출력을 위한 템플릿, 메트릭 |
| YAML task | "작업을 위한 구성 as 코드" | jinja2 템플릿이 있는 YAML |
| Model adapter | "모델 브리지" | API 또는 로컬 모델을 lm-eval-harness에 연결 |
| Agent task | "도구 및 다중 턴이 포함된 작업" | 도구 호출, 리소스 파일, 환경 상태가 있는 작업 |

## 추가 자료

- [lm-eval-harness repo](https://github.com/EleutherAI/lm-evaluation-harness) — primary codebase
- [lm-eval-harness docs](https://lm-eval-harness.readthedocs.io/) — YAML task guide
- [lm-eval-agent-harness](https://github.com/EleutherAI/lm-eval-agent-harness) — agent-specific fork
- [lighteval by Hugging Face](https://github.com/huggingface/lighteval) — simpler alternative, HF-native
