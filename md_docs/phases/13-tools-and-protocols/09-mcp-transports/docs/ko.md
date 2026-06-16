# MCP 전송 — stdio vs Streamable HTTP vs SSE 마이그레이션

> stdio는 로컬에서만 작동하고 다른 곳에서는 작동하지 않습니다. Streamable HTTP(2025-03-26)는 원격 표준입니다. 기존 HTTP+SSE 전송은 폐기되었으며 2026년 중반에 제거되고 있습니다. 잘못된 전송을 선택하면 마이그레이션 비용이 발생합니다; 올바른 전송을 선택하면 세션 연속성과 DNS-리바인딩 보호가 있는 원격 호스팅 가능 MCP 서버를 얻을 수 있습니다.

**Type:** 학습
**Languages:** Python (표준 라이브러리, Streamable HTTP 엔드포인트 스켈레톤)
**Prerequisites:** 13단계 07과, 08과 (MCP 서버 및 클라이언트)
**Time:** 약 45분

## 학습 목표

- 배포 형태(로컬 vs 원격, 단일 프로세스 vs 팔릿)에 따라 stdio와 Streamable HTTP 중에서 선택할 수 있다.
- Streamable HTTP 단일 엔드포인트 패턴(POST는 요청용, GET은 세션 스트림용)을 구현할 수 있다.
- DNS-리바인딩을 막기 위해 `Origin` 검증 및 세션 ID 의미론을 적용할 수 있다.
- 2026년 중반 제거 기한 전에 레거시 HTTP+SSE 서버를 Streamable HTTP로 마이그레이션할 수 있다.

## 문제

첫 번째 MCP 원격 전송(2024-11)은 HTTP+SSE였습니다: 두 개의 엔드포인트, 하나는 클라이언트의 POST용, 하나는 서버-클라이언트 스트림용 Server-Sent-Events 채널. 작동은 했습니다. 그러나 또한 서투르기도 했습니다: 세션당 두 개의 엔드포인트, 일부 CDN 앞에서 깨진 캐시, 일부 WAF가 공격적으로 종료하는 장기 연결 SSE에 대한 하드 종속성.

2025-03-26 사양은 이를 Streamable HTTP로 대체했습니다: 하나의 엔드포인트, POST는 클라이언트 요청용, GET은 세션 스트림 설정용, 둘 다 `Mcp-Session-Id` 헤더 공유. 그 이후로 구축되거나 마이그레이션된 모든 서버는 Streamable HTTP를 사용합니다. 기존 SSE 모드는 폐기되고 있습니다 — Atlassian Rovo는 2026년 6월 30일에 제거, Keboola는 2026년 4월 1일, 대부분의 나머지 엔터프라이즈 서버는 2026년 말까지 제거 예정.

그리고 stdio는 여전히 로컬 서버에 중요합니다. Claude Desktop, VS Code 및 모든 IDE 형태의 클라이언트는 stdio를 통해 서버를 생성합니다. 올바른 개념 모델: "이 머신"용 stdio, "네트워크 너머"용 Streamable HTTP. 교차하지 않습니다.

## 개념

### stdio

- 자식 프로세스 전송. 클라이언트가 서버 생성, stdin/stdout으로 통신.
- 줄당 하나의 JSON 객체. 개행 구분.
- 세션 ID 없음; 프로세스 자체가 세션.
- 인증 불필요(자식이 부모의 신뢰 경계를 상속).
- 원격 서버에는 절대 사용하지 마세요 — SSH나 socat으로 터널링해야 하며, 그럴 바에는 Streamable HTTP 사용.

### Streamable HTTP

단일 엔드포인트 `/mcp`(또는 모든 경로). 세 가지 HTTP 메소드 지원:

- **POST /mcp.** 클라이언트가 JSON-RPC 메시지를 전송. 서버가 단일 JSON 응답 또는 하나 이상의 응답의 SSE 스트림(배치 응답 및 해당 요청과 관련된 알림에 유용)으로 응답.
- **GET /mcp.** 클라이언트가 장기 SSE 채널을 엽니다. 서버가 서버-클라이언트 요청(sampling, 알림, elicitation)에 사용.
- **DELETE /mcp.** 클라이언트가 명시적으로 세션을 종료.

세션은 서버가 첫 번째 응답에 설정하고 클라이언트가 모든 후속 요청에 반영하는 `Mcp-Session-Id` 헤더로 식별됩니다. 세션 ID는 암호학적으로 무작위여야 함(128+ 비트); 클라이언트가 선택한 ID는 안전을 위해 거부됩니다.

### 단일 엔드포인트 vs 두 개

기존 사양의 두 엔드포인트 모드는 2026년에도 여전히 호출 가능 — 사양은 "레거시 호환"으로 선언합니다. 그러나 모든 새 서버는 단일 엔드포인트여야 합니다. 공식 SDK는 단일 엔드포인트를 출력; 마이그레이션되지 않은 원격과 통신할 때만 레거시 모드를 사용하세요.

