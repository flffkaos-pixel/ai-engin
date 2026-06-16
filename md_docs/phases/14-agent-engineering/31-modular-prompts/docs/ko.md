# 모듈러 프롬프트

> 프롬프트는 저장소에 체크인한다. 템플릿 엔진, 버전 관리, 프롬프트 레지스트리. 모놀리식 프롬프트의 함정: 확장 시 깨지기 쉽다. Langfuse, Opik 또는 MLflow 추적을 사용한 구조화된 접근 방식.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 24 (Observability Platforms), Phase 14 · 30 (Custom Evaluation)
**Time:** ~90분

## 학습 목표

- 모놀리식 프롬프트의 함정과 모듈러 프롬프트가 이를 해결하는 방법을 설명한다.
- 모듈러 프롬프트 시스템의 세 가지 핵심 부분을 구현한다: 템플릿 엔진, 프롬프트 레지스트리, A/B 테스트 프레임워크.
- 프롬프트 버전 관리와 평가(레슨 30)를 커스텀 평가에 연결한다.
- 프롬프트 레지스트리를 기존 관찰 가능성 시스템에 연결하기 위한 데이터 형식을 정의한다.

## 문제

프롬프트는 커지고 깨지기 쉬우며 버전이 지정되지 않는다. 프롬프트가 하나의 거대한 문자열로 존재하면 두려움 없이 변경할 수 없다. 모듈러 프롬프트는 프롬프트를 구성 요소 분할한다 (각 부분이 하나의 작업을 담당). 이 레슨은 `tools.py`에서 가드레일까지 프롬프트를 코드에서 분리한다.

## 개념

### 프롬프트는 코드와 동일한 방식으로 변경된다

프롬프트는 실행 가능한 구성이다. 코드와 동일한 엔지니어링 관행이 적용된다: 버전 관리, 리뷰, 테스트, 배포. 프롬프트를 모듈러 구성으로 가져오지 않으면 프롬프트가 깨지기 쉬워지고 변경에 대한 저항이 커진다.

### 모놀리식 대 모듈러 프롬프트

**모놀리식:** 템플릿 문자열에 포함된 시스템 프롬프트, 컨텍스트, 모든 것. 모든 것을 변경. "이 프롬프트가 정확히 무엇을 하는가?"를 결정할 수 없음.

**모듈러:** 프롬프트는 섹션으로 분할: 지침, 컨텍스트, 출력 형식, 제약 조건, 예제. 각 섹션의 버전을 개별적으로 지정. 프롬프트 엔지니어는 한 섹션을 변경하고 다른 섹션을 계속 테스트.

### 프롬프트 레지스트리

프롬프트 레지스트리는 프롬프트를 중앙에서 관리하는 인터페이스다. 프롬프트는 레지스트리에 등록되고 런타임에 검색된다. 레지스트리는 커스텀 평가(레슨 30) 및 A/B 테스트와 통합된다.

레지스트리 스키마:

```json
{
  "prompt_id": "customer-support-v2",
  "version": 3,
  "sections": {
    "system": "...",
    "context": "...",
    "output_format": "...",
    "constraints": "...",
    "examples": []
  },
  "metadata": {
    "model": "claude-4",
    "created_by": "user@example.com",
    "eval_score": 0.92
  }
}
```

### 프롬프트 레지스트리 통합

1. **Langfuse.** 프롬프트 버전 관리, 프롬프트 레지스트리, LLM-as-judge 평가기. 프롬프트 변경은 버전이 지정되고 추적 가능.
2. **Opik.** 프롬프트 버전 관리 + Diff UI + CVE 스캐닝. 프롬프트 변경 사항을 검토하고 취약점 검사.
3. **MLflow 추적.** 프롬프트 템플릿을 추적에 자동 기록. 템플릿 변경 사항을 시간 경과에 따라 검사.

세 가지 모두 프롬프트 템플릿 버전 관리와 평가를 연결한다.

### A/B 테스트

