# 루트와 엘리시테이션 — 범위 지정 및 실행 중 사용자 입력

> 하드코딩된 경로는 사용자가 다른 프로젝트를 여는 순간 깨집니다. 미리 채워진 도구 인자는 사용자가 불충분하게 지정할 때 깨집니다. 루트는 서버를 사용자 제어 URI 집합으로 범위를 지정합니다; 엘리시테이션은 도구 호출 중에 일시 중지하여 양식 또는 URL을 통해 사용자에게 구조화된 입력을 요청합니다. 두 클라이언트 프리미티브, 두 가지 일반적인 MCP 실패 모드에 대한 두 가지 수정. SEP-1036(URL 모드 엘리시테이션, 2025-11-25)은 2026년 상반기까지 실험적입니다 — 이에 의존하기 전에 SDK 버전을 확인하세요.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, 루트 + 엘리시테이션 데모)
**Prerequisites:** 13단계 07과 (MCP 서버)
**Time:** 약 45분

## 학습 목표

- `roots`를 선언하고 `notifications/roots/list_changed`에 응답할 수 있다.
- 서버 파일 작업을 선언된 루트 집합 내의 URI로 제한할 수 있다.
- `elicitation/create`를 사용하여 도구 호출 중에 사용자에게 확인 또는 구조화된 입력을 요청할 수 있다.
- 양식 모드와 URL 모드 엘리시테이션 중에서 선택할 수 있다(후자는 실험적; 드리프트 위험 참고).

## 문제

노트 MCP 서버가 프로덕션에서 겪는 두 가지 구체적인 실패.

**잘못된 경로 가정.** 서버가 `~/notes`에 대해 작성됨. 다른 머신에서 `~/Documents/Notes`에 노트가 있는 사용자는 조용히 실패하는 도구 호출(파일을 찾을 수 없음)을 얻거나, 더 나쁘게는 잘못된 위치에 씀.

**사용자가 알 수 있는 인자 누락.** 사용자가 "오래된 TPS 보고서 노트 삭제" 요청. 모델이 `notes_delete(title: "TPS report")`를 호출하지만 2023, 2024, 2025년의 세 개 일치 노트가 있음. 도구가 추측할 수 없음. "모호함"과 함께 실패하는 것은 짜증나고; 세 개 모두에 실행하는 것은 치명적.

루트가 첫 번째를 수정: 클라이언트가 `initialize`에서 서버가 접근할 수 있는 URI 집합을 선언. 엘리시테이션이 두 번째를 수정: 서버가 도구 호출을 일시 중지하고 `elicitation/create`를 보내 사용자에게 선택하도록 요청.

## 개념

### 루트

클라이언트가 `initialize`에서 루트 목록을 선언:

```json
{
  "capabilities": {"roots": {"listChanged": true}}
}
```

서버가 `roots/list`를 호출할 수 있음:

```json
{"roots": [{"uri": "file:///Users/alice/Documents/Notes", "name": "Notes"}]}
```

서버는 루트를 경계로 취급해야 함: 루트 집합 외부의 파일 읽기 또는 쓰기는 거부됨. 이것은 클라이언트가 강제하지 않음(서버는 여전히 사용자가 신뢰한 코드), 그러나 사양 준수 서버는 이를 존중.

사용자가 루트를 추가하거나 제거할 때 클라이언트가 `notifications/roots/list_changed`를 전송. 서버가 `roots/list`를 다시 호출하고 경계를 업데이트.

### 루트가 클라이언트 프리미티브인 이유

루트는 사용자의 동의 모델을 나타내기 때문에 클라이언트가 선언. 사용자가 Claude Desktop에 "이 노트 서버에 이 두 디렉토리에 대한 접근 권한을 부여"라고 말함. 서버는 그 범위를 넓힐 수 없음.

### 엘리시테이션: 양식 모드 기본값

`elicitation/create`는 양식 스키마와 자연어 프롬프트를 받음:

```json
{
  "method": "elicitation/create",
  "params": {
    "message": "'TPS report'를 삭제하시겠습니까? 여러 노트가 일치합니다; 하나를 선택하세요.",
    "requestedSchema": {
      "type": "object",
      "properties": {
        "note_id": {
          "type": "string",
          "enum": ["note-3", "note-7", "note-14"]
        },
        "confirm": {"type": "boolean"}
      },
      "required": ["note_id", "confirm"]
    }
  }
}
```

클라이언트가 양식을 렌더링하고 사용자의 답변을 수집하여 반환:

```json
{
  "action": "accept",
  "content": {"note_id": "note-14", "confirm": true}
}
```

세 가지 가능한 액션: `accept`(사용자가 작성), `decline`(사용자가 닫음), `cancel`(사용자가 전체 도구 호출 중단).

양식 스키마는 평평함 — 중첩 객체는 v1에서 지원되지 않음. SDK는 일반적으로 단일 계층보다 복잡한 것은 거부.

### 엘리시테이션: URL 모드 (SEP-1036, 실험적)

2025-11-25의 새로운 기능. 스키마 대신 서버가 URL을 전송:

```json
{
  "method": "elicitation/create",
  "params": {
    "message": "GitHub에 로그인",
    "url": "https://github.com/login/oauth/authorize?client_id=..."
  }
}
```

클라이언트가 브라우저에서 URL을 열고 완료를 기다린 후 사용자가 돌아오면 반환. 양식이 충분하지 않은 OAuth 흐름, 결제 승인 및 문서 서명에 유용.

드리프트 위험 참고: SEP-1036 응답 형태는 여전히 안정화 중; 일부 SDK는 콜백 URL을 반환하고 다른 SDK는 완료 토큰을 반환. 프로덕션에서 URL 모드를 사용하기 전에 SDK의 릴리스 노트를 읽으세요.

