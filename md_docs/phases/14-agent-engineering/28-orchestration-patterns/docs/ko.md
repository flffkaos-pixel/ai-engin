# 오케스트레이션 패턴: Supervisor, Swarm, 계층형

> 2026년 프레임워크에서 네 가지 오케스트레이션 패턴이 반복됩니다: supervisor-worker, swarm / peer-to-peer, 계층형(hierarchical), 토론(debate). Anthropic의 조언: "올바른 시스템을 구축하는 것이 중요합니다." 단순하게 시작하고, 단일 에이전트에 5가지 워크플로우 패턴으로 충분하지 않을 때만 토폴로지를 추가하세요.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 12 (Workflow Patterns), Phase 14 · 25 (Multi-Agent Debate)
**Time:** ~60분

## 학습 목표

- 네 가지 반복되는 오케스트레이션 패턴과 각각이 적합한 상황을 명명합니다.
- 2026년 LangChain 권장 사항을 설명합니다: supervisor 라이브러리 대신 도구 호출 기반 감독.
- Anthropic의 "올바른 시스템 구축" 규칙과 이것이 토폴로지 선택을 어떻게 결정하는지 설명합니다.
- 공통 스크립트형 LLM에 대해 stdlib로 네 가지 모두 구현합니다.

## 문제

팀은 필요하기 전에 "다중 에이전트"를 사용하려 합니다. 네 가지 패턴이 프레임워크 전반에 걸쳐 반복됩니다; 이름을 붙일 수 있게 되면 올바른 것을 선택하거나 토폴로지를 완전히 건너뛸 수 있습니다.

## 개념

### Supervisor-worker

- 중앙 라우팅 LLM이 전문 에이전트에게 작업을 할당합니다.
- 결정: 자신에게 돌아가기, 전문가에게 전달, 종료.
- 전문가는 서로 대화하지 않음; 모든 라우팅은 supervisor를 통해 이루어집니다.

프레임워크: LangGraph `create_supervisor`, Anthropic orchestrator-workers, CrewAI Hierarchical Process.

**2026년 LangChain 권장 사항:** `create_supervisor` 대신 직접 도구 호출을 통한 감독 수행. 더 세밀한 컨텍스트 엔지니어링 제어 제공 — 각 전문가가 보는 내용을 정확히 결정 가능.

### Swarm / peer-to-peer

- 에이전트가 공유 도구 표면을 통해 직접 핸드오프.
- 중앙 라우터 없음.
- supervisor보다 낮은 지연 시간 (더 적은 홉).
- 추론하기 더 어려움 (단일 제어 지점 없음).

프레임워크: LangGraph swarm 토폴로지, OpenAI Agents SDK 핸드오프 (모든 에이전트가 다른 모든 에이전트에 핸드오프할 수 있을 때).

### 계층형 (Hierarchical)

- Supervisor가 하위 supervisor를 관리하고, 하위 supervisor가 워커를 관리.
- LangGraph에서 중첩 하위 그래프로 구현; CrewAI에서 중첩 crew로 구현.
- 운영 복잡성을 대가로 대규모 에이전트 인구로 확장 가능.

필요한 경우: 단일 supervisor의 컨텍스트 버짓이 모든 전문가의 설명을 담을 수 없을 때.

### 토론 (Debate)

- 병렬 제안자 + 반복적 상호 비판 (Lesson 25).
- 실제로는 오케스트레이션이라기보다 검증에 가깝지만 — 프레임워크에서 토폴로지 선택으로 나타남.

### CrewAI Crew vs Flow

CrewAI는 두 가지 배포 모드를 공식화합니다:

- **Flow** — 결정론적 이벤트 기반 자동화용 (프로덕션 권장 시작점).
- **Crew** — 자율적 역할 기반 협업용.

이는 위의 네 가지 패턴과 직교하지만 토폴로지에 매핑됩니다: Flow는 일반적으로 supervisor 또는 계층형; Crew는 일반적으로 LLM 라우터가 있는 supervisor.

### Anthropic의 조언

"LLM 공간에서의 성공은 가장 정교한 시스템을 구축하는 것이 아니라 필요에 맞는 올바른 시스템을 구축하는 것입니다."

결정 순서:

