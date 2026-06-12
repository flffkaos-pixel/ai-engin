# 캡스톤 13 — 레지스트리 및 거버넌스가 있는 MCP 서버

> Model Context Protocol은 더 이상 미래가 아닌 2026년의 기본 도구 사용 사양이 되었다. Anthropic, OpenAI, Google, 모든 주요 IDE가 MCP 클라이언트를 shipped한다. Pinterest가 내부 MCP 서버 생태계를 게시했다. AAIF 레지스트리가 `.well-known`에서 기능 메타데이터를 공식화했다. AWS ECS가 기준 상태 비저장 배포를 게시했다. Block의 goose-agent가 동일한 프로토콜을 호스티드 어시스턴트 안에 넣었다. 2026년 운영 형태는: StreamableHTTP 전송, OAuth 2.1 scopes, OPA 정책 게이팅, 플랫폼 팀이 서버를 검색, 검증, 활성화할 수 있는 레지스트리이다. 종단 간 구축한다.

**유형:** 캡스톤
**언어:** Python (FastMCP를 통한 서버) 또는 TypeScript (@modelcontextprotocol/sdk), Go (레지스트리 서비스)
**선수 과목:** Phase 11 (LLM 엔지니어링), Phase 13 (도구 및 MCP), Phase 14 (에이전트), Phase 17 (인프라), Phase 18 (안전)
**활용 phases:** P11 · P13 · P14 · P17 · P18
**소요 시간:** 25시간

## 문제

MCP는 도구 사용 lingua franca가 되었다. Claude Code, Cursor 3, Amp, OpenCode, Gemini CLI, 모든 관리 에이전트가 이제 MCP 서버를 소비한다. 운영挑战은 서버 작성(FastMCP가 쉽게 만들)이 아니라 기업 요구사항으로 규모에 배포하는 것이다: 테넌트별 OAuth scopes, 파괴적 도구에 대한 OPA 정책, StreamableHTTP 상태 비저장 스케일링, 검색을 위한 레지스트리, 도구 호출당 감사 로그. Pinterest의 내부 MCP 생태계와 AAIF 레지스트리 사양이 2026년 기준을 설정했다.

10개의 내부 도구(Postgres 읽기 전용, S3 목록, Jira, Linear, Datadog 등)를 노출하는 MCP 서버, 플랫폼 검색을 위한 레지스트리 UI, 파괴적 도구에 대한 인간 승인 게이트를 구축한다. 부하 테스트는 StreamableHTTP 수평 스케일링을演示한다. 감사 추적이 기업 보안 검토를 만족한다.

## 개념

MCP 2026 개정은 StreamableHTTP를 기본 전송으로mandate한다. earlier stdio-and-SSE 형태와 달리 StreamableHTTP는 기본적으로 상태 비저장이다: 단일 HTTP 엔드포인트가 JSON-RPC 요청을accept하고, 응답을 스트리밍하고, 알림을 위한 장기 연결을 지원한다. 상태 비저장은 로드 밸런서 뒤에서 수평으로 확장 가능함을 의미한다.

권한 부여는 도구별 scopes가 있는 OAuth 2.1이다. 토큰은 `jira:read`, `s3:list`, `postgres:query:readonly`와 같은 scopes를carry한다. MCP 서버는 세션 시작이 아닌 도구 호출 시점에 scopes를检查한다. 고위험 도구의 경우 서버는 지난 N분 이내에 `approved:by:human`으로 상승되지 않은 모든 호출을 거부한다 — 해당 상승은 Slack 검토 카드에서 온다.

레지스트리는 별도의 서비스이다. 모든 MCP 서버는 도구 manifest, 전송 URL, 인증 요구사항과 함께 `.well-known/mcp-capabilities` 문서를 노출한다. 레지스트리가 폴링, 검증, 인덱싱한다. 플랫폼 팀이 레지스트리 UI를 사용하여 사용 가능한 도구, 필요한 scopes, 소유 팀을 확인한다.

## 아키텍처

