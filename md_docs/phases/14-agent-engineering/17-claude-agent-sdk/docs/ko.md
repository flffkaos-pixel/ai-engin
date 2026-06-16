# Claude Agent SDK: 하위 에이전트와 세션 저장소

> Claude Agent SDK는 Claude Code 하네스의 라이브러리 형태다. 내장 도구, 컨텍스트 격리를 위한 하위 에이전트, 훅, W3C 트레이스 전파, 세션 저장소 패리티. Claude Managed Agents는 장기 실행 비동기 작업을 위한 호스팅 대안이다.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 10 (Skill Libraries)
**Time:** ~75분

## 학습 목표

- Anthropic Client SDK(원시 API)와 Claude Agent SDK(하네스 형태)의 차이를 설명한다.
- 하위 에이전트(병렬화 및 컨텍스트 격리)와 이를 사용해야 할 때를 설명한다.
- Python SDK의 세션 저장소 표면(`append`, `load`, `list_sessions`, `delete`, `list_subkeys`)과 `--session-mirror`의 역할을 명명한다.
- 내장 도구, 격리된 컨텍스트가 있는 하위 에이전트 생성, 생명주기 훅, 세션 저장소가 있는 stdlib 하네스를 구현한다.

## 문제

원시 LLM API는 한 번의 왕복만 제공한다. 프로덕션 에이전트는 도구 실행, MCP 서버, 생명주기 훅, 하위 에이전트 생성, 세션 지속성, 트레이스 전파가 필요하다. Claude Agent SDK는 이 형태를 라이브러리로 제공한다 — Claude Code가 사용하는 것과 동일한 하네스, 커스텀 에이전트용으로 공개됨.

## 개념

### Client SDK vs Agent SDK

- **Client SDK (`anthropic`).** 원시 Messages API. 루프, 도구, 상태를 사용자가 소유.
- **Agent SDK (`claude-agent-sdk`).** 내장 도구 실행, MCP 연결, 훅, 하위 에이전트 생성, 세션 저장소. 라이브러리로서의 Claude Code 루프.

### 내장 도구

SDK는 10개 이상의 도구를 기본 제공: 파일 읽기/쓰기, 셸, grep, glob, 웹 페치 등. 커스텀 도구는 표준 도구-스키마 인터페이스를 통해 등록.

### 하위 에이전트

Anthropic이 문서화한 두 가지 목적:

1. **병렬화.** 독립적인 작업을 동시에 실행. "20개 모듈 각각에 대한 테스트 파일 찾기"는 20개의 병렬 하위 에이전트 작업.
2. **컨텍스트 격리.** 하위 에이전트는 자체 컨텍스트 윈도우 사용; 결과만 오케스트레이터에 반환. 오케스트레이터의 예산 보존.

Python SDK 최근 추가: 하위 에이전트 트랜스크립트 읽기를 위한 `list_subagents()`, `get_subagent_messages()`.

### 세션 저장소

TypeScript와의 프로토콜 패리티:

- `append(session_id, message)` — 턴 추가.
- `load(session_id)` — 대화 복원.
- `list_sessions()` — 열거.
- `delete(session_id)` — 하위 에이전트 세션으로 계단식 삭제.
- `list_subkeys(session_id)` — 하위 에이전트 키 나열.

`--session-mirror` (CLI 플래그) — 디버깅을 위해 스트리밍 중 트랜스크립트를 외부 파일에 미러링.

### 훅

등록할 수 있는 생명주기 훅:

- `PreToolUse`, `PostToolUse` — 도구 호출 게이트 또는 감사.
- `SessionStart`, `SessionEnd` — 설정 및 해제.
- `UserPromptSubmit` — 모델이 보기 전에 사용자 입력 처리.
- `PreCompact` — 컨텍스트 압축 전 실행.
- `Stop` — 에이전트 종료 시 정리.
- `Notification` — 사이드 채널 알림.

훅은 pro-workflow (Phase 14 커리큘럼 참조) 및 유사 시스템이 교차 행동을 추가하는 방법이다.

### W3C 트레이스 컨텍스트

