# MCP 기초 — 프리미티브, 라이프사이클, JSON-RPC 기반

> MCP 이전의 모든 통합은 일회성이었습니다. 2024년 11월 Anthropic이 처음 출시하고 현재 Linux Foundation의 Agentic AI Foundation이 관리하는 Model Context Protocol은 검색과 호출을 표준화하여 모든 클라이언트가 모든 서버와 통신할 수 있게 합니다. 2025-11-25 사양은 여섯 가지 프리미티브(서버 3개, 클라이언트 3개), 삼단계 라이프사이클, JSON-RPC 2.0 와이어 형식을 명명합니다. 이것들을 배우면 이 단계의 MCP 챕터 나머지는 읽기만 하면 됩니다.

**Type:** 학습
**Languages:** Python (표준 라이브러리, JSON-RPC 파서)
**Prerequisites:** 13단계 01과~05과 (도구 인터페이스 및 함수 호출)
**Time:** 약 45분

## 학습 목표

- 여섯 가지 MCP 프리미티브(서버의 tools, resources, prompts; 클라이언트의 roots, sampling, elicitation)를 모두 명명하고 각각에 대해 하나의 사용 사례를 말할 수 있다.
- 삼단계 라이프사이클(초기화, 운영, 종료)을 설명하고 각 단계에서 누가 어떤 메시지를 보내는지 말할 수 있다.
- JSON-RPC 2.0 요청, 응답 및 알림 봉투를 파싱하고 생성할 수 있다.
- `initialize`에서 기능 협상이 무엇인지, 그것 없이 무엇이 깨지는지 설명할 수 있다.

## 문제

MCP 이전에는 모든 도구 사용 에이전트가 자체 프로토콜을 가지고 있었습니다. Cursor는 MCP 형태와 호환되지 않는 도구 시스템이 있었습니다. Claude Desktop은 다른 것을 탑재했습니다. VS Code의 Copilot 확장은 세 번째 것을 사용했습니다. "Postgres 쿼리" 도구를 구축한 팀은 동일한 도구를 각각 다른 호스트의 API에 맞춰 세 번 작성했습니다. 재사용하려면 코드를 복사해야 했습니다.

그 결과는 일회성 통합의 캄브리아기 대폭발과 생태계 속도의 한계였습니다.

MCP는 와이어 형식을 표준화하여 이를 수정합니다. 단일 MCP 서버가 모든 MCP 클라이언트에서 작동합니다: Claude Desktop, ChatGPT, Cursor, VS Code, Gemini, Goose, Zed, Windsurf, 2026년 4월 기준 300개 이상의 클라이언트. 월 1억 1천만 SDK 다운로드. 10,000개 이상의 공개 서버. Linux Foundation은 2025년 12월 새로운 Agentic AI Foundation 산하에서 관리를 인수했습니다.

이 단계에서 사용하는 사양 개정판은 **2025-11-25**입니다. 여기에는 비동기 Tasks(SEP-1686), URL 모드 elicitation(SEP-1036), 도구가 있는 sampling(SEP-1577), 증분 범위 동의(SEP-835), OAuth 2.1 리소스 표시기 의미론이 추가됩니다. 13단계 09과~16과가 이러한 확장을 다룹니다. 이 레슨은 기초에서 멈춥니다.

## 개념

### 세 가지 서버 프리미티브

1. **도구(Tools).** 호출 가능한 액션. 13단계 01과의 동일한 4단계 루프.
2. **리소스(Resources).** 노출된 데이터. URI로 주소 지정 가능한 읽기 전용 콘텐츠: `file:///path`, `db://query/...`, 커스텀 스킴.
3. **프롬프트(Prompts).** 재사용 가능한 템플릿. 호스트 UI의 슬래시 명령어; 서버가 템플릿 제공, 클라이언트가 인자 채움.

### 세 가지 클라이언트 프리미티브

4. **루트(Roots).** 서버가 접근할 수 있는 URI 집합. 클라이언트가 선언; 서버가 존중.
5. **샘플링(Sampling).** 서버가 클라이언트의 모델에 완성을 요청. 서버 측 API 키 없이 서버 호스팅 에이전트 루프 활성화.
6. **엘리시테이션(Elicitation).** 서버가 실행 중에 클라이언트의 사용자에게 구조화된 입력을 요청. 양식 또는 URL(SEP-1036).

MCP의 모든 기능은 정확히 이 여섯 가지 중 하나에 속합니다. 13단계 10과~14과가 각각을 깊이 다룹니다.

### 와이어 형식: JSON-RPC 2.0

