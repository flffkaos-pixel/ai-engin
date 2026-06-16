# MCP 보안 II — OAuth 2.1, 리소스 표시기, 증분 범위

> 원격 MCP 서버는 인증뿐만 아니라 권한 부여도 필요합니다. 2025-11-25 사양은 OAuth 2.1 + PKCE + 리소스 표시기(RFC 8707) + 보호 리소스 메타데이터(RFC 9728)와 정렬됩니다. SEP-835은 403 WWW-Authenticate에 대한 단계적 권한 상승과 함께 증분 범위 동의를 추가합니다. 이 레슨은 단계적 상승 흐름을 상태 머신으로 구현하여 모든 홉을 볼 수 있게 합니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, OAuth 상태 머신 시뮬레이터)
**Prerequisites:** 13단계 09과 (전송), 13단계 15과 (보안 I)
**Time:** 약 75분

## 학습 목표

- 리소스 서버와 권한 부여 서버의 책임을 구분할 수 있다.
- PKCE 보호 OAuth 2.1 권한 부여 코드 흐름을 살펴볼 수 있다.
- `resource`(RFC 8707) 및 보호 리소스 메타데이터(RFC 9728)를 사용하여 혼동된 부관 공격을 방지할 수 있다.
- 단계적 권한 상승을 구현할 수 있다: 서버가 403과 WWW-Authenticate로 더 높은 범위를 요청; 클라이언트가 사용자 동의를 다시 묻고 재시도.

## 문제

초기 MCP(2025년 이전)는 임시 API 키 또는 심지어 인증 없이 원격 서버를 출시했습니다. 2025-11-25 사양은 전체 OAuth 2.1 프로파일로 그 격차를 메웁니다.

세 가지 실제 요구사항:

- **일반 원격 서버.** 사용자가 Notion / GitHub / Gmail에 접근하는 원격 MCP 서버를 설치. PKCE가 있는 OAuth 2.1이 올바른 형태.
- **범위 확대.** `notes:read`가 부여된 노트 서버가 특정 액션에 대해 나중에 `notes:write`가 필요. 전체 흐름을 다시 하는 대신 단계적 상승(SEP-835)이 추가 범위를 요청.
- **혼동된 부관 방지.** 클라이언트가 서버 A에 대해 범위가 지정된 토큰을 보유. 서버 A가 악성이며 토큰을 서버 B에 제시하려고 함. 리소스 표시기(RFC 8707)가 토큰을 의도된 수신자에게 고정.

OAuth 2.1은 새롭지 않습니다. 새로운 것은 MCP의 프로파일입니다: 특정 필수 흐름(권한 부여 코드 + PKCE만; 암시적 없음, 기본적으로 클라이언트 자격 증명 없음), 모든 토큰 요청에 리소스 표시기 필수, 클라이언트가 어디로 가야 하는지 알 수 있도록 보호 리소스 메타데이터 게시.

## 개념

### 역할

- **클라이언트.** MCP 클라이언트(Claude Desktop, Cursor 등).
- **리소스 서버.** MCP 서버(노트, GitHub, Postgres 등).
- **권한 부여 서버.** 토큰 발급. 리소스 서버와 동일한 서비스이거나 별도 IdP(Auth0, Keycloak, Cognito)일 수 있음.

MCP의 프로파일에서 리소스 및 권한 부여 서버는 동일한 호스트일 수 있지만 SHOULD는 URL로 구분되어야 함.

### 권한 부여 코드 + PKCE

흐름:

1. 클라이언트가 `code_verifier`(무작위) 및 `code_challenge`(SHA256) 생성.
2. 클라이언트가 사용자를 `/authorize?response_type=code&client_id=...&redirect_uri=...&scope=notes:read&code_challenge=...&resource=https://notes.example.com`으로 리디렉션.
3. 사용자 동의. 권한 부여 서버가 `redirect_uri?code=...`로 리디렉션.
4. 클라이언트가 `/token?grant_type=authorization_code&code=...&code_verifier=...&resource=...`로 POST.
5. 권한 부여 서버가 검증자의 해시를 저장된 challenge와 비교하고 액세스 토큰 발급.
6. 클라이언트가 리소스 서버에 대한 모든 요청에 토큰 사용: `Authorization: Bearer ...`.