```
MCP client (Claude Code, Cursor 3, ...)
          |
          v
StreamableHTTP over HTTPS (JSON-RPC + streaming)
          |
          v
MCP server (FastMCP) behind load balancer
          |
     +------+------+---------+----------+------------+
     v             v         v          v            v
 Postgres    S3 listing  Jira       Linear     Datadog
 (read-only) (paged)     (read)     (read)     (query)
          |
     +------+-------------+
     v                    v
  OPA policy gate   destructive tool MCP (separate server)
                        |
                        v
                   human approval via Slack
                        |
                        v
                   audit log (append-only, per-tenant)

  registry service
     |
     v  GET /.well-known/mcp-capabilities from each server
     v
     UI: search / validate / enable-disable / ownership
```

## 기술 스택

- 서버 프레임워크: FastMCP (Python) 또는 `@modelcontextprotocol/sdk` (TypeScript)
- 전송: HTTPS 위의 StreamableHTTP (상태 비저장)
- 인증: SPIFFE / SPIRE를 통한 워크로드 ID로 OAuth 2.1
- 정책: 도구당 OPA / Rego 규칙; 요청당 정책 결정 서비스
- 레지스트리: 셀프 호스트, `.well-known/mcp-capabilities` manifests를 소비
- 인간 승인: 파괴적 도구를 위한 Slack 대화형 메시지
- 배포: AWS ECS Fargate 또는 Fly.io, 테넌트당 또는 테넌트 스코핑이 있는 공유 서버
- 감사: 테넌트당 per-call 계보가 있는 구조화된 JSONL

## 실습

1. **도구 표면.** 10개의 내부 도구 노출: Postgres 읽기 전용 쿼리, S3 목록 객체, Jira 검색/가져오기, Linear 검색/가져오기, Datadog 메트릭 쿼리, PagerDuty 온콜 조회, GitHub 읽기 전용, Notion 검색, Slack 검색, Salesforce 읽기. 각 도구에 타입화된 스키마와 scope 레이블이 있다.

2. **FastMCP 서버.** 도구를 마운트한다. StreamableHTTP 전송을 구성한다. OAuth 토큰 검토 및 scope 강제를 위한 미들웨어를 추가한다.

3. **OPA 정책.** 도구당 Rego 정책: 어떤 scopes가 호출을 허용하는지, 어떤 PII 재 thérapeut가 적용되는지, 어떤 페이로드 크기 캡이 적용되는지. 모든 도구 호출에서 호출되는 결정 서비스.

4. **레지스트리 서비스.** 등록된 서버에서 `.well-known/mcp-capabilities`를 폴링하고, JSON Schema로 검증하고, 목록/검색/검증/활성화-비활성화 UI를 노출하는 별도의 Go 또는 TS 서비스.

5. **기능 매니페스트.** 각 서버가 `.well-known/mcp-capabilities`를 노출: 도구 목록, 인증 요구사항, 전송 URL, 소유 팀, SLO.

6. **파괴적 도구 분리.** 상태를突变하는 도구(Jira 생성, Linear 생성, Postgres 쓰기)는 더 엄격한 인증 흐름이 있는 두 번째 MCP 서버에 있다: 토큰은 지난 15분 이내에 Slack 카드를 통해 상승된 `approved:by:human` scope가 있어야 한다.

7. **감사 로그.** 테넌트당 추가 전용 JSONL: `{timestamp, user, tool, args_redacted, response_redacted, outcome}`. 쓰기 전에 Presidio를 통한 PII 재 탈착.

8. **부하 테스트.** StreamableHTTP에서 100개의 동시 클라이언트. 두 번째 레플리카를 추가하여 수평 스케일링을演示한다; 로드 밸런서가 세션 고착 없이 재분배하는 것을 보여준다.

9. **순응성 테스트.** 두 서버 모두에 대한 공식 MCP 순응성 테스트 모음을 실행한다. 모든 필수 섹션을 통과한다.

## 활용

