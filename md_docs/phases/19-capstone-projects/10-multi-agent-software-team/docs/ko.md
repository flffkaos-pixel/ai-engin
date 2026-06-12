# 캡스톤 10 — 다중 에이전트 소프트웨어 엔지니어링 팀

> SWE-AF의 팩토리 아키텍처, MetaGPT의 역할 기반 프롬프팅, AutoGen 0.4의 타입화된 액터 그래프, Cognition의 Devin, Factory의 Droids는 모두 2026년 동일한 형태로 수렴했다: 아키텍처가 계획하고, N명의 코더가 병렬 worktree에서 작업하고, 검토자가 게이트하고, 테스터가 검증한다. 병렬 worktree가 wall-clock을 처리량으로 변환한다. 공유 상태 및 핸드오프 프로토콜이 실패 표면이 된다. 캡스톤은 팀을 구축하고, SWE-bench Pro에서 평가하고, 어떤 핸드오프가 중단되는지 그리고 얼마나 자주 중단되는지를 보고하는 것이다.

**유형:** 캡스톤
**언어:** Python / TypeScript (에이전트), Shell (worktree 스크립트)
**선수 과목:** Phase 11 (LLM 엔지니어링), Phase 13 (도구), Phase 14 (에이전트), Phase 15 (자율), Phase 16 (다중 에이전트), Phase 17 (인프라)
**활용 phases:** P11 · P13 · P14 · P15 · P16 · P17
**소요 시간:** 40시간

## 문제

단일 에이전트 코딩 하네스는 큰 작업에서 천장에 부딪힌다. 개별 에이전트가 약해서가 아니라 200k 토큰 컨텍스트가 아키텍처 계획 + 4개의 병렬 코드베이스 슬라이스 + 검토자 코멘터리 + 테스트 출력을 담을 수 없기 때문이다. 다중 에이전트 팩토리는 문제를 분할한다: 아키텍처가 계획을 소유하고, 코더가 병렬 worktree에서 구현을 소유하고, 검토자가 게이트하고, 테스터가 검증한다. SWE-AF의 "팩토리" 아키텍처, MetaGPT의 역할, AutoGen의 타입화된 액터 그래프 — 세 가지 프레임 모두 동일한 형태를 설명한다.

실패 표면은 핸드오프이다. 아키텍처가 코더가 구현할 수 없는 것을 계획한다. 코더가 충돌하는 diff를 생성한다. 검토자가 환각된 수정을 승인한다. 테스터가 아직 작성 중인 코더와 경주한다. 이러한 팀 중 하나를 구축하고 50개의 SWE-bench Pro 이슈에서 실행하며 모든 핸드오프를 추적하고 포스트모템을 게시할 것이다.

## 개념

역할은 타입화된 에이전트이다. **아키텍처** (Claude Opus 4.7)는 이슈를 읽고 계획을 작성하고 명시적 인터페이스가 있는 하위 작업으로 분할한다. **코더** (Claude Sonnet 4.7, N개의 병렬 인스턴스, 각각 `git worktree` + Daytona 샌드박스에서)는 독립적으로 하위 작업을 구현한다. **검토자** (GPT-5.4)는 병합된 diff를 읽고 승인하거나 특정 변경을 요청한다. **테스터** (Gemini 2.5 Pro)는 격리된 샌드박스에서 테스트 스위트를 실행하고 통과/실패를 보고한다.

통신은 공유 작업 보드(파일 지원 또는 Redis)를 통해 이루어진다. 각 역할은 처리할 수 있는 작업을 구독한다. 핸드오프는 A2A 프로토콜 타입화된 메시지이다. 조정关切: 병합 충돌 해결(조정자 역할 또는 자동 three-way 병합), 공유 상태 동기화(코더가 시작되면 계획이 동결됨; replans는 별도 이벤트임), 검토자 게이트키핑(검토자는 자신이 작성한 변경이나 제안한 변경을 승인할 수 없음).

토큰 증폭은 숨겨진 비용이다. 모든 역할 경계가 요약 프롬프트와 핸드오프 컨텍스트를 추가한다. 40턴 단일 에이전트 실행이 4개 역할에서 160 총 턴이 된다. 루브릭은 특히 토큰 효율성과 단일 에이전트 기준선 대비 가중치를 두는데, 질문이 "다중 에이전트가 작동하는가"가 아니라 "달러당 이기는가"이기 때문이다.

