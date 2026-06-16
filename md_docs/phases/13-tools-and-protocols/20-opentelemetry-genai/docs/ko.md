# OpenTelemetry GenAI — 도구 호출 종단간 추적

> 에이전트가 다섯 개의 도구, 세 개의 MCP 서버, 두 개의 하위 에이전트를 호출합니다. 이 모든 것에 걸쳐 하나의 트레이스가 필요합니다. OpenTelemetry GenAI 의미론 규칙(v1.37 이상의 안정적 속성)은 2026년 표준으로, Datadog, Langfuse, Arize Phoenix, OpenLLMetry 및 AgentOps에서 네이티브 지원됩니다. 이 레슨은 필수 속성을 명명하고, 스팬 계층(에이전트 → LLM → 도구)을 살펴보며, 모든 OTel 익스포터에 연결할 수 있는 stdlib 스팬 이미터를 제공합니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, OTel 스팬 이미터)
**Prerequisites:** 13단계 07과 (MCP 서버), 13단계 08과 (MCP 클라이언트)
**Time:** 약 75분

## 학습 목표

- LLM 스팬 및 도구 실행 스팬에 대한 필수 OTel GenAI 속성을 명명할 수 있다.
- 에이전트 루프, LLM 호출, 도구 호출 및 MCP 클라이언트 디스패치를 포함하는 트레이스 계층을 구축할 수 있다.
- 캡처할 콘텐츠(옵트인)와 삭제할 콘텐츠(기본값)를 결정할 수 있다.
- 도구 코드를 재작성하지 않고 로컬 수집기(Jaeger, Langfuse)로 스팬을 출력할 수 있다.

## 문제

2026년 2월의 디버그: 사용자가 "내 에이전트가 때로는 30초, 때로는 3초 만에 응답합니다"라고 보고. 트레이스 없음. 로그는 LLM 호출을 보여주지만, 도구 디스패치, MCP 서버 왕복, 하위 에이전트는 보여주지 않음. 추측만 함. 결국 찾은 것: 하나의 MCP 서버가 콜드 스타트에서 가끔 멈춤.

종단간 추적 없이는 이것을 찾을 수 없음. OTel GenAI가 수정.

규칙은 2025-2026년 OpenTelemetry 의미론 규칙 그룹 아래에서 정착. Datadog, Langfuse, Phoenix, OpenLLMetry 및 AgentOps가 모두 동일한 스팬을 파싱하도록 안정적인 속성 이름을 정의. 한 번 계측; 모든 백엔드로 전송.

## 개념

### 스팬 계층

```
agent.invoke_agent  (최상위, INTERNAL 스팬)
 ├── llm.chat       (CLIENT 스팬)
 ├── tool.execute   (INTERNAL)
 │    └── mcp.call  (CLIENT 스팬)
 ├── llm.chat       (CLIENT 스팬)
 └── subagent.invoke (INTERNAL)
```

전체가 하나의 트레이스 id 아래에 중첩. 스팬 id가 부모-자식 관계 연결.

### 필수 속성

2025-2026 semconv 기준:

- `gen_ai.operation.name` — `"chat"`, `"text_completion"`, `"embeddings"`, `"execute_tool"`, `"invoke_agent"`.
- `gen_ai.provider.name` — `"openai"`, `"anthropic"`, `"google"`, `"azure_openai"`.
- `gen_ai.request.model` — 요청된 모델 문자열(예: `"gpt-4o-2024-08-06"`).
- `gen_ai.response.model` — 실제로 제공된 모델.
- `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens`.
- `gen_ai.response.id` — 상관 관계를 위한 제공자 응답 id.

도구 스팬용:

- `gen_ai.tool.name` — 도구 식별자.
- `gen_ai.tool.call.id` — 특정 호출 id.
- `gen_ai.tool.description` — 도구 설명(선택 사항).

에이전트 스팬용:

- `gen_ai.agent.name` / `gen_ai.agent.id` / `gen_ai.agent.description`.

### 스팬 종류

- `SpanKind.CLIENT` — 프로세스 경계를 넘는 호출용(LLM 제공자, MCP 서버).
- `SpanKind.INTERNAL` — 에이전트 자체 루프 단계 및 도구 실행용.

### 옵트인 콘텐츠 캡처

기본적으로 스팬은 메트릭과 타이밍을 전달 — 프롬프트나 완성이 아님. 대용량 페이로드와 PII는 기본적으로 꺼짐. `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` 및 특정 콘텐츠 캡처 환경 변수를 설정하여 콘텐츠 포함. 프로덕션에서 활성화하기 전에 신중히 검토.

### 스팬의 이벤트

토큰 수준 이벤트를 스팬 이벤트로 추가 가능:

- `gen_ai.content.prompt` — 입력 메시지.
- `gen_ai.content.completion` — 출력 메시지.
- `gen_ai.content.tool_call` — 기록된 도구 호출.

이벤트는 스팬 내에서 시간순으로 정렬되어 세부 재생 가능.

### 익스포터

OTel 스팬은 다음으로 내보내기:

- **Jaeger / Tempo.** OSS, 온프레미스.
- **Langfuse.** LLM 관찰 가능성 특화; 토큰 사용량 시각화.
- **Arize Phoenix.** 평가 + 추적 결합.
- **Datadog.** 상용; `gen_ai.*` 속성을 네이티브 파싱.
- **Honeycomb.** 컬럼 지향; 쿼리 친화적.

