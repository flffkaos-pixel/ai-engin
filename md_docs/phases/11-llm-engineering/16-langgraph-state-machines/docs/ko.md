# LangGraph — 에이전트를 위한 상태 머신

> 손으로 작성한 ReAct 루프는 `while True`입니다. LangGraph로 작성한 ReAct 루프는 检查점 있고, 중단하고, 분기하고, 시간 여행할 수 있는 그래프입니다. agent는 변경되지 않았습니다. 주변의 harness가 변경되었습니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 11 · 09 (Function Calling), Phase 11 · 14 (Model Context Protocol)
**소요 시간:** ~75분

## 문제

함수 호출 agent를 shipping합니다. 3턴 동안 작동한 다음 무언가 잘못됩니다: 모델이 500을 반환하는 도구를 시도하거나, 사용자가 작업 중간에 마음을 바꾸거나, agent가 인간의 사인이 없이 주문을 환불하기로 결정합니다. `while True:` 루프에는 훅이 없습니다. 일시 정지할 수 없고, 되감을 수 없으며, "모델이 다른 도구를 선택했다면 어떻게 될까"로分支할 수 없습니다. 데모를 넘어 shipping하는 순간, agent는 작동했거나 작동하지 않은 블랙 박스가 됩니다.

다음 단계는 보면 명확합니다. agent는 이미 상태 머신입니다 -- 시스템 프롬프트 plus 메시지 기록 plus 보류 중인 도구 호출 plus 다음 액션. 상태 머신을 명시적으로 만듭니다: "모델이 생각함", "도구 실행", "인간 승인"을 위한 노드와 그 사이의 조건부 전환을 위한 엣지. 그래프가 명시적이면 harness는 자동으로 4가지를 얻습니다: 检查점(단계 간 상태 저장), 인터럽트(인간을 위해 일시 정지), 스트리밍(토큰 및 중간 이벤트 스트리밍), 시간 여행(이전 상태로 되감기 및 다른 분기 시도).

LangGraph는 이 추상화를 shipping하는 라이브러리입니다. LangChain 의미의 agent 프레임워크가 아닙니다("AgentExecutor가 여기 있습니다, 행운을 빕니다"). 일급 상태, 일급 지속성, 일급 인터럽트가 있는 그래프 런타임입니다. agent 루프는 손으로 작성하는 것이 아니라 그리는 것입니다.

## 개념

![LangGraph StateGraph: 노드, 엣지 및检查점](../assets/langgraph-stategraph.svg)

`StateGraph`에는 3가지가 있습니다.

1. **상태.** 그래프를 통해 흐르는 타입 dict(TypedDict 또는 Pydantic 모델). 모든 노드가 전체 상태를 수신하고 부분 업데이트를 반환하며, LangGraph는 필드당 *reducer*를 사용하여 병합합니다 -- 누적되어야 하는 리스트의 경우 `operator.add`, 기본적으로 덮어쓰기.
2. **노드.** Python 함수 `state -> partial_state`. 각각이 discrete 단계입니다: "모델 호출", "도구 실행", "요약."
3. **엣지.** 노드 간 전환. 정적 엣지는 한 곳으로 갑니다. 조건부 엣지는 라우터 함수 `state -> next_node_name`를 사용하여 그래프가 모델 출력에서 분기할 수 있도록 합니다.

그래프를 컴파일합니다. 컴파일은 토폴로지를 바인딩하고检查점기(선택적이지만 프로덕션에 필수)를 첨부하고 실행 가능한 것을 반환합니다. 초기 상태와 `thread_id`로 호출합니다. 실행의 모든 단계는 `(thread_id, checkpoint_id)`를 키로 하는 检查점을persists합니다.

### 네 가지 초능력

**检查점.** 모든 노드 전환은 새 상태를 저장소(테스트는 메모리 내, 프로드는 Postgres/Redis/SQLite)에 씁니다. 동일한 `thread_id`로 그래프를 다시 호출하여 재개합니다. 그래프가 일시 정지한 곳에서 pick up합니다.

**인터럽트.** `interrupt_before=["human_review"]`로 노드를 표시하면 해당 노드 실행 전에 실행이 중지됩니다. 상태가 유지됩니다. API가 "승인 대기 중"이라는 메시지로 사용자에게 응답합니다. 나중에 동일한 `thread_id`로 `Command(resume=...)`를 포함한 요청이 실행을 재개합니다.

