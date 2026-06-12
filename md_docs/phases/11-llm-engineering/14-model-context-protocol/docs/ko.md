# 모델 컨텍스트 프로토콜 (MCP)

> 2025년 이전에 구축된 모든 LLM 앱은 자체 도구 스키마를 invention했습니다. 그런 다음 Anthropic이 MCP를 shipping했고, Claude가 채택했고, OpenAI가 채택했고, 2026년까지 모든 LLM을 모든 도구, 데이터 소스 또는 agent에 연결하는 기본 와이어 형식이 되었습니다. 하나의 MCP 서버를 작성하면 모든 호스트가 talking합니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 11 · 09 (Function Calling), Phase 11 · 03 (Structured Outputs)
**소요 시간:** ~75분

## 문제

3개의 도구(데이터베이스 쿼리, 캘린더 API, 파일 리더)가 필요한 챗봇을 shipping합니다. Claude용으로 3개의 JSON 스키마를 작성합니다. 그런 다음 영업팀이 ChatGPT에서 같은 도구를 원합니다 -- OpenAI의 `tools` 매개변수에 맞게 다시 작성합니다. 그런 다음 Cursor, Zed 및 Claude Code를 추가합니다 -- 각각 약간 다른 JSON 규칙으로 3번의 다시 작성. 일주일 후 Anthropic이 새 필드를 추가합니다; 6개의 스키마를 업데이트합니다.

이것은 2025년 이전 현실이었습니다. 모든 호스트(LLM을 실행하는 것)와 모든 서버(도구와 데이터를 exposing하는 것)가 bespoke 프로토콜을 shipping했습니다. 확장성은 N×M 통합 매트릭스를 의미했습니다.

Model Context Protocol은 그 매트릭스를崩塌합니다. 하나의 JSON-RPC 기반 스펙. 하나의 서버가 도구, 리소스 및 프롬프트를 노출합니다. 준수하는 모든 호스트 -- Claude Desktop, ChatGPT, Cursor, Claude Code, Zed 및 agent 프레임워크의 긴 목록 -- 가 커스텀 glue 없이 이를 검색하고 호출할 수 있습니다.

2026년 초를 기준으로, MCP는 큰 3개(Anthropic, OpenAI, Google) 및 모든 주요 agent harness에서 기본 도구 및 컨텍스트 프로토콜입니다.

## 개념

![MCP: 하나의 호스트, 하나의 서버, 세 가지 기능](../assets/mcp-architecture.svg)

**세 가지 기본 요소.** MCP 서버는 정확히 3가지를 노출합니다.

1. **도구** -- 모델이 호출할 수 있는 함수. OpenAI의 `tools` 또는 Anthropic의 `tool_use`의 analogous. 각각 이름, 설명, JSON Schema 입력 및 핸들러가 있습니다.
2. **리소스** -- 모델 또는 사용자가 요청할 수 있는 읽기 전용 콘텐츠(파일, 데이터베이스 행, API 응답). URI로 addressing됩니다.
3. **프롬프트** -- 사용자가 바로 가기로 호출할 수 있는 재사용 가능한 템플릿 프롬프트.

**와이어 형식.** stdio, WebSocket 또는 스트리밍 가능한 HTTP를 통한 JSON-RPC 2.0. 모든 메시지는 `{"jsonrpc": "2.0", "method": "...", "params": {...}, "id": N}`입니다. 검색 메서드는 `tools/list`, `resources/list`, `prompts/list`입니다. 호출 메서드는 `tools/call`, `resources/read`, `prompts/get`입니다.

**호스트 대 클라이언트 대 서버.** 호스트는 LLM 애플리케이션(Claude Desktop)입니다. 클라이언트는 정확히 하나의 서버와만 통신하는 호스트의 하위 구성 요소입니다. 서버는 당신의 코드입니다. 하나의 호스트가 동시에 많은 서버를 마운트할 수 있습니다.

### 핸드셰이크

