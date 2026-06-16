# CrewAI: 역할 기반 Crews와 Flows

> CrewAI는 2026년 역할 기반 멀티 에이전트 프레임워크다. 네 가지 기본 요소: Agent, Task, Crew, Process. 두 가지 최상위 형태: Crews (자율적, 역할 기반 협업)와 Flows (이벤트 기반, 결정론적). 문서는 단호하다: "프로덕션 준비 애플리케이션은 Flow로 시작하라."

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 12 (Workflow Patterns), Phase 14 · 14 (Actor Model)
**Time:** ~75분

## 학습 목표

- CrewAI의 네 가지 기본 요소(Agent, Task, Crew, Process)와 각각이 소유하는 것을 명명한다.
- Sequential, Hierarchical 및 계획된 Consensus 프로세스를 구분하고 워크로드별로 하나를 선택한다.
- Crews(자율적 역할 기반)와 Flows(이벤트 기반 결정론적)를 구분하고 문서의 프로덕션 권장 사항을 설명한다.
- `@tool` 데코레이터와 `BaseTool` 서브클래스로 도구를 연결하고 구조화된 출력과 자유 텍스트에 대해 추론한다.
- 네 가지 CrewAI 메모리 유형과 각각이 효과적인 때를 명명한다.
- 브리프를 생성하는 stdlib 3-에이전트 crew(리서처, 라이터, 에디터)를 구현한다.
- 세 가지 CrewAI 실패 모드(프롬프트 비대, 관리자-LLM 세금, 취약한 핸드오프)를 찾아낸다.

## 문제

멀티 에이전트 프레임워크를 채택하는 팀은 같은 벽에 부딪힌다. "자율적 협업"은 데모에서 훌륭하게 들린다. 그런 다음 고객이 버그를 제출하면 결정론적 재현이 필요하다. 또는 재무 부서가 LLM 라우팅 crew의 실행당 비용을 묻는다. 또는 온콜이 오전 3시에 어떤 에이전트가 중단되었는지 알아야 한다.

자유 형식 LLM 라우팅 crew는 그 어떤 것도 깔끔하게 답하지 못한다. 순수 DAG는 모두 답하지만 브레인스토밍 에이전트가 필요한 탐험적 형태를 잃는다.

CrewAI의 분할은 트레이드오프에 대해 정직하다. Crews는 협업적, 역할 기반, 탐험적 작업용. Flows는 이벤트 기반, 코드 소유, 감사 가능한 프로덕션용. 같은 프레임워크, 두 가지 형태, 표면별로 선택.

## 개념

### 네 가지 기본 요소

CrewAI의 표면은 작다. 이것을 기억하고 나머지는 설정이다.

- **Agent.** `role + goal + backstory + tools + (optional) llm`. 배경 이야기는 중요하다. 어조, 판단, 에이전트가 중지하는 시기를 결정한다. 도구는 에이전트가 호출할 수 있는 함수(아래 참조).
- **Task.** `description + expected_output + agent + (optional) context + (optional) output_pydantic`. 재사용 가능한 작업 단위. `expected_output`은 계약이다. `context`는 출력이 전달되는 업스트림 작업을 나열한다. `output_pydantic`은 구조화된 형태를 강제한다.
- **Crew.** 컨테이너. `agents` 목록, `tasks` 목록, `process` 및 선택적 `memory` + `verbose` + `manager_llm` 설정을 소유한다.
- **Process.** 실행 전략. Sequential, Hierarchical, Consensus (계획됨). 실행의 형태를 선택한다.

에이전트는 서로를 직접 보지 않는다. Task가 에이전트를 참조한다. Crew가 작업을 순서화한다. Process가 다음 작업을 누가 선택할지 결정한다. 그것이 전체 정신 모델이다.

