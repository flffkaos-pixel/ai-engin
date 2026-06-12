# 에이전트 프레임워크 트레이드오프 — LangGraph vs CrewAI vs AutoGen vs Agno

> 모든 프레임워크가 동일한 데모(보고서를 작성하는 연구 agent)를 판매하고 동일한 버그(상태 스키마가 오케스트레이션 레이어와 충돌)를 숨깁니다. 문제의 모양과 일치하는 추상화를 가진 프레임워크를 선택하세요; 나머지는 두 번 작성하는 glue입니다.

**유형:** 학습
**언어:** Python
**선수 과목:** Phase 11 · 09 (Function Calling), Phase 11 · 16 (LangGraph)
**소요 시간:** ~45분

## 문제

둘 이상의 LLM 호출이 필요한 작업이 있습니다. 연구 워크플로일 수 있습니다(계획, 검색, 요약, 인용). 코드 검토 파이프라인일 수 있습니다( diff 분석, 비판, 패치, 검증). 비행기를 예약하고, 이메일을 작성하고, 경비 보고서를 제출하는 다중 턴 어시스턴트일 수 있습니다. 프레임워크를 선택합니다.

3일 후, 프레임워크의 추상화가 유출된다는 것을 발견합니다. CrewAI는 역할을 제공하지만 "연구자"가 "작성자"에게 구조화된 계획을 전달해야 할 때 사용자와 충돌합니다. AutoGen은 에이전트 간 채팅을 제공하지만 일급 상태가 없으므로检查점이 대화 로그의 pickle입니다. LangGraph는 상태 그래프를 제공하지만 에이전트가 무엇을 할지 알기 전에 모든 전환의 이름을 지정하도록 강제합니다. Agno는 단일 agent 추상화를 제공하여 3개의 동시 worker로 fan out하려고 할 때 비명을 지릅니다.

수정은 "최고의 프레임워크를 선택"하는 것이 아닙니다. 문제의 모양과 프레임워크의 핵심 추상화를 일치시키는 것입니다. 이 단원이 그 지도를 그립니다.

## 개념

![Agent 프레임워크 매트릭스: 핵심 추상화 대 문제 모양](../assets/framework-matrix.svg)

네 가지 프레임워크가 2026년 환경을 지배합니다. 핵심 추상화는 동일하지 않습니다.

| 프레임워크 | 핵심 추상화 | 최적 적합 | 최악 적합 |
|-----------|------------------|----------|-----------|
| **LangGraph** | `StateGraph` — 타입 상태, 노드, 조건부 엣지,检查점기. | 명시적 상태 및 인간 참여 인터럽트가 있는 워크플로; 시간 여행 디버깅이 필요한 프로덕션 agent. |拓撲가 알려지지 않은 느슨한 역할 중심 브레인스토밍. |
| **CrewAI** | `Crew` — 역할(목표, 배경 이야기), 작업, 프로세스(순차 또는 계층적). | 짧은 선형/계층적 계획이 있는 역할 연기 또는 페르소나 중심 워크플로. | 턴 기록을 넘어 상태가 필요한 것; 복잡한 분기. |
| **AutoGen** | `ConversableAgent` 쌍 — 종료 조건까지 턴을 번갈아 말하는 두 명 이상의 agent. | 제안자-비평가, 교사-학생처럼 사고가 채팅에서 emerging하는 다중 agent *대화*. | 알려진 DAG가 있는 결정론적 워크플로; 재시작 전반에 걸친 durable 상태가 필요한 것. |
| **Agno** | `Agent` — 도구와 메모리가 있는 단일 LLM, 팀으로 구성 가능. | 빠르게 구축할 단일 agent 및 경량 팀; 강력한 멀티모달리티 및 내장 스토리지 드라이버. | 커스텀 reducer가 있는 깊고 명시적으로 분기된 그래프. |

### "추상화"가 실제로 의미하는 것

프레임워크의 핵심 추상화는 아키텍처를 피칭할 때 화이트보드에 그리는 것입니다.