## 아키텍처

```
GitHub issue URL
      |
      v
Architect (Opus 4.7)
   reads issue, produces plan with subtasks + interfaces
      |
      v
Task board (file / Redis)
      |
   +-- subtask 1 ---+-- subtask 2 ---+-- subtask 3 ---+-- subtask 4 ---+
   v                v                v                v                v
Coder A          Coder B          Coder C          Coder D          (4 parallel)
 (Sonnet)         (Sonnet)         (Sonnet)         (Sonnet)
 worktree A       worktree B       worktree C       worktree D
 Daytona          Daytona          Daytona          Daytona
      |                |                |                |
      +--------+-------+-------+--------+
               v
           merge coordinator  (three-way merge + conflict resolution)
               |
               v
           Reviewer (GPT-5.4)
               |
               v
           Tester  (Gemini 2.5 Pro)  -> passes? -> open PR
                                     -> fails?  -> route back to coder
```

## 기술 스택

- 오케스트레이션: 공유 상태 + 역할당 하위 그래프가 있는 LangGraph
- 메시징: 타입화된 에이전트 간 메시지를 위한 Google 2025 A2A 프로토콜
- 모델: 아키텍처용 Opus 4.7, 코더용 Sonnet 4.7, 검토자용 GPT-5.4, 테스터용 Gemini 2.5 Pro
- Worktree 격리: 코더당 `git worktree add` + Daytona 샌드박스
- 병합 조정자: 커스텀 three-way 병합 + LLM 중재 충돌 해결
- Eval: SWE-bench Pro (50개 이슈), SWE-AF 시나리오, 단위 테스트용 HumanEval++
- 관찰가능성: 역할 태그가 있는 Langfuse, 역할별 토큰 회계
- 배포: 각 역할이 별도 Deployment + 백로그에서 HPA로 K8s에 배포

## 실습

1. **작업 보드.** 타입화된 메시지가 있는 파일 지원 JSONL: `plan_request`, `subtask`, `diff_ready`, `review_needed`, `test_needed`, `approved`, `rejected`, `replan_needed`. 에이전트가 태그를 구독한다.

2. **아키텍처.** GitHub 이슈를 읽고, 명시적 하위 작업 인터페이스(触碰된 파일, 공개 함수, 테스트 영향)가 필요한 계획 템플릿으로 Opus 4.7을 실행한다. 하위 작업 DAG가 포함된 하나의 `plan_request`를 emit한다.

3. **코더.** N개의 병렬 워커가 각각 보드에서 하나의 하위 작업을 claim한다. 각각 새로운 `git worktree add` 분기 + Daytona 샌드박스를 생성한다. 하위 작업을 구현한다. 패치 + 테스트 델타와 함께 `diff_ready`를 emit한다.

4. **병합 조정자.** 모든 코더 완료 시 3개의 분기를 스테이징 분기에 three-way 병합한다. 파일 수준 重複만 있을 때 LLM 중재 충돌 해결만 실행한다.

5. **검토자.** GPT-5.4가 병합된 diff를 읽는다. 자신이 작성한 diff를 승인할 수 없다. `approved`(noop) 또는 특정 변경 요청이 관련 코더로 라우팅되는 `review_feedback`을 emit한다.

6. **테스터.** Gemini 2.5 Pro가 깨끗한 샌드박스에서 테스트 스위트를 실행한다. 아티팩트를 캡처한다. `test_passed` 또는 실패한 스택트레이스와 함께 `test_failed`를 emit한다. 실패한 테스트는 실패한 하위 작업을 소유한 코더로 다시 라우팅된다.

7. **핸드오프 회계.** 역할 경계를 횡단하는 모든 메시지는 페이로드 크기 및 사용된 모델과 함께 Langfuse에서 스팬을 가져온다. 하위 작업당 토큰 증폭을 계산(coder_tokens + reviewer_tokens + tester_tokens + architect_share / coder_tokens).

8. **Eval.** 50개 SWE-bench Pro 이슈에서 실행한다. 통과@1과 $-per-solved-issue를 단일 에이전트 기준선(하나의 Sonnet 4.7이 단일 worktree에서)과 비교한다.

9. **포스트모템.** 각 실패한 이슈에 대해 중단된 핸드오프를 식별한다(계획이 너무 모호함, 병합 충돌, 검토자 false-approve, 테스터 플레이크). 핸드오프-실패 히스토그램을 생성한다.

