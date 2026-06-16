# 프로덕션 MCP 인증 — 등록, JWKS 갱신, 수신자 고정 토큰

> 16과는 OAuth 2.1 상태 머신을 메모리에 구축했습니다. 2026년에는 실제 조직에 출시하는 모든 MCP 서버가 프로덕션 인증 뒤에 있습니다: 무제한 클라이언트 인구로 확장되는 클라이언트 등록(Client ID Metadata Documents 우선, 동적 클라이언트 등록은 이전 버전 호환 대체), 권한 부여 서버 메타데이터 검색(RFC 8414 *또는* OpenID Connect Discovery), 오전 3시 토큰 검증을 망가뜨리지 않는 JWKS 캐시 갱신, 교차 리소스 재생을 거부하는 수신자 고정 토큰. 이 레슨은 권한 부여 서버, 리소스 서버(MCP 서버) 및 클라이언트의 세 가지 역할로 전체 표면을 모델링하여 검증된 도구 호출까지 모든 홉을 추적할 수 있게 합니다.

> **사양 참고 (2025-11-25):** 2025년 11월 MCP 권한 부여 사양은 동적 클라이언트 등록을 `SHOULD`에서 `MAY`로 낮추고 **Client ID Metadata Documents (CIMD)** 를 권장 기본 등록 메커니즘으로 만들었습니다. 이 레슨은 사양의 우선순위 순서대로 둘 다 가르치며, 코드는 DCR이 하나의 프로세스에서 완전히 자체 포함되어 있기 때문에 워크스루용으로 유지합니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리)
**Prerequisites:** 13단계 16과 (OAuth 2.1 상태 머신), 13단계 17과 (게이트웨이)
**Time:** 약 90분

## 학습 목표

- RFC 8414 메타데이터를 통해 권한 부여 서버를 검색하고 계약을 확인할 수 있다.
- RFC 7591 동적 클라이언트 등록을 구현하여 MCP 클라이언트가 관리자 개입 없이 등록할 수 있게 할 수 있다.
- 예약된 일정에 따라 JWKS 키를 캐시하고 갱신하여 서명 검증이 키 교체를 견딜 수 있게 할 수 있다.
- RFC 8707 리소스 표시기를 사용하여 토큰을 단일 MCP 리소스에 고정하고 혼동된 부관 재사용을 거부할 수 있다.
- 세 가지 역할을 깔끔하게 분리(권한 부여 서버, 리소스 서버, 클라이언트)하여 각각이 자신에게 속한 검사만 적용하도록 할 수 있다.
- IdP 기능 매트릭스를 읽고 IdP가 MCP의 인증 프로파일을 만족할 수 없을 때 배포를 거부할 수 있다.

## 문제

16과 시뮬레이터는 OAuth 2.1을 메모리에서 실행합니다. 프로덕션에는 메모리 전용 시뮬레이터가 보지 못하는 세 가지 운영 격차가 있습니다.

첫 번째 격차는 등록입니다. 실제 조직은 수백 개의 MCP 서버와 수천 개의 MCP 클라이언트를 운영합니다. 운영자가 모든 Cursor 사용자를 OAuth 클라이언트로 수동 등록하지 않습니다. 2025-11-25 사양은 클라이언트에게 이를 해결하기 위한 우선순위 순서를 제공합니다: 기존 `client_id`가 있으면 사용, 없으면 **Client ID Metadata Document** 사용(클라이언트가 제어하는 HTTPS URL로 자신을 식별하고 권한 부여 서버가 메타데이터를 *가져옴*), 그 외에는 **RFC 7591 동적 클라이언트 등록**으로 대체(클라이언트가 `POST /register`를 *푸시*하고 즉시 `client_id`를 받음), 마지막으로 사용자에게 프롬프트. CIMD는 서버별 등록을 완전히 제거하면서 DNS에 기반한 신뢰 모델을 유지하기 때문에 권장 기본값입니다; DCR은 이전 버전 호환성을 위해 유지됩니다. 둘 다 권한 부여 서버의 메타데이터에서 진입점을 검색합니다: CIMD용 `client_id_metadata_document_supported`, DCR용 `registration_endpoint`.

두 번째 격차는 키 교체입니다. JWT 검증은 권한 부여 서버의 서명 키(JSON Web Key Set으로 게시됨)에 의존합니다. 권한 부여 서버는 예약된 일정에 따라 이를 교체합니다(종종 매시간, 때로는 인시던트 대응 하에 더 빠르게). 한 번 부팅 시 JWKS를 가져오는 MCP 서버는 교체 기간까지 잘 검증합니다 — 그 후 매 요청이 재시작까지 실패합니다. 프로덕션은 JWKS를 캐시된 값으로 연결하고 이전 키가 만료되기 전에 캐시를 덮어쓰는 갱신 작업을 추가하며, 캐시 미스 시 캐시보다 최신 키로 서명된 토큰이 도착하는 경우를 대비한 폴백 가져오기를 추가합니다.