PKCE는 권한 부여 코드 가로채기 공격을 방지. 리소스 표시기는 토큰이 다른 곳에서 유효하지 않도록 방지.

### 보호 리소스 메타데이터 (RFC 9728)

리소스 서버가 `.well-known/oauth-protected-resource` 문서 게시:

```json
{
  "resource": "https://notes.example.com",
  "authorization_servers": ["https://auth.example.com"],
  "scopes_supported": ["notes:read", "notes:write", "notes:delete"]
}
```

클라이언트가 리소스 서버로부터 권한 부여 서버를 검색. 구성 감소 — 클라이언트는 리소스 URL만 필요.

### 리소스 표시기 (RFC 8707)

토큰 요청의 `resource` 파라미터가 토큰의 의도된 수신자를 고정. 발급된 토큰에는 `aud: "https://notes.example.com"`이 포함됨. 이 토큰을 받는 다른 MCP 서버는 `aud`를 확인하고 거부.

### 범위 모델

범위는 공백으로 구분된 문자열. 일반적인 MCP 규칙:

- `notes:read`, `notes:write`, `notes:delete`
- `admin:*` (관리자 기능, 절약해서 사용)
- `profile:read` (신원)

범위 선택은 최소 권한이어야 함: 지금 필요한 것만 요청, 더 필요할 때 단계적 상승.

### 단계적 권한 상승 (SEP-835)

사용자가 `notes:read` 부여. 나중에 노트를 삭제하도록 에이전트에 요청. 서버가 응답:

```
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope",
    scope="notes:delete", resource="https://notes.example.com"
```

클라이언트가 insufficient_scope 오류를 확인하고, 추가 범위에 대한 동의 대화상자로 사용자에게 프롬프트하고, 이에 대한 미니 OAuth 흐름을 수행하고, 새 토큰으로 요청 재시도.

### 토큰 수신자 검증

모든 요청: 서버가 `token.aud == self.resource_url` 확인. 불일치 = 401. 이것이 교차 서버 토큰 재사용을 중단.

### 단기 토큰 및 갱신

액세스 토큰은 SHOULD 단기(기본 1시간). 갱신 토큰은 모든 갱신마다 교체. 클라이언트가 백그라운드에서 조용히 갱신 처리.

### 토큰 패스스루 없음

샘플링 서버(13단계 11과)는 MUST NOT 클라이언트의 토큰을 다른 서비스로 전달. 샘플링 요청이 경계.

### 혼동된 부관 방지

토큰이 `aud`에 바인딩. 클라이언트가 `client_id`에 바인딩. 모든 요청이 둘 다에 대해 검증. 사양은 MCP 이전 원격 도구 생태계에서 흔했던 이전 "토큰 전달" 패턴을 명시적으로 금지.

### 클라이언트 ID 검색

각 MCP 클라이언트가 고정 URL에 메타데이터 게시. 권한 부여 서버가 클라이언트의 메타데이터 문서를 가져와 리디렉션 URI 및 연락처 정보를 검색 가능. 이는 수동 클라이언트 등록을 제거.

### 게이트웨이 및 OAuth

13단계 17과는 엔터프라이즈 게이트웨이가 OAuth를 처리하는 방법을 보여줌: 게이트웨이가 업스트림 서버에 대한 자격 증명 보유, 클라이언트에 대한 토큰은 게이트웨이 발급, 업스트림 토큰은 게이트웨이를 떠나지 않음. 이는 신뢰 모델을 뒤집음 — 사용자가 게이트웨이에 한 번 인증; 게이트웨이가 N개의 서버 권한 부여를 처리.

## 사용하기

`code/main.py`는 전체 OAuth 2.1 단계적 상승 흐름을 상태 머신으로 시뮬레이션. 구현:

- PKCE 코드 검증자 / challenge 생성.
- 리소스 표시기가 있는 권한 부여 코드 흐름.
- 보호 리소스 메타데이터 엔드포인트.
- 수신자 확인이 있는 토큰 검증.
- `insufficient_scope`에 대한 단계적 상승.

이 레슨에는 HTTP 서버 없음; 상태 머신이 메모리에서 실행되어 모든 홉을 추적 가능. 13단계 17과의 게이트웨이 레슨이 이를 실제 전송에 연결.

## 배포하기

이 레슨은 `outputs/skill-oauth-scope-planner.md`를 생성합니다. 도구가 있는 원격 MCP 서버가 주어지면 스킬이 범위 집합, 고정 규칙 및 단계적 상승 정책을 설계합니다.

## 실습

1. `code/main.py`를 실행하세요. 두 범위 단계적 상승 흐름을 추적하세요. 단계적 상승 시 어떤 홉이 반복되는지 기록하세요.

2. 갱신 토큰 교체 추가: 모든 갱신이 새 갱신 토큰 발급 및 이전 토큰 무효화. 교체 후 도난된 갱신 토큰 사용을 시뮬레이션하고 실패 확인.

3. stdlib http.server를 사용하여 보호 리소스 메타데이터 엔드포인트를 실제 HTTP 응답으로 구현. 09과의 /mcp 엔드포인트 미러링.

4. GitHub MCP 서버를 위한 범위 계층 설계: repo 읽기, PR 쓰기, PR 승인, PR 병합, 관리자. 각 수준 사이에 단계적 상승 사용.

5. RFC 8707 및 RFC 9728 읽기. MCP가 RFC의 예제와 다르게 사용하는 9728의 필드 식별. (힌트: `scopes_supported` 관련.)

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| OAuth 2.1 | "최신 OAuth" | PKCE를 의무화하고 암시적 흐름을 금지하는 통합 RFC |
| PKCE | "소유 증명" | 코드 검증자 + challenge이 권한 부여 코드 가로채기 방어 |
| 리소스 표시기(Resource indicator) | "토큰 수신자" | RFC 8707 `resource` 파라미터, 토큰을 하나의 서버에 고정 |
| 보호 리소스 메타데이터 | "검색 문서" | RFC 9728 `.well-known/oauth-protected-resource` |
| 단계적 권한 상승(Step-up authorization) | "증분 동의" | 필요 시 범위를 추가하는 SEP-835 흐름 |
| `insufficient_scope` | "403 with WWW-Authenticate" | 더 큰 범위를 위해 재동의하라는 서버 신호 |
| 혼동된 부관(Confused deputy) | "서비스 간 토큰 재사용" | 신뢰할 수 있는 보유자가 부적절하게 토큰을 전달하는 공격 |
| 단기 토큰(Short-lived token) | "액세스 토큰 TTL" | 빠르게 만료되는 Bearer; 갱신 토큰이 갱신 |
| 범위 계층(Scope hierarchy) | "최소 권한 스택" | 수준 간 단계적 상승이 있는 점진적 범위 집합 |
| 클라이언트 ID 메타데이터 | "클라이언트 검색 문서" | 클라이언트가 자체 OAuth 메타데이터를 게시하는 URL |

## 추가 자료

- [MCP — Authorization spec](https://modelcontextprotocol.io/specification/draft/basic/authorization) — 표준 MCP OAuth 프로파일
- [den.dev — MCP November authorization spec](https://den.dev/blog/mcp-november-authorization-spec/) — 2025-11-25 변경 사항 워크스루
- [RFC 8707 — Resource indicators for OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc8707) — 수신자 고정 RFC
- [RFC 9728 — OAuth 2.0 protected resource metadata](https://datatracker.ietf.org/doc/html/rfc9728) — 검색 문서 RFC
- [Aembit — MCP OAuth 2.1, PKCE and the future of AI authorization](https://aembit.io/blog/mcp-oauth-2-1-pkce-and-the-future-of-ai-authorization/) — 실용적인 단계적 상승 흐름 워크스루
