# 캐피톤 01 — 터미널 네이티브 코딩 에이전트

> 2026년이 되자 코딩 에이전트의 형태가 확정되었다. TUI 해네스, 상태 저장 계획, 샌드박스 도구 표면, 계획-실행-관찰-복구 루프. Claude Code, Cursor 3, OpenCode는 50피트 거리에서는 모두 동일해 보인다. 이 캐피톤은 종단 간 구축을 요청한다 — CLI 입력, 풀 리퀘스트 출력 — 그리고 mini-swe-agent 및 Live-SWE-agent와 함께 SWE-bench Pro에서 측정. 가장 어려운 부분은 모델 호출이 아니라 도구 루프, 샌드박스, 50턴 실행에서의 비용 상한이라는 것을 배우게 될 것이다.

**유형:** 캐피톤
**언어:** TypeScript / Bun (해네스), Python (평가 스크립트)
**선수 과목:** Phase 11 (LLM 엔지니어링), Phase 13 (도구 및 프로토콜), Phase 14 (에이전트), Phase 15 (자율 시스템), Phase 17 (인프라)
**연습 phases:** P0 · P5 · P7 · P10 · P11 · P13 · P14 · P15 · P17 · P18
**시간:** 35시간

## 문제

코딩 에이전트는 2026년 지배적인 AI 애플리케이션 카테고리가 되었다. Claude Code (Anthropic), Cursor 3의 Composer 2 및 Agent Tabs (Cursor), Amp (Sourcegraph), OpenCode (112k 스타), Factory Droids, Google Jules 모두 동일한 아키텍처의 변형을 제공한다: 터미널 해네스, 권한이 부여된 도구 표면, 샌드박스, 프론티어 모델을 중심으로 구축된 계획-실행-관찰 루프. 프론티어는 좁다 — Live-SWE-agent는 Opus 4.5로 SWE-bench Verified에서 79.2%에 도달했다 — 하지만 엔지니어링Craft는 광범위하다. 대부분의 실패 모드는 모델 실수가 아니다. 도구 루프 불안정성, 컨텍스트 오염,失控 토큰 비용, 파괴적인 파일 시스템 작업이다.

对这些 에이전트를 외부에서 추론할 수 없다. 하나를 구축하고, ripgrep이 8MB의 일치 항목을 반환할 때 턱 47에서 루프가 충돌하는 것을 보고, then truncate 레이어를 다시 구축해야 한다. 이것이 이 캐피톤의 요점이다.

## 개념

해네스에는 네 가지 표면이 있다. **계획**은 모델이 각 턴마다 덮어 쓰는 TodoWrite 스타일 상태 객체를 유지한다. **실행**은 도구 호출(read, edit, run, search, git)을 디스패치한다. **관찰**은 stdout/stderr/exit 코드를 캡처하고, then truncate하고, 요약을 다시 피드백한다. **복구**는 컨텍스트 창을 날리는 나가는 않고 영원히 루프되지 않고 도구 오류를 처리한다. 2026년 형태는 하나를 더 추가한다: **훅**. `PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `Notification`, `Stop`, `PreCompact` — 운영자가 정책, 텔레메트리, 가드레일을 주입하는 구성 가능한 확장 포인트.

샌드박스는 E2B 또는 Daytona이다. 각 작업은 git worktree가 읽기-쓰기로 마운트된 새로운 devcontainer에서 실행된다. 해네스는 호스트 파일 시스템을 절대 건드리지 않는다. worktree는 성공 또는 실패 시 해체된다. 비용 제어는 세 가지 레이어에서 적용된다: 턴당 토큰 상한, 세션당 달러 예산, 하드 턴 제한(일반적으로 50). 가시성 레이어는 자체 호스팅 Langfuse로 전송되는 GenAI 의미 규칙이 있는 OpenTelemetry 스팬이다.

## 아키텍처

```
  user CLI  ->  harness (Bun + Ink TUI)
                  |
                  v
           plan / act / observe loop  <--->  Claude Sonnet 4.7 / GPT-5.4-Codex / Gemini 3 Pro
                  |                          (via OpenRouter, model-agnostic)
                  v
           tool dispatcher (MCP StreamableHTTP client)
                  |
      +------------+------------+----------+
      v            v            v          v
   read/edit    ripgrep     tree-sitter   git/run
      |            |            |          |
      +------------+------------+----------+
                  |
                  v
           E2B / Daytona sandbox  (worktree isolated)
                  |
                  v
           hooks: Pre/Post, Session, Prompt, Compact
                  |
                  v
           OpenTelemetry -> Langfuse (spans, tokens, $)
                  |
                  v
           PR via GitHub app
