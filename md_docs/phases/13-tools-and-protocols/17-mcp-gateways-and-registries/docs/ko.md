# MCP 게이트웨이와 레지스트리 — 엔터프라이즈 컨트롤 플레인

> 기업은 모든 개발자가 임의의 MCP 서버를 설치하도록 할 수 없습니다. 게이트웨이는 인증, RBAC, 감사, 속도 제한, 캐싱 및 도구 중독 탐지를 중앙화한 다음 병합된 도구 표면을 단일 MCP 엔드포인트로 노출합니다. 공식 MCP 레지스트리(Anthropic + GitHub + PulseMCP + Microsoft, 네임스페이스 확인)는 표준 업스트림입니다. 이 레슨은 게이트웨이가 어디에 맞는지 명명하고, 최소 구현을 살펴보며, 2026년 벤더 환경을 조사합니다.

**Type:** 학습
**Languages:** Python (표준 라이브러리, 최소 게이트웨이)
**Prerequisites:** 13단계 15과 (도구 중독), 13단계 16과 (OAuth 2.1)
**Time:** 약 45분

## 학습 목표

- MCP 게이트웨이가 어디에 위치하는지(MCP 클라이언트와 여러 백엔드 MCP 서버 사이) 설명할 수 있다.
- 다섯 가지 게이트웨이 책임(인증, RBAC, 감사, 속도 제한, 정책)을 구현할 수 있다.
- 게이트웨이 계층에서 고정 도구 해시 매니페스트를 적용할 수 있다.
- 공식 MCP 레지스트리와 메타레지스트리(Glama, MCPMarket, MCP.so, Smithery, LobeHub)를 구분할 수 있다.

## 문제

Fortune 500 기업은 30개의 승인된 MCP 서버, 5000명의 개발자, 규정 준수 및 감사 요구사항, 중앙화된 정책을 원하는 보안 팀이 있습니다. 모든 개발자가 IDE에 임의의 서버를 설치하도록 하는 것은 불가능합니다.

게이트웨이 패턴:

1. 게이트웨이가 개발자가 연결하는 단일 Streamable HTTP 엔드포인트로 실행.
2. 게이트웨이가 각 백엔드 MCP 서버에 대한 자격 증명 보유.
3. 모든 개발자 요청이 게이트웨이 자체 OAuth를 통해 인증 및 범위 지정.
4. 게이트웨이가 정책을 적용하여 백엔드 서버로 요청 라우팅.
5. 모든 호출이 감사를 위해 기록.

Cloudflare MCP Portals, Kong AI Gateway, IBM ContextForge, MintMCP, TrueFoundry, Envoy AI Gateway — 모두 2025-2026년에 게이트웨이 또는 게이트웨이 기능을 출시.

한편, 공식 MCP 레지스트리는 표준 업스트림으로 출시: 큐레이션, 네임스페이스 확인, 게이트웨이가 가져올 수 있는 역방향 DNS 명명 서버. 메타레지스트리(Glama, MCPMarket, MCP.so, Smithery, LobeHub)는 여러 소스의 서버를 집계.

## 개념

### 다섯 가지 게이트웨이 책임

1. **인증.** OAuth 2.1로 개발자 식별; 사용자 역할에 매핑.
2. **RBAC.** 사용자별 정책: 어떤 서버, 어떤 도구, 어떤 범위.
3. **감사.** 모든 호출이 누가, 무엇을, 언제, 결과와 함께 기록.
4. **속도 제한.** 사용자별 / 도구별 / 서버별 상한으로 남용 방지.
5. **정책.** 중독된 설명 거부, Rule of Two 적용, PII 삭제.

### 게이트웨이를 단일 엔드포인트로

개발자에게 게이트웨이는 하나의 MCP 서버처럼 보임. 내부적으로 N개의 백엔드로 라우팅. 세션 ID(13단계 09과)는 경계에서 재작성됨.

### 자격 증명 금고

