# Azure AI Agent Service

> Microsoft Azure AI Agent Service — 벡터 저장소와 통합된 완전 관리형 에이전트 오케스트레이션. OpenAI(Swarm, 레슨 16), Anthropic(Claude Agent SDK, 레슨 17), Microsoft(Azure AI Agent Service) — 각각 하나의 호스팅된 복합 오케스트레이터를 제공한다. Azure의 것은 Azure의 벡터 DB 및 ID 시스템과 깊게 통합된다.

**Type:** Learn
**Languages:** Python, REST
**Prerequisites:** Phase 14 · 16 (OpenAI Agents SDK), Phase 14 · 33 (Dify)
**Time:** ~45분

## 학습 목표

- Azure AI Agent Service가 OpenAI Assistant API(레슨 16)와 어떻게 다른지 설명한다.
- Azure AI Agent Service의 세 가지 주요 기본 요소를 명명한다: 에이전트, 스레드, 벡터 저장소.
- 벡터 저장소와 ID 통합이 기존 Azure 배포에 어떤 이점을 제공하는지 설명한다.
- Azure AI Agent Service를 유사한 관리형 서비스와 비교한다.

## 문제

에이전트는 코드 어딘가에서 실행된다. 에이전트가 필요하지만 에이전트 플랫폼을 구축하고 싶지 않은 팀이 있다. Azure AI Agent Service는 관리형 오케스트레이션(호스팅)을 제공한다 — 자체 루프, 리소스, 또는 관찰 가능성을 구축하지 않고도 사용할 수 있다.

## 개념

### Azure AI Agent Service

- 완전 관리형: Azure가 에이전트를 호스팅, 실행, 오케스트레이션.
- OpenAI Assistant API(레슨 16) 위에 구축되었지만 Azure 에코시스템으로 확장됨.
- 코드 예시:

```python
from azure.ai.agents import AIAgentClient

client = AIAgentClient(endpoint="...")
agent = client.create_agent(
    model="gpt-4o",
    tools=[code_interpreter, file_search]
)
```

### OpenAI Assistant API와의 차이점

| 측면 | OpenAI Assistant API | Azure AI Agent Service |
|-------|---------------------|------------------------|
| 호스팅 | OpenAI | Azure |
| 벡터 저장소 | OpenAI Vector Store | Azure AI Search / Cosmos DB |
| ID | OpenAI API 키 | Microsoft Entra ID (RBAC) |
| 보안 | API 키 | 관리 ID, RBAC |
| 데이터 지역 | OpenAI 리전 | Azure 리전 (데이터 상주) |
| 도구 | OpenAI 내장 도구 | + Azure Functions, Logic Apps |
| 모니터링 | OpenAI 대시보드 | Azure Monitor (Log Analytics) |

### 기본 요소

1. **에이전트.** 도구와 모델이 있는 에이전트 구성. 일단 생성되면 Azure가 실행을 관리.
2. **스레드.** 대화 상태. 각 스레드는 독립적인 컨텍스트를 유지.
3. **벡터 저장소.** Azure AI Search 또는 Cosmos DB에 저장된 문서. Azure AI Search는 벡터 검색, 의미 검색, 하이브리드 검색을 지원.

### 벡터 저장소 통합

Azure의 장점은 검색이다. 벡터 저장소가 Azure AI Search에 연결되므로 기존 인덱스, 청킹 전략, RBAC를 사용할 수 있다.

### 하이브리드 검색

키워드 + 벡터 검색을 결합. 인덱스가 하이브리드 검색을 위해 구성되면 에이전트는 검색 관련성을 자동으로 개선.

### ID 및 보안

Azure AI Agent Service는 다음을 사용:

- **Microsoft Entra ID** for authentication (RBAC).
- **관리 ID** for agent-to-service access (agent → Azure AI Search, agent → Azure Functions).

### 포지셔닝

