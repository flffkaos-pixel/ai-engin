# MCP 리소스와 프롬프트 — 도구를 넘어선 컨텍스트 노출

> 도구는 MCP 관심의 90%를 차지합니다. 다른 두 서버 프리미티브는 다른 문제를 해결합니다. 리소스는 읽기용 데이터를 노출합니다; 프롬프트는 슬래시 명령어로 재사용 가능한 템플릿을 노출합니다. 많은 서버가 읽기를 도구로 래핑하는 대신 리소스를 사용하고, 클라이언트 프롬프트에 워크플로를 하드코딩하는 대신 프롬프트를 사용해야 합니다. 이 레슨은 결정 규칙을 명명하고 `resources/*` 및 `prompts/*` 메시지를 살펴봅니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, 리소스 + 프롬프트 핸들러)
**Prerequisites:** 13단계 07과 (MCP 서버)
**Time:** 약 45분

## 학습 목표

- 주어진 도메인에 대해 기능을 도구, 리소스 또는 프롬프트로 노출할지 결정할 수 있다.
- `resources/list`, `resources/read`, `resources/subscribe`를 구현하고 `notifications/resources/updated`를 처리할 수 있다.
- 인자 템플릿으로 `prompts/list` 및 `prompts/get`을 구현할 수 있다.
- 호스트가 프롬프트를 슬래시 명령어로 표시하는지 자동 주입 컨텍스트로 표시하는지 인식할 수 있다.

## 문제

노트 앱을 위한 순진한 MCP 서버는 모든 것을 도구로 노출합니다: `notes_read`, `notes_list`, `notes_search`. 이는 모든 데이터 접근을 모델 주도 도구 호출로 래핑합니다. 결과:

- 모델은 컨텍스트에 도움이 될 수 있는 모든 쿼리에 대해 `notes_read`를 호출할지 결정해야 함.
- 읽기 전용 콘텐츠를 구독하거나 호스트의 사이드 패널로 스트리밍할 수 없음.
- 클라이언트 UI(Claude Desktop의 리소스 첨부 패널, Cursor의 "파일 포함" 선택기)가 데이터를 표시할 수 없음.

올바른 분할: 데이터를 리소스로 노출, 변경 또는 계산된 액션을 도구로 노출, 재사용 가능한 다단계 워크플로를 프롬프트로 노출. 각 프리미티브에는 자체 UX 어포던스와 접근 패턴이 있습니다.

## 개념

### 도구 vs 리소스 vs 프롬프트 — 결정 규칙

| 기능 | 프리미티브 |
|------------|-----------|
| 사용자가 데이터를 검색, 필터링 또는 변환하려고 함 | 도구 |
| 사용자가 호스트가 이 데이터를 컨텍스트로 포함하기를 원함 | 리소스 |
| 사용자가 재실행할 수 있는 템플릿화된 워크플로를 원함 | 프롬프트 |

지침: 모델이 관련 쿼리마다 호출하는 것이 유익하면 도구. 사용자가 대화에 첨부하는 것이 유익하면 리소스. 전체 다단계 워크플로가 사용자가 재사용하려는 단위이면 프롬프트.

### 리소스

`resources/list`는 `{resources: [{uri, name, mimeType, description?}]}`를 반환. `resources/read`는 `{uri}`를 받고 `{contents: [{uri, mimeType, text | blob}]}`를 반환.

URI는 주소 지정 가능한 모든 것이 될 수 있습니다:

- `file:///Users/alice/notes/mcp.md`
- `postgres://my-db/query/SELECT ...`
- `notes://note-14` (커스텀 스킴)
- `memory://session-2026-04-22/recent` (서버 특정)

`contents[]`는 텍스트와 바이너리를 모두 지원. 바이너리는 base64 인코딩 문자열 + `mimeType`으로 `blob` 사용.

### 리소스 구독

기능에서 `{resources: {subscribe: true}}` 선언. 클라이언트가 `resources/subscribe {uri}` 호출. 서버가 리소스 변경 시 `notifications/resources/updated {uri}` 전송. 클라이언트가 다시 읽음.

