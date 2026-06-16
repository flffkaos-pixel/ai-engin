# LangGraph: 상태 저장 그래프와 내구성 있는 실행

> LangGraph는 2026년 저수준 상태 저장 오케스트레이션의 참조다. 에이전트는 상태 머신이다; 노드는 함수, 엣지는 전환, 상태는 불변이며 모든 단계 후 체크포인트된다. 어떤 실패에서든 정확히 중단된 지점에서 재개한다.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 12 (Workflow Patterns)
**Time:** ~75분

## 학습 목표

- LangGraph의 핵심 모델을 설명한다: 불변 상태, 함수 노드, 조건부 엣지, 단계 후 체크포인트가 있는 상태 머신.
- 문서가 강조하는 네 가지 기능을 명명한다: 내구성 있는 실행, 스트리밍, 인간-인-더-루프, 포괄적 메모리.
- LangGraph가 지원하는 세 가지 오케스트레이션 토폴로지를 설명한다: supervisor, peer-to-peer (swarm), hierarchical (중첩 하위 그래프).
- 불변 상태, 조건부 엣지, 체크포인트/재개 사이클이 있는 stdlib 상태 그래프를 구현한다.

## 문제

에이전트와 워크플로우는 공통된 문제를 공유한다: 40단계 실행이 38단계에서 실패할 때, 처음부터 시작하지 않고 38단계에서 재개하고 싶다. 이류 상태 모델은 운영자가 새 실행을 가정하는 라이브러리 주위에 재시도를 해킹하게 만든다.

LangGraph의 설계 답변: 상태는 일급 타입 객체이고, 변이는 명시적이며, 체크포인트가 모든 노드 후에 지속된다. 재개는 `load_state(session_id)` 호출이다.

## 개념

### 그래프

그래프는 다음으로 정의된다:

- **상태 타입.** 모든 노드가 읽고 변이하는 타입화된 딕셔너리(Pydantic 모델).
- **노드.** 순수 함수 `(state) -> state_update`. 업데이트는 반환 후 상태에 병합.
- **엣지.** 노드 간 조건부 또는 직접 전환.
- **진입 및 종료.** `START`와 `END` 센티널 노드가 경계를 표시.

예: `classify`, `refund`, `bug`, `sales`, `done` 노드가 있는 에이전트 — 그래프로서의 라우팅 워크플로우.

### 내구성 있는 실행

각 노드가 반환된 후 런타임은 상태를 직렬화하고 체크포인터(SQLite, Postgres, Redis, 커스텀)에 기록한다. N단계에서 실패 시 런타임은 `resume(session_id)`로 정확한 상태로 N+1단계부터 계속할 수 있다.

LangGraph 문서는 이것이 중요한 프로덕션 사용자를 명시적으로 언급한다: Klarna, Uber, J.P. Morgan. 주장은 그래프 형태가 아니라 그래프 형태 + 체크포인팅이 복구를 저렴하게 만든다는 것이다.

### 스트리밍

모든 노드는 부분 출력을 생성할 수 있다. 그래프는 호출자에게 노드별 델타 이벤트를 스트리밍하여 그래프가 실행될 때 UI가 업데이트되도록 한다.

### 인간-인-더-루프

노드 간 상태 검사 및 수정. 구현: 중요한 노드 전에 일시 중지, 상태를 인간에게 표시, 수정 수락, 재개. 체크포인터가 상태를 이미 직렬화했기 때문에 쉽다.

### 메모리

단기(실행 내 — 상태의 대화 기록) 및 장기(실행 간 — 체크포인터 + 별도 장기 저장소를 통해 지속). LangGraph는 도구를 통해 외부 메모리 시스템(Mem0, 커스텀)과 통합.

### 세 가지 토폴로지

1. **Supervisor.** 중앙 라우터 LLM이 전문 하위 에이전트에 디스패치. `langgraph-supervisor`의 `create_supervisor()` (LangChain 팀은 2026년에 더 많은 컨텍스트 제어를 위해 도구 호출을 통해 직접 수행할 것을 권장).
2. **Swarm / peer-to-peer.** 에이전트가 공유 도구 표면을 통해 직접 핸드오프. 중앙 라우터 없음.
3. **Hierarchical.** 중첩 하위 그래프로 구현된 감독자를 관리하는 감독자.