개발자는 백엔드 토큰을 절대 보지 못함. 게이트웨이가 보유(또는 자격 증명을 보유한 IdP에 프록시). 게이트웨이에서 `notes:read` 권한이 있는 개발자는 게이트웨이 자체 백엔드 자격 증명으로 노트 MCP 서버에 전이적으로 접근 가능 — 그러나 전이적 접근을 바인딩하는 정책 하에서만.

### 게이트웨이의 도구 해시 고정

게이트웨이가 승인된 도구 설명의 매니페스트(SHA256 해시) 보유. 검색 시 각 백엔드의 `tools/list`를 가져와 매니페스트와 해시 비교, 설명이 변이된 도구 제거. 이것이 13단계 15과의 rug pull 방어를 중앙에서 적용.

### 정책-애즈-코드

고급 게이트웨이는 OPA/Rego, Kyverno 또는 Styra에서 정책 표현. "사용자 `alice`는 `acme` 조직의 저장소에서만 `github.open_pr`을 호출할 수 있음" 같은 규칙이 선언적으로 인코딩. 단순 게이트웨이는 수제 Python 사용. 두 형태 모두 유효.

### 세션 인식 라우팅

사용자의 세션이 서버 혼합을 포함할 때 게이트웨이가 다중화: 개발자의 단일 MCP 세션이 서버당 하나씩 N개의 백엔드 세션 보유. 모든 백엔드의 알림이 게이트웨이를 통해 개발자의 세션으로 라우팅.

### 네임스페이스 병합

게이트웨이가 모든 백엔드의 도구 네임스페이스를 병합, 일반적으로 충돌 시 접두사 사용. `github.open_pr`, `notes.search`. 이렇게 하면 라우팅이 명확.

### 레지스트리

- **공식 MCP 레지스트리 (`registry.modelcontextprotocol.io`).** Anthropic, GitHub, PulseMCP, Microsoft 관리 하에 출시. 네임스페이스 확인(역방향 DNS: `io.github.user/server`). 기본 품질에 대해 사전 필터링.
- **Glama.** 검색 중심 메타레지스트리, 여러 소스 집계.
- **MCPMarket.** 상업적 성향의 디렉토리, 벤더 목록 포함.
- **MCP.so.** 커뮤니티 디렉토리; 공개 제출.
- **Smithery.** 패키지 관리자 스타일 설치 흐름.
- **LobeHub.** LobeChat 앱에 통합된 UI 레지스트리.

엔터프라이즈 게이트웨이는 기본적으로 공식 레지스트리에서 가져오고, 메타레지스트리의 관리자 큐레이션 추가를 허용하며, 고정되지 않은 것은 거부.

### 역방향 DNS 명명

공식 레지스트리는 공개 서버에 대해 역방향 DNS 이름을 의무화: `io.github.alice/notes`. 네임스페이스는 스쿼팅을 방지하고 신뢰 위임을 명확하게 함.

### 벤더 설문조사, 2026년 4월

| 벤더 | 강점 |
|--------|----------|
| Cloudflare MCP Portals | 엣지 호스팅; OAuth 통합; 무료 티어 |
| Kong AI Gateway | K8s 네이티브; 세분화된 정책; OpenTelemetry 로그 |
| IBM ContextForge | 엔터프라이즈 IAM; 규정 준수; 감사 내보내기 |
| TrueFoundry | DevOps 중심; 메트릭 우선 |
| MintMCP | 개발자 플랫폼 지향 |
| Envoy AI Gateway | 오픈 소스; 커스터마이즈 가능한 필터 |

17단계(프로덕션 인프라)는 게이트웨이 운영을 더 깊이 다룹니다.

## 사용하기

`code/main.py`는 약 150줄의 최소 게이트웨이 제공: 가짜 Bearer 토큰으로 사용자 인증, 사용자별 RBAC 정책 보유, 두 백엔드 MCP 서버로 요청 라우팅, 모든 호출을 감사 로그에 기록, 속도 제한 적용, 설명 해시가 고정 매니페스트와 일치하지 않는 백엔드 도구 거부.