세 번째 격차는 수신자 바인딩입니다. 16과는 RFC 8707 리소스 표시기를 소개했습니다. 프로덕션에서 이 표시기는 모든 요청에 대한 하드 클레임 검사가 됩니다. MCP 서버는 `token.aud`를 자체 표준 리소스 URL과 비교하고 불일치 시 HTTP 401로 거부합니다. 이것이 업스트림 MCP 서버(또는 한 서버용 토큰을 보유한 악성 클라이언트)가 동일한 신뢰 메시의 다른 서버에 대해 해당 토큰을 재생하는 것을 방지하는 유일한 방어입니다.

이 레슨은 각 격차를 표면의 구체적인 조각에 매핑합니다. 메타데이터 문서는 HTTP 엔드포인트입니다. JWKS 캐시 갱신은 예약된 작업과 키-값 캐시입니다. JWT 검증은 리소스 서버가 도구를 디스패치하기 전에 실행하는 루틴입니다. 세 가지 역할을 분리하고 각각이 자신이 소유한 검사만 적용합니다: 권한 부여 서버는 키를 발급하고 교체하며, 리소스 서버는 캐시하고 검증하며, 클라이언트는 검색하고 등록합니다.

## 개념

### RFC 8414 — OAuth 권한 부여 서버 메타데이터

`/.well-known/oauth-authorization-server`의 문서가 클라이언트에 필요한 모든 것을 설명:

```json
{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/token",
  "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
  "registration_endpoint": "https://auth.example.com/register",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "scopes_supported": ["mcp:tools.read", "mcp:tools.invoke"],
  "token_endpoint_auth_methods_supported": ["none", "private_key_jwt"]
}
```

MCP 리소스 URL이 주어진 클라이언트는 검색 체인을 연결: RFC 9728의 `oauth-protected-resource`(리소스 서버의 문서)가 발급자를 명명, 그런 다음 `oauth-authorization-server`(이 RFC)가 모든 엔드포인트를 명명. 클라이언트는 권한 부여 URL을 하드코딩하지 않음.

MCP용 IdP를 신뢰하기 전에 확인하는 계약:

- `code_challenge_methods_supported`에 `S256` 포함(PKCE per RFC 7636). 사양은 명시적: 이 필드가 **없으면** 권한 부여 서버가 PKCE를 지원하지 않으며 클라이언트는 **MUST** 진행을 거부.
- `grant_types_supported`에 `authorization_code` 포함, `password` 및 `implicit` 거부.
- 최소한 하나의 등록 경로가 광고됨: `client_id_metadata_document_supported: true` (CIMD, 선호) **또는** `registration_endpoint` (RFC 7591 DCR, 대체). 둘 중 하나가 계약을 충족; 더 이상 DCR을 하드 요구하지 않음.
- `response_types_supported`는 OAuth 2.1에 대해 정확히 `["code"]`.

`S256`가 없으면 MCP 서버는 이 IdP에 대해 배포를 거부 — PKCE에는 저하된 모드가 없음. *어느* 등록 경로도 광고되지 않고 사전 등록된 `client_id`도 없으면 등록할 수 없음; 배포 매니페스트가 잘못된 것이지 코드가 아님.

### RFC 9728 (요약) — 보호 리소스 메타데이터

16과가 RFC 9728을 다루었음. 프로덕션에서의 차이점: 이 문서는 클라이언트가 *이* MCP 서버가 신뢰하는 권한 부여 서버를 찾는 유일한 장소. 단일 MCP 서버는 여러 IdP(직원용 하나, 파트너용 하나)의 토큰을 수락할 수 있음. RFC 9728이 그 집합을 선언; RFC 8414가 각 IdP가 지원하는 것을 문서화.

```json
{
  "resource": "https://notes.example.com",
  "authorization_servers": ["https://auth.example.com", "https://partners.example.com"],
  "scopes_supported": ["mcp:tools.invoke"],
  "bearer_methods_supported": ["header"],
  "resource_documentation": "https://notes.example.com/docs"
}
```

### Client ID Metadata Documents (권장 기본값)

CIMD는 등록을 *푸시*에서 *풀*로 역전시킴. 권한 부여 서버에 `client_id`를 발급받도록 요청하는 대신, 클라이언트가 제어하는 HTTPS URL을 `client_id`**로** 사용. URL이 JSON 메타데이터 문서로 확인됨; 권한 부여 서버가 OAuth 흐름 중에 필요 시 가져옴. 신뢰는 DNS에 기반: 서버 운영자가 `app.example.com`을 신뢰하면 `https://app.example.com/client.json`에서 제공되는 클라이언트를 신뢰. 등록 왕복 없음, `client_id` 네임스페이스 고갈 없음, 동기화할 서버별 상태 없음.

