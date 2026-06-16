# Anthropic의 워크플로우 패턴: 단순함이 복잡함보다 낫다

> Schluntz와 Zhang (Anthropic, Dec 2024)은 워크플로우(미리 정의된 경로)와 에이전트(동적 도구 사용)를 구분한다. 다섯 가지 워크플로우 패턴이 대부분의 경우를 다룬다. 직접 API 호출로 시작하라. 단계를 예측할 수 없을 때만 에이전트를 추가하라.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop)
**Time:** ~60분

## 학습 목표

- Anthropic의 다섯 가지 워크플로우 패턴을 명명한다: prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer.
- 에이전트-대-워크플로우 구분과 각각의 엔지니어링 비용을 설명한다.
- 워크플로우 대신 에이전트를 선택해야 할 때를 식별한다(그리고 그 반대).
- 스크립트 기반 LLM에 대해 stdlib에서 다섯 가지 패턴을 모두 구현한다.

## 문제

팀은 단일 함수 호출로 해결되는 문제에 멀티 에이전트 프레임워크를 사용한다. 비용은 실제다: 프레임워크는 프롬프트를 모호하게 하고, 제어 흐름을 숨기며, 조기 복잡성을 초대하는 레이어를 추가한다. Schluntz와 Zhang의 2024년 12월 게시물은 가장 많이 인용된 업계 반박이다: 간단하게 시작하고, 비용을 정당화할 때만 복잡성을 추가하라.

## 개념

### 워크플로우 vs 에이전트

- **워크플로우.** 미리 정의된 코드 경로를 통해 조정되는 LLM과 도구. 엔지니어가 그래프를 소유.
- **에이전트.** LLM이 자신의 도구를 동적으로 지시하고 자신의 단계를 수행. 모델이 그래프를 소유.

둘 다 각자의 자리가 있다. 워크플로우는 더 저렴하고, 빠르며, 디버깅하기 쉽다. 에이전트는 개방형 문제를 열어주지만 실패 모드를 추론하기 어렵게 만든다.

### 증강된 LLM

다섯 가지 패턴 모두의 기초: 검색(검색), 도구(행동), 메모리(지속성)의 세 가지 기능이 연결된 하나의 LLM. 모든 API 호출이 이를 사용할 수 있다.

### 다섯 가지 패턴

1. **Prompt chaining.** 호출 1의 출력이 호출 2의 입력. 작업이 깔끔한 선형 분해를 가질 때 사용. 단계 간 선택적 프로그래밍 방식 게이트.

2. **Routing.** 분류기 LLM이 어떤 다운스트림 LLM 또는 도구를 호출할지 선택. 범주적으로 다른 입력이 다른 처리가 필요할 때 사용 (1차 지원 vs 환불 vs 버그 vs 영업).

3. **Parallelization.** N개의 LLM 호출을 동시에 실행, 결과 집계. 두 가지 형태: 섹셔닝(다른 청크)과 투표(같은 프롬프트, N회 실행, 다수/합성).

4. **Orchestrator-workers.** 오케스트레이터 LLM이 어떤 워커(역시 LLM)를 실행할지 동적으로 결정하고 출력을 합성. 에이전트 루프와 유사하지만 오케스트레이터가 무한 루프를 돌지 않음.

5. **Evaluator-optimizer.** 하나의 LLM이 답변을 제안하고, 다른 LLM이 평가. 평가기가 통과할 때까지 반복. 일반화된 Self-Refine (레슨 05).

### 워크플로우가 에이전트를 이기는 경우

- **예측 가능한 작업.** 단계를 열거할 수 있다면 그래야 함.
- **비용이 제한된 작업.** 워크플로우는 단계 수가 제한됨; 에이전트는 나선형으로 갈 수 있음.
- **규정 준수가 필요한 작업.** 감사자는 궤적에서 추론하는 대신 그래프를 읽고 싶어함.

### 에이전트가 워크플로우를 이기는 경우

- **개방형 연구.** 다음 단계가 마지막 단계의 반환에 달려 있을 때.
- **가변 길이 작업.** 단계 수를 알 수 없는 분에서 시간 단위 작업.
- **새로운 도메인.** 올바른 워크플로우를 아직 모를 때 — 먼저 탐험, 나중에 코드화.