살펴볼 내용:

- `user_id`를 키로 하고 허용된 `server_tool` 항목이 있는 `RBAC` 딕셔너리.
- `AUDIT_LOG`는 추가 전용 이벤트 목록.
- 속도 제한은 사용자당 토큰 버킷 사용.
- 고정 매니페스트는 `server::tool -> hash`의 딕셔너리.

## 배포하기

이 레슨은 `outputs/skill-gateway-bootstrap.md`를 생성합니다. 엔터프라이즈 MCP 계획(사용자, 백엔드, 규정 준수)이 주어지면 스킬이 게이트웨이 구성 사양을 생성합니다.

## 실습

1. `code/main.py`를 실행하세요. 허용된 사용자, 허용되지 않은 사용자, 속도 제한 초과 버스트로 각각 호출하세요. 세 가지 흐름을 모두 확인하세요.

2. 결과를 클라이언트에 반환하기 전에 PII를 삭제하는 정책을 추가하세요. SSN 형태 문자열에 대한 간단한 정규식 패스를 사용하세요; 격차(이메일, 전화번호)를 기록하세요.

3. 감사 로그를 확장하여 OpenTelemetry GenAI 스팬을 출력하세요. 13단계 20과가 정확한 속성을 다룹니다.

4. 5개의 백엔드(notes, github, postgres, jira, slack)가 있는 50명 개발자 팀을 위한 RBAC 정책을 설계하세요. 각각에 대해 누가 읽기 전용이고 누가 쓰기 권한이 있나요?

5. Cloudflare 엔터프라이즈 MCP 포스트를 처음부터 끝까지 읽으세요. Cloudflare가 제공하지만 이 stdlib 게이트웨이는 제공하지 않는 기능을 식별하세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 게이트웨이(Gateway) | "MCP 프록시" | 클라이언트와 백엔드 사이를 중앙화하는 서버 |
| 자격 증명 금고(Credential vaulting) | "백엔드 토큰은 서버 측에 유지" | 개발자가 업스트림 토큰을 절대 보지 못함 |
| 세션 인식 라우팅(Session-aware routing) | "다중 백엔드 세션" | 게이트웨이가 개발자 세션당 N개의 백엔드 세션 다중화 |
| 도구 해시 고정(Tool-hash pinning) | "승인된 매니페스트" | 모든 승인된 도구 설명의 SHA256; rug pull 중앙 차단 |
| RBAC | "사용자별 정책" | 도구 및 서버에 대한 역할 기반 접근 제어 |
| 정책-애즈-코드(Policy-as-code) | "선언적 규칙" | 게이트웨이에서 적용되는 OPA/Rego, Kyverno, Styra 정책 |
| 감사 로그(Audit log) | "누가, 무엇을, 언제" | 규정 준수를 위한 추가 전용 이벤트 로그 |
| 속도 제한(Rate limit) | "사용자당 토큰 버킷" | 남용 방지를 위한 분당 상한 |
| 공식 MCP 레지스트리(Official MCP Registry) | "표준 업스트림" | `registry.modelcontextprotocol.io`, 네임스페이스 확인 |
| 역방향 DNS 명명(Reverse-DNS naming) | "레지스트리 네임스페이스" | `io.github.user/server` 규칙 |

## 추가 자료

- [Official MCP Registry](https://registry.modelcontextprotocol.io/) — 표준 업스트림, 네임스페이스 확인
- [Cloudflare — Enterprise MCP](https://blog.cloudflare.com/enterprise-mcp/) — OAuth 및 정책이 있는 게이트웨이 패턴
- [agentic-community — MCP gateway registry](https://github.com/agentic-community/mcp-gateway-registry) — 오픈 소스 참조 게이트웨이
- [TrueFoundry — What is an MCP gateway?](https://www.truefoundry.com/blog/what-is-mcp-gateway) — 기능 비교 기사
- [IBM — MCP context forge](https://github.com/IBM/mcp-context-forge) — IBM의 엔터프라이즈 게이트웨이