- **LangGraph** → 그래프를 그립니다. 노드는 단계, 엣지는 전환이며 모든 지점의 상태 객체는 타입화됩니다. 정신 모델은 상태 머신입니다.
- **CrewAI** → 조직도를 그립니다. 각 역할에는 작업 설명이 있고 관리자가 작업을 라우팅합니다. 정신 모델은 전문가들의 소규모 팀입니다.
- **AutoGen** → Slack DM을 그립니다. 두 agent가 서로에게 메시지를 보냅니다; 필요하면 세 번째가 중재자로 참여합니다. 정신 모델은 채팅입니다.
- **Agno** → 도구가 달린 단일 상자를 그립니다. 팀을 위해 상자 옆에 놓습니다. 정신 모델은 "배터리가 포함된 agent"입니다.

### 상태 질문

상태는 대부분의 프레임워크 선택이 프로덕션에서 중단되는 곳입니다.

- **LangGraph.** 타입 상태(`TypedDict` 또는 Pydantic 모델), 필드당 reducer, 일급检查점기(SQLite/Postgres/Redis). 재개, 인터럽트 및 시간 여행이 무료입니다. *(Phase 11 · 16 참조.)*
- **CrewAI.** 상태는 `context` 필드를 통해 작업 간에 문자열로 흐르거나 `output_pydantic`를 통해 구조화됩니다. 기본 제공되는 durable per-crew 저장소가 없습니다; 크루가 재시작을 살아남아야 하면 자체를 덧붙입니다.
- **AutoGen.** 상태는 채팅 기록 및 사용자 정의 `context`입니다. 대화 기록이 persistence됩니다; 임의의 워크플로 상태는 어댑터를 작성하지 않는 한 그렇지 않습니다.
- **Agno.** 내장 스토리지 드라이버(SQLite, Postgres, Mongo, Redis, DynamoDB)가 `Agent`에 `storage=`를 통해 연결됩니다 -- 대화 세션과 사용자 메모리가 자동으로 persistence됩니다. 완전한 그래프检查점기가 아닙니다; 세션 저장소입니다.

### 분기 질문

사소하지 않은 모든 agent가分支합니다. 누가分支하는지가 중요합니다.

- **LangGraph** — 조건부 엣지를 통해 결정합니다. 라우팅은 명명된 분기가 있는 Python 함수입니다. 분기는 컴파일된 그래프에서 일급입니다;检查점기가 어떤 분기가 취해졌는지 기록합니다.
- **CrewAI** — 계층 모드에서 관리자가 결정합니다; 순차 모드에서 빌드 시점에 결정합니다. 라우팅은 작업 목록에서 암묵적입니다; 관리자의 프롬프트 외부에 일급 "if"가 없습니다.
- **AutoGen** — 채팅을 통해 agent가 결정합니다.分支는 다음에 누가 말하는지에서 emerging합니다. `GroupChatManager`가 다음 스피커를 선택합니다; 기본값은 LLM驱动이지만 `speaker_selection_method`를 손으로 작성할 수 있습니다.
- **Agno** — agent가 다음에 호출할 도구에 의해 결정합니다. 팀에는 coordinator/router/collaborator 모드가 있습니다; 그 이상의分支는 개발자의 책임입니다.

### 관찰 가능성 질문

- **LangGraph** — LangSmith 또는 any OTel 익스포터経由のOpenTelemetry. 모든 노드 전환은 trace 스팬입니다;检查점이 replay 가능한 trace로 doubled합니다. LangSmith가 기본 옵션입니다; Langfuse/Phoenix에도 어댑터가 있습니다.
- **CrewAI** — 2025년 후반부터 일급 OpenTelemetry; Langfuse, Phoenix, Opik, AgentOps와 통합.
- **AutoGen** — `autogen-core`를 통한 OpenTelemetry 통합; AgentOps 및 Opik에 커넥터가 있습니다. 추적 세분성은 노드당不再是 agent-메시지당.
- **Agno** — 내장 `monitoring=True` 플래그 plus OpenTelemetry 익스포터; 세션 추적을 위한 Langfuse와 긴밀한 통합.

### 비용 및 지연 시간