### 이 패턴이 잘못되는 경우

- **너무 작은 체크포인트.** 대화 턴만 체크포인팅하면 도구 상태와 메모리 쓰기가 복구 불가능. 전체 상태가 직렬화되어야 함.
- **비결정론적 노드.** 재개는 노드 입력이 동일한 상태 업데이트를 생성한다고 가정. 랜덤 시드, 벽시계, 외부 API가 캡처되어야 함.
- **조건부 엣지의 과잉 사용.** 모든 엣지가 조건부인 그래프는 추론할 수 없는 상태 머신. 가끔 분기가 있는 선형 체인을 선호.

## 직접 구현하기

`code/main.py`는 stdlib 상태 저장 그래프를 구현한다:

- `State` — `messages`, `step`, `route`, `output`, `human_approval`이 있는 타입화된 딕셔너리.
- `Node` — 상태를 받아 업데이트 딕셔너리를 반환하는 호출 가능.
- `StateGraph` — 노드 + 엣지 + 조건부 엣지 + 실행 + 재개.
- `SQLiteCheckpointer` (인메모리 가짜) — 모든 노드 후 상태 직렬화; `load(session_id)` 복원.
- 데모 그래프: classify -> branch(refund / bug / sales) -> human gate -> send.

실행:

```
python3 code/main.py
```

트레이스는 첫 번째 실행이 휴먼 게이트에서 실패하고, 지속성, 그 다음 재개가 최종 출력을 생성하는 것을 보여준다.

## 활용하기

- **LangGraph** — 참조, 프로덕션 준비. `create_react_agent`, `create_supervisor` 사용 또는 자체 그래프 구축.
- **AutoGen v0.4** (레슨 14) — 높은 동시성 시나리오를 위한 액터 모델 대안.
- **Claude Agent SDK** (레슨 17) — 내장 세션 저장소가 있는 관리형 하네스.
- **커스텀** — 상태 형태나 체크포인터 백엔드에 대한 정확한 제어가 필요할 때.

## 배포하기

`outputs/skill-state-graph.md`는 모든 대상 런타임에서 체크포인팅과 재개가 연결된 LangGraph 형태의 상태 그래프를 생성한다.

## 연습 문제

1. 분류 신뢰도가 임계값 미만일 때 `classify`에서 `end`로의 조건부 엣지를 추가. 인간이 수동으로 `route`를 설정한 후 재개.
2. SQLite 유사 가짜를 실제 SQLite 체크포인터로 교체. 단계별 직렬화 오버헤드 측정.
3. 병렬 엣지 구현: 두 노드가 동시에 실행, 커스텀 리듀서로 병합. 불변 상태가 여기서 무엇을 제공하는가?
4. `langgraph-supervisor` 참조 읽기. 장난감을 `create_supervisor`로 포팅. 트레이스 형태 비교.
5. 스트리밍 추가: 각 노드가 실행 중에 부분 상태를 생성. 델타가 도착할 때 출력.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| State graph | "상태 머신으로서의 에이전트" | 타입화된 상태 + 노드 + 엣지 + 리듀서 |
| Checkpointer | "지속성 백엔드" | 모든 노드 후 상태 직렬화; 재개 활성화 |
| Reducer | "상태 병합기" | 현재 상태를 노드 업데이트와 결합하는 함수 |
| Conditional edge | "분기" | 상태의 함수에 의해 선택된 엣지 |
| Subgraph | "중첩 그래프" | 다른 그래프 내에서 노드로 사용되는 그래프 |
| Durable execution | "실패에서 재개" | 마지막 성공 노드에서 정확한 상태로 재시작 |
| Supervisor | "라우터 LLM" | 전문 하위 에이전트를 위한 중앙 디스패처 |
| Swarm | "P2P 에이전트" | 에이전트가 공유 도구를 통해 핸드오프; 중앙 라우터 없음 |

## 추가 자료

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — 참조 문서
- [langgraph-supervisor reference](https://reference.langchain.com/python/langgraph/supervisor/) — supervisor 패턴 API
- [AutoGen v0.4, Microsoft Research](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — 액터-모델 대안
- [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — 세션 저장소 및 하위 에이전트
