# ReWOO와 Plan-and-Execute: 분리된 계획

> ReAct는 생각과 행동을 하나의 스트림에 인터리브한다. ReWOO는 이를 분리한다: 하나의 큰 계획을 먼저 세우고 실행한다. HotpotQA에서 5배 적은 토큰, +4% 정확도, 그리고 플래너를 7B 모델로 증류할 수 있다. Plan-and-Execute가 이를 일반화했고, Plan-and-Act가 웹 탐색으로 확장했다.

**Type:** Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop)
**Time:** ~60분

## 학습 목표

- ReWOO의 Planner / Worker / Solver 분할이 ReAct의 인터리브드 루프보다 토큰을 절약하고 견고성을 향상시키는 이유를 설명한다.
- 계획 DAG, 의존성 순서 실행기, Worker 출력을 구성하는 Solver를 모두 stdlib으로 구현한다.
- 작업이 인터리브드 ReAct 대신 계획-후-실행으로 실행되어야 하는 경우를 2026년 "다섯 가지 워크플로우 패턴"(Anthropic) 프레이밍을 사용하여 결정한다.
- 장기 웹 또는 모바일 작업에 Plan-and-Act의 합성 계획 데이터가 필요한 시점을 인식한다.

## 문제

ReAct의 인터리브드 thought-action-observation 루프는 간단하고 유연하지만, 각 도구 호출은 이전 모든 생각을 포함한 전체 이전 컨텍스트를 전달해야 한다. 토큰 사용량은 깊이에 따라 이차적으로 증가한다. 더 나쁜 것은: 루프 중간에 도구가 실패하면 모델이 오류 관찰로부터 전체 계획을 다시 도출해야 한다.

ReWOO (Xu et al., arXiv:2305.18323, May 2023)는 이를 인지하고 한 가지 선택을 했다: 모든 것을 먼저 계획하고, 증거를 병렬로 가져오고, 마지막에 답변을 구성한다. 계획에 하나의 LLM 호출, 증거에 N개의 도구 호출(병렬 가능), 해결에 하나의 LLM 호출. 유연성(계획이 정적임)을 희생하는 대신 훨씬 더 나은 토큰 효율성과 명확한 실패 모드를 얻는다.

## 개념

### 세 가지 역할

```
Planner:  user_question -> [plan_dag]
Workers:  [plan_dag]     -> [evidence]        (tool calls, possibly parallel)
Solver:   user_question, plan_dag, evidence -> final_answer
```

Planner는 DAG를 생성한다. 각 노드는 도구 이름, 인수, 의존하는 이전 노드(`#E1`, `#E2` 같은 참조)를 지정한다. Workers는 노드를 위상 순서로 실행한다. Solver는 모든 것을 함께 엮는다.

### 5배 적은 토큰의 이유

ReAct는 step 수에 따라 프롬프트 길이가 선형적으로 증가한다. 10번째 step에서 프롬프트에는 생각1 + 행동1 + 관찰1 + 생각2 + 행동2 + 관찰2 등이 포함된다. 각 중간 단계는 원래 프롬프트도 중복해서 포함한다.

ReWOO는 하나의 큰 플래너 프롬프트, N개의 작은 worker 프롬프트(각각 도구 호출만 있고 체인 없음), 그리고 하나의 solver 프롬프트를 사용한다. HotpotQA에서 논문은 +4 절대 정확도를 기록하면서 ~5배 적은 토큰을 측정했다.

### 더 견고한 이유

ReAct에서 worker 3이 실패하면 루프가 오류로부터 중간에 추론해야 한다. ReWOO에서 worker 3은 오류 문자열을 반환하고, solver는 원래 계획과 함께 컨텍스트에서 이를 보고 정상적으로 처리할 수 있다. 실패 위치 파악은 step별이 아니라 노드별이다.

### Planner 증류

논문의 두 번째 결과: planner는 관찰을 보지 않기 때문에, 175B 교사로부터 planner 출력으로 7B 모델을 미세 조정할 수 있다. 작은 모델이 계획을 처리하고, 큰 모델은 추론에 필요하지 않다. 이는 이제 표준이며, 많은 2026년 프로덕션 에이전트는 작은 플래너와 큰 실행기를 사용하거나 그 반대다.

### Plan-and-Execute (LangChain, 2023)

LangChain 팀의 2023년 8월 게시물은 ReWOO를 패턴 이름으로 일반화했다: Plan-and-Execute. 업프론트 플래너가 step 목록을 출력하고, 실행기가 각 step을 실행하며, 옵션으로 재계획자가 결과를 관찰한 후 수정할 수 있다. 이는 ReWOO보다 ReAct에 더 가깝지만(재계획자가 관찰을 계획에 다시 가져옴), 토큰 절약 효과는 유지한다.

### Plan-and-Act (Erdogan et al., arXiv:2503.09572, ICML 2025)

Plan-and-Act는 이 패턴을 장기 웹 및 모바일 에이전트로 확장한다. 주요 기여는 합성 계획 데이터다: 레이블이 지정된 궤적 생성기가 계획이 명시적인 훈련 데이터를 생성한다. 단일 ReAct 궤도가 일관성을 잃는 30-50 step 이상의 WebArena 유사 작업에서 작동하는 플래너 모델을 미세 조정하는 데 사용된다.

### 어떤 것을 선택할지