호출자의 OTel 스팬이 W3C 트레이스 컨텍스트 헤더를 통해 CLI 하위 프로세스로 전파. 전체 멀티 프로세스 트레이스가 백엔드에서 하나의 트레이스로 표시.

### Claude Managed Agents

호스팅 대안 (베타 헤더 `managed-agents-2026-04-01`). 장기 실행 비동기 작업, 내장 프롬프트 캐싱, 내장 압축. 제어를 관리형 인프라와 교환.

### 이 패턴이 잘못되는 경우

- **하위 에이전트 과잉 생성.** 100개의 작은 작업에 100개의 하위 에이전트 생성. 오버헤드가 지배. 배치로 처리.
- **훅 증식.** 모든 팀이 훅을 추가; 시작 시간 증가. 분기별 훅 검토.
- **세션 비대.** 세션 축적; 크기 증가. `list_sessions` + 만료 정책 사용.

## 직접 구현하기

`code/main.py`는 SDK 형태를 stdlib으로 구현한다:

- `Tool`, `ToolRegistry` with built-in `read_file`, `write_file`, `list_dir`.
- `Subagent` — 개인 컨텍스트, 격리된 실행, 결과 반환.
- `SessionStore` — append, load, list, delete, list_subkeys.
- `Hooks` — `pre_tool_use`, `post_tool_use`, `session_start`, `session_end`.
- 데모: 메인 에이전트가 3개의 하위 에이전트를 병렬로 생성(각각 격리됨), 결과 집계, 세션 지속.

실행:

```
python3 code/main.py
```

트레이스는 하위 에이전트 컨텍스트 격리(오케스트레이터 컨텍스트 크기 제한 유지), 훅 실행 및 세션 지속성을 보여준다.

## 활용하기

- **Claude Agent SDK** for Claude-first products that want the Claude Code harness shape.
- **Claude Managed Agents** for hosted long-running async work.
- **OpenAI Agents SDK** (레슨 16) for OpenAI-first counterparts.
- **LangGraph + custom tools** if you want the graph-shaped state machine instead.

## 배포하기

`outputs/skill-claude-agent-scaffold.md` scaffolds a Claude Agent SDK app with subagents, hooks, session store, MCP server attachment, and W3C trace propagation.

## 연습 문제

1. 하위 에이전트 생성기가 20개의 작업을 5개의 병렬 하위 에이전트 그룹으로 배치. 작업당 하나와 비교하여 오케스트레이터 컨텍스트 크기 측정.
2. 세션당 분당 5회로 `write_file` 호출을 제한하는 `PreToolUse` 훅 구현. 동작 추적.
3. 하위 에이전트 트리를 렌더링하도록 `list_subkeys` 연결. 깊은 중첩은 어떻게 보이는가?
4. 장난감을 실제 `claude-agent-sdk` Python 패키지로 포팅. 도구 등록에 대해 무엇이 바뀌는가?
5. Claude Managed Agents 문서 읽기. 자체 호스팅에서 관리형으로 전환하는 시기는?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Agent SDK | "라이브러리로서의 Claude Code" | 하네스 형태: 도구, MCP, 훅, 하위 에이전트, 세션 저장소 |
| Subagent | "자식 에이전트" | 별도 컨텍스트, 자체 예산; 결과가 위로 버블링 |
| Session store | "대화 DB" | 하위 에이전트 계단식으로 턴 저장, 로드, 나열, 삭제 |
| Hook | "생명주기 콜백" | 도구 전/후, 세션, 프롬프트 제출, 압축, 중지 |
| W3C trace context | "프로세스 간 트레이스" | 부모 스팬이 CLI 하위 프로세스로 전파 |
| Managed Agents | "호스팅 하네스" | Anthropic 호스팅 장기 실행 비동기 작업 |
| `--session-mirror` | "트랜스크립트 미러" | 스트리밍 중 세션 턴을 외부 파일에 기록 |
| MCP server | "도구 표면" | 에이전트에 연결된 외부 도구/리소스 소스 |

## 추가 자료

- [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — the library form of Claude Code
- [Anthropic, Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — production patterns
- [Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) — hosted alternative
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) — counterpart