네 가지 프레임워크 모두 호출당 overhead를 추가합니다(프레임워크 로직, 검증, 직렬화). 증가 overhead의 대략적인 순서: Agno ≈ LangGraph < CrewAI ≈ AutoGen. 차이는 프레임워크가 수행하는 추가 LLM 라우팅 양에 의해 지배됩니다. CrewAI의 계층적 관리자는 다음에 누가가는지를 결정하는 데 토큰을 사용합니다; AutoGen의 `GroupChatManager`도 마찬가지입니다. LangGraph는 `llm.invoke`를 작성하는 곳에서만 토큰을 사용합니다. Agno의 단일 agent 경로는 얇습니다.

실행당 비용이 중요한 경우 명시적 라우팅(LangGraph 엣지, AutoGen `speaker_selection_method`)을 LLM 선택 라우팅보다 선호합니다.

### 상호 운용성

- **LangGraph** ↔ **LangChain** 도구, 검색기, LLM. 일급 MCP 어댑터(도구가 MCP 서버로 가져옴).
- **CrewAI** ↔ `BaseTool`에서 상속하는 도구; LangChain 도구, LlamaIndex 도구 및 MCP 도구가 모두 적용됩니다. `allow_delegation=True`를 통한 크루 간 위임.
- **AutoGen** → `FunctionTool`이 any Python 호출 가능을 wrapping합니다; MCP 어댑터 사용 가능. agent 대 agent 패턴을 위한 AG2 에코시스템과 긴밀한 결합.
- **Agno** → `@tool` 장식 또는 BaseTool 하위 클래스; MCP 어댑터; 도구는 agent와 팀 전체에서 공유될 수 있습니다.

## 스킬

> 주어진 프레임워크가 주어진 agent 문제에 적합한 이유를 한 문장으로 설명할 수 있습니다.

사전 구축 체크리스트:

1. **모양을 그립니다.** 이것이 그래프인가(타입 상태, 명명된 전환)? 역할 연기인가(전문가가 작업을 전달)? 채팅인가(완료될 때까지 agent가 이야기)? 도구가 있는 단일 agent인가?
2. **누가分支하는지 결정합니다.** 개발자 결정分支 → LangGraph. 관리자-agent 결정 → CrewAI 계층적. 채팅 emerging → AutoGen. 도구 호출 결정 → Agno.
3. **상태 예산을 확인합니다.**检查점부터 재개해야 하나요? 시간 여행? 실행 중 인간 인터럽트? 그렇다면 LangGraph가 기본값입니다; Agno 세션은 대화 범위 상태를 다룹니다.
4. **비용 예산을 확인합니다.** LLM 선택 라우팅은 턴당 추가 토큰이 듭니다. agent가 하루에 수천 번 실행되면 명시적 라우팅을 선호합니다.
5. **프레임워크 overhead를 예산화합니다.** 모든 프레임워크는 또 다른 종속성입니다. 작업이 두 개의 LLM 호출과 도구라면 30줄의 일반 Python을 작성하세요; 프레임워크보다 저렴한 것은 없습니다.

그래프, 조직도, 채팅 또는 agent 상자를 그릴 수 있기 전에는 프레임워크에手を伸ば지 마세요. 실제로 필요하는 것に対してその状態モデルと戦わなければならないフレームワークは選ばないでください。

## 결정 매트릭스

| 문제 모양 | 선호 프레임워크 | 이유 |
|---------------|---------------------|-----|
| 타입 상태, 인간 승인, 장기 실행이 있는 워크플로 DAG | LangGraph | 일급 상태,检查점기, 인터럽트, 시간 여행. |
| 고유한 역할이 있는 연구/쓰기 파이프라인 | CrewAI (순차) 또는 LangGraph 하위 그래프 | 역할별 작업은 CrewAI에서 저렴하게 표현됩니다;分支가 복잡해지면 LangGraph로 확장. |
| 제안자-비평가 또는 교사-학생 대화 | AutoGen | 2 agent 채팅이 기본 모양입니다. |
| 도구, 세션, 메모리가 있는 단일 agent | Agno | 가장 얇은 설정, 내장 스토리지 및 메모리. |
| reducer가 있는 수천 개의 병렬 fanout | LangGraph + `Send` | 일급 병렬 dispatch API가 있는 유일한 것. |
| 빠른 프로토타입, 프레임워크 커밋 없음 | 일반 Python + 제공자 SDK | 프레임워크보다 빠른 것은 없습니다. |

## 연습 문제