| 패턴 | 시기 |
|------|------|
| ReAct | 짧은 작업, 알 수 없는 환경, 반응형 예외 처리 필요 |
| ReWOO | 알려진 도구가 있는 구조화된 작업, 토큰 민감, 병렬화 가능한 증거 |
| Plan-and-Execute | 부분 실행 후 재계획이 있는 ReWOO와 유사 |
| Plan-and-Act | 장기(>30 step), 웹/모바일/컴퓨터 사용 |
| Tree of Thoughts | 검색 비용을 지불할 가치가 있는 경우 (레슨 04) |

Anthropic의 2024년 12월 지침: 가장 간단한 것부터 시작하라. 작업이 하나의 도구 호출과 요약이면 ReWOO를 구축하지 마라. 작업이 40단계 연구 과제면 ReAct만으로 하지 마라.

## 직접 구현하기

`code/main.py`는 장난감 ReWOO를 구현한다:

- `Planner` — 프롬프트에서 계획 DAG를 출력하는 스크립트 기반 정책.
- `Worker` — 레지스트리를 통해 각 노드의 도구 호출을 디스패치.
- `Solver` — 증거를 읽고 최종 답변을 생성하는 스크립트 기반 구성.
- 의존성 해결 — `#E1` 같은 참조를 이전 worker 출력으로 대체.

데모는 "프랑스 수도 인구를 백만 단위로 반올림하여 알려줘"라는 질문에 두 단계 계획으로 답한다: (1) 수도 조회, (2) 인구 조회, 그런 다음 해결.

실행:

```
python3 code/main.py
```

트레이스는 먼저 전체 계획, 그 다음 worker 결과, 마지막으로 solver 구성을 보여준다. 토큰 수(대략적인 문자 수 출력)를 ReAct 스타일의 인터리브드 실행과 비교하라 — ReWOO가 이런 구조화된 작업에서 승리한다.

## 활용하기

LangGraph는 Plan-and-Execute를 레시피로 제공한다(`create_react_agent`는 ReAct용, plan-execute용 커스텀 그래프). CrewAI의 Flows는 패턴을 직접 인코딩한다: 작업을 업프론트 정의하고 Flow DAG가 실행한다. Plan-and-Act의 합성 데이터 접근 방식은 여전히 대부분 연구 단계이며, 런타임 패턴(명시적 계획 DAG)은 LangGraph와 CrewAI Flows를 통해 프로덕션에 제공된다.

## 배포하기

`outputs/skill-rewoo-planner.md`는 도구 카탈로그가 주어지면 사용자 요청에서 ReWOO 계획 DAG를 생성한다. 실행기에 전달하기 전에 계획을 검증한다(비순환, 모든 참조 해결, 모든 도구 존재).

## 연습 문제

1. 독립적인 계획 노드에 대해 worker 실행을 병렬화하라. 2개의 병렬 그룹이 있는 6개 노드 DAG에서 무엇을 얻을 수 있는가?
2. worker가 오류를 반환하면 발동하는 재계획 노드를 추가하라. ReWOO를 Plan-and-Execute로 만드는 가장 작은 변경은 무엇인가?
3. `Planner`를 작은 모델(7B급)로 교체하고 `Solver`는 프론티어 모델에 유지하라. 종단 간 품질을 비교하라 — 분할은 어디서 실패하는가?
4. ReWOO 논문의 planner 증류에 관한 섹션 4를 읽어라. 175B -> 7B 결과를 개념적으로 재현하라: 어떤 훈련 데이터가 필요하고, 계획 품질을 어떻게 측정할 것인가?
5. 장난감을 Plan-and-Act의 궤적 형태로 포팅하라: 계획은 DAG가 아닌 시퀀스다. 어떤 트레이드오프가 바뀌는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| ReWOO | "관찰 없는 추론" | 계획, 증거를 병렬로 가져오고, 해결 — 계획 프롬프트에 관찰 없음 |
| Plan-and-Execute | "LangChain의 plan-execute 패턴" | 실행 후 옵션 재계획 노드가 있는 ReWOO |
| Plan-and-Act | "확장된 plan-execute" | 장기 작업을 위한 합성 계획 훈련 데이터가 있는 명시적 플래너/실행기 분할 |
| Evidence reference | "#E1, #E2, ..." | 디스패치 시 이전 worker 출력으로 대체되는 계획 노드 플레이스홀더 |
| Planner distillation | "작은 플래너, 큰 실행기" | 큰 교사의 플래너 트레이스로 작은 모델 미세 조정 |
| Token efficiency | "적은 왕복" | 논문에서 ReAct 대비 HotpotQA에서 5배 적은 토큰 |
| DAG executor | "위상 디스패처" | 의존성 순서로 계획 노드 실행; 각 레벨에서 병렬 |

## 추가 자료

- [Xu et al., ReWOO: Decoupling Reasoning from Observations (arXiv:2305.18323)](https://arxiv.org/abs/2305.18323) — 표준 논문
- [Erdogan et al., Plan-and-Act (arXiv:2503.09572)](https://arxiv.org/abs/2503.09572) — 합성 계획이 있는 확장된 플래너-실행기
- [LangGraph Plan-and-Execute tutorial](https://docs.langchain.com/oss/python/langgraph/overview) — 프레임워크 레시피
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — 작동하는 가장 간단한 패턴 선택