### 엘리시테이션이 올바른 도구인 경우

- 파괴적 액션 전 사용자 확인(파괴적 힌트 + 엘리시테이션).
- 명확화(N개 일치 중 하나 선택).
- 첫 실행 설정(API 키, 디렉토리, 기본 설정).
- OAuth 스타일 흐름(URL 모드).

### 엘리시테이션이 잘못된 경우

- 모델이 산문으로 요청할 수 있었던 도구의 필수 인자 채우기. 엘리시테이션 대화상자가 아닌 일반 재프롬프트 사용.
- 고빈도 호출. 엘리시테이션은 대화를 중단; 루프 내부에서 실행하지 마세요.
- 서버가 사후에 검증할 수 있는 모든 것. 검증하고, 오류를 반환하고, 모델이 텍스트로 사용자에게 물어보게 하세요.

### 인간-인-더-루프 브리지

엘리시테이션과 샘플링이 함께 MCP의 "인간-인-더-루프" 모델을 가능하게 함. 서버의 에이전트 루프는 사용자 입력(엘리시테이션) 또는 모델 추론(샘플링)을 위해 일시 중지할 수 있음. 13단계 11과는 샘플링을 다루었음; 이 레슨은 엘리시테이션을 다룹니다. 전체 미드루프 제어를 위해 함께 사용하세요.

## 사용하기

`code/main.py`는 노트 서버를 확장합니다:

- 서버가 루트 목록 변경 알림 후 재쿼리하는 `roots/list` 응답.
- 여러 노트가 일치할 때 `elicitation/create`를 사용하여 명확화하는 `notes_delete` 도구.
- URL 모드 엘리시테이션을 사용하여 첫 실행 설정 페이지(시뮬레이션)를 여는 `notes_setup` 도구.
- 선언된 루트 외부의 URI에 대한 작업을 거부하는 경계 검사.

데모는 세 가지 시나리오를 실행: 행복 경로(하나 일치), 명확화(세 개 일치, 엘리시테이션 발동), 루트 외부 쓰기(거부됨).

## 배포하기

이 레슨은 `outputs/skill-elicitation-form-designer.md`를 생성합니다. 사용자 확인 또는 명확화가 필요할 수 있는 도구가 주어지면 스킬이 엘리시테이션 양식 스키마와 메시지 템플릿을 설계합니다.

## 실습

1. `code/main.py`를 실행하세요. 명확화 경로를 트리거하고 시뮬레이션된 사용자 답변이 도구로 다시 라우팅되는지 확인하세요.

2. 매번 엘리시테이션 확인이 필요한(파괴적 힌트) 새 도구 `notes_archive`를 추가하세요. UX를 확인하세요: 이것이 모델이 텍스트로 다시 묻는 것과 어떻게 비교되나요?

3. 첫 실행 OAuth 흐름을 위한 URL 모드 엘리시테이션을 구현하세요. 드리프트 위험을 참고하고 SDK 버전 가드를 추가하세요.

4. `roots/list` 처리를 확장: 알림이 도착하면 서버가 원자적으로 다시 읽고 범위를 벗어날 수 있는 열린 파일 핸들을 다시 검사해야 함.

5. GitHub에서 SEP-1036 이슈 토론 스레드를 읽으세요. 서버가 URL 모드 콜백을 처리하는 방법에 영향을 미치는 하나의 미해결 질문을 식별하세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 루트(Root) | "동의 경계" | 클라이언트가 서버가 접근하도록 허용한 URI |
| `roots/list` | "서버가 범위 요청" | 클라이언트가 현재 루트 집합 반환 |
| `notifications/roots/list_changed` | "사용자가 범위 변경" | 클라이언트가 루트 집합이 변경되었음을 신호 |
| 엘리시테이션(Elicitation) | "호출 중 사용자 질문" | 구조화된 사용자 입력에 대한 서버 주도 요청 |
| `elicitation/create` | "메소드" | 엘리시테이션 요청을 위한 JSON-RPC 메소드 |
| 양식 모드(Form mode) | "스키마 기반 양식" | 클라이언트 UI에서 양식으로 렌더링되는 평평한 JSON Schema |
| URL 모드(URL mode) | "브라우저 리디렉션" | SEP-1036 실험적; URL을 열고 대기 |
| `accept` / `decline` / `cancel` | "사용자 응답 결과" | 서버가 처리하는 세 가지 분기 |
| 명확화(Disambiguation) | "하나 선택" | 도구에 N개 후보가 있을 때 일반적인 엘리시테이션 사용 사례 |
| 평평한 양식(Flat form) | "최상위 속성만" | 엘리시테이션 스키마는 중첩 불가 |

## 추가 자료

- [MCP — Client roots spec](https://modelcontextprotocol.io/specification/draft/client/roots) — 표준 루트 참조
- [MCP — Client elicitation spec](https://modelcontextprotocol.io/specification/draft/client/elicitation) — 표준 엘리시테이션 참조
- [Cisco — What's new in MCP elicitation, structured content, OAuth enhancements](https://blogs.cisco.com/developer/whats-new-in-mcp-elicitation-structured-content-and-oauth-enhancements) — 2025-11-25 추가 사항 워크스루
- [MCP — GitHub SEP-1036](https://github.com/modelcontextprotocol/modelcontextprotocol) — URL 모드 엘리시테이션 제안 (실험적, 드리프트 위험)
- [The New Stack — How elicitation brings human-in-the-loop to AI tools](https://thenewstack.io/how-elicitation-in-mcp-brings-human-in-the-loop-to-ai-tools/) — UX 워크스루