> **CrewAI 0.86 (2026-05)에 대해 검증됨.** 최신 버전에서는 프로세스 유형의 이름이 바뀌거나 병합될 수 있음; 특정 형태에 의존하기 전에 [CrewAI Processes 문서](https://docs.crewai.com/concepts/processes)를 확인하라.

### Sequential vs Hierarchical vs Consensus

- **Sequential.** 작업이 선언 순서대로 실행. 작업 N의 출력이 작업 N+1에 `context`로 사용 가능. 가장 저렴함. 가장 예측 가능함. 순서가 고정된 경우 사용.
- **Hierarchical.** 관리자 Agent(별도 LLM 호출)가 전문가 간 라우팅. CrewAI는 `manager_llm` 설정 또는 기본값에서 관리자를 생성. 관리자가 각 라운드에서 다음 작업을 선택하고 거부하거나 재라우팅할 수 있음. 네 명 이상의 전문가가 있고 순서가 실제로 이전 출력에 따라 달라질 때 사용.
- **Consensus.** 계획됨, 현재 공개 API에 구현되지 않음. 문서는 미래의 투표 기반 프로세스를 위해 이름을 예약. 현재 의존하지 마라.

Hierarchical은 모든 전문가 호출 위에 라운드당 LLM 호출(관리자)을 추가한다. 5단계 실행에서 토큰 비용이 3배가 될 수 있음. 라우팅이 필요할 때만 비용을 지불하라.

### Crews vs Flows

이것이 2026년 문서가 선두로 제시하는 프레이밍이다.

- **Crew.** LLM 기반 자율성. 프레임워크가 런타임에 형태를 선택. 좋은 대상: 연구, 브레인스토밍, 초안, 경로가 답의 일부인 모든 곳. 재현하기 어려움. 테스트하기 어려움. 프로토타입 제작이 저렴함.
- **Flow.** 사용자가 소유하는 이벤트 기반 그래프. `@start`는 진입점을 표시. `@listen(topic)`은 다른 단계가 해당 토픽을 출력할 때 발동하는 단계를 표시. 각 단계는 일반 Python (내부적으로 Crew를 호출할 수 있음). 좋은 대상: 프로덕션. 관찰 가능. 테스트 가능. 결정론적.

2026년 문서의 프로덕션 권장 사항: Flow로 시작하라. 자율성이 비용을 정당화할 때 Flow 단계 내부에서 `Crew.kickoff()` 호출로 Crews를 접어 넣어라. Flow는 감사 추적을 제공하고, Crew는 탐험을 제공한다. 구성하라, 선택하지 마라.

### 도구 통합

Agent에 도구를 제공하는 세 가지 방법. 가장 간단한 것을 선택하라.

1. **`@tool` 데코레이터.** 순수 함수가 도구가 됨. 시그니처는 스키마, 독스트링은 LLM이 보는 설명. 일회성 헬퍼에 가장 좋음.

2. **`BaseTool` 서브클래스.** 명시적 args 스키마, 비동기 지원, 재시도가 있는 클래스 기반 도구. 도구에 상태(클라이언트, 캐시)가 있거나 구조화된 args가 필요할 때 사용.

3. **내장 툴킷.** CrewAI는 자사 어댑터를 제공: `SerperDevTool`, `FileReadTool`, `DirectoryReadTool`, `CodeInterpreterTool`, `RagTool`, `WebsiteSearchTool`. 한 번의 임포트로 연결.

구조화된 출력은 Pydantic을 사용. Task에 `output_pydantic=MyModel`을 전달. CrewAI는 LLM 응답을 모델에 대해 검증하고 강제 변환하거나 재시도. 빡빡한 `expected_output` 문자열과 함께 사용하라. 자유 텍스트 출력은 초안에 좋고, 구조화된 출력은 다운스트림 Flows가 소비할 수 있는 것이다.

### 메모리 훅

CrewAI는 네 가지 메모리 유형을 기본으로 제공. 구성 가능: Crew는 네 가지를 모두 동시에 활성화할 수 있음.

> **CrewAI 0.86 (2026-05)에 대해 검증됨.** 최근 릴리스는 네 가지 저장소를 래핑하는 통합 `Memory` 시스템을 통해 모든 것을 라우팅. 아래 개념적 모델은 여전히 유효하지만, 공개 클래스 표면은 최신 버전에서 단일 `Memory` 진입점으로 축소될 수 있음; 현재 API는 [CrewAI memory 문서](https://docs.crewai.com/concepts/memory)를 확인하라.

- **단기.** 단일 실행 내 대화 버퍼. 종료 시 지워짐.
- **장기.** 실행 간 지속. 벡터 DB(기본 Chroma, 교체 가능)에 저장. 현재 작업과의 유사도로 검색.
- **엔터티.** 엔터티별 사실. "고객 X는 엔터프라이즈 요금제 사용 중." 유사도가 아닌 엔터티 키로 지정. 실행 간 유지.
- **컨텍스트.** 조립 시간 검색. 미리 로드되지 않고 Agent가 필요할 때 관련 메모리를 가져옴.

Crew에서 `memory=True` 또는 유형별 설정으로 활성화. 구성하는 임베딩 프로바이더(기본 OpenAI, 로컬로 교체 가능)가 지원. 메모리는 CrewAI가 더 얇은 프레임워크보다 우위를 점하는 부분 중 하나; 순수 LangGraph는 각각을 직접 연결해야 함.

### CrewAI가 적합한 경우

- 명명된 역할과 협업 워크플로우가 있는 3-6개 에이전트. 초안 작성, 검토, 계획, 브레인스토밍.
- 다음 단계에 대한 LLM의 판단이 가치의 일부인 라우팅(Hierarchical).
- 팀이 그래프 정의보다 `role + goal + backstory`를 읽는 것을 선호하는 모든 곳.

### CrewAI가 적합하지 않은 경우

- 엄격한 순서의 결정론적 DAG. LangGraph (레슨 13) 사용. 그래프 형태가 올바른 추상화; CrewAI의 역할 프레이밍은 마찰.
- 서브초 지연 시간 예산. Hierarchical은 왕복을 추가. Sequential조차 배경 이야기와 이전 출력을 포함하는 프롬프트를 직렬화.
- 단일 에이전트 루프. 프레임워크 생략; 에이전트 루프(레슨 1) + 도구 레지스트리가 더 짧음.

레슨 17 (Agent Framework Tradeoffs)이 이를 매트릭스로 제시. 짧은 버전: CrewAI는 "협업적 역할 기반" 코너에 위치.

### 의존성 형태

LangChain과 독립적. Python 3.10 ~ 3.13. `uv` 사용. 별 수: [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) 참조 (2026-05 기준 스냅샷). AWS Bedrock 통합이 문서화됨; 벤더 벤치마크는 QA 워크로드에서 LangGraph 대비 상당한 속도 향상을 보고하지만 방법론(데이터셋, 하드웨어, 평가 메트릭)이 게시되지 않았으므로 프레임워크-벤더 수치는 방향성으로만 취급.

### 이 패턴이 잘못되는 경우

- **배경 이야기로 인한 프롬프트 비대.** 에이전트당 2000단어 배경 이야기와 5-에이전트 crew는 첫 도구 호출 전에 컨텍스트 예산을 소진. 배경 이야기를 200단어 미만으로 유지. 에이전트 간 구문 재사용; 하우스 스타일을 다섯 번 반복하지 마라.
- **관리자-LLM 토큰 세금.** Hierarchical 프로세스는 모든 전문가 호출 전에 관리자 LLM 호출을 추가. 5-작업 crew에서 6개의 LLM 호출(5개 대신)이고, 관리자 호출은 전체 작업 목록과 이전 출력을 전달. 라우팅이 출력에 의존하지 않으면 Sequential로 전환.
- **취약한 핸드오프.** 작업 N의 `expected_output`이 "개요"임. 작업 N+1이 `context`로 읽고 세 개의 섹션을 구문 분석하려 함. LLM이 네 개를 생성. 다운스트림 Agent가 즉석에서 처리. 작업 N에 `output_pydantic`으로 수정하여 작업 N+1이 자유 텍스트 대신 타입 객체를 읽도록 함.
- **Crew-as-prod.** Flow 래퍼 없이 프로덕션에 출시된 자유 형식 Crew. 출력 변동성이 높음; 재현이 불가능; 온콜이 나쁜 실행과 좋은 실행을 비교할 수 없음. Flow로 래핑.

## 직접 구현하기

`code/main.py`는 두 형태의 stdlib 버전과 3-에이전트 crew를 구현한다.

형태:

- CrewAI의 표면과 일치하는 `Agent`, `Task` 데이터클래스.
- `SequentialCrew.kickoff(inputs)`는 선언 순서대로 작업을 실행, 출력을 `context`로 스레딩.
- `HierarchicalCrew.kickoff(topic)`은 관리자 Agent가 매 라운드 다음 전문가를 선택, "done"에서 중지.
- `@start` 및 `@listen(topic)` 데코레이터, 작은 이벤트 루프, 트레이스가 있는 `Flow`.
- CrewAI의 `@tool` 형태를 미러링하는 `tool(name)` 데코레이터.
- `short_term`, `long_term`, `entity` 저장소가 있는 `Memory`; 모의 유사도는 numpy 사용.
- 모의 LLM 응답은 역할 + 입력 접두사에 키가 지정된 하드코딩 문자열. 네트워크 없음. 결정론적.

구체적 데모: "agent engineering 2026"에 대한 브리프를 생성하는 리서처, 라이터, 에디터 crew. 리서처가 (모의) 소스를 가져옴. 라이터가 초안 작성. 에디터가 다듬음. 동일한 crew가 결정론적 형태를 보여주기 위해 Flow를 통해 실행.

실행:

```bash
python3 code/main.py
```

트레이스 내용: sequential crew가 `context`를 통해 출력을 스레딩, hierarchical crew가 관리자 선택(리서처, 라이터, 에디터, 그 다음 "done"), flow가 명시적 토픽(`researched`, `drafted`, `edited`)으로 동일한 세 단계 실행, `@tool`을 통한 도구 호출 라우팅, 두 번의 kickoff에서 유지되는 장기 메모리.

Crew 트레이스는 유동적; 관리자는 원칙적으로 재정렬 가능. Flow 트레이스는 고정. 그 선택이 교훈이다.

## 활용하기

- **CrewAI Flow** for production. Flow가 한 단계로 `Crew.kickoff()`를 호출하더라도. Flow가 감사 경계를 제공.
- **CrewAI Crew (Sequential)** for clear-ordering collaborative work, especially first drafts and review loops.
- **CrewAI Crew (Hierarchical)** when routing depends on output and you have four or more specialists.
- **LangGraph** (레슨 13) for explicit state machines, durable resume, strict ordering.
- **AutoGen v0.4** (레슨 14) for actor-model concurrency and fault isolation.
- **OpenAI Agents SDK** (레슨 16) for OpenAI-first products with handoffs and guardrails.
- **Claude Agent SDK** (레슨 17) for Claude-first products with subagents and session store.

## 배포하기

`outputs/skill-crew-or-flow.md` picks Crew vs Flow for a task and scaffolds the minimal implementation. Hard rejects on Crew-without-backstory, Flow-without-explicit-topics, Hierarchical with under three specialists.

## 함정

- **배경 이야기를 맛으로 사용.** 출력을 형성. 에이전트당 세 가지 변형 테스트; 차이는 실제. 하나 선택, 고정.
- **`expected_output` 건너뛰기.** 작업당 계약 없이 다운스트림 작업은 LLM이 생성한 것을 그대로 가져옴. Crew는 실행되지만 감사는 실패.
- **메모리 항상 켜짐.** 모든 실행에서 장기 쓰기. 벡터 DB 성장. 검색 노이즈 증가. 사실이 지속적인 작업으로 쓰기를 범위 지정.
- **관리자 프롬프트 드리프트.** Hierarchical의 관리자 프롬프트는 암시적. 라우팅이 이상해지면 verbose 모드로 덤프하고 읽기.
- **Crews의 도구 부작용.** Crew가 예상보다 더 많이 도구를 호출할 수 있음. POST, DELETE, 결제는 Flow 단계에 속하며, Crew 도구에는 절대 안 됨.

## 연습 문제

1. Sequential crew를 Flow로 변환. 변동성이 떨어지는 접점 수를 세기. 가독성이 떨어진 곳을 기록.
2. crew에 엔터티 메모리 추가: 고객에 관한 사실이 kickoff 간 유지. 검색이 올바른 엔터티를 가져오는지 확인.
3. Hierarchical 프로세스 구현: 관리자가 라이터의 출력이 최소 세 문단이 될 때까지 에디터로 라우팅을 거부. 재시도 추적.
4. (모의) 웹 검색을 위한 `BaseTool` 서브클래스 연결. 트레이스 형태를 `@tool` 데코레이터 버전과 비교.
5. 에디터 작업에 `output_pydantic=Brief` 추가, `Brief`는 `title`, `summary`, `sections`를 가짐. 라이터 작업이 한 번 잘못된 JSON을 출력하게 하고 CrewAI의 재시도 동작을 트레이스에서 확인.
6. CrewAI 문서 소개 읽기. 장난감을 실제 `crewai` API로 포팅. stdlib 버전이 어떤 보장을 건너뛰었는가?
7. 실제 실행에 AgentOps 또는 Langfuse (레슨 24) 연결. stdlib 버전에서 어떤 트레이스가 누락되었는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Agent | "페르소나" | 역할 + 목표 + 배경 이야기 + 도구 |
| Task | "작업 단위" | 설명 + 예상 출력 + 담당자 + 선택적 구조화된 출력 |
| Crew | "에이전트 팀" | Agents + Tasks + Process의 컨테이너 |
| Process | "실행 전략" | Sequential / Hierarchical / Consensus (계획됨) |
| Flow | "결정론적 워크플로우" | 이벤트 기반, 코드 소유, 테스트 가능 |
| Backstory | "페르소나 프롬프트" | Agent의 어조와 판단 형성기 |
| `@tool` | "함수 도구" | 함수를 Agent가 호출할 수 있는 도구로 바꾸는 데코레이터 |
| `BaseTool` | "클래스 도구" | args 스키마, 재시도, 비동기 지원이 있는 클래스 기반 도구 |
| Entity memory | "엔터티별 사실" | 고객 / 계정 / 이슈로 범위 지정된 메모리 |
| Long-term memory | "교차 실행 메모리" | kickoff 간 유지되는 벡터 기반 메모리 |
| Contextual memory | "적시 검색" | Agent가 필요할 때 가져오는 메모리 |
| Manager LLM | "라우터 에이전트" | Hierarchical 프로세스에서 다음 작업을 선택하는 추가 LLM |
| `expected_output` | "작업 계약" | Agent(및 감사)에게 반환할 형태를 알려주는 문자열 |

## 추가 자료

- [CrewAI docs introduction](https://docs.crewai.com/en/introduction): 개념과 권장 프로덕션 경로
- [CrewAI Flows guide](https://docs.crewai.com/en/concepts/flows): 이벤트 기반 형태, `@start`, `@listen`
- [CrewAI tools reference](https://docs.crewai.com/en/concepts/tools): `@tool`, `BaseTool`, 내장 툴킷
- [CrewAI memory](https://docs.crewai.com/en/concepts/memory): 단기, 장기, 엔터티, 컨텍스트
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents): 멀티 에이전트가 도움이 되는 경우와 그렇지 않은 경우
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview): 상태 머신 대안