모든 메시지는 다음 필드가 있는 JSON 객체입니다:

- 요청: `{jsonrpc: "2.0", id, method, params}`.
- 응답: `{jsonrpc: "2.0", id, result | error}`.
- 알림: `{jsonrpc: "2.0", method, params}` — `id` 없음, 응답 예상 없음.

기본 사양에는 프리미티브별로 그룹화된 약 15개의 메소드가 있습니다. 중요한 것:

- `initialize` / `initialized` (핸드셰이크)
- `tools/list`, `tools/call`
- `resources/list`, `resources/read`, `resources/subscribe`
- `prompts/list`, `prompts/get`
- `sampling/createMessage` (서버-클라이언트)
- `notifications/tools/list_changed`, `notifications/resources/updated`, `notifications/progress`

### 삼단계 라이프사이클

**1단계: 초기화.**

클라이언트가 `capabilities`와 `clientInfo`와 함께 `initialize`를 전송. 서버가 자체 `capabilities`, `serverInfo` 및 지원하는 사양 버전으로 응답. 클라이언트가 응답을 소화한 후 `notifications/initialized`를 전송. 이후부터는 협상된 기능에 따라 양쪽이 요청을 보낼 수 있음.

**2단계: 운영.**

양방향. 클라이언트가 `tools/list`를 호출하여 검색, 그런 다음 `tools/call`을 호출하여 실행. 서버는 해당 기능을 선언한 경우 `sampling/createMessage`를 보낼 수 있음. 서버는 도구 집합이 변경될 때 `notifications/tools/list_changed`를 보낼 수 있음. 클라이언트는 사용자가 루트 범위를 변경할 때 `notifications/roots/list_changed`를 보낼 수 있음.

**3단계: 종료.**

양쪽이 전송을 닫음. MCP에는 구조화된 종료 메소드가 없음; 전송(stdio 또는 Streamable HTTP, 13단계 09과)이 연결 종료 신호를 전달함.

### 기능 협상

`initialize` 핸드셰이크의 `capabilities`가 계약입니다. 서버의 예:

```json
{
  "tools": {"listChanged": true},
  "resources": {"subscribe": true, "listChanged": true},
  "prompts": {"listChanged": true}
}
```

서버가 `tools/list_changed` 알림을 보낼 수 있고 `resources/subscribe`를 지원한다고 선언합니다. 클라이언트가 자체를 선언하여 동의:

```json
{
  "roots": {"listChanged": true},
  "sampling": {},
  "elicitation": {}
}
```

클라이언트가 `sampling`을 선언하지 않으면 서버는 `sampling/createMessage`를 호출하지 않아야 합니다. 대칭적으로: 서버가 `resources.subscribe`를 선언하지 않으면 클라이언트는 구독을 시도하지 않아야 합니다.

이것이 생태계 표류를 방지하는 것입니다. 샘플링을 지원하지 않는 클라이언트도 유효한 MCP 클라이언트입니다; `sampling`을 호출하지 않는 서버도 유효한 MCP 서버입니다. 함께 해당 기능을 사용하지 않을 뿐입니다.

### 구조화된 콘텐츠 및 오류 형태

`tools/call`은 타입화된 블록(`text`, `image`, `resource`)의 `content` 배열을 반환합니다. 13단계 14과는 MCP Apps(`ui://` 대화형 UI)를 이 목록에 추가합니다.

오류는 JSON-RPC 오류 코드를 사용합니다. 사양 정의 추가 사항: `-32002` "Resource not found", `-32603` "Internal error", MCP 특정 오류 데이터는 `error.data`로.

### 클라이언트 기능 vs 도구 호출 세부 사항

흔한 혼동: `capabilities.tools`는 클라이언트가 도구 목록 변경 알림을 지원하는지 여부입니다. 클라이언트가 특정 도구를 호출할지 여부는 모델이 주도하는 런타임 선택이며, 기능 플래그가 아닙니다. 기능 플래그는 사양 수준 계약입니다. 모델의 선택은 직교적입니다.

### 왜 JSON-RPC이고 REST가 아닌가?

JSON-RPC 2.0(2010)은 가벼운 양방향 프로토콜입니다. REST는 클라이언트 주도입니다. MCP에는 서버 주도 메시지(sampling, 알림)가 필요했으므로 대칭적 요청/응답 형태의 JSON-RPC가 자연스러운 선택이었습니다. JSON-RPC는 또한 stdio 및 WebSocket/Streamable HTTP 위에서 HTTP의 요청 형태를 재발명하지 않고 깔끔하게 구성됩니다.

## 사용하기