1. 단일 에이전트 + 워크플로우 패턴 (Lesson 12) — 여기서 시작.
2. Supervisor-worker — 2-4명의 전문가가 있을 때.
3. Swarm — 지연 시간이 추론 명확성보다 중요할 때.
4. 계층형 — supervisor 컨텍스트 버짓이 실패할 때만.
5. 토론 — 정확도가 비용보다 중요할 때.

### 이 패턴이 실패하는 경우

- **토폴로지 우선 사고.** 다중 에이전트가 해결하는 문제가 무엇인지 식별하기 전에 "다중 에이전트가 필요함".
- **Swarm에서 바운싱 핸드오프.** A -> B -> A -> B. 홉 카운터 사용.
- **가짜 계층 구조.** "엔터프라이즈"니까 세 레이어; 실제 팀은 두 개. 축소.

## 빌드하기

`code/main.py`는 스크립트형 LLM에 대해 stdlib로 네 가지 패턴을 모두 구현합니다:

- `Supervisor` — 중앙 라우터.
- `Swarm` — 직접 핸드오프가 있는 P2P.
- `Hierarchical` — supervisor의 supervisor.
- `Debate` — 병렬 제안자 + 비판.

각 패턴은 동일한 세 가지 의도 작업(환불 / 버그 / 영업)을 처리합니다. 트레이스 형태가 다릅니다.

실행:

```
python3 code/main.py
```

출력: 패턴별 트레이스 + 작업 수. Supervisor가 가장 깔끔; swarm이 가장 짧음; 계층형이 가장 깊음; 토론이 가장 비쌈.

## 사용하기

- **LangGraph** — supervisor 및 계층형 (중첩 하위 그래프)용.
- **OpenAI Agents SDK** — 도구로서의 핸드오프 (supervisor 형태)용.
- **CrewAI Flow** — 프로덕션 결정론적 작업용.
- **커스텀** — 토론 또는 정확한 제어가 필요할 때.

## 배포하기

`outputs/skill-orchestration-picker.md`는 토폴로지를 선택하고 구현합니다.

## 연습 문제

1. 라우터를 제거하여 supervisor-worker를 swarm으로 변환. 무엇이 깨지나요? 무엇이 개선되나요?
2. swarm에 홉 카운터 추가: 3번의 핸드오프 후 거부. A->B->A 바운싱을 잡아내나요?
3. 12개 전문가 도메인을 위한 2계층 계층형 시스템 구축. 중첩 없이 컨텍스트 버짓이 어디서 실패하나요?
4. 프로덕션 형태 워크로드에서 네 가지 패턴 프로파일링. 어떤 메트릭(지연 시간, 비용, 정확도, 디버깅 용이성)에서 어떤 패턴이 승리하나요?
5. Anthropic의 "Building Effective Agents" 게시물을 읽기. 각 프로덕션 흐름을 네 가지 중 하나에 매핑. 깔끔하게 매핑되지 않는 것이 있나요?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|------------------|-----------|
| Supervisor-worker | "라우터 + 전문가" | 중앙 LLM이 전문가에게 할당; 그들은 서로 대화하지 않음 |
| Swarm | "Peer-to-peer" | 공유 도구를 통한 직접 핸드오프; 중앙 라우터 없음 |
| Hierarchical | "Supervisor의 supervisor" | 대규모 인구를 위한 중첩 하위 그래프 |
| Debate | "제안자 + 비판" | 병렬 제안자, 상호 비판 (Lesson 25) |
| Tool-call-based supervision | "라이브러리 없는 Supervisor" | 컨텍스트 제어를 위해 직접 도구 호출로 supervisor 구현 |
| Crew | "자율 팀" | CrewAI의 역할 기반 협업 모드 |
| Flow | "결정론적 워크플로우" | CrewAI의 이벤트 기반 프로덕션 모드 |

## 추가 자료

- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — 다섯 가지 패턴 + 에이전트 vs 워크플로우
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — supervisor, swarm, 계층형
- [CrewAI docs](https://docs.crewai.com/en/introduction) — Crew vs Flow
- [Du et al., Society of Minds (arXiv:2305.14325)](https://arxiv.org/abs/2305.14325) — 토론 패턴