클라이언트가 호스팅하는 메타데이터 문서:

```json
{
  "client_id": "https://app.example.com/oauth/client.json",
  "client_name": "Example MCP Client",
  "client_uri": "https://app.example.com",
  "redirect_uris": ["http://127.0.0.1:7333/callback", "http://localhost:7333/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none"
}
```

문서의 `client_id` 값은 **MUST** 제공되는 URL과 동일해야 함(권한 부여 서버가 확인; 불일치 시 거부). 권한 부여 서버는 RFC 8414 메타데이터에서 `client_id_metadata_document_supported: true`로 지원을 광고.

사양이 직설적으로 말하는 두 가지 보안 사실:

- **SSRF.** 권한 부여 서버가 공격자가 제공한 URL을 가져옴. 서버 측 요청 위조(내부/관리 엔드포인트로의 가져오기 금지)를 방어해야 함.
- **localhost 사칭.** CIMD만으로는 로컬 공격자가 합법적인 클라이언트의 메타데이터 URL을 주장하고 `localhost` 리디렉션을 바인딩하는 것을 막을 수 없음. 권한 부여 서버는 **MUST** 동의 중에 리디렉션 URI 호스트명을 명확히 표시하고 **SHOULD** `localhost` 전용 리디렉션에 대해 경고.

CIMD는 서버 측 상태가 필요 없으므로 DCR이 요구하는 방식의 등록 기관을 구축할 필요가 없음. 클라이언트 측은 읽기 전용: 정적 HTTPS 엔드포인트에서 메타데이터 문서를 제공하고 권한 부여 서버가 가져오도록 함.

### RFC 7591 — 동적 클라이언트 등록 (대체 / 이전 버전 호환)

DCR은 이제 `MAY`이며, 2025-11-25 이전 배포 및 아직 CIMD를 지원하지 않는 IdP와의 이전 버전 호환성을 위해 유지. 그것 없이(그리고 CIMD나 사전 등록 없이) 모든 MCP 클라이언트(Cursor, Claude Desktop, 커스텀 에이전트)는 IdP 관리자와의 대역외 교환이 필요. DCR로 클라이언트가 POST:

```json
POST /register
Content-Type: application/json

{
  "redirect_uris": ["http://127.0.0.1:7333/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none",
  "scope": "mcp:tools.invoke",
  "client_name": "Cursor",
  "software_id": "com.cursor.cursor",
  "software_version": "0.42.0"
}
```

서버가 `client_id`와 추후 업데이트용 `registration_access_token`으로 응답:

```json
{
  "client_id": "c_3e7f1a",
  "client_id_issued_at": 1769472000,
  "redirect_uris": ["http://127.0.0.1:7333/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "registration_access_token": "regt_b2...",
  "registration_client_uri": "https://auth.example.com/register/c_3e7f1a"
}
```

`token_endpoint_auth_method: none`은 사용자 기기에서 실행되는 MCP 클라이언트의 올바른 기본값. `client_id`만 받음 — 유출할 `client_secret` 없음. PKCE가 공개 클라이언트에 필요한 소유 증명 제공.

세 가지 프로덕션 함정:

- 등록 엔드포인트는 소스 IP로 속도 제한해야 함. 없으면 적대적 행위자가 수백만 개의 가짜 등록을 스크립팅하고 `client_id` 네임스페이스를 고갈시킴. 등록 기관이 요청을 처리하기 전에 속도 제한 검사 실행.
- `software_statement`(클라이언트를 보증하는 서명된 JWT)는 일부 엔터프라이즈 IdP에서 필요. 이 레슨의 목업은 건너뜀; 프로덕션은 localhost 리디렉션 URI 이외의 것에서 서명되지 않은 등록을 거부하는 확인 단계 연결.
- `registration_access_token`은 해시로 저장되어야 하며, 평문이 아님. 이 토큰의 도난은 공격자가 클라이언트의 리디렉션 URI를 재작성할 수 있음을 의미.

### RFC 8707 (요약) — 리소스 표시기

16과가 형태를 확립. 프로덕션 규칙: 모든 토큰 요청에는 `resource=<canonical-mcp-url>`이 포함되고, MCP 서버는 모든 호출에서 `token.aud`가 자체 리소스 URL과 일치하는지 확인. 표준 URI는 서버에 대한 *가장 구체적인* 식별자: 소문자 스킴과 호스트 사용, 프래그먼트 없음, 관례상 후행 슬래시 없음. 경로 컴포넌트는 개별 MCP 서버를 식별하는 데 필요할 때 규칙에 의해 제거되지 않음. `https://mcp.example.com`, `https://mcp.example.com/mcp`, `https://mcp.example.com:8443`, `https://mcp.example.com/server/mcp` 모두 유효한 표준 URI. 서버당 하나를 선택하고 `aud`를 정확히 그것에 고정. (이 레슨의 목업은 간결성을 위해 `https://notes.example.com` 같은 베어 호스트 수신자를 사용; 하나의 출처 아래 여러 MCP 서버를 공동 호스팅하는 배포는 경로로 구분.)

