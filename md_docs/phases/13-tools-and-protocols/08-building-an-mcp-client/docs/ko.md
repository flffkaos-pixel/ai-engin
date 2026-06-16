# MCP 클라이언트 구축 — 검색, 호출, 세션 관리

> 대부분의 MCP 콘텐츠는 서버 튜토리얼을 제공하고 클라이언트는 대충 넘깁니다. 클라이언트 코드는 어려운 오케스트레이션이 있는 곳입니다: 프로세스 생성, 기능 협상, 여러 서버에 걸친 도구 목록 병합, 샘플링 콜백, 재연결, 네임스페이스 충돌 해결. 이 레슨은 세 개의 다른 MCP 서버를 모델을 위한 하나의 평면 도구 네임스페이스로 끌어올리는 다중 서버 클라이언트를 구축합니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, 다중 서버 MCP 클라이언트)
**Prerequisites:** 13단계 07과 (MCP 서버 구축)
**Time:** 약 75분

## 학습 목표

- MCP 서버를 자식 프로세스로 생성하고 `initialize`를 완료하며 `notifications/initialized`를 보낼 수 있다.
- 서버별 세션 상태(기능, 도구 목록, 마지막으로 본 알림 ID)를 유지할 수 있다.
- 여러 서버의 도구 목록을 충돌 처리와 함께 하나의 네임스페이스로 병합할 수 있다.
- 도구 호출을 소유한 서버로 라우팅하고 응답을 재조립할 수 있다.

## 문제

실제 에이전트 호스트(Claude Desktop, Cursor, Goose, Gemini CLI)는 한 번에 여러 MCP 서버를 로드합니다. 사용자는 파일시스템 서버, Postgres 서버, GitHub 서버를 동시에 실행할 수 있습니다. 클라이언트의 작업:

1. 각 서버 생성.
2. 각각 독립적으로 핸드셰이크.
3. 각각에서 `tools/list`를 호출하고 결과를 평탄화.
4. 모델이 `notes_search`를 출력하면 병합된 네임스페이스에서 조회하여 올바른 서버로 라운팅.
5. 차단 없이 모든 서버의 알림(`tools/list_changed`) 처리.
6. 전송 실패 시 재연결.

이 모든 것을 수작업으로 하는 것이 "장난감"과 "서비스 가능"을 구분하는 것입니다. 공식 SDK가 이를 래핑하지만 개념 모델은 여러분의 것이어야 합니다.

## 개념

### 자식 프로세스 생성

`subprocess.Popen` with `stdin=PIPE, stdout=PIPE, stderr=PIPE`. `bufsize=1` 설정하고 줄별 읽기를 위해 텍스트 모드 사용. 각 서버는 하나의 프로세스; 클라이언트는 서버당 하나의 `Popen` 핸들을 보유.

### 서버별 세션 상태

서버당 `Session` 객체가 보유:

- `process` — Popen 핸들.
- `capabilities` — 서버가 `initialize`에서 선언한 것.
- `tools` — 마지막 `tools/list` 결과.
- `pending` — 요청 ID를 응답을 기다리는 약속/퓨처에 매핑.

요청은 본질적으로 비동기입니다; 서버 A에 보낸 `tools/call`이 서버 B가 호출 중일 때 차단되어서는 안 됩니다. 스레드와 큐 또는 asyncio를 사용하세요.

### 병합된 네임스페이스

클라이언트가 전체 도구 목록을 볼 때 이름이 충돌할 수 있습니다. 두 서버가 모두 `search`를 노출할 수 있습니다. 클라이언트에는 세 가지 옵션이 있습니다:

1. **서버 이름으로 접두사.** `notes/search`, `files/search`. 명확하지만 보기 흉함.
2. **조용히 먼저 온 것 우선.** 나중 서버의 `search`가 이전 것을 재정의. 위험; 충돌 숨김.
3. **충돌 거부.** 두 번째 서버 로드 거부; 사용자에게 알림. 보안에 민감한 호스트에 가장 안전.

