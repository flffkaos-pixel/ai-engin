# MCP Apps — `ui://`를 통한 대화형 UI 리소스

> 텍스트 전용 도구 출력은 에이전트가 보여줄 수 있는 것에 한계가 있습니다. MCP Apps(SEP-1724, 2026년 1월 26일 공식)를 사용하면 도구가 Claude Desktop, ChatGPT, Cursor, Goose 및 VS Code에서 인라인으로 렌더링되는 샌드박스 처리된 대화형 HTML을 반환할 수 있습니다. 대시보드, 양식, 지도, 3D 장면, 모두 하나의 확장을 통해. 이 레슨은 `ui://` 리소스 스킴, `text/html;profile=mcp-app` MIME, iframe-sandbox postMessage 프로토콜 및 서버가 HTML을 렌더링하도록 허용할 때 따르는 보안 표면을 다룹니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, UI 리소스 이미터), HTML (샘플 앱)
**Prerequisites:** 13단계 07과 (MCP 서버), 13단계 10과 (리소스)
**Time:** 약 75분

## 학습 목표

- 도구 호출에서 `ui://` 리소스를 반환하고 올바른 MIME 및 메타데이터를 설정할 수 있다.
- `_meta.ui.resourceUri`, `_meta.ui.csp`, `_meta.ui.permissions`로 도구의 연결된 UI를 선언할 수 있다.
- UI-호스트 통신을 위한 iframe 샌드박스 postMessage JSON-RPC를 구현할 수 있다.
- UI 기원 공격을 방어하는 CSP 및 permissions-policy 기본값을 적용할 수 있다.

## 문제

2025년 시대의 `visualize_timeline` 도구는 "다음은 14개의 노트를 시간순으로 정리한 것입니다: ..."를 반환할 수 있습니다. 그것은 한 문단입니다. 사용자는 실제로 대화형 타임라인을 원합니다. MCP Apps 이전의 옵션은 클라이언트별 위젯 API(Claude artifacts, OpenAI Custom GPT HTML) 또는 UI 없음이었습니다.

MCP Apps(SEP-1724, 2026년 1월 26일 출시)는 계약을 표준화합니다. 도구 결과에는 URI가 `ui://...`이고 MIME이 `text/html;profile=mcp-app`인 `resource`가 포함됩니다. 호스트는 제한된 CSP와 명시적으로 허용되지 않는 한 네트워크 접근 없이 샌드박스 처리된 iframe에서 렌더링합니다. iframe 내부의 UI는 작은 postMessage JSON-RPC 방언을 통해 호스트에 메시지를 게시합니다.

모든 호환 클라이언트(Claude Desktop, ChatGPT, Goose, VS Code)는 동일한 `ui://` 리소스를 동일한 방식으로 렌더링합니다. 하나의 서버, 하나의 HTML 번들, 보편적 UI.

## 개념

### `ui://` 리소스 스킴

도구가 반환:

```json
{
  "content": [
    {"type": "text", "text": "노트 타임라인입니다:"},
    {"type": "ui_resource", "uri": "ui://notes/timeline"}
  ],
  "_meta": {
    "ui": {
      "resourceUri": "ui://notes/timeline",
      "csp": {
        "defaultSrc": "'self'",
        "scriptSrc": "'self' 'unsafe-inline'",
        "connectSrc": "'self'"
      },
      "permissions": []
    }
  }
}
```

그런 다음 호스트가 `ui://notes/timeline` URI에서 `resources/read`를 호출하고 다음을 반환받음:

```json
{
  "contents": [{
    "uri": "ui://notes/timeline",
    "mimeType": "text/html;profile=mcp-app",
    "text": "<!doctype html>..."
  }]
}
```

### Iframe 샌드박스

호스트가 HTML을 샌드박스 처리된 `<iframe>` 내부에 렌더링:

- `sandbox="allow-scripts allow-same-origin"`(또는 서버 선언에 따라 더 엄격하게)
- 서버 선언 CSP가 응답 헤더를 통해 적용.
- 호스트 출처의 쿠키, localStorage 없음.
- CSP의 `connectSrc`로 제한된 네트워크 접근.

### postMessage 프로토콜