### RFC 7636 (요약) — PKCE

PKCE는 OAuth 2.1에서 필수. 레슨의 권한 부여 코드 흐름은 항상 `code_challenge`와 `code_verifier`를 전달. 서버는 검증자 없이 또는 검증자가 저장된 challenge와 일치하는 해시를 생성하지 않는 토큰 요청을 거부.

### MCP 사양 2025-11-25 인증 프로파일

MCP 사양(2025-11-25)은 MCP 서버의 인증 계층이 해야 하는 일에 대해 정확함:

- RFC 9728 보호 리소스 메타데이터 구현, 위치를 401의 `WWW-Authenticate: Bearer resource_metadata="..."` 헤더 **또는** well-known URI `/.well-known/oauth-protected-resource`를 통해 제공(SEP-985가 헤더를 well-known 대체로 선택 사항으로 만듦). 메타데이터 `authorization_servers` 필드는 **MUST** 최소 하나의 서버를 명명.
- 모든 요청에 대해 `Authorization: Bearer ...`를 통해서만 토큰 수락 — 쿼리 문자열 절대 안 됨, 세션 시작 시에만 검증 안 됨.
- 요청별로 `aud`, `iss`, `exp` 및 필수 범위 검증. 서버는 **MUST** 토큰이 특별히 자신을 위해 발급되었는지 검증(수신자); 누락되거나 일치하지 않는 `aud`는 거부되며, 와일드카드로 처리되지 않음.
- 401/403에서 `WWW-Authenticate: Bearer`를 반환, `error=...`, `resource_metadata="<PRM-URL>"` 파라미터(메타데이터 문서의 URL, *베어 리소스가 아님*), 그리고 `insufficient_scope`(403)의 경우 `scope="..."`를 포함. 참고: 파라미터는 `resource_metadata`로, 검색 포인터 — challenge에는 `resource` 파라미터가 없음.
- 권한 부여 서버 검색은 **RFC 8414 OAuth 메타데이터** 또는 **OpenID Connect Discovery 1.0** 중 하나를 수락; 클라이언트는 우선순위 순서로 두 well-known 접미사를 시도해야 함.
- 클라이언트(서버가 아님)가 **mix-up 공격**을 방어: 리디렉션 전에 예상 `issuer`를 기록하고, 코드를 교환하기 전에 `iss` 권한 부여 응답 파라미터(RFC 9207)를 검증. PKCE만으로는 mix-up을 막지 못함, 클라이언트가 `code_verifier`를 전달받은 토큰 엔드포인트에 넘겨주기 때문.

OAuth 2.1 초안이 기판; RFC 8414/7591/8707/9728/9207 + RFC 7636 + CIMD가 표면; MCP 사양이 프로파일.

### IdP 기능 매트릭스

모든 IdP가 전체 MCP 프로파일을 지원하는 것은 아님. 아래 매트릭스는 2025-11-25 사양 기준의 사실적 기능 설명을 문서화. *배포 게이트*이지, 추천이 아님.

CIMD는 2025-11-25 사양과 기본 OAuth 초안이 2025년 10월에야 채택되었으므로 출시됨, 따라서 벤더 지원이 아직 도착 중 — 아래 "CIMD"를 "오늘날의 상태, 테넌트에서 확인"으로 취급, 영구적 진술이 아님.

| IdP 카테고리 | AS 메타데이터 (8414/OIDC) | CIMD | RFC 7591 DCR | RFC 8707 resource | RFC 7636 S256 PKCE | 비고 |
|---|---|---|---|---|---|---|
| 자체 호스팅 (Keycloak) | 예 | 등장 중 | 예 | 예 (24.x부터) | 예 | 이 레슨의 MCP 프로파일 참조 IdP; 종단간 전체 DCR 경로, CIMD는 새 사양 추적. |
| 엔터프라이즈 SSO (Microsoft Entra ID) | 예 | 등장 중 | 예 (프리미엄 티어) | 예 | 예 | DCR 가용성은 테넌트 티어에 따라 다름; 배포 전 대상 테넌트에서 확인. |
| 엔터프라이즈 SSO (Okta) | 예 | 등장 중 | 예 (Okta CIC / Auth0) | 예 | 예 | DCR은 Auth0(현재 Okta CIC)에서 사용 가능; 클래식 Okta 조직은 관리자 사전 등록 필요. |
| 소셜 로그인 IdP (일반) | 다양함 | 아니오 | 드물게 | 드물게 | 예 | 대부분의 소셜 IdP는 클라이언트를 정적 파트너로 취급; 셀프 서비스 등록 없음. ID 소스로만 사용, 자체 MCP 인식 권한 부여 서버를 위에 계층화. |
| 커스텀 / 자체 개발 | 상황에 따라 다름 | 상황에 따라 다름 | 상황에 따라 다름 | 상황에 따라 다름 | 상황에 따라 다름 | 자체를 출시하면 전체 프로파일을 출시하고 CIMD 선호. PKCE 또는 수신자 바인딩 건너뛰면 MCP 인증 계약이 깨짐. |