### `Origin` 검증 및 DNS-리바인딩

브라우저는 MCP 클라이언트가 아닙니다(현재), 그러나 공격자는 브라우저가 `localhost:1234/mcp`로 POST하도록 하는 웹페이지를 만들 수 있습니다 — 사용자의 로컬 MCP 서버가 수신하는 곳입니다. 서버가 `Origin`을 확인하지 않으면 브라우저의 동일 출처 정책이 `Origin: http://evil.com`이 교차 출처로 유효하기 때문에 도움이 되지 않습니다.

2025-11-25 사양은 서버가 허용 목록에 없는 `Origin`의 요청을 거부하도록 요구합니다. 허용 목록에는 일반적으로 MCP 클라이언트 호스트(`https://claude.ai`, `vscode-webview://*`) 및 로컬 UI용 localhost 변형이 포함됩니다.

### 세션 ID 라이프사이클

1. 클라이언트가 `Mcp-Session-Id` 없이 첫 번째 요청 전송.
2. 서버가 무작위 ID 할당, 응답 헤더에 `Mcp-Session-Id` 설정.
3. 클라이언트가 모든 후속 요청 및 스트림용 `GET /mcp`에 해당 헤더 반영.
4. 서버가 세션을 취소할 수 있음; 클라이언트가 후속 요청에서 404를 확인하고 재초기화해야 함.
5. 클라이언트가 명시적 DELETE로 세션을 깔끔하게 종료 가능.

### 킵얼라이브 및 재연결

SSE 연결이 끊어집니다. 클라이언트는 동일한 `Mcp-Session-Id`로 다시 GET하여 재설정. 서버는 중단 중에 놓친 이벤트를 큐에 저장하고(합리적인 기간까지) 클라이언트가 반영하는 `last-event-id` 헤더를 통해 재생해야 합니다.

13단계 13과는 전체 세션 재연결에서도 살아남는 장기 실행 작업인 Tasks를 다룹니다.

### 이전 버전 호환성 프로브

기존 서버와 새 서버를 모두 지원하려는 클라이언트:

1. `/mcp`로 POST.
2. 응답이 JSON 또는 SSE와 함께 `200 OK`이면 Streamable HTTP.
3. 응답이 `Content-Type: text/event-stream` 및 보조 엔드포인트를 가리키는 `Location` 헤더와 함께 `200 OK`이면 레거시 HTTP+SSE; `Location`을 따름.

### Cloudflare, ngrok 및 호스팅

2026년 프로덕션 원격 MCP 서버는 Cloudflare Workers(MCP Agents SDK 사용), Vercel Functions 또는 컨테이너화된 Node/Python에서 실행됩니다. 핵심: 호스팅이 SSE GET을 위한 장기 HTTP 연결을 지원해야 합니다. Vercel의 무료 티어는 10초로 제한되어 부적합. Cloudflare Workers는 무제한 스트림을 지원합니다.

### 게이트웨이 구성

여러 MCP 서버를 게이트웨이(13단계 17과) 앞에 둘 때, 게이트웨이는 세션 ID를 재작성하고 업스트림을 다중화하는 단일 Streamable HTTP 엔드포인트입니다. 도구는 게이트웨이 계층에서 병합됩니다; 클라이언트는 단일 논리적 서버를 봅니다.

### 전송 실패 모드

- **stdio SIGPIPE.** 쓰기 중 자식 프로세스 사망이 SIGPIPE 발생; 서버는 깔끔하게 종료해야 함. 클라이언트는 EOF를 감지하고 세션을 죽은 것으로 표시해야 함.
- **HTTP 502 / 504.** Cloudflare, nginx 및 기타 프록시가 업스트림 실패 시 이를 출력. Streamable HTTP 클라이언트는 짧은 백오프 후 한 번 재시도해야 함.
- **SSE 연결 끊김.** TCP RST, 프록시 타임아웃 또는 클라이언트 네트워크 변경으로 스트림 종료. 클라이언트가 `Mcp-Session-Id` 및 선택적 `last-event-id`로 재연결하여 재개.
- **세션 취소.** 서버가 세션 ID를 무효화; 클라이언트가 다음 요청에서 404 확인. 클라이언트가 재핸드셰이크해야 함.
- **시계 불일치.** 클라이언트의 리소스-TTL 계산이 서버와 차이. 클라이언트는 서버 타임스탬프를 권위 있는 것으로 간주해야 함.

### Streamable HTTP를 우회해야 할 때

일부 기업은 자체 네트워크 내부에서 gRPC 또는 메시지 큐 전송 뒤에 MCP 서버를 배포합니다. 이것은 비표준입니다 — MCP의 사양이 공식적으로 정의하지 않습니다. 게이트웨이는 내부적으로 gRPC를 사용하면서 MCP 클라이언트에 Streamable HTTP 표면을 노출할 수 있습니다. 외부 표면을 사양 준수로 유지; 게이트웨이가 변환을 담당합니다.