```
$ curl -H "Authorization: Bearer eyJhbGc..." \
       -X POST https://mcp.internal.example.com/ \
       -d '{"jsonrpc":"2.0","method":"tools/call",
            "params":{"name":"postgres.readonly","arguments":{"sql":"SELECT 1"}}}'
[registry]   capability validated: postgres.readonly v1.2
[policy]    scope postgres:query:readonly present; allowed
[audit]     logged: user=u42 tool=postgres.readonly outcome=ok
response:    { "result": { "rows": [[1]] } }
```

## 결과물

`outputs/skill-mcp-server.md`가 결과물을 설명한다. OAuth 2.1 scopes 및 OPA 게이팅이 있는 내부 도구용 운영 등급 MCP 서버 + 레지스트리 + 감사 레이어.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 사양 순응성 | StreamableHTTP + 기능 매니페스트가 MCP 순응성 테스트를 통과 |
| 20 | 보안성 | 범위 적용, 모든 도구에 대한 OPA 적용 범위, 시크릿 hygene |
| 20 | 관찰 가능성 | PII 재 탈착이 포함된 도구 호출당 감사 로그 |
| 20 | 규모 | 100-클라이언트 부하 테스트 수평 스케일링演示 |
| 15 | 레지스트리 UX | 검색/검증/활성화-비활성화 워크플로 |
| **100** | | |

## 연습 문제

1. 새 도구(Confluence 검색)를 추가한다. 코어 서버를 만지지 않고 레지스트리 검증 흐름을 통해 shipped한다.

2. `email`, `ssn`, `phone`라는 이름의 열이 포함된 Postgres 쿼리 결과를 재 탈착하는 OPA 정책을 작성한다. 프로브 쿼리로 연습한다.

3. 로컬 지연에서 StreamableHTTP 대 stdio를 벤치마크한다. 호출당 p50/p95를 보고한다.

4. 테넌트당 할당량 구현: 도구당 테넌트당 분당 최대 N 호출. 두 번째 OPA 규칙을 통해 적용한다.

5. [mcp-conformance-tests](https://github.com/modelcontextprotocol/conformance)에서 MCP 순응성 테스트 모음을 실행하고 모든 실패를 수정한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| StreamableHTTP | "2026 MCP transport" | 상태 비저장 HTTP + 스트리밍; 네트워크 서버를 위해 SSE + stdio를 대체 |
| 기능 매니페스트 | "Well-known doc" | 도구 목록, 인증, 전송 URL이 포함된 `.well-known/mcp-capabilities` |
| OPA / Rego | "Policy engine" | 외부 규칙에 대해 도구 호출을 승인하기 위한 Open Policy Agent |
| Scope 상승 | "Approved-by-human" | 파괴적 도구에 필요한, Slack 승인을 통해 부여된 단기 scope |
| 레지스트리 | "Tool discovery" | 기능 매니페스트에서 MCP 서버를 인덱싱하는 서비스 |
| 워크로드 ID | "SPIFFE / SPIRE" | OAuth 토큰 발급을 위한 암호화 서비스 ID |
| 순응성 모음 | "Spec tests" | StreamableHTTP + 도구 매니페스트 정확성에 대한 공식 MCP 테스트 배터리 |

## 추가 자료

- [Model Context Protocol 2026 Roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — StreamableHTTP, 기능 메타데이터, 레지스트리
- [AAIF MCP Registry spec](https://github.com/modelcontextprotocol/registry) — 2026년 레지스트리 사양
- [AWS ECS reference deployment](https://aws.amazon.com/blogs/containers/deploying-model-context-protocol-mcp-servers-on-amazon-ecs/) — 기준 운영 배포
- [Pinterest 내부 MCP 생태계](https://www.infoq.com/news/2026/04/pinterest-mcp-ecosystem/) — 기준 내부 배포
- [Block `goose` MCP 사용](https://block.github.io/goose/) — 기준 에이전트 소비 패턴
- [FastMCP](https://github.com/jlowin/fastmcp) — Python 서버 프레임워크
- [Open Policy Agent](https://www.openpolicyagent.org/) — 정책 엔진 기준
- [SPIFFE / SPIRE](https://spiffe.io) — 워크로드 ID 기준