## 활용

```
$ team run --issue https://github.com/acme/widget/issues/842
[architect] plan: 4 subtasks (parser, cache, api, migration)
[board]     dispatched to 4 coders in parallel worktrees
[coder-A]   subtask parser  -> 42 lines, tests pass locally
[coder-B]   subtask cache   -> 88 lines, tests pass locally
[coder-C]   subtask api     -> 31 lines, tests pass locally
[coder-D]   subtask migration -> 19 lines, tests pass locally
[merge]     3-way merge: 0 conflicts
[reviewer]  comments on cache (thread pool sizing); routed to coder-B
[coder-B]   revision: 92 lines; submits
[reviewer]  approved
[tester]    all 412 tests pass
[pr]        opened #3382   4 coders, 1 revision, $4.90, 18m
```

## 결과물

`outputs/skill-multi-agent-team.md`가 결과물이다. 이슈 URL 및 병렬 처리 수준이 주어지면 팀이 역할별 토큰 회계와 함께 병합 가능한 PR을 생성한다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 | 일치하는 50개 이슈 하위 집합, pass@1 |
| 20 | 병렬 스피드업 | 단일 에이전트 기준선 대비 wall-clock |
| 20 | 검토 품질 | 주입된 버그 프로브에 대한 false-승인율 |
| 20 | 토큰 효율성 | 해결된 이슈당 총 토큰 대 단일 에이전트 |
| 15 | 조정 엔지니어링 | 병합-충돌 해결, 핸드오프-실패 히스토그램 |
| **100** | | |

## 연습 문제

1. 실행 중mid에 明らかな 버그를 diff에 주입한다(메인 본문 전에 추가 `return None`). 검토자의 false-승인율을 측정한다. false-승인이 5% 미만일 때까지 검토자 프롬프트를 조정한다.

2. 2명의 코더로 줄인다(아키텍처 + 코더 + 검토자 + 테스터, 코더가 2개의 하위 작업을 순차적으로 실행). Wall-clock 및 통과율을 비교한다.

3. 병합 조정자를 단일 작성자 제약으로 교체한다(하위 작업이 disjoint 파일 집합을触碰). 아키텍처의 계획 부담을 측정한다.

4. 검토자를 GPT-5.4에서 Claude Opus 4.7로 교체한다. false-승인율 및 토큰 비용 delta를 측정한다.

5. 다섯 번째 역할 추가: 문서 작성자(Haiku 4.5). 검토 후 Changelog 항목을 생성한다. 문서 품질이额外的 토큰 지출을 정당화하는지 측정한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 병렬 worktree | "Isolated branch" | 코더당 새로운 작업 트리를 생성하는 `git worktree add` |
| 작업 보드 | "Shared message bus" | 에이전트가 구독하는 태그가 있는 파일 또는 Redis 저장소 |
| 핸드오프 | "Role boundary" | 한 역할의 컨텍스트에서 다른 역할의 컨텍스트로 횡단하는 모든 메시지 |
| 토큰 증폭 | "Multi-agent overhead" | 동일 작업에 대한 단일 에이전트 토큰 대비 역할 전반의 총 토큰 |
| A2A 프로토콜 | "Agent-to-agent" | Google의 2025 타입화된 에이전트 간 메시지 사양 |
| 병합 조정자 | "Integrator" | three-way 병합을 실행하고 충돌을 중재하는 구성요소 |
| 거짓 승인 | "Reviewer hallucination" | 알려진 버그가 있는 diff를 검토자가 승인함 |

## 추가 자료

- [SWE-AF factory architecture](https://github.com/Agent-Field/SWE-AF) — 2026년 다중 에이전트 팩토리 기준
- [MetaGPT](https://github.com/FoundationAgents/MetaGPT) — 역할 기반 다중 에이전트 프레임워크
- [AutoGen v0.4](https://github.com/microsoft/autogen) — Microsoft의 타입화된 액터 프레임워크
- [Cognition AI (Devin)](https://cognition.ai) — 기준 제품
- [Factory Droids](https://www.factory.ai) — 대체 기준 제품
- [Google A2A protocol](https://developers.google.com/agent-to-agent) — 에이전트 간 메시징 사양
- [git worktree documentation](https://git-scm.com/docs/git-worktree) — 격리 기판
- [SWE-bench Pro](https://www.swebench.com) — 평가 대상