### 컨텍스트 엔지니어링 동반

"Effective context engineering for AI agents" (Anthropic 2025)는 인접 학문을 공식화: 200k 윈도우는 예산이지 컨테이너가 아니다. 무엇을 포함할지, 언제 압축할지, 언제 컨텍스트를 성장시킬지. 이 커리큘럼의 Phase 14 초기 레슨에서 자세히 다룸.

## 직접 구현하기

`code/main.py`는 `ScriptedLLM`에 대해 다섯 가지 워크플로우 패턴을 모두 구현한다:

- `prompt_chain(input, steps)` — 순차적.
- `route(input, classifier, handlers)` — 분류 + 디스패치.
- `parallel_vote(prompt, n, aggregator)` — N회 실행, 집계.
- `orchestrator_workers(task, workers)` — 오케스트레이터가 워커 선택.
- `evaluator_optimizer(task, proposer, evaluator, max_iter)` — 통과까지 반복.

실행:

```
python3 code/main.py
```

각 패턴이 트레이스를 출력. 패턴당 코드 줄 수는 ~10-15; 프레임워크의 비용은 수천 줄로 측정됨.

## 활용하기

- 대부분의 작업에 직접 API 호출.
- 패턴이 진정으로 지속적 상태(LangGraph), 액터-모델 동시성(AutoGen v0.4), 또는 역할 템플릿(CrewAI)을 필요로 할 때만 프레임워크.
- 다시 구축하지 않고 Claude Code 하네스 형태를 원할 때 Claude Agent SDK 사용.

## 배포하기

`outputs/skill-workflow-picker.md`는 주어진 작업 설명에 대해 올바른 패턴을 선택하며, 결정 근거와 워크플로우가 부족할 경우 에이전트로의 리팩터 경로를 포함한다.

## 연습 문제

1. 신뢰도 임계값으로 라우팅 구현. 임계값 미만 -> 사람에게 에스컬레이션. 1차 지원 사용 사례에서 임계값은 어디에 위치하는가?
2. `parallel_vote`에 타임아웃 추가. 하나의 호출이 중단되면 어떻게 되는가? 누락된 투표로 어떻게 집계하는가?
3. `evaluator_optimizer`를 밴디트로 전환: 반복 간 상위 2개 출력을 유지하여 늦은 좋은 결과가 늦은 나쁜 결과에 의해 덮어쓰여지지 않도록 함.
4. prompt chaining과 routing 결합: 라우터가 세 개의 체인 중 하나를 선택. 큰 단일 프롬프트 대안과 토큰 비용 측정.
5. 프로덕션 기능 중 하나를 선택. 워크플로우 그래프 그리기. 단계 수 세기. 여기서 에이전트가 실제로 더 나을까?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Workflow | "미리 정의된 흐름" | 엔지니어 소유의 LLM 및 도구 호출 그래프 |
| Agent | "자율 AI" | 모델 소유 그래프; 동적 도구 지시 |
| Augmented LLM | "도구가 있는 LLM" | LLM + 검색 + 도구 + 메모리; 원자 단위 |
| Prompt chaining | "순차적 호출" | 호출 N의 출력이 호출 N+1의 입력 |
| Routing | "분류기 디스패치" | 어떤 체인/모델이 입력을 처리할지 선택 |
| Parallelization | "팬 아웃" | N개의 동시 호출; 섹셔닝 또는 투표로 집계 |
| Orchestrator-workers | "디스패처 에이전트" | 오케스트레이터 LLM이 전문 LLM을 동적으로 선택 |
| Evaluator-optimizer | "제안자 + 판사" | 평가기가 통과할 때까지 반복; 일반화된 Self-Refine |

## 추가 자료

- [Anthropic, Building Effective Agents (Dec 2024)](https://www.anthropic.com/research/building-effective-agents) — 다섯 가지 워크플로우 패턴
- [Anthropic, Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — 동반 학문
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — 상태 저장 그래프가 비용을 정당화할 때
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) — 제품화된 orchestrator-workers 패턴