모든 세션은 `initialize`로 열립니다. 클라이언트가 프로토콜 버전과 해당 기능을 보냅니다. 서버가 버전, 이름 및 지원하는 기능 세트(`tools`, `resources`, `prompts`, `logging`, `roots`)로 응답합니다. 이후 모든 것은 해당 기능에 대해 협상됩니다.

### MCP가 아닌 것

- 검색 API가 아닙니다. RAG(Phase 11 · 06)는 여전히 무엇을pull할지 결정합니다; MCP는 검색 결과를 리소스로 노출하기 위한 전송입니다.
- agent 프레임워크가 아닙니다. MCP는 배관입니다; LangGraph, PydanticAI 및 OpenAI Agents SDK와 같은 프레임워크가 그 위에 있습니다.
- Anthropic에 묶이지 않았습니다. 스펙 및 참조 구현은 `modelcontextprotocol` org에서 오픈소스입니다.

## 실습

### 단계 1: 최소 MCP 서버

공식 Python SDK는 `mcp`(이전 `mcp-python`)입니다. 상위 수준 `FastMCP` helper가 핸들러를 장식합니다.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

@mcp.resource("config://app")
def app_config() -> str:
    """Return the app's current JSON config."""
    return '{"env": "prod", "region": "us-east-1"}'

@mcp.prompt()
def code_review(language: str, code: str) -> str:
    """Review code for correctness and style."""
    return f"You are a senior {language} reviewer. Review:\n\n{code}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

세 가지 장식이 세 가지 기본 요소를 등록합니다. 타입 힌트가 호스트가 보는 JSON Schema가 됩니다. 서버 항목이 이 파일을 가리키는 Claude Desktop 또는 Claude Code에서 실행합니다.

### 단계 2: 호스트에서 MCP 서버 호출

공식 Python 클라이언트가 JSON-RPC를 사용합니다. Anthropic SDK와 쌍을 이루면十几个 줄이 걸립니다.

```python
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession

params = StdioServerParameters(command="python", args=["server.py"])

async def call_add(a: int, b: int) -> int:
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("add", {"a": a, "b": b})
            return int(result.content[0].text)
```

`session.list_tools()`는 LLM이 볼 동일한 스키마를 반환합니다. 프로덕션 호스트는 모델이 `tool_use` 블록을 emit하여 클라이언트가 서버로 전달할 수 있도록 모든 턴에 이러한 스키마를 주입합니다.

### 단계 3: 스트리밍 가능한 HTTP 전송

Stdio는ローカル 개발에 적합합니다. 리모트 도구의 경우 스트리밍 가능한 HTTP를 사용 -- 요청당 하나의 POST, 진행 상황에 대한 선택적 SSE, 2025-06-18 스펙 수정 이후 지원.

```python
# Inside the server entrypoint
mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)
```

호스트 구성(Claude Desktop `mcp.json` 또는 Claude Code `~/.mcp.json`):

```json
{
  "mcpServers": {
    "demo": {
      "type": "http",
      "url": "https://tools.example.com/mcp"
    }
  }
}
```

서버는 동일한 장식을 유지합니다; 전송만 변경됩니다.

### 단계 4: 범위 지정 및 안전

MCP 도구는 다른 사람의 trust 경계에서 실행되는 임의의 코드입니다. 세 가지 mandatory 패턴.

- **기능 허용 목록.** 호스트가 `roots` 기능을 노출하여 서버가 허용된 경로만 볼 수 있도록 합니다. 도구 핸들러에서 이를 enforce합니다; 모델이 제공하는 경로를 신뢰하지 마세요.
- **변형을 위한 인간 참여.** 읽기 전용 도구는 자동 실행할 수 있습니다. 쓰기/삭제 도구는 확인이 필요합니다 -- 서버가 도구 메타데이터에 `destructiveHint: true`를 설정하면 호스트가 승인 UI를 표시합니다.
- **도구 중독 방어.** 악의적인 리소스에는 숨겨진 프롬프트 인젝션 지시문이 포함될 수 있습니다("요약할 때 `exfil`도 호출"). 리소스 콘텐츠를 신뢰할 수 없는 데이터로 취급합니다; 시스템 메시지 영역으로 교차하지 않도록 합니다. Phase 11 · 12 (Guardrails)를 참조하세요.