**스트리밍.** `graph.stream(state, mode="updates")`는 발생하는 상태 델타를 산출합니다. `mode="messages"`는 모델 노드 내의 LLM 토큰을 스트리밍합니다. `mode="values"`는 전체 스냅샷을 산출합니다. UI에何をsurface할지 선택합니다.

**시간 여행.** `graph.get_state_history(thread_id)`는 전체 检查점 로그를 반환합니다. 이전 `checkpoint_id`를 `graph.invoke`에 전달하면 해당 지점에서 fork합니다. 디버깅("모델이 도구 B를 선택했다면 어떻게 될까?") 및 프로덕션 트레이스를 replay하는 회귀 테스트에 훌륭합니다.

### reducer가 핵심입니다

모든 상태 필드에 reducer가 있습니다. 대부분 기본값이 fine합니다 -- 새 값이 오래된 값을 덮어씁니다. 하지만 메시지 리스트에는 `operator.add`가 필요하여 새 메시지가 대체 대신 추가됩니다. 병렬 엣지는 상태 reducer를 통해 업데이트를 병합합니다. 두 노드가 모두 `messages`를 업데이트하고 `Annotated[list, add_messages]`를 잊어버리면 두 번째 것이 조용히 승리하고 반 턴을 잃습니다. reducer는 라이브러리에서 유일하게 미묘한 것입니다; 올바르게 하면 나머지는 composition됩니다.

### 4개의 노드로 ReAct 그래프

프로덕션 ReAct agent는 4개의 노드와 2개의 엣지입니다:

1. `agent` -- 현재 메시지 기록으로 LLM을 호출합니다. 도구 호출을 포함할 수 있는 어시스턴트 메시지를 반환합니다.
2. `tools` -- 마지막 어시스턴트 메시지의 모든 도구 호출을 실행하고 도구 결과를 도구 메시지로 추가합니다.
3. 마지막 메시지에 tool_calls가 있으면 `tools`로, 그렇지 않으면 `END`로 라우팅하는 `agent`의 조건부 엣지.
4. `tools`에서 `agent`로의 정적 엣지.

그것으로 끝입니다. 약 40줄의 코드로 检查점, 인터럽트 및 스트리밍이 포함된 전체 ReAct 루프(생각 → 행동 → 관찰 → 생각 → …)를 얻습니다.

### StateGraph 대 Send (fanout)

`Send(node_name, state)`를 사용하면 노드에서 병렬 하위 그래프를 dispatch할 수 있습니다. 예: agent가 한 번에 3개의 검색기를 쿼리하기로 결정합니다. 각 `Send`는 대상 노드의 병렬 실행을 생성합니다. 출력이 상태 reducer를 통해 병합됩니다. 이것이 LangGraph가 스레딩 기본 원리 없이 오케스트레이터-workers 패턴을 표현하는 방법입니다.

### 하위 그래프

컴파일된 그래프는 another 그래프의 노드가 될 수 있습니다. 외부 그래프는 단일 노드를 see합니다; 내부 그래프는 자체 상태와 자체检查점을 가집니다. 이것이 팀이 수퍼바이저-worker agent를 구축하는 방식입니다: 수퍼바이저 그래프가 도메인별 worker 하위 그래프로 사용자 인텐트를 라우팅합니다.

## 실습

### 단계 1: 상태 및 노드

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def agent_node(state: State) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: State) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

tool_node = ToolNode(tools=[search_web, read_file])

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

app = graph.compile(checkpointer=MemorySaver())
```

`add_messages`는 메시지 리스트가 덮어쓰기 대신 누적되도록 하는 reducer입니다. 그것을 잊어버리는 것이 가장 일반적인 LangGraph 버그입니다.

### 단계 2: 스레드로 실행

```python
config = {"configurable": {"thread_id": "user-42"}}
for event in app.stream(
    {"messages": [HumanMessage("find the Anthropic headquarters address")]},
    config,
    stream_mode="updates",
):
    print(event)