```

## 스택

- 해네스 런타임: Bun 1.2 + Ink 5 (React-in-terminal)
- 모델 액세스: Claude Sonnet 4.7, GPT-5.4-Codex, Gemini 3 Pro, Opus 4.5 (가장 어려운 작업용)를 갖춘 OpenRouter 통합 API
- 도구 전송: 모델 컨텍스트 프로토콜 StreamableHTTP (MCP 2026 수정)
- 샌드박스: E2B sandboxes (JS SDK) 또는 Daytona devcontainers
- 코드 검색: 17개 언어용 ripgrep 하위 프로세스, tree-sitter 파서(사전 컴파일됨)
- 격리: 작업당 `git worktree add -b agent/$TASK_ID`, 성공/실패 시 정리
- 평가 해네스: SWE-bench Pro (검증된 하위 집합) + Terminal-Bench 2.0 + 자체 30개 작업 홀드아웃
- 가시성: `gen_ai.*` semconv가 있는 OpenTelemetry SDK → 자체 호스팅 Langfuse
- PR 게시: 세분화된 토큰이 있는 GitHub App, 대상repo로 범위 제한

## 구축

1. **TUI 및 명령 루프.** Ink로 Bun 프로젝트 스캐폴딩. `agent run <repo> "<task>"`를 받아들인다. 분할 보기 인쇄: 계획 창(상단), 도구 호출 스트림(가운데), 토큰 예산(하단). Ctrl-C에서 취소는 종료 전 `SessionEnd` 훅을 실행한다.

2. **계획 상태.** Typed TodoWrite 스키마 정의 (메모가 있는 pending/in_progress/done 항목). 모델은 각 턴마다 전체 상태를 도구 호출로 덮어 쓴다 — 점진적으로 변형하지 않는다. 크래시에서 재개할 수 있도록 `.agent/state.json`에 계획을 유지한다.

3. **도구 표면.** 6개 도구 정의: `read_file`, `edit_file`(diff 미리보기 포함), `ripgrep`, `tree_sitter_symbols`, `run_shell`(타임아웃 포함), `git`(status/diff/commit/push). 해네스가 transport에 구애받지 않도록 MCP StreamableHTTP로 노출. 모든 도구는 then truncate된 출력을 반환(호출당 4k 토큰으로 제한).

4. **샌드박스 래핑.** 각 작업은 E2B 샌드박스를 생성한다. `git worktree add -b agent/$TASK_ID` 새 분기. 모든 도구 호출은 샌드박스 내에서 실행된다. 호스트 파일 시스템에 연결할 수 없다.

5. **훅.** 8개의 2026 훅 유형 모두 구현. 최소 4개의 사용자 제작 훅 연결: (a) worktree 외부에서 `rm -rf`를 차단하는 `PreToolUse` 파괴적 명령 가드, (b) `PostToolUse` 토큰 회계, (c) `SessionStart` 예산 초기화, (d) `Stop` 최종 추적 번들 작성.

6. **평가 루프.** SWE-bench Pro Python의 30개 이슈 하위 집합 클론. 각 항목에 대해 해네스 실행. pass@1, 턴/작업, $/작업에서 mini-swe-agent(최소 기준)와 비교. 결과를 `eval/results.jsonl`에 기록.

7. **비용 제어.** 하드 컷오프: 50턴, 200k 컨텍스트, 작업당 $5. `PreCompact` 훅은 150k 표시에서 이전 턴을 사전 상태 블록으로 요약하여 새 관찰을 위한 공간을 확보하면서 계획을 손실하지 않는다.

8. **PR 게시.** 성공 시 최종 단계는 `git push` + PR을 여는 GitHub API 호출으로 본문에 계획과 diff 요약을 포함한다.

## 사용

```
$ agent run ./my-repo "Fix the race condition in worker.rs"
[plan]  1 locate worker.rs and enumerate mutex uses
        2 identify shared state under contention
        3 propose fix, verify tests