모듈러 프롬프트 시스템을 사용하면 프롬프트 변형을 동시에 실행할 수 있다. 기본 프롬프트와 실험 프롬프트, 둘 다 관찰 가능성 및 평가와 연결. 프롬프트 레지스트리가 버전을 관리하므로 두 변형을 동시에 배포하고 프로덕션 트래픽을 분할할 수 있다. 관찰 가능성(레슨 23-24)이 결과를 추적하고, 평가(레슨 30)가 실험 결과를 게시한다.

### 이 패턴이 잘못되는 경우

- **과잉 분할.** 프롬프트가 20개의 템플릿으로 분할되어 두려움 없이 변경할 수 없게 됨. 3-5개 섹션이면 충분.
- **프롬프트 레지스트리만으로 충분하다고 가정.** 레지스트리가 버전을 관리하지만 평가를 실행하지 않으면 프롬프트가 무엇을 하는지 알 수 없음.
- **관찰 가능성 연결 없음.** 프롬프트 레지스트리가 분리됨. 평가 점수와 프롬프트 버전을 함께 표시해야 함.

## 직접 구현하기

`code/main.py`는 모듈러 프롬프트 시스템을 구현:

- 템플릿 엔진: `{{system}}`, `{{context}}`, `{{output_format}}`, `{{constraints}}`를 렌더링.
- 프롬프트 레지스트리: 프롬프트 등록, 버전별 검색, 메타데이터 저장.
- A/B 테스트 프레임워크: 프롬프트 변형 분할, 각 변형의 버전을 관찰 가능성에 기록.
- 관찰 가능성 연결: 프롬프트 ID, 버전, 변형이 포함된 로그. 평가기 인터페이스에 게시.

실행:

```
python3 code/main.py
```

출력: 한 번의 A/B 테스트 실행; 프롬프트 버전 관찰 가능성; 평가 점수.

## 활용하기

- 모든 프롬프트에 대해 모듈러 템플릿 구조(3-5개 섹션)로 시작.
- 프롬프트 레지스트리 사용: Langfuse, Opik, MLflow.
- 프롬프트 변경 사항을 지속적으로 평가하기 위해 A/B 테스트 연결.

## 배포하기

`outputs/skill-modular-prompts.md` scaffolds a modular prompt system with template engine, prompt registry, A/B testing, and observability integration.

## 연습 문제

1. 프롬프트 레지스트리 확장: 프롬프트를 YAML 또는 JSON 파일에서 로드 (DB가 아님).
2. A/B 테스트 추가: 시스템 프롬프트의 변형 2개를 동시에 실행.
3. 모듈러 시스템에서 프롬프트 평가 연결: 스코어 카드의 버전 번호 게시.
4. 프롬프트 레지스트리를 실험 관리(레슨 34)와 통합: 템플릿 변경을 실험으로 추적.
5. 프롬프트 레지스트리에서 폴백 체인 구현: 프롬프트 버전을 찾을 수 없으면 기본값으로 대체.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Modular prompts | "프롬프트 구성" | 지침, 컨텍스트, 형식, 제약 조건, 예제가 분할됨 |
| Prompt registry | "프롬프트 저장소" | 프롬프트 버전, 메타데이터, 평가 점수의 중앙 저장소 |
| A/B test | "프롬프트 실험" | 프롬프트 변형을 동시에 실행, 측정, 비교 |
| Monolithic prompt | "하나의 거대한 프롬프트" | 모든 것이 포함된 단일 템플릿 문자열; 깨지기 쉽고 변경 불가 |

## 추가 자료

- [Langfuse, Prompt Management](https://langfuse.com/docs/prompts) — prompt registry + versioning + evals
- [Opik, Prompt Management](https://www.comet.com/docs/opik/prompt-management/overview/) — versioning, diff, CVE scanning
- [MLflow, Prompt Engineering UI](https://mlflow.org/docs/latest/llm/prompt-engineering-ui/index.html) — prompt templates + tracing
- [OpenAI, Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering) — modular prompt strategies
