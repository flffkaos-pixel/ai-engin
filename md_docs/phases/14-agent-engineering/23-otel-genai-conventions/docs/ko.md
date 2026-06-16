# OpenTelemetry GenAI 시맨틱 규칙

> OpenTelemetry의 GenAI SIG(2024년 4월 출범)는 에이전트 텔레메트리를 위한 표준 스키마를 정의합니다. 스팬 이름, 속성 및 콘텐츠 캡처 규칙이 벤더 간에 통합되어 Datadog, Grafana, Jaeger, Honeycomb에서 에이전트 트레이스가 동일한 의미를 갖도록 합니다.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 13 (LangGraph), Phase 14 · 24 (Observability Platforms)
**Time:** ~60분

## 학습 목표

- GenAI 스팬 카테고리(model/client, agent, tool)를 명명합니다.
- `invoke_agent` CLIENT 스팬과 INTERNAL 스팬을 구분하고 각각이 적용되는 경우를 이해합니다.
- 최상위 GenAI 속성(provider name, request model, data-source ID)을 나열합니다.
- 콘텐츠 캡처 계약(opt-in, `OTEL_SEMCONV_STABILITY_OPT_IN`, 외부 참조 권장)을 설명합니다.

## 문제

모든 벤더가 자체 스팬 이름을 발명합니다. 운영팀은 결국 프레임워크별 대시보드를 구축하게 됩니다. OpenTelemetry의 GenAI SIG는 전체 에코시스템이 대상으로 삼는 하나의 표준을 정의하여 이 문제를 해결합니다.

## 개념

### 스팬 카테고리

1. **Model / client 스팬.** 원시 LLM 호출을 다룹니다. 제공자 SDK(Anthropic, OpenAI, Bedrock) 및 프레임워크 모델 어댑터에 의해 생성됩니다.
2. **Agent 스팬.** `create_agent`(에이전트가 생성될 때)와 `invoke_agent`(실행될 때)입니다.
3. **Tool 스팬.** 도구 호출당 하나씩 생성되며, 부모-자식 관계로 에이전트 스팬에 연결됩니다.

### 에이전트 스팬 명명

- 스팬 이름: 이름이 있는 경우 `invoke_agent {gen_ai.agent.name}`, 없으면 `invoke_agent`로 폴백합니다.
- 스팬 종류:
  - **CLIENT** — 원격 에이전트 서비스용(OpenAI Assistants API, Bedrock Agents).
  - **INTERNAL** — 프로세스 내 에이전트 프레임워크용(LangChain, CrewAI, 로컬 ReAct).

### 주요 속성

- `gen_ai.provider.name` — `anthropic`, `openai`, `aws.bedrock`, `google.vertex`.
- `gen_ai.request.model` — 모델 ID.
- `gen_ai.response.model` — 확인된 모델(라우팅으로 인해 요청과 다를 수 있음).
- `gen_ai.agent.name` — 에이전트 식별자.
- `gen_ai.operation.name` — `chat`, `completion`, `invoke_agent`, `tool_call`.
- `gen_ai.data_source.id` — RAG의 경우: 어떤 코퍼스나 저장소가 참조되었는지.

Anthropic, Azure AI Inference, AWS Bedrock, OpenAI에 대한 기술별 규칙이 존재합니다.

### 콘텐츠 캡처

기본 규칙: 계측은 기본적으로 입력/출력을 캡처하지 않아야 합니다(SHOULD NOT). 캡처는 opt-in 방식입니다:

- `gen_ai.system_instructions`
- `gen_ai.input.messages`
- `gen_ai.output.messages`

권장 프로덕션 패턴: 콘텐츠를 외부(S3, 로그 저장소)에 저장하고, 스팬에는 참조(포인터 ID, 텍스트가 아님)를 기록합니다. 이는 관찰 가능성에 연결된 Lesson 27의 콘텐츠 중독 방어입니다.

### 안정성

대부분의 규칙은 2026년 3월 기준으로 실험 단계입니다. 안정적인 미리보기를 선택하려면:

```
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
```

Datadog v1.37+는 GenAI 속성을 LLM Observability 스키마에 기본적으로 매핑합니다. 다른 백엔드(Grafana, Honeycomb, Jaeger)는 원시 속성을 지원합니다.