배포 매니페스트에 대한 거부 규칙: 선택한 IdP가 `code_challenge_methods_supported`에 `S256`을 나열하지 않으면 MCP 서버가 시작을 거부 — PKCE에는 저하된 모드가 없음. 등록은 더 부드러운 게이트: *하나*의 작동 경로(사전 등록된 `client_id`, `client_id_metadata_document_supported: true`, 또는 `registration_endpoint`)가 필요. DCR의 부재만으로는 더 이상 거부 트리거가 아님, CIMD 또는 사전 등록이 커버할 수 있기 때문.

### JWKS 갱신 패턴 (AS에서 교체, 리소스 서버에서 갱신)

두 동사를 분리하세요, 혼동하는 것은 실제 프로덕션 버그이기 때문:

- **교체**는 *권한 부여 서버*가 하는 것: 새 서명 키를 생성하고, JWKS에 게시하고, 나중에 이전 키를 폐기. 리소스 서버는 이에 참여하지 않으며 할 수 없음 — IdP의 개인 키를 보유하지 않음.
- **갱신**은 *리소스 서버*가 하는 것: 게시된 JWKS를 캐시로 다시 `GET`. 그것이 리소스 서버가 수행하는 유일한 JWKS 동작.

프로덕션 실패 모드는 오래된 캐시. 예약된 갱신 작업과 키-값 캐시로 해결. 리소스 서버가 고정 간격으로(크론, 타이머, 런타임이 제공하는 것) `<issuer>/.well-known/jwks.json`을 가져와 `cache[issuer] = {keys, fetched_at}`를 덮어쓰는 작업 실행. 검증기가 그 캐시에서 읽음. `kid`가 캐시에 없는 토큰은 **하나의** 동기식 갱신을 폴백으로 트리거한 후 재확인. 이는 두 가지 경우를 한 번에 처리: 예약된 갱신, 그리고 예약된 다음 갱신 전에 새로운 키로 서명된 토큰이 도착하는 키 중복 기간.

폴백은 **반드시 재가져오기여야 하며, 절대 교체가 아님**. 캐시 미스 경로를 교체-및-발급으로 연결하면 두 가지가 깨짐: (1) 새 키를 발급하면 *여전히* 토큰과 일치하지 않는 `kid`가 생성되므로 조회가 어쨌든 실패; (2) 무작위 `kid` 값으로 토큰을 뿌리는 공격자는 무제한의 키 생성을 강제 — 자체 DoS. 재가져오기는 멱등이므로, 가짜 `kid`는 최대 한 번의 낭비된 가져오기 비용만 듦.

캐시 형태:

```json
{
  "https://auth.example.com": {
    "keys": [
      {"kid": "k_2026_03", "kty": "RSA", "n": "...", "e": "AQAB", "alg": "RS256", "use": "sig"},
      {"kid": "k_2026_04", "kty": "RSA", "n": "...", "e": "AQAB", "alg": "RS256", "use": "sig"}
    ],
    "fetched_at": 1772668800
  }
}
```

한 번에 두 개의 키가 정상 상태. 권한 부여 서버는 이전 키(`k_2026_03`)를 폐기하기 전에 다음 키(`k_2026_04`)를 도입하여 교체하므로, 이전 키로 발급된 토큰은 만료될 때까지 유효. 캐시는 합집합을 보유; 검증기는 `kid`로 선택.

### 검증 루틴

MCP 서버는 도구를 디스패치하기 전에 검증을 실행. `code/main.py`가 사용하는 형태:

```python
result = server.validate(bearer_token, required_scope="mcp:tools.invoke")
if not result["valid"]:
    return {"status": result["status"], "WWW-Authenticate": result["www_authenticate"]}
```

`validate`는 JWT를 디코딩하고, JWKS 캐시에서 서명 키를 확인(미스 시 한 번 갱신)하고, 서명을 검증한 다음 `iss`를 허용 목록에 대해, `aud`를 이 서버의 표준 리소스에 대해, `exp` 및 필수 범위를 확인 — 첫 번째 실패 시 `WWW-Authenticate` challenge 반환. 리소스 서버에서 단일 루틴으로 유지하면 모든 진입점(모든 도구 호출, 모든 전송)이 동일한 검사를 통과함; 먼저 검증하지 않고 도구에 도달하는 경로가 없음.

### 수신자 재생 워크스루 (액세스 토큰 권한 제한)