Claude Desktop은 서버별 접두사를 사용합니다. Cursor는 명확한 오류와 함께 충돌 거부를 사용합니다. VS Code MCP도 서버별 접두사를 채택합니다.

### 라우팅

병합 후 디스패치 테이블이 `tool_name -> session`을 매핑합니다. 모델이 이름으로 호출을 출력; 클라이언트가 세션을 찾고 해당 서버의 stdin에 `tools/call` 메시지를 쓴 후 응답을 기다립니다.

### 샘플링 콜백

서버가 `initialize`에서 `sampling` 기능을 선언한 경우 `sampling/createMessage`를 보내 클라이언트에게 LLM을 실행하도록 요청할 수 있습니다. 클라이언트는:

1. 샘플이 해결될 때까지 해당 서버에 대한 추가 요청 차단, 또는 동시성을 지원하는 경우 파이프라인 처리.
2. 자체 LLM 제공자 호출.
3. 응답을 서버로 다시 전송.

11과는 샘플링을 종단간 다룹니다. 이 레슨은 완전성을 위해 스텁으로 처리합니다.

### 알림 처리

`notifications/tools/list_changed`는 `tools/list` 재호출을 의미합니다. `notifications/resources/updated`는 사용 중인 리소스를 다시 읽는 것을 의미합니다. 알림은 응답을 생성해서는 안 됩니다 — 확인하려고 하지 마세요.

흔한 클라이언트 버그: 스트림에 알림이 있는 동안 `tools/call`에서 읽기 루프를 차단하는 것. 모든 메시지를 큐에 푸시하는 백그라운드 리더 스레드를 사용하세요; 메인 스레드가 큐에서 꺼내 디스패치합니다.

### 재연결

전송이 실패할 수 있습니다: 서버 충돌, OS가 프로세스 종료, stdio 파이프 끊김. 클라이언트는 stdout에서 EOF를 감지하고 세션을 죽은 것으로 처리합니다. 옵션:

- 서버를 조용히 재시작하고 재핸드셰이크. 순수 읽기 전용 서버에 적합.
- 사용자에게 실패 표시. 상태 저장 서버 및 사용자에게 보이는 세션에 적합.

13단계 09과는 Streamable HTTP 재연결 의미론을 다룹니다; stdio는 더 간단합니다.

### 킵얼라이브 및 세션 ID

Streamable HTTP는 `Mcp-Session-Id` 헤더를 사용합니다. Stdio에는 세션 ID가 없습니다 — 프로세스 자체가 세션입니다. 킵얼라이브 핑은 선택 사항; stdio 파이프는 비활성 상태에서 끊어지지 않습니다.

## 사용하기

`code/main.py`는 세 개의 시뮬레이션된 MCP 서버를 하위 프로세스로 생성하고, 각각과 핸드셰이크하고, 도구 목록을 병합하고, 도구 호출을 올바른 서버로 라우팅합니다. "서버"는 실제로 장난감 응답기를 실행하는 다른 Python 프로세스입니다(실제 LLM 없음). 실행하여 확인:

- 각각 고유한 기능 집합이 있는 세 개의 초기화.
- 7개 도구 네임스페이스로 병합된 세 개의 `tools/list` 결과.
- 도구 이름에 기반한 라우팅 결정.
- 네임스페이스 접두사로 방지된 충돌.

살펴볼 내용:

- `Session` 데이터클래스가 서버별 상태를 깔끔하게 보유.
- 백그라운드 리더 스레드가 메인 스레드를 차단하지 않고 stdout의 모든 줄을 큐에서 제거.
- 디스패치 테이블은 단순한 `dict[str, Session]`.
- 충돌 처리가 명시적: 두 서버가 동일한 이름을 선언하면 나중 서버가 접두사로 이름이 변경됨.

## 배포하기