Iframe은 `window.postMessage`를 통해 호스트와 통신. 작은 JSON-RPC 2.0 방언:

```js
// iframe에서 호스트로 (호스트 출처로 고정)
window.parent.postMessage({
  jsonrpc: "2.0",
  id: 1,
  method: "host.callTool",
  params: { name: "notes_update", arguments: { id: "note-14", title: "..." } }
}, "https://host.example.com");

// 호스트에서 iframe으로 (iframe 출처로 고정)
iframe.contentWindow.postMessage({
  jsonrpc: "2.0",
  id: 1,
  result: { content: [...] }
}, "https://iframe.example.com");

// 양쪽의 수신자
window.addEventListener("message", (event) => {
  if (event.origin !== "https://expected-peer.example.com") return;
  // event.data를 안전하게 처리
});
```

UI가 호출할 수 있는 호스트 측 메소드:

- `host.callTool(name, arguments)` — 서버 도구 호출.
- `host.readResource(uri)` — MCP 리소스 읽기.
- `host.getPrompt(name, arguments)` — 프롬프트 템플릿 가져오기.
- `host.close()` — UI 닫기.

모든 호출은 여전히 MCP 프로토콜을 통과하며 서버의 권한을 상속.

### 권한

`_meta.ui.permissions` 목록이 추가 기능을 요청:

- `camera` — 사용자 카메라 접근(문서 스캔 UI에 사용).
- `microphone` — 음성 입력.
- `geolocation` — 위치.
- `network:*` — `connectSrc`만으로 허용되는 것보다 더 넓은 네트워크 접근.

각 권한은 UI가 렌더링되기 전에 사용자가 보는 프롬프트.

### 보안 위험

iframe의 HTML은 여전히 HTML입니다. 새로운 공격 표면:

- **UI를 통한 프롬프트 주입.** 악성 서버 UI가 시스템 메시지처럼 보이는 텍스트를 표시하여 사용자를 속임. 호스트 렌더링은 서버 UI를 호스트 UI와 시각적으로 구분해야 함.
- **`connectSrc`를 통한 유출.** CSP가 `connect-src: *`를 허용하면 UI가 데이터를 어디로든 보낼 수 있음. 기본값은 엄격해야 함.
- **클릭재킹.** UI가 호스트 크롬을 오버레이. 호스트는 z-index 조작을 방지하고 불투명도 규칙을 적용해야 함.
- **포커스 도용.** UI가 키보드 포커스를 가져가 다음 메시지를 캡처. 호스트가 가로채야 함.

13단계 15과는 MCP 보안의 일부로 이를 깊이 다루며; 이 레슨은 소개합니다.

### `ui/initialize` 핸드셰이크

Iframe 로드 후 postMessage로 `ui/initialize` 전송:

```json
{"jsonrpc": "2.0", "id": 0, "method": "ui/initialize",
 "params": {"theme": "dark", "locale": "en-US", "sessionId": "..."}}
```

호스트가 기능 및 세션 토큰으로 응답. UI가 모든 후속 호스트 호출에 세션 토큰 사용.

### AppRenderer / AppFrame SDK 프리미티브

ext-apps SDK는 두 가지 편의 프리미티브를 노출:

- `AppRenderer` (서버 측) — React / Vue / Solid 컴포넌트를 래핑하고 올바른 MIME 및 메타데이터로 `ui://` 리소스 출력.
- `AppFrame` (클라이언트 측) — 리소스를 수신하고 iframe을 마운트하며 postMessage 중재.

이것들을 사용하거나 HTML과 JSON-RPC를 수제작할 수 있음.

### 생태계 현황

MCP Apps는 2026년 1월 26일에 출시됨. 2026년 4월 기준 클라이언트 지원:

- **Claude Desktop.** 2026년 1월부터 완전 지원.
- **ChatGPT.** Apps SDK를 통한 완전 지원(동일한 기본 MCP Apps 프로토콜).
- **Cursor.** 베타; 설정에서 활성화.
- **VS Code.** Insider 빌드 전용.
- **Goose.** 완전 지원.
- **Zed, Windsurf.** 로드맵에 있음.

프로덕션 서버: 대시보드, 지도 시각화, 데이터 테이블, 차트 빌더, 샌드박스 IDE 미리보기.