모두 와이어 형식인 OTLP를 사용. 코드는 상관하지 않음.

### MCP를 통한 전파

MCP 클라이언트가 서버를 호출할 때 W3C traceparent 헤더를 요청에 주입. Streamable HTTP는 표준 헤더를 지원. Stdio는 HTTP 헤더를 네이티브로 전달하지 않음; 사양의 2026 로드맵은 JSON-RPC 호출에 `_meta.traceparent` 필드 추가를 논의.

그것이 출시될 때까지: 모든 요청의 `_meta`에 traceparent를 수동으로 포함. 서버가 트레이스 id를 기록.

### 메트릭

스팬과 함께 GenAI semconv는 메트릭을 정의:

- `gen_ai.client.token.usage` — 히스토그램.
- `gen_ai.client.operation.duration` — 히스토그램.
- `gen_ai.tool.execution.duration` — 히스토그램.

호출별 세부 정보가 필요 없는 대시보드에 사용.

### AgentOps 계층

AgentOps(2024년 설립)는 GenAI 관찰 가능성에 특화. 인기 프레임워크(LangGraph, Pydantic AI, CrewAI)를 래핑하여 OTel 스팬을 자동 출력. 스택이 지원되는 프레임워크를 사용하면 유용; 그렇지 않으면 수동 계측 사용.

## 사용하기

`code/main.py`는 LLM을 호출하고, 두 도구를 디스패치하고, 하나의 MCP 왕복을 수행하는 에이전트에 대해 OTel 형태의 스팬을 stdout(OTLP-JSON-유사 형식)으로 출력합니다. 실제 익스포터 없음 — 레슨은 스팬 형태와 속성 집합에 초점. 출력을 OTLP 호환 뷰어에 붙여넣거나 그냥 읽으세요.

살펴볼 내용:

- 트레이스 id가 모든 스팬에서 공유됨.
- 부모-자식 링크가 `parentSpanId`로 인코딩됨.
- 필수 `gen_ai.*` 속성이 채워짐.
- 콘텐츠 캡처는 기본적으로 꺼짐; 하나의 시나리오가 환경 변수를 통해 켬.

## 배포하기

이 레슨은 `outputs/skill-otel-genai-instrumentation.md`를 생성합니다. 에이전트 코드베이스가 주어지면 스킬이 계측 계획을 생성: 스팬을 추가할 위치, 채울 속성, 대상 익스포터.

## 실습

1. `code/main.py`를 실행하세요. 스팬을 세고 CLIENT vs INTERNAL을 식별하세요.

2. 콘텐츠 캡처 켜기(환경 변수)하고 `gen_ai.content.prompt` 및 `gen_ai.content.completion` 이벤트가 나타나는지 확인하세요. PII에 대한 영향을 기록하세요.

3. 도구 실행 메트릭 `gen_ai.tool.execution.duration`을 추가하고 호출당 히스토그램 샘플로 출력하세요.

4. 부모 에이전트 스팬에서 MCP 요청의 `_meta.traceparent` 필드로 traceparent를 전파하세요. MCP 서버가 동일한 트레이스 id를 볼 수 있는지 확인하세요.

5. OTel GenAI semconv 사양을 읽으세요. 이 레슨의 코드가 출력하지 않는 semconv에 나열된 속성을 식별하세요. 추가하세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| OTel | "OpenTelemetry" | 트레이스, 메트릭, 로그를 위한 개방형 표준 |
| GenAI semconv | "GenAI 의미론 규칙" | LLM / 도구 / 에이전트 스팬을 위한 안정적인 속성 이름 |
| `gen_ai.*` | "속성 네임스페이스" | 모든 GenAI 속성이 이 접두사 공유 |
| 스팬(Span) | "시간이 측정된 작업" | 시작, 종료 및 속성이 있는 작업 단위 |
| 트레이스(Trace) | "스팬 간 계통" | 트레이스 id를 공유하는 스팬 트리 |
| SpanKind | "CLIENT / SERVER / INTERNAL" | 스팬 방향에 대한 힌트 |
| OTLP | "OpenTelemetry Line Protocol" | 익스포터용 와이어 형식 |
| 옵트인 콘텐츠(Opt-in content) | "프롬프트/완성 캡처" | 기본적으로 꺼짐; 활성화하려면 환경 변수 |
| traceparent | "W3C 헤더" | 서비스 간 트레이스 컨텍스트 전파 |
| 익스포터(Exporter) | "백엔드 특정 전송자" | 스팬을 Jaeger / Datadog 등으로 보내는 컴포넌트 |

## 추가 자료

- [OpenTelemetry — GenAI semconv](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — GenAI 스팬, 메트릭 및 이벤트에 대한 표준 규칙
- [OpenTelemetry — GenAI spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/) — LLM 및 도구 실행 스팬 속성 목록
- [OpenTelemetry — GenAI agent spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/) — 에이전트 수준 `invoke_agent` 스팬
- [open-telemetry/semantic-conventions — GenAI spans](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-spans.md) — GitHub 호스팅 진실 공급원
- [Datadog — LLM OTel semantic convention](https://www.datadoghq.com/blog/llm-otel-semantic-convention/) — 프로덕션 통합 워크스루