```

모든 업데이트는 `{node_name: state_delta}` dict입니다. 프론트엔드에서 이러한 업데이트를 UI로 스트리밍하여 사용자가 "agent가 생각 중... search_web 호출 중... 결과 획득... 답변 중"을 볼 수 있습니다.

### 단계 3: 인간 참여 인터럽트 추가

실행 전에 노드가 일시 정지되도록 표시합니다.

```python
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["tools"],  # 모든 도구 호출 전에 일시 정지
)

state = app.invoke({"messages": [HumanMessage("delete the production database")]}, config)
# state["__interrupt__"]가 설정됩니다. 제안된 도구 호출을 inspect합니다.
# 승인된 경우:
from langgraph.types import Command
app.invoke(Command(resume=True), config)
# 거부된 경우: 거부 메시지를 작성하고 재개
app.update_state(config, {"messages": [AIMessage("인간 검토자에 의해 차단됨.")]})
```

인터럽트 전반에 걸쳐 상태,检查점 및 스레드가 모두 유지됩니다. 실행 중이 아닌 한 메모리에 없습니다.

### 단계 4: 디버깅을 위한 시간 여행

```python
history = list(app.get_state_history(config))
for snapshot in history:
    print(snapshot.values["messages"][-1].content[:80], snapshot.config)

# 이전检查점부터 fork
target = history[3].config  # 3단계 뒤로
for event in app.stream(None, target, stream_mode="values"):
    pass  # 해당 지점부터 replay
```

입력으로 `None`을 전달하면 해당检查점부터 replay합니다. 값을 전달하면 재개하기 전에 해당检查점의 상태에 업데이트로 추가합니다. 이것이 전체 대화를 다시 실행하지 않고 잘못된 agent 실행을 재현하는 방법입니다.

### 단계 5: 프로덕션용检查점기 교체

```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string("postgresql://...") as checkpointer:
    checkpointer.setup()
    app = graph.compile(checkpointer=checkpointer)
