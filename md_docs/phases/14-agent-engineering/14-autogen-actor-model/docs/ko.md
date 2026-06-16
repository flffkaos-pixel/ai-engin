# AutoGen v0.4: 액터 모델과 에이전트 프레임워크

> AutoGen v0.4 (Microsoft Research, Jan 2025)는 액터 모델을 중심으로 에이전트 오케스트레이션을 재설계했다. 비동기 메시지 교환, 이벤트 기반 에이전트, 장애 격리, 자연스러운 동시성. 이 프레임워크는 현재 유지보수 모드이며, Microsoft Agent Framework (2025년 10월 공개 프리뷰)가 후속 제품이 될 예정이다.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 12 (Workflow Patterns)
**Time:** ~75분

## 학습 목표

- 액터 모델을 설명한다: 에이전트는 액터, 메시지는 유일한 IPC, 액터별 장애 격리.
- AutoGen v0.4의 세 가지 API 레이어(Core, AgentChat, Extensions)와 각각의 용도를 명명한다.
- 메시지 전달과 처리를 분리하는 것이 장애 격리와 자연스러운 동시성을 제공하는 이유를 설명한다.
- Python에서 stdlib 액터 런타임을 구현하고 2-에이전트 코드 리뷰 플로우를 그 위에 포팅한다.

## 문제

대부분의 에이전트 프레임워크는 동기식이다: 하나의 에이전트가 생성하고, 하나가 소비하며, 콜 스택에서 이루어진다. 실패는 스택을 중단시킨다. 동시성은 나중에 추가된다. 분산은 재작성이 필요하다.

AutoGen v0.4의 답변: 액터 모델. 각 에이전트는 개인 받은 편지함이 있는 액터다. 메시지는 유일한 상호작용이다. 런타임은 전달과 처리를 분리한다. 실패는 하나의 액터로 격리된다. 동시성은 네이티브다. 분산은 단지 다른 전송일 뿐이다.

## 개념

### 액터

액터는 다음을 가진다:

- 개인 상태 (외부에서 직접 접근 불가).
- 받은 편지함 (메시지 큐).
- 핸들러: `receive(message) -> effects`, effects는 "응답", "다른 액터에게 전송", "새 액터 생성", "상태 업데이트", "자체 중지"가 될 수 있음.

두 액터는 메모리를 공유할 수 없다. 메시지만 보낼 수 있다.

### AutoGen v0.4의 세 가지 API 레이어

1. **Core.** 저수준 액터 프레임워크. `AgentRuntime`, `Agent`, `Message`, `Topic`. 비동기 메시지 교환, 이벤트 기반.
2. **AgentChat.** 작업 기반 고수준 API (v0.2의 ConversableAgent 대체). `AssistantAgent`, `UserProxyAgent`, `RoundRobinGroupChat`, `SelectorGroupChat`.
3. **Extensions.** 통합 — OpenAI, Anthropic, Azure, 도구, 메모리.

### 분리가 중요한 이유

v0.2 모델에서 `agent_a.chat(agent_b)`를 호출하면 agent_b가 반환될 때까지 agent_a가 동기적으로 차단된다. v0.4에서 `send(agent_b, msg)`는 메시지를 agent_b의 받은 편지함에 넣고 반환된다. 런타임이 나중에 전달한다. 세 가지 결과:

- **장애 격리.** Agent B 충돌이 Agent A를 충돌시키지 않음 — 런타임이 B의 핸들러에서 실패를 잡고 무엇을 할지 결정(로그, 재시도, 데드 레터).
- **자연스러운 동시성.** 한 번에 많은 메시지가 전송 중; 액터는 동시에 받은 편지함을 처리.
- **분산 준비.** 받은 편지함 + 전송은 액터가 인프로세스든 다른 호스트든 동일한 추상화.

### 토폴로지

- **RoundRobinGroupChat.** 에이전트가 고정된 순서로 번갈아 가며 진행.
- **SelectorGroupChat.** 선택기 에이전트가 대화 컨텍스트에 따라 다음 차례를 선택.
- **Magentic-One.** 웹 브라우징, 코드 실행, 파일 처리를 위한 참조 멀티 에이전트 팀. AgentChat 기반.

### 관찰 가능성

