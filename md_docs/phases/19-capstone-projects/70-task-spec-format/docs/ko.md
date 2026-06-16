# 작업 사양 형식

> AI 평가는 작업 사양에 의해 구동됩니다: 입력 프롬프트, 참조 답변, 평가 메트릭 및 채점 기준을 포함하는 구조화된 형식입니다. 평가 하네스(레슨 49, 63, 68)를 사용하려면 표준 작업 사양 형식이 필요합니다. 이 레슨은 프롬프트, 참조 답변, 메트릭 및 채점 기준을 포함한 JSON 작업 사양을 정의하고, 로드하고, 검증하는 작업 사양 파서를 구축합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 30-37
**Time:** ~60 minutes

## Learning Objectives

- 프롬프트, 참조 답변, 메트릭 및 채점 기준을 포함하는 표준 JSON 작업 사양 형식을 정의합니다.
- 형식에 대해 작업 사양을 로드하고 검증하는 파서를 구현합니다.

## The Problem

모든 평가 하네스(레슨 49, 63, 68)에는 입력이 필요합니다: 작업 사양. 일관된 형식이 없으면 각 하네스는 작업 사양을 다르게 정의합니다. 표준 형식은 교차 호환성을 보장합니다.

## The Concept

```json
{
  "task_name": "factual_qa",
  "description": "Assess factual recall",
  "prompt_template": "Answer: {input}",
  "reference_answers": ["Paris", "paris"],
  "metric": "exact_match",
  "scoring_criteria": {
    "case_sensitive": false,
    "strip_whitespace": true
  },
  "source": "validation_set_v1",
  "tags": ["qa", "factual"]
}
```

### Task spec fields

- `task_name` - 작업의 고유 식별자
- `description` - 작업의 사람이 읽을 수 있는 설명
- `prompt_template` - 프롬프트를 형식화하는 템플릿, `{input}`이 현재 입력으로 대체됨
- `reference_answers` - 각 입력에 대한 하나 이상의 참조 답변
- `metric` - 사용할 평가 메트릭(정확히 일치, F1, ROUGE-L, CIDEr 등)
- `scoring_criteria` - 점수 계산을 위한 선택적 기준(예: 대소문자 구분, 공백 제거)
- `source` - 작업 사양의 출처(선택 사항)
- `tags` - 작업 분류를 위한 선택적 태그

### Validation

파서는 JSON 스키마에 대해 작업 사양을 검증합니다. 유효성 검사 오류가 명확한 오류 메시지와 함께 보고됩니다.

## Build It

`code/main.py` implements:

- `TaskSpec` - JSON 작업 사양을 위한 데이터 클래스.
- `TaskSpecParser` - JSON 문자열/파일에서 작업 사양을 로드하고 검증합니다.
- `TaskSpecValidator` - JSON 스키마에 대해 작업 사양을 검증합니다.

파일 하단의 데모는 JSON 작업 사양을 로드하고, 검증하고, 내용을 출력합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 작업 사양 내용을 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 평가 인프라로 확장합니다.

**Versioned task specs.** 작업 사양은 버전이 지정되어야 합니다. 버전 관리를 통해 시간이 지남에 따라 작업 사양이 어떻게 변경되었는지 추적할 수 있습니다.

**Task spec repository.** 작업 사양은 중앙 저장소(예: git 저장소)에 저장되어야 합니다. 평가 하네스는 저장소에서 작업 사양을 참조합니다.

**Extensible task specs.** 작업 사양은 사용자 정의 메트릭 및 채점 기준을 지원해야 합니다.

## Use It

프로덕션 패턴:

- **Task specs as Git LFS objects.** 작업 사양이 큰 데이터를 포함하는 경우 Git LFS에 저장되어야 합니다.
- **Task spec inheritance.** 작업 사양은 다른 작업 사양에서 상속되어 유사한 작업 간에 공통 필드를 공유할 수 있습니다.

## Ship It

`outputs/skill-task-spec-format.md`는 실제 프로젝트에서 사용할 작업 사양 형식, 작업 사양이 저장되는 위치 및 버전이 지정되는 방법을 설명합니다. 이 레슨은 엔진을 제공합니다.

## Exercises

1. 파일에서 작업 사양을 로드하는 `--from-file` CLI 플래그를 추가합니다.
2. 작업 사양에 대한 버전 관리(필드 `version`)를 추가합니다.
3. 다른 작업 사양에서 상속하는 작업 사양 상속을 추가합니다.
4. 사용자 정의 메트릭 및 채점 기준에 대한 확장성 후크를 추가합니다.
5. 작업 사양 형식을 JSON에 대해 YAML을 지원하도록 확장합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Task spec | "Evaluation job" | 프롬프트, 답변, 메트릭 및 기준을 포함한 구조화된 평가 사양 |
| Prompt template | "Format string" | `{input}`을 대체하여 프롬프트를 생성하는 템플릿 |
| Reference answer | "Golden answer" | 비교를 위한 참조 답변 |
| Scoring criteria | "Grading rules" | 점수 계산을 위한 선택적 기준(예: 대소문자 구분) |

## Further Reading

- [JSON Schema](https://json-schema.org/) - 작업 사양 검증을 위한 스키마 언어
- [LM Evaluation Harness task format](https://github.com/EleutherAI/lm-evaluation-harness) - 유사한 작업 사양 형식
- Phase 19 · 49 - LM 평가 하네스(작업 사양 사용)
- Phase 19 · 63 - 비전-언어 평가(작업 사양 사용)
- Phase 19 · 68 - RAG 평가(작업 사양 사용)
- Phase 19 · 74 - 리더보드 집계(리더보드에 작업 사양 제출)