서버 A(`notes.example.com`)와 서버 B(`tasks.example.com`)가 동일한 권한 부여 서버에 등록. 서버 A가 손상됨. 공격자가 사용자의 노트 토큰을 가져와 서버 B에 재생.

서버 B의 검증기:

1. JWT 디코드, `kid`로 JWKS 가져오기, 서명 확인.
2. `iss`를 보호 리소스 메타데이터의 `authorization_servers`에 대해 확인. (통과 — 동일 IdP.)
3. `aud == "https://tasks.example.com"` 확인. (실패 — 토큰의 `aud`는 `https://notes.example.com`.)
4. `WWW-Authenticate: Bearer error="invalid_token", error_description="audience mismatch", resource_metadata="https://tasks.example.com/.well-known/oauth-protected-resource"`와 함께 401 반환.

수신자 클레임은 프로토콜 계층에서 이 공격에 대한 유일한 방어. 성능을 위해 건너뛰는 것이 가장 흔한 프로덕션 실수; 검증기는 모든 요청에 실행되어야 하며, 세션 시작 시에만이 아님. 사양은 이를 **액세스 토큰 권한 제한**이라고 부름: MCP 서버는 `MUST` 자신을 수신자로 명명하지 않은 토큰을 거부.

> **명명 참고.** 사양은 *혼동된 부관*이라는 용어를 관련 있지만 별개의 문제에 대해 예약: MCP 서버가 정적 클라이언트 ID를 사용하여 타사 API에 대한 OAuth **프록시** 역할을 하면서, 클라이언트별 사용자 동의 없이 토큰을 전달하는 것. 수신자 바인딩은 위의 재생을 수정; 혼동된 부관 수정은 클라이언트별 동의 **더하기** 인바운드 토큰을 업스트림 API에 절대 전달하지 않는 것(MCP 서버는 `MUST` 자체 별도 업스트림 토큰을 얻음).

### Mix-up 공격 (서버가 제공할 수 없는 클라이언트 측 방어)

클라이언트는 수명 동안 많은 권한 부여 서버와 통신. 악성 AS는 정직한 AS의 권한 부여 코드를 공격자의 토큰 엔드포인트에서 교환하도록 클라이언트를 속일 수 있음. 수신자 바인딩은 여기서 도움이 되지 않음 — 공격은 토큰이 존재하기 전에 발생. 방어는 클라이언트에 있음(RFC 9207):

1. 리디렉션 전에 클라이언트가 검증된 AS 메타데이터에서 예상 `issuer` 기록.
2. 권한 부여 응답에서 클라이언트가 반환된 `iss` 파라미터를 기록된 발급자와 비교(단순 문자열 비교, 정규화 없음)한 후 코드를 어디로든 전송.
3. 불일치(또는 AS가 `authorization_response_iss_parameter_supported`를 광고했는데 `iss`가 없음) → 거부, `error` 필드도 표시하지 않음.

PKCE만으로는 mix-up을 막지 못함, 클라이언트가 `code_verifier`를 전달받은 토큰 엔드포인트에 넘겨주기 때문. 이것이 사양이 PKCE 검증기 및 `state`와 함께 요청별로 발급자를 기록하는 이유.

### 실패 모드

- **오래된 JWKS.** AS가 키를 교체한 후 검증기가 유효한 토큰을 거부. 수정은 크론-갱신 + 캐시-미스-재가져오기 패턴. JWKS를 갱신 작업 없이 캐시하지 마세요.
- **폴백-애즈-교체.** 캐시 미스 경로를 재가져오기 대신 교체-및-발급으로 연결하는 것은 실제 버그: 누락된 `kid`를 생성하지 않으며, 공격자 제어 `kid` 값을 키 생성 DoS로 바꿈. 폴백은 멱등인 `refresh-jwks`여야 함.
- **누락된 `aud` 클레임.** 일부 IdP는 토큰 요청에 `resource`가 없으면 `aud`를 생략하는 것이 기본값. 검증기는 누락된 `aud`를 와일드카드로 처리하지 않고 거부해야 함.
- **누락된 `iss` 검사로 인한 Mix-up.** 리디렉션 전 기록한 발급자에 대해 RFC 9207 `iss` 권한 부여 응답 파라미터를 검증하지 않는 클라이언트는 정직한 AS의 코드를 공격자의 토큰 엔드포인트에서 교환하도록 유도될 수 있음. 이것은 클라이언트 측 실패; 리소스 서버가 이를 보상할 수 없음.
- **범위 업그레이드 경합.** 동일 사용자에 대한 두 개의 동시 단계적 상승 흐름이 둘 다 성공하여 다른 범위의 두 액세스 토큰을 생성할 수 있음. 검증기는 요청에 제시된 토큰을 사용해야 하며, "사용자의 현재 범위"를 조회하지 않아야 함 — 이는 TOCTOU 윈도우를 생성.
- **등록 토큰 도난.** 유출된 `registration_access_token`은 공격자가 리디렉션 URI를 재작성할 수 있게 함. 저장 시 해시; 모든 업데이트 시 클라이언트가 평문을 제시하도록 요구; 의심 시 교체.
- **`iss`가 고정되지 않음.** 모든 `iss`를 수락하는 검증기는 공격자가 자체 권한 부여 서버를 구축하고, 대상 수신자에 대한 클라이언트를 등록하고, 토큰을 발급할 수 있게 함. 보호 리소스 메타데이터의 `authorization_servers` 목록이 허용 목록; 이를 적용.