사용 사례: 리소스가 디스크의 파일인 노트 서버; 파일 감시자가 업데이트 알림 트리거; Claude Desktop이 호스트 외부에서 편집될 때 파일을 컨텍스트로 다시 가져옴.

### 리소스 템플릿 (2025-11-25 추가)

`resourceTemplates`를 사용하면 파라미터화된 URI 패턴을 노출할 수 있음: `notes://{id}` with `id` as a completion target. 클라이언트가 리소스 선택기에서 ID를 자동 완성할 수 있음.

### 프롬프트

`prompts/list`는 `{prompts: [{name, description, arguments?}]}`를 반환. `prompts/get`은 `{name, arguments}`를 받고 `{description, messages: [{role, content}]}`를 반환.

프롬프트는 호스트가 모델에 공급하는 메시지 목록으로 채워지는 템플릿입니다. 예를 들어 `code_review` 프롬프트는 `file_path` 인자를 받고 세 메시지 시퀀스(시스템 메시지, 파일 본문이 포함된 사용자 메시지, 추론 템플릿이 포함된 어시스턴트 시작 메시지)를 반환합니다.

### 호스트와 프롬프트

Claude Desktop, VS Code 및 Cursor는 프롬프트를 채팅 UI의 슬래시 명령어로 노출합니다. 사용자가 `/code_review`를 입력하고 양식에서 인자를 선택합니다. 서버의 프롬프트는 "사용자 단축키"와 "모델에 전송된 전체 프롬프트" 사이의 계약입니다.

모든 클라이언트가 아직 프롬프트를 지원하는 것은 아닙니다 — 기능 협상을 확인하세요. 프롬프트 기능이 선언된 서버와 프롬프트 지원이 없는 클라이언트는 슬래시 명령어가 표시되지 않습니다.

### "목록 변경" 알림

리소스와 프롬프트 모두 집합이 변경될 때 `notifications/list_changed`를 출력합니다. 방금 20개의 새 노트를 가져온 노트 서버는 `notifications/resources/list_changed`를 출력합니다; 클라이언트가 `resources/list`를 다시 호출하여 추가 사항을 가져옵니다.

### 콘텐츠 타입 규칙

텍스트: `mimeType: "text/plain"`, `text/markdown`, `application/json`.
바이너리: `image/png`, `application/pdf` + `blob` 필드.
MCP Apps(14과): `ui://` URI의 `text/html;profile=mcp-app`.

### 동적 리소스

리소스 URI가 정적 파일에 해당할 필요는 없습니다. `notes://recent`는 읽을 때마다 최근 5개 노트를 반환할 수 있습니다. `db://query/users/active`는 파라미터화된 쿼리를 실행할 수 있습니다. 서버는 콘텐츠를 동적으로 자유롭게 계산할 수 있습니다.

규칙: 클라이언트가 URI로 캐시할 수 있으면 URI는 안정적이어야 함. 계산이 일회성이면 URI에 타임스탬프나 nonce를 포함하여 클라이언트 캐시가 오래되지 않도록 해야 함.

### 구독 vs 폴링

구독 가능 클라이언트는 `notifications/resources/updated`를 통해 서버 푸시를 받음. 구독 이전 클라이언트 또는 지원하지 않는 호스트는 다시 읽어서 폴링. 둘 다 사양 준수. 서버의 기능 선언이 클라이언트에게 어떤 것을 지원하는지 알려줌.

구독 비용: 서버의 세션별 상태(누가 무엇을 구독하는지). 구독 집합을 제한적으로 유지; 연결이 끊긴 클라이언트는 타임아웃되어야 함.

### 프롬프트 vs 시스템 프롬프트

MCP의 프롬프트는 시스템 프롬프트가 아닙니다. 호스트의 시스템 프롬프트(자체 운영 지침)와 MCP 프롬프트(사용자가 호출한 서버 제공 템플릿)는 나란히 존재합니다. 잘 동작하는 클라이언트는 서버 프롬프트가 자체 시스템 프롬프트를 재정의하도록 허용하지 않습니다; 계층화합니다.