OpenTelemetry 지원이 내장되어 있다. 모든 메시지가 스팬을 출력하고, 도구 호출은 2026년 OTel GenAI 시맨틱 규칙(레슨 23)에 따라 `gen_ai.*` 속성을 전달한다.

### 상태: 유지보수 모드

2026년 초: AutoGen v0.7.x는 연구 및 프로토타이핑에 안정적이다. Microsoft는 활성 개발을 Microsoft Agent Framework (2025년 10월 1일 공개 프리뷰; 1.0 GA는 2026년 Q1 말 목표)로 전환했다. AutoGen 패턴은 깨끗하게 포팅된다 — 액터 모델은 내구성 있는 아이디어다.

## 직접 구현하기

`code/main.py`는 stdlib 액터 런타임을 구현한다:

- `Message` — `sender`, `recipient`, `topic`, `body`가 있는 타입화된 페이로드.
- `Actor` — `receive(message, runtime)`이 있는 추상 클래스.
- `Runtime` — 공유 큐, 전달, 장애 격리가 있는 이벤트 루프.
- 2-액터 데모: `ReviewerAgent`가 코드를 검토하고, `ChecklistAgent`가 체크리스트 실행; 합의에 도달할 때까지 메시지 교환.

실행:

```
python3 code/main.py
```

트레이스는 메시지 전달, 한 액터의 시뮬레이션된 실패가 다른 액터를 충돌시키지 않음, 공유 평결에 대한 수렴을 보여준다.

## 활용하기

- **AutoGen v0.4/v0.7** (유지보수) — 연구, 프로토타이핑, 멀티 에이전트 패턴에 안정적.
- **Microsoft Agent Framework** (공개 프리뷰) — 향후 경로; 새로워진 API의 동일한 액터-모델 아이디어.
- **LangGraph swarm 토폴로지** (레슨 13) — 공유 도구 핸드오프를 통한 유사 패턴.
- **커스텀 액터 런타임** — 특정 전송(NATS, RabbitMQ, gRPC)이 필요할 때.

## 배포하기

`outputs/skill-actor-runtime.md`는 최소 액터 런타임과 주어진 멀티 에이전트 작업에 대한 팀 템플릿(RoundRobin 또는 Selector)을 생성한다.

## 연습 문제

1. 데드 레터 큐 추가: 핸들러가 예외를 발생시키면 실패한 메시지를 사람 검사를 위해 보류. 장난감에서 DLQ가 얼마나 자주 적중되는가?
2. `SelectorGroupChat` 구현: 선택기 액터가 대화 상태에 따라 다음 메시지를 처리할 대상을 선택.
3. 분산 전송 추가: 인프로세스 큐를 JSON-over-HTTP 서버로 교체하여 액터가 별도 프로세스에서 실행될 수 있도록 함.
4. 메시지당 OTel 스팬(또는 no-op 대체) 연결. 레슨 23에 따라 `gen_ai.agent.name`, `gen_ai.operation.name` 출력.
5. AutoGen v0.4의 아키텍처 게시물 읽기. 장난감을 실제 `autogen_core` API로 포팅. 프로덕션에서 중요한 것을 무엇을 건너뛰었는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Actor | "에이전트" | 개인 상태 + 받은 편지함 + 핸들러; 공유 메모리 없음 |
| Message | "이벤트" | 타입화된 페이로드; 액터가 상호작용하는 유일한 방법 |
| Inbox | "사서함" | 액터별 보류 메시지 큐 |
| Runtime | "에이전트 호스트" | 메시지를 라우팅하고 실패를 격리하는 이벤트 루프 |
| Topic | "채널" | 액터 간 명명된 게시-구독 경로 |
| Fault isolation | "죽게 두기" | 한 액터의 실패가 다른 액터를 충돌시키지 않음 |
| RoundRobinGroupChat | "고정 순환 팀" | 에이전트가 순서대로 번갈아 가며 진행 |
| SelectorGroupChat | "컨텍스트 라우팅 팀" | 선택기가 다음 차례를 선택 |
| Magentic-One | "참조 팀" | 웹 + 코드 + 파일을 위한 멀티 에이전트 스쿼드 |

## 추가 자료

- [AutoGen v0.4, Microsoft Research](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — 재설계 게시물
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — 그래프 형태 대안
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — AutoGen이 기본으로 출력하는 스팬