이 레슨은 `outputs/skill-mcp-client-harness.md`를 생성합니다. MCP 서버의 선언적 목록(이름, 명령어, 인자)이 주어지면 스킬이 이를 생성하고, 도구 목록을 병합하고, 충돌 해결이 있는 라우팅 함수를 제공하는 하네스를 생성합니다.

## 실습

1. `code/main.py`를 실행하고 서버 생성 로그를 관찰하세요. 시뮬레이션된 서버 프로세스 중 하나를 SIGTERM으로 종료하고 클라이언트가 EOF를 감지하고 해당 세션을 죽은 것으로 표시하는 방식을 관찰하세요.

2. 네임스페이스 접두사를 구현하세요. 두 서버가 `search`를 노출하면 두 번째 것을 `<server>/search`로 이름을 바꾸세요. 디스패치 테이블을 업데이트하고 도구 호출이 올바르게 라우팅되는지 확인하세요.

3. 서버 재시작을 위한 연결 풀 스타일 백오프를 추가하세요: 연속 실패에 기하급수적 백오프, 30초 상한, 3회 실패 후 사용자에게 알림.

4. 100개의 동시 MCP 서버를 지원하는 클라이언트를 스케치하세요. 어떤 데이터 구조가 단순 디스패치 사전을 대체하나요? (힌트: 접두사 네임스페이싱을 위한 트라이, 서버당 도구 수를 위한 메트릭.)

5. 클라이언트를 공식 MCP Python SDK로 포팅하세요. SDK는 `stdio_client`와 `ClientSession`을 래핑합니다. 코드가 약 200줄에서 약 40줄로 줄어들면서 다중 서버 라우팅을 유지해야 합니다.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| MCP 클라이언트 | "에이전트 호스트" | 서버를 생성하고 도구 호출을 오케스트레이션하는 프로세스 |
| 세션(Session) | "서버별 상태" | 기능, 도구 목록 및 보류 중인 요청 관리 |
| 병합된 네임스페이스(Merged namespace) | "하나의 도구 목록" | 모든 활성 서버에 걸친 도구 이름의 평면 집합 |
| 네임스페이스 충돌(Namespace collision) | "두 서버 동일 도구" | 클라이언트가 중복에 대해 접두사, 거부 또는 선착순 처리 |
| 라우팅(Routing) | "누가 이 호출을 받나?" | 도구 이름에서 소유 서버로의 디스패치 |
| 백그라운드 리더(Background reader) | "비차단 stdout" | 서버 stdout을 큐로 드레인하는 스레드 또는 태스크 |
| 샘플링 콜백(Sampling callback) | "LLM-as-a-Service" | 서버의 `sampling/createMessage`에 대한 클라이언트 핸들러 |
| `notifications/*_changed` | "프리미티브 변경" | 클라이언트가 재검색 또는 재읽기해야 한다는 신호 |
| 재연결 정책(Reconnection policy) | "서버가 죽었을 때" | 전송 실패 시 재시작 의미론 |
| Stdio 세션 | "프로세스 = 세션" | 세션 ID 없음; 자식 프로세스 수명이 세션 |

## 추가 자료

- [Model Context Protocol — Client spec](https://modelcontextprotocol.io/specification/2025-11-25/client) — 표준 클라이언트 동작
- [MCP — Quickstart client guide](https://modelcontextprotocol.io/quickstart/client) — Python SDK를 사용한 hello-world 클라이언트 튜토리얼
- [MCP Python SDK — client module](https://github.com/modelcontextprotocol/python-sdk) — 참조 `ClientSession` 및 `stdio_client`
- [MCP TypeScript SDK — Client](https://github.com/modelcontextprotocol/typescript-sdk) — TS 병렬
- [VS Code — MCP in extensions](https://code.visualstudio.com/api/extension-guides/ai/mcp) — VS Code가 단일 편집기 호스트에서 여러 MCP 서버를 다중화하는 방법