## 사용하기

`code/main.py`는 표준 라이브러리 Python과 세 가지 역할(`AuthorizationServer`, `ResourceServer`, `Client`)로 전체 프로덕션 흐름을 보여줍니다. 흐름:

1. 권한 부여 서버가 `/.well-known/oauth-authorization-server`에 RFC 8414 메타데이터 게시.
2. MCP 클라이언트가 메타데이터 엔드포인트를 호출하고 등록 옵션(`client_id_metadata_document_supported` for CIMD, `registration_endpoint` for DCR) 및 `S256` PKCE 지원 확인.
3. 워크스루가 DCR 폴백 경로를 사용: 클라이언트가 `/register`(RFC 7591)로 POST하고 `client_id` 수신. (CIMD 클라이언트는 대신 자체 HTTPS `client_id` URL을 제시하고 이 단계를 건너뜀.)
4. MCP 클라이언트가 `resource` 표시기(RFC 8707)와 함께 PKCE 보호 권한 부여 코드 흐름(RFC 7636) 실행.
5. MCP 클라이언트가 `Authorization: Bearer ...`로 MCP 서버에서 도구 호출.
6. MCP 서버가 `validate` 실행, JWKS 캐시에서 서명 키 확인.
7. IdP가 키 교체; 예약된 갱신이 JWKS를 캐시로 다시 가져옴.
8. 다음 호출이 재시작 없이 갱신된 키에 대해 검증하고, 이전 토큰이 중복 기간 동안 여전히 유효.
9. 다른 MCP 리소스에 대한 수신자 재생 시도가 `audience mismatch` 및 `resource_metadata` 포인터와 함께 401을 받음.

여기서 JWT는 공유 시크릿으로 HS256 사용(레슨이 표준 라이브러리에서만 실행되도록). 프로덕션은 RS256 또는 EdDSA와 위의 JWKS 패턴 사용; 검증 로직은 그 외에는 동일. IdP와 리소스 서버가 하나의 프로세스에 있으므로 `refresh_jwks`는 권한 부여 서버의 키 목록을 직접 읽음; 와이어를 통해서는 `jwks_uri`에 대한 HTTP `GET`임.

## 배포하기

이 레슨은 `outputs/skill-mcp-auth.md`를 생성합니다. MCP 서버 구성과 IdP 기능 집합이 주어지면 스킬이 구축할 인증 표면(보호 리소스 메타데이터, 사용할 등록 경로(CIMD, 사전 등록 또는 DCR 폴백), JWKS 갱신 일정, 범위 매핑 및 IdP가 전체 RFC 프로파일을 지원하지 않을 때 적용할 거부 규칙)을 출력합니다.

## 실습

1. `code/main.py`를 실행하고 흐름을 추적하세요. IdP가 6단계에서 키를 교체하고, 예약된 `refresh_jwks`가 게시된 집합을 다시 가져오며, 이전 토큰(중복 기간)과 새 토큰이 재시작 없이 검증되는 방식을 주목하세요.

2. 보호 리소스 메타데이터의 `authorization_servers` 목록에 새 IdP를 추가하세요. 새 IdP가 서명한 토큰을 발급하고 검증기가 수락하는지 확인하세요. 목록에 없는 IdP가 서명한 토큰을 발급하고 검증기가 `WWW-Authenticate: Bearer error="invalid_token", error_description="iss not allowed"`로 거부하는지 확인하세요.

3. `register_client`에 등록 기관이 요청을 수락하기 전에 실행되는 속도 제한 검사를 추가하세요. IP로 키가 지정된 작은 딕셔너리에 보관된 소스 IP당 토큰 버킷을 사용하세요.

4. RFC 7591을 읽고 레슨의 `/register` 핸들러가 검증하지 않는 두 필드를 식별하세요. 검증을 추가하세요. (힌트: `software_statement` 및 `redirect_uris` URI 스킴.)

5. Client ID Metadata Document 경로를 추가하세요. `client_id`가 자체 URL과 동일한 `client.json`을 제공하고, 권한 부여 서버가 가져와서 확인하도록 하세요(`client_id` ≠ URL이면 거부). CIMD 클라이언트가 `register_client` 호출 없이 등록하는지 확인하세요.