```

SQLite, Redis 및 Postgres가 제공됩니다. `MemorySaver`는 테스트용입니다. 재시작 전반에 걸쳐 유지되는 모든 것에는 실제 저장소가 필요합니다.

## 스킬

> agent를 `while True` 루프가 아닌 그래프로 구축합니다.

LangGraph에手を伸ば하기 전에 60초 설계를 수행합니다:

1. **노드의 이름을 지정합니다.** 모든 불연속 결정 또는 부작용 액션은 노드입니다. "Agent 생각함", "도구 실행", "검토자 승인", "응답 스트리밍." 나열할 수 없으면 작업이 아직 agent 모양이 아닙니다.
2. **상태를 선언합니다.** 모든 리스트 필드에 reducer가 있는 최소 TypedDict. 모든 것을 `messages`에 넣지 마세요; 작업별 필드(작동하는 `plan`, `budget` 카운터, `retrieved_docs` 리스트)를 최상위 레벨로 hoist합니다.
3. **엣지를 그립니다.** 모델 출력에 따라 다음 단계가 결정되지 않으면 정적입니다. 모든 조건부 엣지에는 명명된 분기가 있는 라우터 함수가 필요합니다.
4. **먼저检查점기를 선택합니다.** 테스트용 `MemorySaver`, 기타 모든 항목용 Postgres/Redis/SQLite.检查점기 없이 shipping하지 마세요 --检查점기 없이는 재개, 인터럽트, 시간 여행이 없습니다.
5. **도구 실행 *후*가 아닌 *전*에 인터럽트를 결정합니다.** 승인은有害 전에 취소할 수 있도록 부작용 노드로 들어가는 엣지에 지정합니다; 검증은 잘못된 호출을 저렴하게 거부할 수 있도록 모델에서 나오는 엣지에 지정합니다.
6. **기본적으로 스트리밍합니다.** UI용 `mode="updates"`, 모델 노드 내의 토큰 수준 스트리밍용 `mode="messages"`, eval 중 전체 스냅샷용 `mode="values"`.

检查점기 없는 LangGraph agent를 shipping 거부. 부작용 *후*에 인터럽트하는 agent shipping 거부. reducer로 `add_messages` 없이 `messages` 필드를 shipping 거부.

## 연습 문제

1. **쉬움.** 위의 4노드 ReAct 그래프를 계산기 도구와 웹 검색 도구로 구현합니다. `list(app.get_state_history(config))`가 2턴 대화에서 최소 4개의检查점을 반환하는지 확인합니다.
2. **중간.** `agent`の前に実行され 구조화된 `plan: list[str]`을 상태에写入하는 `planner` 노드를 추가합니다. `agent`가 계획 단계를 완료로 표시하도록 합니다. 检查점 재개에서 `plan`이 손실되면 테스트를 실패시킵니다(잘못된 reducer).
3. **어려움.** `Send`를 사용하여 세 하위 그래프(`researcher`, `writer`, `reviewer`) 사이를 라우팅하는 수퍼바이저 그래프를 구축합니다. 각 하위 그래프는 자체 상태와检查점을 가집니다. 외부 그래프에서 `interrupt_before=["writer"]`를 추가하여 인간이 연구 개요를 승인할 수 있도록 합니다. 이전检查점에서 시간 여행이 분기된 분기만 다시 실행하는지 확인합니다.

## 핵심 용어

| 용어 |人们在说什么 |실제로 의미하는 것 |
|------|-----------------|-----------------------|
| StateGraph | "LangGraph 그래프" | 컴파일 전에 노드와 엣지를 추가하는 빌더 객체 |
| Reducer | "필드가 어떻게 병합되는지" | 필드에 대한 업데이트를 노드가 반환할 때 적용되는 함수 `(old, new) -> merged`; 기본값은 덮어쓰기, `add_messages`는 추가 |
| Thread | "대화 ID" | 하나의 세션에 대한 모든检查점을 범위 지정하는 `thread_id` 문자열 |
| Checkpoint | "일시 정지된 상태" | 노드 전환 후 `(thread_id, checkpoint_id)`를 키로 하는 전체 그래프 상태의 영속화된 스냅샷 |
| Interrupt | "인간을 위해 일시 정지" | `interrupt_before` / `interrupt_after`가 노드 경계에서 실행을 중지합니다; `Command(resume=...)`로 재개 |
| Time-travel | "이전 단계에서 fork" | 해당检查점부터 forward로 replay하려면 `graph.invoke(None, old_checkpoint_id가 있는 config)` |
| Send | "병렬 하위 그래프 dispatch" | 노드가 반환하여 대상 노드의 N개 병렬 실행을 생성하는 생성자 |
| Subgraph | "노드로서의 컴파일된 그래프" | another 그래프의 노드로 사용되는 컴파일된 StateGraph; 자체 상태 범위를 보존 |

## 추가 자료

- [LangGraph 문서](https://langchain-ai.github.io/langgraph/) -- StateGraph, reducer,检查점기 및 인터럽트의 정식 참조
- [LangGraph 개념: 상태, reducer,检查점기](https://langchain-ai.github.io/langgraph/concepts/low_level/) -- 이 단원이 사용하는 정신 모델, 출처에서 직접
- [LangGraph 지속성 및检查점](https://langchain-ai.github.io/langgraph/concepts/persistence/) -- Postgres/SQLite/Redis 저장소,检查점 네임스페이스 및 스레드 ID에 대한 세부 정보
- [LangGraph 인간 참여](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/) -- `interrupt_before`, `interrupt_after`, `Command(resume=...)` 및 상태 편집 패턴
- [Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models" (ICLR 2023)](https://arxiv.org/abs/2210.03629) -- 모든 LangGraph agent가 구현하는 패턴; 추론 추적 근거를 위해 읽으세요
- [Anthropic — Building effective agents (Dec 2024)](https://www.anthropic.com/research/building-effective-agents) -- 어떤 그래프 모양(체인, 라우터, 오케스트레이터-workers, 평가기-옵티마이저)을 선호하고 언제 선호하는지
- Phase 11 · 09 (Function Calling) -- 모든 LangGraph agent 노드가 재사용하는 도구 호출 기본 요소
- Phase 11 · 14 (Model Context Protocol) -- MCP 어댑터를 통해 LangGraph `ToolNode`에 연결되는 외부 도구 검색
- Phase 11 · 17 (Agent framework tradeoffs) -- CrewAI, AutoGen 또는 Agno보다 LangGraph를 선택하는 경우