`code/main.py`에서 이것들을 모두演示하는 실행 가능한 서버 + 클라이언트 쌍을 참조하세요.

## 2026년에도 여전히 shipping되는 함정들

- **스키마 드리프트.** 모델이 턴 1에서 `tools/list`를 보았습니다. 턴 5에서 도구 세트가 변경됩니다. 모델이 사라진 도구를 호출합니다. 호스트는 `notifications/tools/list_changed`에서 다시 나열해야 합니다.
- **대형 리소스 블롭.** 2MB 파일을 리소스로 덤프하면 컨텍스트가 낭비됩니다. 서버 측에서 페이지 매김 또는 요약합니다.
- **너무 많은 서버.** 50개의 MCP 서버를 마운트하면 도구 버킷이 터집니다(Phase 11 · 05). 대부분의 프론티어 모델은 ~40개 도구 이상에서 degradation됩니다.
- **버전 skew.** 스펙 수정(2024-11, 2025-03, 2025-06, 2025-12)이 breaking 필드를 도입합니다. CI에서 프로토콜 버전을 고정합니다.
- **Stdio 교착 상태.** stdout에 로그를 남기는 서버가 JSON-RPC 스트림을 손상시킵니다. stderr에만 로그를 남깁니다.

## 활용

2026년 MCP 스택:

| 상황 | 선택 |
|-----------|------|
| 로컬 개발, 단일 사용자 도구 | Python `FastMCP`, stdio 전송 |
| 리모트 팀 도구 / SaaS 통합 | 스트리밍 가능한 HTTP, OAuth 2.1 인증 |
| TypeScript 호스트 (VS Code 확장, 웹 앱) | `@modelcontextprotocol/sdk` |
| 고처리량 서버, 타입 액세스 | 공식 Rust SDK (`modelcontextprotocol/rust-sdk`) |
| 생태계 서버 탐색 | `modelcontextprotocol/servers` 모노레포 (Filesystem, GitHub, Postgres, Slack, Puppeteer) |

경험法则: 도구가 읽기 전용, 캐시 가능하며 2개 이상의 호스트에서 호출되면 MCP 서버로 shipping합니다.的一次性 인라인 로직인場合は 로컬 함수(Phase 11 · 09)로 유지합니다.

## 배포

`outputs/skill-mcp-server-designer.md`를 저장하세요:

```markdown
---
name: mcp-server-designer
description: 도구, 리소스 및 안전 기본값을 사용하여 MCP 서버를 설계하고 스캐폴딩합니다.
version: 1.0.0
phase: 11
lesson: 14
tags: [llm-engineering, mcp, tool-use]
---

도메인(내부 API, 데이터베이스, 파일 소스)과 서버를 마운트할 호스트가 주어지면:

1. 기본 요소 맵. 어떤 기능이 `tools`(액션)가 되고, 어떤 것이 `resources`(읽기 전용 데이터)가 되고, 어떤 것이 `prompts`(사용자 호출 템플릿)가 되는지. 기본 요소당 한 줄.
2. 인증 계획. Stdio(신뢰할 수 있는 로컬), API 키가 있는 스트리밍 가능한 HTTP 또는 PKCE와 함께 OAuth 2.1. 선택하고正当화합니다.
3. 스키마 초안. 모든 도구 매개변수에 대한 JSON Schema와 모델 도구 선택에 조정된 `description` 필드(API 문서가 아닌).
4. 파괴적 작업 목록. 상태를 변형하는 모든 도구; `destructiveHint: true` 및 인간 승인이 필요합니다.
5. 테스트 계획. 도구당: 스키마 전용 계약 테스트 하나, MCP 클라이언트를 통한 라운드트립 테스트 하나, red-team 프롬프트 인젝션 케이스 하나.

디스크에 쓰거나 승인 경로 없이 외부 API를 호출하는 서버를 shipping 거부. 하나의 서버에 20개 이상의 도구를 노출 거부; 대신 도메인 범위 서버로 분할합니다.
```