`code/main.py`는 최소 JSON-RPC 2.0 파서와 생성기를 제공한 다음 `initialize` → `tools/list` → `tools/call` → `shutdown` 시퀀스를 수동으로 실행하며 모든 메시지를 출력합니다. 실제 전송 없음; 메시지 형태만 있습니다. 추가 자료에 링크된 사양과 비교하여 각 봉투를 확인하세요.

살펴볼 내용:

- `initialize`는 양방향으로 기능을 선언; 응답에는 `serverInfo`와 `protocolVersion: "2025-11-25"`가 있음.
- `tools/list`는 `tools` 배열 반환; 각 항목에는 `name`, `description`, `inputSchema`가 있음.
- `tools/call`은 `params.name`과 `params.arguments`를 사용.
- 응답 `content`는 `{type, text}` 블록의 배열.

## 배포하기

이 레슨은 `outputs/skill-mcp-handshake-tracer.md`를 생성합니다. MCP 클라이언트-서버 상호작용의 pcap 스타일 기록이 주어지면 스킬이 각 메시지에 어떤 프리미티브, 어떤 라이프사이클 단계, 어떤 기능에 의존하는지 주석을 답니다.

## 실습

1. `code/main.py`를 실행하세요. 기능 협상이 발생하는 줄을 식별하고 서버가 `tools.listChanged`를 선언하지 않으면 무엇이 바뀔지 설명하세요.

2. 파서를 확장하여 `notifications/progress`를 처리하세요. 메시지 형태: `{method: "notifications/progress", params: {progressToken, progress, total}}`. 장기 실행 `tools/call`이 진행 중일 때 이를 출력하고 클라이언트 핸들러가 진행률 표시줄을 표시할지 확인하세요.

3. MCP 2025-11-25 사양을 처음부터 끝까지 읽으세요 — 전체 문서는 약 80페이지입니다. 대부분의 서버가 필요로 하지 않는 기능 플래그를 식별하세요. 힌트: 리소스 구독과 관련됩니다.

4. 가상의 "cron 작업" 기능이 속할 프리미티브를 종이에 스케치하세요. (힌트: 서버가 예약된 시간에 클라이언트가 호출하도록 하려고 합니다. 오늘날 여섯 가지 프리미티브 중 어느 것도 맞지 않습니다.) MCP의 2026 로드맵에는 이에 대한 초안 SEP가 있습니다.

5. GitHub의 공개 MCP 서버에서 하나의 세션 로그를 파싱하세요. 요청 대 응답 대 알림 메시지 수를 세세요. 트래픽 중 라이프사이클 대 운영의 비율을 계산하세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| MCP | "Model Context Protocol" | 모델-도구 검색 및 호출을 위한 개방형 프로토콜 |
| 서버 프리미티브(Server primitive) | "서버가 노출하는 것" | 도구(액션), 리소스(데이터), 프롬프트(템플릿) |
| 클라이언트 프리미티브(Client primitive) | "클라이언트가 서버에 제공하는 것" | 루트(범위), 샘플링(LLM 콜백), 엘리시테이션(사용자 입력) |
| JSON-RPC 2.0 | "와이어 형식" | 대칭적 요청/응답/알림 봉투 |
| `initialize` 핸드셰이크 | "기능 협상" | 첫 번째 메시지 쌍; 서버와 클라이언트가 지원 기능 선언 |
| `tools/list` | "검색" | 클라이언트가 서버에 현재 도구 집합 요청 |
| `tools/call` | "호출" | 클라이언트가 서버에 인자로 도구 실행 요청 |
| `notifications/*_changed` | "변경 이벤트" | 서버가 프리미티브 목록이 변경되었음을 클라이언트에 알림 |
| 콘텐츠 블록(Content block) | "타입화된 결과" | 도구 결과의 `{type: "text" | "image" | "resource" | "ui_resource"}` |
| SEP | "사양 진화 제안" | 명명된 초안 제안(예: 비동기 Tasks용 SEP-1686) |

## 추가 자료

- [Model Context Protocol — Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — 표준 사양 문서
- [Model Context Protocol — Architecture concepts](https://modelcontextprotocol.io/docs/concepts/architecture) — 여섯 프리미티브 개념 모델
- [Anthropic — Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) — 2024년 11월 출시 포스트
- [MCP blog — First MCP anniversary](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/) — 1주년 회고 및 2025-11-25 사양 변경 사항
- [WorkOS — MCP 2025-11-25 spec update](https://workos.com/blog/mcp-2025-11-25-spec-update) — SEP-1686, 1036, 1577, 835, 1724 요약
