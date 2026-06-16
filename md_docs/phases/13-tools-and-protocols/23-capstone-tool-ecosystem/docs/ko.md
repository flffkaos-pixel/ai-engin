# 캡스톤 — 완전한 도구 생태계 구축

> 13단계는 모든 조각을 가르쳤습니다. 이 캡스톤은 이를 하나의 프로덕션 형태 시스템으로 연결합니다: 도구 + 리소스 + 프롬프트 + Tasks + UI가 있는 MCP 서버, 에지의 OAuth 2.1, RBAC 게이트웨이, 다중 서버 클라이언트, A2A 하위 에이전트 호출, 수집기로의 OTel 추적, CI의 도구 중독 탐지, 그리고 AGENTS.md + SKILL.md 번들. 마치면 모든 아키텍처 선택을 방어할 수 있습니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, 종단간 생태계 하네스)
**Prerequisites:** 13단계 01과~21과
**Time:** 약 120분

## 학습 목표

- 도구, 리소스, 프롬프트 및 `ui://` 앱이 있는 태스크를 노출하는 MCP 서버를 구성할 수 있다.
- RBAC 및 고정 해시를 적용하는 OAuth 2.1 게이트웨이로 서버를 앞에 둘 수 있다.
- 종단간 OTel GenAI 속성으로 추적하는 다중 서버 클라이언트를 작성할 수 있다.
- 워크로드의 일부를 A2A 하위 에이전트에 위임하고 불투명성이 보존되는지 확인할 수 있다.
- AGENTS.md + SKILL.md로 전체 스택을 패키징하여 다른 에이전트가 구동할 수 있게 할 수 있다.

## 문제

"연구 및 보고" 시스템 출시:

- 사용자가 묻습니다: "에이전트 프로토콜에 대한 2026년 가장 많이 인용된 arXiv 논문 세 개를 요약해줘."
- 시스템: MCP를 통해 arXiv 검색; A2A를 통해 전문 작가 에이전트에 논문 요약 위임; 결과 집계; MCP Apps `ui://` 리소스로 대화형 보고서 렌더링; 모든 단계를 OTel에 기록.

13단계의 모든 프리미티브가 나타납니다. 이것은 장난감이 아닙니다 — 2026년 Anthropic(Claude Research 제품), OpenAI(GPTs with Apps SDK) 및 타사가 출시한 프로덕션 연구-어시스턴트 시스템이 정확히 이 형태를 가집니다.

## 개념

### 아키텍처

```
[사용자] -> [클라이언트] -> [게이트웨이 (OAuth 2.1 + RBAC)] -> [연구 MCP 서버]
                                                       |
                                                       +- MCP 도구: arxiv_search (순수)
                                                       +- MCP 리소스: notes://recent
                                                       +- MCP 프롬프트: /research_topic
                                                       +- MCP 태스크: generate_report (장기)
                                                       +- MCP Apps UI: ui://report/current
                                                       +- A2A 호출: writer-agent (tasks/send)
                                                       |
                                                       +- OTel GenAI 스팬
```

### 트레이스 계층

```
agent.invoke_agent
 ├── llm.chat (시작)
 ├── mcp.call -> tools/call arxiv_search
 ├── mcp.call -> resources/read notes://recent
 ├── mcp.call -> prompts/get research_topic
 ├── a2a.tasks/send -> writer-agent
 │    └── 작업 전이 (불투명한 내부)
 ├── mcp.call -> tools/call generate_report (태스크 증강)
 │    └── tasks/status 폴링
 │    └── tasks/result (완료, ui:// 리소스 반환)
 └── llm.chat (최종 합성)
```

하나의 트레이스 id. 모든 스팬이 올바른 `gen_ai.*` 속성을 가짐.

### 보안 태세

- OAuth 2.1 + PKCE, 리소스 표시기가 수신자를 게이트웨이에 고정.
- 게이트웨이가 업스트림 자격 증명 보유; 사용자가 절대 보지 못함.
- RBAC: `alice`는 `research:read`, `research:write`를 가지며 모든 도구 호출 가능. `bob`은 `research:read`를 가지며 `generate_report`를 호출할 수 없음.
- 고정 설명 매니페스트: 도구 해시가 변경된 서버는 삭제.
- Rule of Two 감사: 신뢰할 수 없는 입력, 민감한 데이터 및 결과적 액션을 결합하는 도구 없음.

### 렌더링

최종 `generate_report` 태스크는 콘텐츠 블록과 `ui://report/current` 리소스를 반환. 클라이언트의 호스트(Claude Desktop 등)가 샌드박스 iframe에서 대화형 대시보드를 렌더링. 대시보드는 정렬된 논문 목록, 인용 횟수 및 사용자가 클릭하는 모든 논문에 대해 `host.callTool('summarize_paper', {arxiv_id})`를 호출하는 버튼을 포함.

### 패키징

전체가 다음과 같이 출시:

```
research-system/
  AGENTS.md                     # 프로젝트 규칙
  skills/
    run-research/
      SKILL.md                  # 최상위 워크플로
  servers/
    research-mcp/               # MCP 서버
      pyproject.toml
      src/
  agents/
    writer/                     # A2A 에이전트
  gateway/
    config.yaml                 # RBAC + 고정 매니페스트
```

사용자가 `docker compose up`으로 배포. Claude Code, Cursor, Codex 및 opencode 사용자는 `run-research` 스킬을 호출하여 시스템 구동 가능.

