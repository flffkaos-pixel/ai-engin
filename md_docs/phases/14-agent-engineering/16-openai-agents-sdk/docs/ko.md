# OpenAI Agents SDK: Handoffs, Guardrails, Tracing

> OpenAI Agents SDK는 Responses API 기반의 경량 멀티 에이전트 프레임워크다. 다섯 가지 기본 요소: Agent, Handoff, Guardrail, Session, Tracing. Handoffs는 `transfer_to_<agent>`라는 이름의 도구다. Guardrails는 입력 또는 출력에서 발동한다. Tracing은 기본적으로 켜져 있다.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 06 (Tool Use)
**Time:** ~75분

## 학습 목표

- OpenAI Agents SDK의 다섯 가지 기본 요소를 명명한다.
- Handoffs를 설명한다: 도구로 모델링되는 이유, 모델이 보는 이름 형태, 컨텍스트 전송 방법.
- 입력 가드레일, 출력 가드레일, 도구 가드레일을 구분하고 `run_in_parallel`과 블로킹 모드를 설명한다.
- Handoffs + Guardrails + 스팬 스타일 트레이싱이 있는 stdlib 런타임을 구현한다.

## 문제

깔끔하게 위임할 수 없는 에이전트는 모든 것을 하나의 프롬프트에 채워 넣는다. 가드레일이 없는 에이전트는 PII, 정책 위반 출력을 제공하거나 무한 루프에 빠진다. OpenAI의 SDK는 멀티 에이전트 작업을 다루기 쉽게 만드는 세 가지 기본 요소를 코드화한다.

## 개념

### 다섯 가지 기본 요소

1. **Agent.** LLM + 지시사항 + 도구 + handoffs.
2. **Handoff.** 다른 에이전트로의 위임. 모델에 `transfer_to_<agent_name>`이라는 도구로 표시.
3. **Guardrail.** 입력(첫 번째 에이전트만), 출력(마지막 에이전트만), 또는 도구 호출(함수 도구별)에 대한 검증.
4. **Session.** 턴 간 자동 대화 기록.
5. **Tracing.** LLM 생성, 도구 호출, handoffs, guardrails에 대한 내장 스팬.

### 도구로서의 Handoffs

모델은 도구 목록에서 `transfer_to_billing_agent`를 본다. 호출은 런타임에 다음을 지시:

1. 대화 컨텍스트 복사 (또는 `nest_handoff_history` 베타를 통해 축소).
2. 대상 에이전트를 해당 지시사항으로 초기화.
3. 대상 에이전트로 실행 계속.

이것이 제품화된 supervisor 패턴(레슨 13 / 레슨 28)이다.

### Guardrails

세 가지 종류:

- **입력 가드레일.** 첫 번째 에이전트의 입력에서 실행. 모든 LLM 호출 전에 안전하지 않거나 범위 외 요청 거부.
- **출력 가드레일.** 마지막 에이전트의 출력에서 실행. PII 누출, 정책 위반, 잘못된 형식 응답 포착.
- **도구 가드레일.** 함수 도구별 실행. 인수 검증, 권한 확인, 실행 감사.

모드:

- **병렬** (기본). 가드레일 LLM이 메인 LLM과 함께 실행. 더 낮은 꼬리 지연 시간. 발동 시 메인 LLM의 작업 폐기(토큰 낭비).
- **블로킹** (`run_in_parallel=False`). 가드레일 LLM이 먼저 실행. 발동 시 메인 호출에 토큰 낭비 없음.

트립와이어는 `InputGuardrailTripwireTriggered` / `OutputGuardrailTripwireTriggered`를 발생시킨다.

### Tracing

기본적으로 켜짐. 모든 LLM 생성, 도구 호출, handoff 및 guardrail이 스팬을 출력. `OPENAI_AGENTS_DISABLE_TRACING=1`로 옵트아웃. `add_trace_processor(processor)`는 OpenAI의 것과 함께 자체 백엔드로 스팬을 전달.

### Sessions

`Session`은 대화 기록을 백엔드(SQLite, Redis, 커스텀)에 저장. `Runner.run(agent, input, session=session)`은 자동 로드 및 추가.

### 이 패턴이 잘못되는 경우

- **Handoff 드리프트.** Agent A가 Agent B로 핸드오프, B가 다시 A로 핸드오프. 홉 카운터 추가.
- **Guardrail 우회.** 도구 가드레일은 함수 도구에서만 발동; 내장 도구(파일 리더, 웹 페치)는 별도 정책 필요.
- **과도한 트레이싱.** 스팬의 민감 콘텐츠. OTel GenAI 콘텐츠 캡처 규칙(레슨 23)과 함께 사용 — 외부 저장, ID로 참조.

## 직접 구현하기

`code/main.py`는 stdlib에서 SDK 형태를 구현한다:

- `Agent`, `FunctionTool`, `Handoff` (전송 의미가 있는 함수 도구).
- 입력/출력/도구 가드레일, handoff 디스패치 및 홉 카운터가 있는 `Runner`.
- 트레이스 형태를 보여주는 간단한 스팬 이미터.
- 사용자 쿼리에 따라 청구 또는 지원으로 핸드오프하는 트라이지 에이전트; 하나의 입력에서 가드레일 발동.

실행:

```
python3 code/main.py
```

트레이스는 두 번의 성공적인 핸드오프, 한 번의 입력 가드레일 발동 및 실제 SDK가 출력하는 것을 미러링하는 스팬 트리를 보여준다.

## 활용하기

- **OpenAI Agents SDK** for OpenAI-first products.
- **Claude Agent SDK** (레슨 17) for Claude-first products.
- **LangGraph** (레슨 13) when you want explicit state and durable resume.
- **Custom** when you need exact control (voice, multi-provider, federated deployments).

## 배포하기

`outputs/skill-agents-sdk-scaffold.md` scaffolds an Agents SDK app with a triage agent, handoffs, input/output/tool guardrails, session store, and a trace processor.

## 연습 문제

1. 핸드오프 홉 카운터 추가: N회 전송 후 거부. 동작 추적.
2. `nest_handoff_history`를 옵션으로 구현 — 전송 전에 이전 메시지를 하나의 요약으로 축소.
3. 블로킹 출력 가드레일 작성. 발동할 프롬프트와 통과할 프롬프트의 지연 시간 비교.
4. `add_trace_processor`를 JSON 로거에 연결. 스팬당 어떤 형태를 출력하는가?
5. SDK 문서 읽기. stdlib 장난감을 `openai-agents-python`으로 포팅. 무엇을 잘못 모델링했는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Agent | "LLM + 지시사항" | SDK의 Agent 유형; 도구와 handoffs 소유 |
| Handoff | "전송" | 다른 에이전트에 위임하기 위해 모델이 호출하는 도구 |
| Guardrail | "정책 확인" | 입력 / 출력 / 도구 호출에 대한 검증 |
| Tripwire | "가드레일 발동" | 가드레일이 거부할 때 발생하는 예외 |
| Session | "기록 저장소" | 실행 간 유지되는 대화 메모리 |
| Tracing | "스팬" | LLM + 도구 + handoff + guardrail에 대한 내장 관찰 가능성 |
| Blocking guardrail | "순차적 확인" | 가드레일이 먼저 실행; 발동 시 토큰 낭비 없음 |
| Parallel guardrail | "동시 확인" | 가드레일이 함께 실행; 더 낮은 지연 시간, 발동 시 토큰 낭비 |

## 추가 자료

- [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/) — primitives, handoffs, guardrails, tracing
- [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — Claude-flavored counterpart
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — when to reach for handoffs at all
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — the standard Agents SDK spans map to