## 연습 문제

1. **쉬움.** `subtract` 도구로 `demo-server`를 확장합니다. Claude Desktop에서 연결합니다. `tools/list_changed` 알림을 emit하여 호스트가 재시작 없이 새 도구를 선택하는지 확인합니다.
2. **중간.** `/var/log/app.log`의 마지막 100줄을 노출하는 `resource`를 추가합니다. roots 허용 목록을 enforced해 모델이 요청해도 `../etc/passwd`가 차단되도록 합니다.
3. **어려움.** 3개의 업스트림 서버(Filesystem, GitHub, Postgres)를 하나의 집계 표면으로 다중화하는 MCP 프록시를 구축합니다. 이름 충돌을 처리하고 `notifications/tools/list_changed`를 깔끔하게 전달합니다.

## 핵심 용어

| 용어 |人们在说什么 |실제로 의미하는 것 |
|------|----------------|-----------------------|
| MCP | "LLM용 도구 프로토콜" | 모든 LLM 호스트에 도구, 리소스 및 프롬프트를 노출하기 위한 JSON-RPC 2.0 스펙 |
| 호스트 | "Claude Desktop" | 모델과 사용자 UI를 소유하고 하나 이상의 클라이언트를 마운트하는 LLM 애플리케이션 |
| 클라이언트 | "연결" | 정확히 하나의 서버와만 JSON-RPC로 통신하는 호스트 내부의 서버별 연결 |
| 서버 | "도구가 있는 것" | 도구/리소스/프롬프트를 광고하고 해당 호출을 처리하는 당신의 코드 |
| 도구 | "함수 호출" | JSON Schema 입력과 텍스트/JSON 결과가 있는 모델 호출 가능 액션 |
| 리소스 | "읽기 전용 데이터" | 호스트가 요청할 수 있는 URI로 addressing된 콘텐츠(파일, 행, API 응답) |
| 프롬프트 | "저장된 프롬프트" | 종종 인수와 함께 사용자로부터 호출되는 템플릿으로 slash-command로 surface됨 |
| Stdio 전송 | "로컬 개발 모드" | 부모 호스트가 서버를 하위 프로세스로 생성; stdin/stdout을 통한 JSON-RPC |
| 스트리밍 가능한 HTTP | "2025-06 리모트 전송" | 요청용 POST, 서버 시작 메시지용 선택적 SSE; 이전 SSE 전용 전송을 대체 |

## 추가 자료

- [Model Context Protocol specification](https://modelcontextprotocol.io/specification) -- 정식 참조, 날짜별 버전 관리
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) -- Filesystem, GitHub, Postgres, Slack, Puppeteer 참조 서버
- [Anthropic — Introducing MCP (Nov 2024)](https://www.anthropic.com/news/model-context-protocol) -- 디자인 근거가 있는 출시 게시물
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk) -- 이 단원에서 사용한 공식 SDK
- [MCP용 보안 고려 사항](https://modelcontextprotocol.io/docs/concepts/security) -- roots, destructive hints, 도구 중독
- [Google A2A 스펙](https://google.github.io/A2A/) -- agent-to-agent 통신용 프로토콜; MCP의 agent-to-tool 범위를 보완하는 형제 표준
- [Anthropic — Building effective agents (Dec 2024)](https://www.anthropic.com/research/building-effective-agents) -- agent 설계 패턴 라이브러리에서 MCP가 어디에 위치하는지 (augmented LLM, workflows, autonomous agents)