## 사용하기

`code/main.py`는 07과의 노트 서버를 확장합니다:

- 노트별 리소스(`notes://note-1` 등) with `resources/subscribe` 지원.
- 세 메시지 템플릿으로 렌더링되는 `review_note` 프롬프트.
- 노트가 수정될 때 `notifications/resources/updated`를 출력하는 파일 감시자 시뮬레이션.
- 항상 최근 5개 노트를 반환하는 `notes://recent` 동적 리소스.

데모를 실행하여 전체 흐름을 확인하세요.

## 배포하기

이 레슨은 `outputs/skill-primitive-splitter.md`를 생성합니다. 제안된 MCP 서버가 주어지면 스킬이 각 기능을 근거와 함께 도구/리소스/프롬프트로 분류합니다.

## 실습

1. `code/main.py`를 실행하세요. 초기 리소스 목록을 관찰한 다음 노트 편집을 트리거하고 `notifications/resources/updated` 이벤트가 발생하는지 확인하세요.

2. `resources/list_changed` 이미터를 추가하세요: 새 노트가 생성될 때 알림을 보내 클라이언트가 재검색하도록 하세요.

3. GitHub MCP 서버를 위한 세 가지 프롬프트를 설계하세요: `summarize_pr`, `triage_issue`, `release_notes`. 각각 인자 스키마가 있어야 합니다. 프롬프트 본문은 추가 편집 없이 실행 가능해야 합니다.

4. 07과 서버의 기존 도구를 가져와 도구로 남아 있어야 하는지 아니면 리소스 + 도구 쌍으로 분할되어야 하는지 분류하세요. 한 문장으로 정당화하세요.

5. 사양의 `server/resources` 및 `server/prompts` 섹션을 읽으세요. `resources/read`에서 드물게 채워지지만 사양이 지원하는 필드를 식별하세요. 힌트: 리소스 콘텐츠의 `_meta`를 보세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 리소스(Resource) | "노출된 데이터" | 호스트가 읽을 수 있는 URI 주소 지정 콘텐츠 |
| 리소스 URI | "데이터 포인터" | 스킴 접두사 식별자(`file://`, `notes://` 등) |
| `resources/subscribe` | "변경 감시" | 특정 URI에 대한 클라이언트 옵트인 서버 푸시 업데이트 |
| `notifications/resources/updated` | "리소스 변경됨" | 구독된 리소스에 새 콘텐츠가 있음을 클라이언트에 신호 |
| 리소스 템플릿(Resource template) | "파라미터화된 URI" | 호스트 선택기를 위한 완성 힌트가 있는 URI 패턴 |
| 프롬프트(Prompt) | "슬래시 명령어 템플릿" | 인자 슬롯이 있는 명명된 다중 메시지 템플릿 |
| 프롬프트 인자(Prompt arguments) | "템플릿 입력" | 렌더링 전 클라이언트가 수집하는 타입화된 파라미터 |
| `prompts/get` | "템플릿 렌더링" | 서버가 채워진 메시지 목록을 반환 |
| 콘텐츠 블록(Content block) | "타입화된 청크" | `{type: text | image | resource | ui_resource}` |
| 슬래시 명령어 UX | "사용자 단축키" | 호스트가 `/`로 시작하는 명령어로 프롬프트 표시 |

## 추가 자료

- [MCP — Concepts: Resources](https://modelcontextprotocol.io/docs/concepts/resources) — 리소스 URI, 구독 및 템플릿
- [MCP — Concepts: Prompts](https://modelcontextprotocol.io/docs/concepts/prompts) — 프롬프트 템플릿 및 슬래시 명령어 통합
- [MCP — Server resources spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/resources) — 전체 `resources/*` 메시지 참조
- [MCP — Server prompts spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts) — 전체 `prompts/*` 메시지 참조
- [MCP — Protocol info site: resources](https://modelcontextprotocol.info/docs/concepts/resources/) — 공식 문서를 확장하는 커뮤니티 가이드