Azure AI Agent Service는 기존 Azure 투자가 있는 팀에게 적합. OpenAI나 Anthropic에 비해 사용자 지정에서 제한이 있지만, 규정 준수, 데이터 상주, ID 통합이 필요할 때 뛰어남.

중소 팀, 단순한 사용 사례에는 Claude Agent SDK(레슨 17) 또는 OpenAI Agents SDK(레슨 16)가 더 쉬운 시작점을 제공할 수 있다. 대기업 Azure 팀은 AI Agent Service의 통합이 더 가치 있다고 느낄 것이다.

### 이 패턴이 잘못되는 경우

- **Azure 외부에서 사용.** Azure AI Agent Service는 다른 클라우드와 잘 작동하지 않음. Azure가 아닌 스택을 사용하는 경우 이 서비스를 건너뛰어라.
- **관리형 서비스를 기본값으로 사용.** 작은 작업의 경우 관리형 서비스는 오버엔지니어링. 간단한 프롬프트 API 호출로 충분.
- **사용자 지정 부족.** Azure가 오케스트레이션을 제어 — 사용자 정의 도구 또는 사용자 지정 워크플로우를 추가하기 어려움.

## 직접 구현하기

`code/main.py`는 Azure AI Agent Service 형태의 장난감 구현:

- 에이전트 생성기: 도구와 모델로 구성.
- 스레드 관리자: 독립적인 대화 상태 생성.
- 벡터 저장소: 메모리에 문서 검색.
- 도구: code_interpreter 스타일, file_search 스타일.
- 데모: 에이전트 생성, 스레드 생성, 도구 호출, 벡터 검색.

실행:

```
python3 code/main.py
```

출력: 에이전트 실행, 스레드 상태, 벡터 검색 결과.

## 활용하기

- **Azure AI Agent Service** for Azure-centric teams with compliance and identity needs.
- **OpenAI Assistant API** for OpenAI-centric teams without Azure dependencies.
- **Claude Agent SDK** for Claude-centric teams with subagent and session store needs.

## 배포하기

`outputs/skill-azure-agent-service.md` scaffolds an Azure AI Agent Service configuration with vector store, identity, and monitoring.

## 연습 문제

1. Azure AI Agent Service 설정의 스크린샷을 캡처하는 대신, 공식 문서의 빠른 시작을 안내하라. 시작하는 데 필요한 주요 단계는 무엇인가?
2. Azure의 자사 벡터 저장소(Azure AI Search)를 Azure AI Agent Service와 통합하면 어떤 이점이 있는가?
3. Entra ID(RBAC)를 사용하는 것이 API 키를 사용하는 것보다 보안에 어떤 이점을 제공하는가?
4. AI Agent Service와 직접 OpenAI Assistant API를 사용하는 경우를 비교. 어느 한쪽이 더 나은 경우는 언제인가?
5. Azure AI Agent Service를 같은 에이전트 작업에 대해 Anthropic의 Claude Agent SDK와 대조.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Azure AI Agent Service | "관리형 에이전트" | Azure Vector Store + ID가 있는 호스팅 오케스트레이션 |
| Thread | "대화 상태" | 에이전트당 독립적인 대화 컨텍스트 |
| Vector store | "Azure AI Search" | 에이전트 검색을 위한 벡터 + 키워드 검색 |
| Entra ID | "Azure ID" | 에이전트를 위한 RBAC + 관리 ID |
| Hybrid search | "키워드 + 벡터" | 검색 관련성을 위한 결합된 검색 접근 방식 |

## 추가 자료

- [Azure AI Agent Service docs](https://learn.microsoft.com/en-us/azure/ai-services/agents/) — hosted agent orchestration
- [Azure AI Search vector store](https://learn.microsoft.com/en-us/azure/search/vector-search-overview) — vector + hybrid search
- [OpenAI Assistants API](https://platform.openai.com/docs/assistants/overview) — the service Azure extends
- [Anthropic Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) — the self-hosted alternative