## 사용하기

`code/main.py`는 노트 서버를 SVG 타임라인이 있는 작지만 완전한 HTML 번들을 반환하는 `ui://notes/timeline` 리소스를 반환하는 `visualize_timeline` 도구와 해당 URI에 대한 `resources/read` 핸들러로 확장합니다. HTML은 표준 라이브러리 템플릿 — 빌드 시스템 없음. postMessage는 표준 라이브러리가 브라우저를 구동할 수 없으므로 JS 주석에 스케치됨.

살펴볼 내용:

- 도구 응답의 `_meta.ui`가 resourceUri, CSP, permissions를 전달.
- HTML이 네트워크 접근 없이 렌더링; 모든 데이터가 인라인.
- JS가 `window.parent.postMessage`를 통해 `host.callTool` 호출(문서화되었지만 이 stdlib 데모에서는 비활성).

## 배포하기

이 레슨은 `outputs/skill-mcp-apps-spec.md`를 생성합니다. 대화형 UI가 도움이 될 도구가 주어지면 스킬이 전체 MCP Apps 계약을 생성: `ui://` URI, CSP, permissions, postMessage 진입점 및 보안 체크리스트.

## 실습

1. `code/main.py`를 실행하고 출력된 HTML을 검사하세요. 브라우저에서 HTML을 직접 열고 SVG가 렌더링되는지 확인하세요. 그런 다음 UI가 `host.callTool("notes_update", ...)`을 호출하는 데 사용할 postMessage 계약을 스케치하세요.

2. CSP 강화: `'unsafe-inline'`을 제거하고 nonce 기반 스크립트 정책을 사용하세요. HTML 생성 코드에서 무엇이 변경되나요?

3. 제자리에서 노트를 편집하기 위한 양식이 있는 두 번째 UI 리소스 `ui://notes/editor`를 추가하세요. 사용자가 제출하면 iframe이 `host.callTool("notes_update", ...)`을 호출합니다.

4. UI의 공격 표면을 감사하세요. 악성 서버가 콘텐츠를 주입할 수 있는 곳은 어디인가요? iframe 샌드박스가 무엇을 방어하고 무엇을 방어하지 않나요?

5. SEP-1724 사양을 읽고 이 장난감 구현이 사용하지 않는 MCP Apps SDK의 기능을 식별하세요. (힌트: 컴포넌트 수준 상태 동기화.)

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| MCP Apps | "대화형 UI 리소스" | 2026-01-26 출시 SEP-1724 확장 |
| `ui://` | "앱 URI 스킴" | UI 번들을 위한 리소스 스킴 |
| `text/html;profile=mcp-app` | "MIME" | MCP App HTML을 위한 콘텐츠 타입 |
| Iframe 샌드박스 | "렌더 컨테이너" | CSP 및 권한이 있는 UI의 브라우저 샌드박싱 |
| postMessage JSON-RPC | "UI-호스트 와이어" | 호스트 호출을 위한 작은 JSON-RPC-over-postMessage 방언 |
| `_meta.ui` | "도구-UI 바인딩" | 도구 결과를 UI 리소스에 연결하는 메타데이터 |
| CSP | "Content-Security-Policy" | 스크립트, 네트워크, 스타일에 대해 허용된 출처 선언 |
| AppRenderer | "서버 SDK 프리미티브" | 프레임워크 컴포넌트를 `ui://` 리소스로 변환 |
| AppFrame | "클라이언트 SDK 프리미티브" | postMessage를 중재하는 iframe 마운트 헬퍼 |
| `ui/initialize` | "핸드셰이크" | UI에서 호스트로의 첫 번째 postMessage |

## 추가 자료

- [MCP ext-apps — GitHub](https://github.com/modelcontextprotocol/ext-apps) — 참조 구현 및 SDK
- [MCP Apps specification 2026-01-26](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx) — 공식 사양 문서
- [MCP — Apps extension overview](https://modelcontextprotocol.io/extensions/apps/overview) — 고수준 문서
- [MCP blog — MCP Apps launch](https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/) — 2026년 1월 출시 포스트
- [MCP Apps API reference](https://apps.extensions.modelcontextprotocol.io/api/) — JSDoc 스타일 SDK 참조