6. DoS 수정을 증명하세요. 무작위 `kid`로 검증기에 토큰을 보내고 `refresh_jwks`가 최대 한 번 실행되고 권한 부여 서버의 키 수가 증가하지 않는지 확인하세요. 그런 다음 폴백을 교체-및-발급으로 의도적으로 다시 연결하고 키 수가 가짜 토큰당 증가하는 것을 관찰하세요 — 그 후 재가져오기로 복원하세요.

7. mix-up 섹션의 클라이언트 측 RFC 9207 `iss` 검사를 구현하세요: 권한 부여 요청 전에 예상 발급자를 기록한 다음, `iss`가 일치하지 않는 권한 부여 응답을 거부하세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| ASM | "OAuth 메타데이터 문서" | RFC 8414 `/.well-known/oauth-authorization-server` JSON |
| CIMD | "클라이언트 메타데이터 URL" | Client ID Metadata Document — `client_id`로 사용되는 HTTPS URL; AS가 JSON을 가져옴. 2025-11-25부터 권장 기본값 |
| DCR | "셀프 서비스 클라이언트 등록" | RFC 7591 `POST /register` 흐름; 2025-11-25에서 `MAY` 폴백으로 낮춤 |
| JWKS | "JWT 검증용 공개 키" | JSON Web Key Set, `jwks_uri`에서 가져옴, `kid`로 인덱싱 |
| 교체 vs 갱신 | "키 업데이트" | *교체* = AS가 서명 키 생성/폐기; *갱신* = 리소스 서버가 게시된 집합 재가져오기. 리소스 서버는 오직 갱신만 함 |
| 리소스 표시기(Resource indicator) | "수신자 파라미터" | RFC 8707 `resource` 파라미터, 토큰을 하나의 서버에 고정 |
| `aud` 클레임 | "수신자" | 검증기가 표준 리소스 URL과 비교하는 JWT 클레임 |
| 수신자 재생(Audience replay) | "토큰 재생" | 서버 A용으로 발급된 토큰을 서버 B에 제시; 수신자 검증으로 방어(사양: 액세스 토큰 권한 제한) |
| 혼동된 부관(Confused deputy) | "프록시 토큰 남용" | 정적 클라이언트 ID로 클라이언트별 동의 없이 토큰을 전달하는 MCP 프록시; 수신자 재생과 구분됨 |
| Mix-up 공격 | "잘못된 토큰 엔드포인트" | 클라이언트가 정직한 AS의 코드를 공격자의 엔드포인트에서 교환하도록 유도; RFC 9207 `iss`로 클라이언트 측 방어 |
| `iss` 허용 목록 | "신뢰된 권한 부여 서버" | 보호 리소스 메타데이터의 `authorization_servers`에 명명된 집합 |
| `resource_metadata` | "PRM 문서 위치" | 401/403에서 RFC 9728 메타데이터 URL을 명명하는 `WWW-Authenticate` 파라미터 |
| 공개 클라이언트(Public client) | "네이티브 또는 브라우저 클라이언트" | `client_secret`이 없는 OAuth 클라이언트; PKCE가 보완 |
| `WWW-Authenticate` | "401/403 응답 헤더" | 클라이언트 복구를 구동하는 `Bearer error=...` 지시문 전달 |

## 추가 자료

- [MCP — Authorization spec (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) — 이 레슨이 구현하는 MCP 인증 프로파일
- [MCP blog — One Year of MCP: November 2025 Spec Release](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/) — 2025-11-25 변경 사항 (CIMD, XAA, DCR 강등)
- [Aaron Parecki — Client Registration in the November 2025 MCP Authorization Spec](https://aaronparecki.com/2025/11/25/1/mcp-authorization-spec-update) — CIMD-over-DCR 근거
- [OAuth Client ID Metadata Document (draft-ietf-oauth-client-id-metadata-document-00)](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-client-id-metadata-document-00) — CIMD
- [RFC 8414 — OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414) — 검색 계약
- [RFC 7591 — OAuth 2.0 Dynamic Client Registration Protocol](https://datatracker.ietf.org/doc/html/rfc7591) — DCR (폴백 경로)
- [RFC 7636 — Proof Key for Code Exchange (PKCE)](https://datatracker.ietf.org/doc/html/rfc7636) — 공개 클라이언트 소유 증명
- [RFC 8707 — Resource Indicators for OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc8707) — 수신자 고정
- [RFC 9728 — OAuth 2.0 Protected Resource Metadata](https://datatracker.ietf.org/doc/html/rfc9728) — 리소스 서버 검색
- [RFC 9207 — OAuth 2.0 Authorization Server Issuer Identification](https://datatracker.ietf.org/doc/html/rfc9207) — mix-up 공격 방어 `iss` 파라미터
- [OAuth 2.1 draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1) — 통합 OAuth 기판