### 이 패턴이 실패하는 경우

- **스팬에 전체 프롬프트 캡처.** 운영팀이 읽을 수 있는 트레이스에 PII, 비밀, 고객 데이터가 포함됩니다. 외부에 저장하세요.
- **`gen_ai.provider.name` 누락.** 속성이 누락되면 다중 제공자 대시보드가 작동하지 않습니다.
- **부모 링크가 없는 스팬.** 고아 도구 스팬이 발생합니다. 항상 컨텍스트를 전파하세요.
- **안정성 opt-in 미설정.** 백엔드 업그레이드 시 속성 이름이 변경될 수 있습니다.

## 빌드하기

`code/main.py`는 GenAI 규칙을 따르는 stdlib 스팬 이미터를 구현합니다:

- GenAI 속성 스키마를 가진 `Span`.
- `start_span`, 중첩 컨텍스트를 가진 `Tracer`.
- 다음을 생성하는 스크립트형 에이전트 실행: `create_agent`, `invoke_agent`(INTERNAL), 도구별 스팬, LLM 호출용 `chat` 스팬.
- 프롬프트를 외부에 저장하고 스팬에 ID를 기록하는 콘텐츠 캡처 모드.

실행:

```
python3 code/main.py
```

출력: 모든 필수 GenAI 속성을 가진 스팬 트리와 opt-in 콘텐츠 참조를 보여주는 "외부 저장소".

## 사용하기

- **Datadog LLM Observability** (v1.37+) — 속성을 기본적으로 매핑.
- **Langfuse / Phoenix / Opik** (Lesson 24) — 에코시스템 자동 계측.
- **Jaeger / Honeycomb / Grafana Tempo** — 원시 OTel 트레이스; GenAI 속성에서 대시보드 구축.
- **자가 호스팅** — GenAI 프로세서와 함께 OTel Collector 실행.

## 배포하기

`outputs/skill-otel-genai.md`는 콘텐츠 캡처 기본값과 외부 참조 저장소를 사용하여 기존 에이전트에 OTel GenAI 스팬을 연결합니다.

## 연습 문제

1. Lesson 01의 ReAct 루프에 `invoke_agent`(INTERNAL) + 도구별 스팬을 계측합니다. Jaeger 인스턴스로 전송하세요.
2. "참조 전용" 모드의 콘텐츠 캡처를 추가합니다: 프롬프트는 SQLite로, 스팬 속성은 행 ID만 전달합니다.
3. `gen_ai.data_source.id`에 대한 스펙을 읽습니다. Lesson 09의 Mem0 검색에 연결하세요.
4. `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`을 설정하고 속성이 collector에 의해 이름이 변경되지 않는지 확인합니다.
5. 대시보드를 구축합니다: "어떤 도구 오류가 어떤 모델과 상관관계가 있는지"를 GenAI 속성만으로 파악합니다.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|------------------|-----------|
| GenAI SIG | "OpenTelemetry GenAI 그룹" | 스키마를 정의하는 OTel 워킹 그룹 |
| invoke_agent | "에이전트 스팬" | 에이전트 실행을 나타내는 스팬 이름 |
| CLIENT 스팬 | "원격 호출" | 원격 에이전트 서비스 호출 스팬 |
| INTERNAL 스팬 | "프로세스 내" | 프로세스 내 에이전트 실행 스팬 |
| gen_ai.provider.name | "제공자" | anthropic / openai / aws.bedrock / google.vertex |
| gen_ai.data_source.id | "RAG 소스" | 검색에 사용된 코퍼스/저장소 |
| Content capture | "프롬프트 로깅" | 메시지의 Opt-in 캡처; 프로덕션에서는 외부 저장 |
| Stability opt-in | "미리보기 모드" | 실험적 규칙을 고정하는 환경 변수 |

## 추가 자료

- [OpenTelemetry GenAI 의미 규칙](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 스펙
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) — 기본 GenAI 스팬
- [AutoGen v0.4 (Microsoft Research)](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — 내장 OTel 스팬
- [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) — W3C 트레이스 컨텍스트 전파