### 각 13단계 레슨의 기여

| 레슨 | 캡스톤이 사용하는 것 |
|--------|------------------------|
| 01-05 | 도구 인터페이스, 제공자 이식성, 병렬 호출, 스키마, 린팅 |
| 06-10 | MCP 프리미티브, 서버, 클라이언트, 전송, 리소스 + 프롬프트 |
| 11-14 | 샘플링, 루트 + 엘리시테이션, 비동기 Tasks, `ui://` 앱 |
| 15-17 | 도구 중독, OAuth 2.1, 게이트웨이 + 레지스트리 |
| 18 | A2A 하위 에이전트 위임 |
| 19 | OTel GenAI 추적 |
| 20 | LLM 계층용 라우팅 게이트웨이 |
| 21 | SKILL.md + AGENTS.md 패키징 |

## 사용하기

`code/main.py`는 이전 레슨의 패턴을 하나의 실행 가능한 데모로 연결합니다. 모두 표준 라이브러리, 모두 인프로세스이므로 종단간 읽을 수 있음. 연구-및-보고 시나리오에 대한 전체 흐름 실행: 게이트웨이와 핸드셰이크, OAuth 2.1 시뮬레이션, tools/list 병합, 태스크로서의 generate_report, writer에 대한 A2A 호출, 반환된 ui:// 리소스, 출력된 OTel 스팬.

살펴볼 내용:

- 모든 홉에 걸친 하나의 트레이스 id.
- 게이트웨이 정책이 두 번째 사용자의 쓰기를 차단.
- 태스크 라이프사이클이 working → completed로 가고 텍스트 및 ui:// 콘텐츠 모두 반환.
- A2A 호출의 내부 상태가 오케스트레이터에게 불투명.
- AGENTS.md 및 SKILL.md가 다른 에이전트가 워크플로를 재현하는 데 필요한 유일한 파일.

## 배포하기

이 레슨은 `outputs/skill-ecosystem-blueprint.md`를 생성합니다. 제품 요구사항(연구, 요약, 자동화)이 주어지면 스킬이 전체 아키텍처를 생성: 어떤 MCP 프리미티브, 어떤 게이트웨이 제어, 어떤 A2A 호출, 어떤 텔레메트리, 어떤 패키징.

## 실습

1. `code/main.py`를 실행하세요. 단일 트레이스 id와 스팬이 중첩되는 방식을 기록하세요. 데모가 13단계의 몇 가지 프리미티브를 사용하는지 세세요.

2. 데모 확장: 두 번째 백엔드 MCP 서버(예: `bibliography`)를 추가하고 게이트웨이가 해당 도구를 동일한 네임스페이스로 병합하는지 확인하세요.

3. 가짜 A2A 작가 에이전트를 하위 프로세스에서 실행되는 실제 에이전트로 교체하세요. 19과 하네스를 사용하세요.

4. 오케스트레이터와 LLM 사이의 라우팅 게이트웨이에 PII 삭제 단계를 추가하세요. 사용자 쿼리의 이메일이 삭제되는지 확인하세요.

5. 이 시스템을 유지보수할 팀원을 위한 AGENTS.md를 작성하세요. 읽는 데 5분 미만이 걸리고 Cursor 또는 Codex에서 캡스톤을 구동하는 데 필요한 모든 것을 제공해야 합니다.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 캡스톤(Capstone) | "13단계 통합 데모" | 모든 프리미티브를 사용하는 종단간 시스템 |
| 연구 및 보고(Research and report) | "시나리오" | 검색, 요약, 렌더링 패턴 |
| 생태계(Ecosystem) | "모든 조각이 함께" | 서버 + 클라이언트 + 게이트웨이 + 하위 에이전트 + 텔레메트리 + 패키지 |
| 트레이스 계층(Trace hierarchy) | "단일 트레이스 id" | 모든 홉의 스팬이 트레이스 공유; 스팬 id로 부모-자식 |
| 게이트웨이 발급 토큰(Gateway-issued token) | "전이적 인증" | 클라이언트는 게이트웨이의 토큰만 봄; 게이트웨이가 업스트림 자격 증명 보유 |
| 병합된 네임스페이스(Merged namespace) | "모든 도구가 하나의 평면 목록에" | 게이트웨이에서 다중 서버 병합, 충돌 시 접두사 |
| 불투명성 경계(Opacity boundary) | "A2A 호출이 내부 숨김" | 하위 에이전트의 추론이 오케스트레이터에게 보이지 않음 |
| 세 가지 계층 스택(Three-layer stack) | "AGENTS.md + SKILL.md + MCP" | 프로젝트 컨텍스트 + 워크플로 + 도구 |
| 심층 방어(Defense-in-depth) | "여러 보안 계층" | 고정 해시, OAuth, RBAC, Rule of Two, 감사 로그 |
| 사양 준수 매트릭스(Spec compliance matrix) | "사양이 요구하는 것을 출시" | 산출물을 2025-11-25 요구사항에 매핑하는 체크리스트 |

## 추가 자료

- [MCP — Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — 통합 참조
- [MCP blog — 2026 roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — 프로토콜이 가는 방향
- [a2a-protocol.org](https://a2a-protocol.org/latest/) — A2A v1.0 참조
- [OpenTelemetry — GenAI semconv](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 표준 추적 규칙
- [Anthropic — Claude Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) — 프로덕션 에이전트 런타임 패턴