1. **쉬움.** 동일한 작업 -- "Anthropic 본사를 연구하고, 200단어 요약을 작성하고, 출처를 인용" -- 을 LangGraph(4개 노드: 계획, 검색, 쓰기, 인용)와 CrewAI(3개 역할: 연구자, 작성자, 편집자)에서 구현합니다. 실행당 토큰 비용과 코드 줄을 보고합니다.
2. **중간.** AutoGen(연구자 ↔ 작성자 채팅, 편집자가 `GroupChat`을 통해 참여)과 Agno(단일 agent + `search_tools` 및 `write_tools` + 세션 저장소)에서 동일한 작업을 구축합니다. 4가지 구현을 (a) 실행당 비용, (b) 충돌 후 재개 능력, (c) 쓰기 단계 전에 인간 승인을 주입하는 능력으로 순위를 매깁니다.
3. **어려움.** 짧은 문제 설명(JSON: `{has_typed_state, has_roles, has_dialogue, has_parallel_fanout, needs_resume}`)을 가져와서 한 문장 정당화와 함께 권장 사항을 반환하는 결정 트리 스크립트 `pick_framework.py`를 구축합니다. 직접 디자인한 6개 케이스에서 검증합니다.

## 핵심 용어

| 용어 |人们在说什么 |실제로 의미하는 것 |
|------|-----------------|-----------------------|
| 오케스트레이션 | "에이전트 조정 방법" | 다음에実行할 노드/역할/에이전트를 결정하는 레이어 |
| Durable 상태 | "재시작 후 재개" |プロセス終了を生き延びる状態で、检查点またはセッショ store에 attached됨 |
| LLM 선택 라우팅 | "모델에게 결정하도록させる" | 각 턴에서 다음 단계를 선택하는 플래너 LLM; 유연하지만 모든 결정에 토큰을 지불합니다 |
| 명시적 라우팅 | "개발자가 결정" | Python 함수 또는 정적 엣지가 다음 단계를 선택합니다; 저렴하고 감사 가능합니다 |
| Crew | "CrewAI 팀" | 역할 + 작업 + 프로세스(순차 또는 계층적)가 단일 실행 가능한 것으로 바인딩됩니다 |
| GroupChat | "AutoGen의 다중 agent 채팅" | 스피커 선택기가 있는 N agent 간의 관리된 대화 |
| Team (Agno) | "멀티 agent Agno" | 에이전트 세트에 대한 route / coordinate / collaborate 모드 |
| StateGraph | "LangGraph의 그래프" | 타입 상태, 노드, 조건부 엣지,检查점기 추상화 |

## 추가 자료

- [LangGraph 문서](https://langchain-ai.github.io/langgraph/) -- StateGraph,检查점기, 인터럽트, 시간 여행
- [CrewAI 문서](https://docs.crewai.com/) -- Crews, Flows, Agents, Tasks, Processes
- [AutoGen 문서](https://microsoft.github.io/autogen/) -- ConversableAgent, GroupChat, teams, tools
- [Agno 문서](https://docs.agno.com/) -- Agent, Team, Workflow, storage, memory
- [Anthropic — Building effective agents (Dec 2024)](https://www.anthropic.com/research/building-effective-agents) -- 프레임워크에 구애받지 않는 패턴 라이브러리(프롬프트 체aining, 라우팅, 병렬화, 오케스트레이터-workers, 평가기-옵티마이저)
- [Yao et al., "ReAct: Synergizing Reasoning and Acting" (ICLR 2023)](https://arxiv.org/abs/2210.03629) -- 모든 프레임워크가 장식하는 루프
- [Wu et al., "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation" (2023)](https://arxiv.org/abs/2308.08155) -- AutoGen의 디자인 논문
- [Park et al., "Generative Agents: Interactive Simulacra of Human Behavior" (UIST 2023)](https://arxiv.org/abs/2304.03442) -- CrewAI 스타일 페르소나 스택이 구축하는 역할 연기 기초
- Phase 11 · 16 (LangGraph) -- 이 단원이 벤치마크하는 프레임워크
- Phase 11 · 19 (Reflexion) -- LangGraph에 깔끔하게 매핑되지만 CrewAI에 어색하게 매핑되는 패턴
- Phase 11 · 22 (Production observability) -- 선택한 프레임워크를 계측하는 방법