[tool]  ripgrep mutex.*lock -t rust           (44 matches, truncated)
[tool]  read_file src/worker.rs 120..180
[tool]  edit_file src/worker.rs (+8 -3)
[tool]  run_shell cargo test worker::          (passed)
[plan]  1 done · 2 done · 3 done
[done]  PR opened: #482   turns=9   tokens=38k   cost=$0.41
```

## 발송

산출물 skill은 `outputs/skill-terminal-coding-agent.md`에 있다. repo 경로와 작업 설명이 주어지면 샌드박스에서 전체 계획-실행-관찰 루프를 실행하고 PR URL과 추적 번들을 반환한다. 이 캐피톤의 기준표:

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 vs 기준선 | 30개 일치 Python 작업에서 해네스 vs mini-swe-agent |
| 20 | 아키텍처 명확성 | Plan/act/observe 분리, 훅 표면, 도구 스키마 — Live-SWE-agent 레이아웃과 비교하여 검토 |
| 20 | 안전성 | 샌드박스 이스케이프 테스트, 권한 프롬프트, 파괴적 명령 가드 레드팀 통과 |
| 20 | 가시성 | 추적 완전성(도구 호출의 100% 스팬), 턴당 토큰 회계 |
| 15 | 개발자 UX | 콜드 스타트 < 2초, 크래시 복구 계획 재개, Ctrl-C가 도중 도구에서 깔끔하게 취소 |
| **100** | | |

## 연습 문제

1. 지원 모델을 Claude Sonnet 4.7에서 vLLM에서 서비스되는 Qwen3-Coder-30B로 전환한다. pass@1과 $/작업을 비교한다. 열린 모델이 성능이 저하되는 위치를 보고한다.

2. PR 게시 전에 diff를 읽고 수정 루프를 요청할 수 있는 `reviewer` 하위 에이전트를 추가한다. 거짓 양성 검토가 SWE-bench 패스 비율을 단일 에이전트 기준선 아래로 떨어뜨리는지 측정한다(힌트: 일반적으로 그렇다).

3. 샌드박스 스트레스 테스트: 외부 URL로 `curl`을 시도하는 작업과 worktree 외부에 작성하는 작업을 작성한다. 둘 다 `PreToolUse` 훅에 의해 차단되는지 확인한다. 시도를 기록한다.

4. 더 작은 모델(Haiku 4.5)로 `PreCompact` 요약을 구현한다. 3x 압축에서 계획 충실도가 얼마나 손실되는지 측정한다.

5. MCP StreamableHTTP 전송을 stdio로 전환한다. 콜드 스타트 및 호출당 지연 시간 벤치마크. 로컬 전용 사용 시 승자를 선택한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| Harness | "에이전트 루프" | 도구를 디스패치하고, 계획 상태를 유지하고, 예산을 적용하는 모델을 둘러싼 코드 |
| Hook | "에이전트 이벤트 리스너" | 해네스에 의해 8개의 수명 주기 이벤트 중 하나에서 실행되는 사용자 제작 스크립트 |
| Worktree | "Git 샌드박스" | 별도 경로의 링크된 git 체크아웃; 메인 클론을 건드리지 않고 폐기 가능 |
| TodoWrite | "계획 상태" | 모델이 각 턴마다 덮어 쓰는 pending/in-progress/done 항목의 타입 목록 |
| StreamableHTTP | "MCP 전송" | 2026 MCP 수정: 양방향 스트리밍이 있는 긴 수명 HTTP 연결; SSE 대체 |
| Token ceiling | "컨텍스트 예산" | 턴당 또는 세션당 입력+출력 토큰에 대한 상한; 압축 또는 종료를 트리거 |
| pass@1 | "단일 시도 패스율" | 재시도 또는 테스트 세트 피킹 없이 첫 번째 실행에서 해결된 SWE-bench 작업의 비율 |

## 추가 자료

- [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) — Anthropic의 참조 해네스
- [Cursor 3 changelog](https://cursor.com/changelog) — Agent Tabs 및 Composer 2 제품 노트
- [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) — SWE-bench 해네스 비교를 위한 최소 기준
- [Live-SWE-agent](https://github.com/OpenAutoCoder/live-swe-agent) — Opus 4.5로 79.2% SWE-bench Verified 달성
- [OpenCode](https://opencode.ai) — 열린 해네스, 112k 스타
- [SWE-bench Pro leaderboard](https://www.swebench.com) — 이 캐피톤이目标是 평가
- [Model Context Protocol 2026 roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — StreamableHTTP, 기능 메타데이터
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 도구 호출 및 토큰 사용에 대한 스팬 스키마