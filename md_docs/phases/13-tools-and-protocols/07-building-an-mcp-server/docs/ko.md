# MCP 서버 구축 — Python + TypeScript SDK

> 대부분의 MCP 튜토리얼은 stdio hello-world만 보여줍니다. 실제 서버는 도구와 리소스 및 프롬프트를 노출하고, 기능 협상을 처리하며, 구조화된 오류를 출력하고, SDK에 관계없이 동일하게 작동합니다. 이 레슨은 노트 서버를 종단간 구축합니다: 표준 라이브러리 stdio 전송, JSON-RPC 디스패치, 세 가지 서버 프리미티브, 그리고 Python SDK의 FastMCP나 TypeScript SDK로 전환할 때 그대로 사용할 수 있는 순수 함수 스타일.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, stdio MCP 서버)
**Prerequisites:** 13단계 06과 (MCP 기초)
**Time:** 약 75분

## 학습 목표

- `initialize`, `tools/list`, `tools/call`, `resources/list`, `resources/read`, `prompts/list`, `prompts/get` 메소드를 구현할 수 있다.
- stdin에서 JSON-RPC 메시지를 읽고 stdout에 응답을 쓰는 디스패치 루프를 작성할 수 있다.
- JSON-RPC 2.0 사양 및 MCP의 추가 코드에 따라 구조화된 오류 응답을 출력할 수 있다.
- 도구 로직을 재작성하지 않고 표준 라이브러리 구현을 FastMCP(Python SDK) 또는 TypeScript SDK로 전환할 수 있다.

## 문제

원격 전송(13단계 09과)이나 인증 계층(13단계 16과)을 사용하기 전에 깔끔한 로컬 서버가 필요합니다. 로컬은 stdio를 의미합니다: 서버가 클라이언트에 의해 자식 프로세스로 생성되고, 메시지는 stdin/stdout 개행 구분으로 흐릅니다.

2025-11-25 사양은 stdio 메시지가 명시적 `\n` 구분자가 있는 JSON 객체로 인코딩되도록 규정합니다. 여기에는 SSE가 없습니다; SSE는 이전 원격 모드였으며 2026년 중반에 제거되고 있습니다(Atlassian의 Rovo MCP 서버가 2026년 6월 30일에 폐기, Keboola가 2026년 4월 1일에 폐기). stdio의 경우 줄당 하나의 JSON 객체가 전체 와이어 형식입니다.

노트 서버는 세 가지 서버 프리미티브를 모두 사용하기 때문에 좋은 형태입니다. 도구는 변경(`notes_create`)을 수행합니다. 리소스는 데이터(`notes://{id}`)를 노출합니다. 프롬프트는 템플릿(`review_note`)을 제공합니다. 이 레슨의 형태는 모든 도메인으로 일반화됩니다.

## 개념

### 디스패치 루프

```
루프:
  line = stdin.readline()
  msg = json.loads(line)
  id 있음:
    요청 처리 -> 응답 쓰기
  없음:
    알림 처리 -> 응답 없음
```

세 가지 규칙:

- JSON-RPC 봉투가 아닌 것을 stdout에 인쇄하지 마세요. 디버그 로그는 stderr로.
- 모든 요청은 동일한 `id`를 가진 응답과 일치해야 합니다.
- 알림에는 응답해서는 안 됩니다.

### `initialize` 구현

```python
def initialize(params):
    return {
        "protocolVersion": "2025-11-25",
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {"listChanged": True, "subscribe": False},
            "prompts": {"listChanged": False},
        },
        "serverInfo": {"name": "notes", "version": "1.0.0"},
    }
```

지원하는 것만 선언하세요. 클라이언트는 기능 집합에 의존하여 기능을 게이트합니다.

### `tools/list` 및 `tools/call` 구현

`tools/list`는 각 항목에 `name`, `description`, `inputSchema`가 있는 `{tools: [...]}`를 반환합니다. `tools/call`은 `{name, arguments}`를 받고 `{content: [blocks], isError: bool}`을 반환합니다.

콘텐츠 블록은 타입화되어 있습니다. 가장 일반적인 것:

```json
{"type": "text", "text": "2개의 노트를 찾았습니다"}
{"type": "resource", "resource": {"uri": "notes://14", "text": "..."}}
{"type": "image", "data": "<base64>", "mimeType": "image/png"}
```

도구 오류는 두 가지 형태로 옵니다. 프로토콜 수준 오류(알 수 없는 메소드, 잘못된 파라미터)는 JSON-RPC 오류입니다. 도구 수준 오류(유효한 호출이지만 도구 실패)는 `{content: [...], isError: true}`로 반환됩니다. 이를 통해 모델이 컨텍스트에서 실패를 볼 수 있습니다.

### 리소스 구현

리소스는 설계상 읽기 전용입니다. `resources/list`는 매니페스트를 반환; `resources/read`는 콘텐츠를 반환합니다. URI는 `file://...`, `http://...`, 또는 `notes://`와 같은 커스텀 스킴이 될 수 있습니다.

도구 대신 리소스로 데이터를 노출할 때:

- 모델이 "호출"하지 않음; 클라이언트가 사용자 요청 시 컨텍스트에 주입 가능.
- 구독을 통해 서버가 리소스 변경 시 업데이트 푸시 가능(13단계 10과).
- 13단계 14과는 대화형 리소스를 위해 `ui://`로 확장.

### 프롬프트 구현

프롬프트는 명명된 인자가 있는 템플릿입니다. 호스트가 슬래시 명령어로 표시합니다. `review_note` 프롬프트는 `note_id` 인자를 받고 클라이언트가 모델에 공급하는 다중 메시지 프롬프트 템플릿을 생성할 수 있습니다.