## 사용하기

`code/main.py`는 `http.server`(표준 라이브러리)를 사용하여 최소 Streamable HTTP 엔드포인트를 구현합니다. `/mcp`에서 POST, GET 및 DELETE를 처리하고, 첫 번째 응답에 `Mcp-Session-Id`를 설정하며, `Origin`을 검증하고, 허용 목록에 없는 출처의 요청을 거부합니다. 핸들러는 07과 노트 서버의 디스패치 로직을 재사용합니다.

살펴볼 내용:

- POST 핸들러가 JSON-RPC 본문을 읽고, 디스패치하고, JSON 응답을 씁니다(단일 응답 변형; SSE 변형은 구조적으로 유사).
- `Origin` 검사가 기본 `http://evil.example` 프로브를 거부하지만 `http://localhost`는 수락.
- 세션 ID는 무작위 128비트 16진수 문자열; 서버는 세션별 상태를 메모리에 유지.

## 배포하기

이 레슨은 `outputs/skill-mcp-transport-migrator.md`를 생성합니다. HTTP+SSE(레거시) MCP 서버가 주어지면 스킬이 세션 ID 연속성, Origin 검사 및 이전 버전 호환 프로브 지원이 포함된 Streamable HTTP로의 마이그레이션 계획을 생성합니다.

## 실습

1. `code/main.py`를 실행하세요. `curl`에서 `initialize`를 POST하고 `Mcp-Session-Id` 응답 헤더를 관찰하세요. 헤더를 반영하여 두 번째 요청을 POST하고 세션 연속성을 확인하세요.

2. SSE 스트림을 여는 GET 핸들러를 추가하세요. 5초마다 하나의 `notifications/progress` 이벤트를 보내세요. 동일한 세션 ID로 GET을 다시 보내 재연결하고 서버가 수락하는지 확인하세요.

3. `last-event-id` 재생 로직을 구현하세요. 재연결 시 해당 ID 이후에 생성된 모든 이벤트를 재생하세요.

4. `Origin` 검증을 와일드카드 패턴(`https://*.example.com`)을 지원하도록 확장하고 `https://app.example.com`은 수락하지만 `https://evil.example.com.attacker.net`은 거부하는지 확인하세요.

5. 공식 레지스트리에서 레거시 HTTP+SSE 서버(여러 개 있음)를 가져와 마이그레이션을 스케치하세요: 엔드포인트 처리, 세션 ID 생성 및 헤더 의미론에서 무엇이 변경되나요?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| stdio 전송 | "로컬 자식 프로세스" | stdin/stdout을 통한 JSON-RPC, 개행 구분 |
| Streamable HTTP | "원격 전송" | 단일 엔드포인트 POST + GET + 선택적 SSE, 2025-03-26 사양 |
| HTTP+SSE | "레거시" | 2026년 중반 제거 예정인 두 엔드포인트 모델 |
| `Mcp-Session-Id` | "세션 헤더" | 서버가 할당한 무작위 ID, 모든 후속 요청에 반영됨 |
| `Origin` 허용 목록 | "DNS-리바인딩 방어" | 출처가 승인되지 않은 요청 거부 |
| 단일 엔드포인트 | "하나의 URL" | `/mcp`가 모든 세션 작업에 대해 POST / GET / DELETE 처리 |
| `last-event-id` | "SSE 재생" | 놓친 이벤트 없이 끊긴 스트림 재개에 사용되는 헤더 |
| 이전 버전 호환 프로브 | "이전 vs 새 감지" | 전송을 자동 선택하는 클라이언트 응답 형태 검사 |
| 장기 HTTP | "SSE 스트리밍" | 서버가 하나의 TCP 연결에서 몇 분 또는 몇 시간 동안 이벤트 푸시 |
| 세션 취소 | "강제 재초기화" | 서버가 세션 ID 무효화; 클라이언트가 다시 핸드셰이크해야 함 |

## 추가 자료

- [MCP — Basic transports spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) — stdio 및 Streamable HTTP에 대한 표준 참조
- [MCP — Basic transports spec 2025-03-26](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) — Streamable HTTP를 도입한 개정판
- [Cloudflare — MCP transport](https://developers.cloudflare.com/agents/model-context-protocol/transport/) — Workers 호스팅 Streamable HTTP 패턴
- [AWS — MCP transport mechanisms](https://builder.aws.com/content/35A0IphCeLvYzly9Sw40G1dVNzc/mcp-transport-mechanisms-stdio-vs-streamable-http) — 배포 형태별 비교
- [Atlassian — HTTP+SSE deprecation notice](https://community.atlassian.com/forums/Atlassian-Remote-MCP-Server/HTTP-SSE-Deprecation-Notice/ba-p/3205484) — 구체적인 마이그레이션 기한 예시