### Stdio 전송 세부 사항

- 개행 구분 JSON. 길이 접두사 프레이밍 없음.
- 버퍼링하지 마세요. 각 쓰기 후 `sys.stdout.flush()`.
- 클라이언트가 수명을 제어. stdin이 닫히면(EOF) 깔끔하게 종료.
- SIGPIPE를 조용히 처리하지 말고 기록하고 종료.

### 주석

각 도구는 안전 속성을 설명하는 `annotations`를 가질 수 있습니다:

- `readOnlyHint: true` — 순수 읽기, 재시도 안전.
- `destructiveHint: true` — 되돌릴 수 없는 부수 효과; 클라이언트가 확인해야 함.
- `idempotentHint: true` — 동일 입력이 동일 출력 생성.
- `openWorldHint: true` — 외부 시스템과 상호작용.

클라이언트는 이를 사용하여 UX(확인 대화상자, 상태 표시기) 및 라우팅(13단계 17과)을 결정합니다.

### 전환 경로

`code/main.py`의 표준 라이브러리 서버는 약 180줄입니다. FastMCP(Python)는 동일한 로직을 데코레이터 스타일로 축약합니다:

```python
from fastmcp import FastMCP
app = FastMCP("notes")

@app.tool()
def notes_search(query: str, limit: int = 10) -> list[dict]:
    ...
```

TypeScript SDK도 동등한 형태를 가집니다. 전환 경로는 준비가 되면 드롭인입니다; 개념(기능, 디스패치, 콘텐츠 블록)은 동일합니다.

## 사용하기

`code/main.py`는 stdio를 통한 완전한 노트 MCP 서버로, 표준 라이브러리만 사용합니다. `initialize`, 세 가지 도구(`notes_list`, `notes_search`, `notes_create`)에 대한 `tools/list` 및 `tools/call`, 각 노트에 대한 `resources/list` 및 `resources/read`, `review_note` 프롬프트를 처리합니다. JSON-RPC 메시지를 파이핑하여 구동할 수 있습니다:

```
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python main.py
```

살펴볼 내용:

- 디스패처는 메소드 이름을 키로 하는 `dict[str, Callable]`입니다.
- 모든 도구 실행자는 문자열이 아닌 콘텐츠 블록 목록을 반환합니다.
- 실행자가 예외를 발생시키면 `isError: true`가 설정됩니다.

## 배포하기

이 레슨은 `outputs/skill-mcp-server-scaffolder.md`를 생성합니다. 도메인(노트, 티켓, 파일, 데이터베이스)이 주어지면 스킬이 올바른 도구/리소스/프롬프트 분할과 SDK 전환 경로로 MCP 서버를 스캐폴딩합니다.

## 실습

1. `code/main.py`를 실행하고 수작업 JSON-RPC 메시지로 구동하세요. `notes_create`를 실행한 다음 `resources/read`로 새 노트를 검색하세요.

2. `annotations: {destructiveHint: true}`가 있는 `notes_delete` 도구를 추가하세요. 클라이언트가 확인 대화상자를 표시할지 확인하세요(실제 호스트 필요; Claude Desktop이 작동).

3. `resources/subscribe`를 구현하여 노트가 수정될 때마다 서버가 `notifications/resources/updated`를 푸시하도록 하세요. 킵얼라이브 태스크를 추가하세요.

4. 서버를 FastMCP로 포팅하세요. Python 파일이 80줄 미만으로 줄어들어야 합니다. 와이어 동작은 동일해야 합니다; 동일한 JSON-RPC 테스트 하네스로 확인하세요.

5. 사양의 `server/tools` 섹션을 읽고 이 레슨의 서버에서 구현되지 않은 도구 정의의 필드를 식별하세요. (힌트: 여러 개가 있습니다; 하나를 선택하여 추가하세요.)

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| MCP 서버 | "도구를 노출하는 것" | stdio 또는 HTTP를 통해 MCP JSON-RPC를 말하는 프로세스 |
| stdio 전송 | "자식 프로세스 모델" | 서버가 클라이언트에 의해 생성; stdin/stdout으로 통신 |
| 디스패처 | "메소드 라우터" | JSON-RPC 메소드 이름에서 핸들러 함수로의 매핑 |
| 콘텐츠 블록(Content block) | "도구 결과 청크" | 도구 응답의 `content` 배열에 있는 타입화된 요소 |
| `isError` | "도구 수준 실패" | 도구 실패 신호; JSON-RPC 오류와 구분 |
| 주석(Annotations) | "안전 힌트" | readOnly / destructive / idempotent / openWorld 플래그 |
| FastMCP | "Python SDK" | MCP 프로토콜 위의 데코레이터 기반 고수준 프레임워크 |
| 리소스 URI | "주소 지정 가능한 데이터" | 리소스를 식별하는 `file://`, `db://` 또는 커스텀 스킴 |
| 프롬프트 템플릿 | "슬래시 명령어 요약" | 호스트 UI를 위한 인자 슬롯이 있는 서버 제공 템플릿 |
| 기능 선언 | "기능 토글" | `initialize`에서 선언된 프리미티브별 플래그 |

## 추가 자료

- [Model Context Protocol — Python SDK](https://github.com/modelcontextprotocol/python-sdk) — 참조 Python 구현
- [Model Context Protocol — TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) — 병렬 TS 구현
- [FastMCP — server framework](https://gofastmcp.com/) — MCP 서버용 데코레이터 스타일 Python API
- [MCP — Quickstart server guide](https://modelcontextprotocol.io/quickstart/server) — SDK를 사용한 종단간 튜토리얼
- [MCP — Server tools spec](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) — tools/* 메시지 전체 참조
