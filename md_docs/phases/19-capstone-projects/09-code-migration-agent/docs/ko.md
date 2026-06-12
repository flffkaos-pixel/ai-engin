# 캡스톤 09 — 코드 마이그레이션 에이전트 (Repo 수준 언어/런타임 업그레이드)

> Amazon의 MigrationBench (Java 8 to 17)와 Google의 App Engine Py2-to-Py3 마이그레이터가 2026년 기준을 설정했다. Moderne의 OpenRewrite는规模的으로 결정론적 AST 재작성를 수행한다. Grit은 codemod 스타일 DSL로 동일한 문제를 겨냥한다. 운영 패턴은 둘 다 결합한다: 안전한 재작성을 위한 결정론적 기판 + 모호한 케이스를 위한 에이전트 레이어 + 분기당 빌드를 위한 샌드박스 + PR이 열리기 전에 초록으로 전환하는 테스트 하네스이다. 캡스톤은 50개의 실제 repo를 마이그레이션하고 실패 분류와 함께 통과율을 게시하는 것이다.

**유형:** 캡스톤
**언어:** Python (에이전트), Java / Python (대상), TypeScript (대시보드)
**선수 과목:** Phase 5 (NLP), Phase 7 (트랜스포머), Phase 11 (LLM 엔지니어링), Phase 13 (도구), Phase 14 (에이전트), Phase 15 (자율), Phase 17 (인프라)
**활용 phases:** P5 · P7 · P11 · P13 · P14 · P15 · P17
**소요 시간:** 30시간

## 문제

대규모 코드 마이그레이션은 2026년 가장 깔끔한 운영 코딩 에이전트 응용 프로그램 중 하나이다. ground truth는 명확하다(마이그레이션 후 테스트 스위트가 통과하는가?), 보상은 실제적이다(Java-8 fleet 마이그레이션은 인력 규모의 프로젝트이다), 벤치마크는 공개되어 있다(MigrationBench 50-repo 하위 집합). Moderne의 OpenRewrite가 결정론적 측면을 처리한다. 에이전트 레이어가 레시피가 처리할 수 없는 모든 것을 처리한다: 모호한 재작성을 포함한 모호한 케이스, 빌드 시스템 드리프트, 롱테일 구문, 전이적 의존성 중단.

Java 8 repo(또는 Python 2 repo)를 가져와서 green-CI 마이그레이션 분기를 생성하는 에이전트를 구축한다. 통과율, 테스트 coverage 보존, repo당 비용을 측정하고 실패 분류를 구축한다. 결정론적 전용 기준선과 나란히 비교하면 에이전트의 가치가 실제로 어디에 있는지 알 수 있다.

## 개념

파이프라인에는 두 레이어가 있다. **결정론적 기판** (Java용 OpenRewrite, Python용 libcst)는 대량의 기계적 재작성을 안전하게 처리한다: 가져오기, 메서드 시그니처, null-안전 편집, try-with-resources, 사용 중단된 API 교체. 빠르고 감사 가능한 diff를 생성한다. **에이전트 레이어** (Claude Opus 4.7 및 GPT-5.4-Codex 위의 OpenAI Agents SDK 또는 LangGraph)는 레시피가 처리할 수 없는 케이스를 처리한다: 빌드 파일 업그레이드(Maven/Gradle/pyproject), 전이적 의존성 충돌, 테스트 플레이크, 커스텀 어노테이션.

각 repo는 대상 런타임이 사전 설치된 Daytona 샌드박스를 가져온다. 에이전트는 반복한다: 빌드 실행, 실패 분류, 수정 적용, 재실행. 하드 제한: repo당 30분, $8, 20 에이전트 턴. 모든 테스트가 통과하고 coverage delta가 음수가 아니면 PR이 열린다. 그렇지 않으면 repo가 증거와 함께 실패 클래스에归档된다.

실패 분류가 결과물이다. 50개 repo에서 무엇이 중단되었는가? 전이적 deps? 커스텀 어노테이션? 빌드 도구 버전? 마이그레이션과 관련 없는 테스트 플레이크? 각 클래스에 카운트와 예제 diff가 있다. 미래 레시피 작성자는 상위 3개를 겨냥할 수 있다.

## 아키텍처

```
target repo
      |
      v
OpenRewrite / libcst deterministic recipes
   (safe, fast, auditable, ~70-80% of fixes)
      |
      v
Daytona sandbox per branch
      |
      v
agent loop (Claude Opus 4.7 / GPT-5.4-Codex):
   - run build -> capture failures
   - classify failures (build, test, lint)
   - apply fix (patch or retry recipe)
   - rerun
   - budget: 30 min, $8, 20 turns
      |
      v
test + coverage delta gate
      |
      v (passed)
open PR
      |
      v (failed)
file under failure class + attach repro
```

## 기술 스택

- 결정론적 기판: Java용 OpenRewrite 또는 Python용 libcst
- 에이전트: Claude Opus 4.7 + GPT-5.4-Codex 위의 OpenAI Agents SDK 또는 LangGraph
- 샌드박스: 각 분기당 Daytona devcontainers, 사전 설치된 대상 런타임(Java 17 / Python 3.12)
- 빌드 시스템: Maven, Gradle, uv (Python)
- 벤치마크: Amazon MigrationBench 50-repo 하위 집합(Java 8 to 17), Google App Engine Py2-to-Py3 repos
- 테스트 하네스: 병렬 실행기, Jacoco(Java) 또는 coverage.py(Python)를 통한 coverage
- 관찰가능성: repo당 모든 diff 청크가 포함된 Langfuse + trace 번들
- 대시보드: 클래스별 카운트 및 예제 diff가 있는 실패 분류 대시보드

## 실습

1. **레시피 패스.** 먼저 OpenRewrite (Java) 또는 libcst (Python) 레시피를 실행한다. 기계적인 마이그레이션의 70-80%를Catch한다. "recipe" 커밋으로 커밋한다.

2. **빌드 시험.** Daytona 샌드박스: 대상 런타임 설치, 빌드 실행. green이면 tests로 건너뛰기. red이면 에이전트에 전달.

3. **에이전트 루프.** 도구가 있는 LangGraph: `run_build`, `read_file`, `edit_file`, `run_test`, `git_diff`. 에이전트가 실패를 분류하고(dep, syntax, test, build-tool) 목표로 하는 수정 을 적용한다. 재실행.

4. **예산 캡.** repo당 30분 wall-clock, $8 비용, 20 에이전트 턴. 모든 breach가 발생하면 현재 diff와 함께 "budget_exhausted" 아래에归档한다.

5. **테스트 + coverage 게이트.** 빌드가 green 된 후 테스트 스위트를 실행한다. 기본 repo와 coverage를 비교한다. coverage가 2% 이상 떨어지면 "coverage_regression" 아래에归档한다.

6. **PR 열기.** 성공 시 분기를 push하고 diff와 적용된 레시피 및 에이전트가 작성한 커밋의 요약과 함께 PR을 연다.

7. **실패 분류.** 실패한 각 repo에 클래스를 태그한다: `dep_upgrade_required`, `build_tool_drift`, `custom_annotation`, `test_flake`, `syntax_edge_case`, `budget_exhausted`. 대시보드를 구축한다.

8. **50-repo 실행.** MigrationBench 하위 집합에서 실행한다. 클래스별 통과율, repo당 비용, coverage 보존, 결정론적 전용 기준선 대비 비교를 보고한다.

## 활용

```
$ migrate legacy-java-service --target java17
[recipe]   27 rewrites applied (JUnit 4->5, HashMap initializer, try-with-resources)
[build]    FAIL: cannot find symbol sun.misc.BASE64Encoder
[agent]    turn 1 classify: removed_jdk_api
[agent]    turn 2 apply: sun.misc.BASE64Encoder -> java.util.Base64
[build]    OK
[tests]    412/412 passing; coverage 84.1% -> 84.3%
[pr]       opened #1841  cost=$3.20  turns=4
```

## 결과물

`outputs/skill-migration-agent.md`가 결과물이다. repo가 주어지면 결정론적 레시피를 실행한 다음 에이전트 루프를 실행하여 green 마이그레이션 분기를 생성하거나 repo를 분류 클래스 아래에归档한다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | MigrationBench 통과율 | 50-repo 하위 집합 pass@1 |
| 20 | 테스트 coverage 보존 | 기본 대비 평균 coverage delta |
| 20 | 마이그레이션된 repo당 비용 | 통과 실행에서 $/repo |
| 20 | 에이전트/결정론적 도구 통합 | OpenRewrite가 처리한 수정 비율 대 에이전트가 작성한 수정 비율 |
| 15 | 실패 분석 보고서 | 예제가 포함된 분류 완전성 |
| **100** | | |

## 연습 문제

1. 에이전트 없이 OpenRewrite만으로 마이그레이션 파이프라인을 실행한다. 전체 파이프라인과 통과율을 비교한다. 에이전트만이 차이를 만드는 케이스를 식별한다.

2. "lint-clean" 검사를 구현한다: 마이그레이션 후 스타일 린터(Java의 spotless, Python의 ruff)를 실행한다. 새로운 린트 오류가 나타나면 PR을 실패시킨다. Coverage는 보존되었지만 스타일이 퇴보한 비율을 측정한다.

3. "minimal-diff" 옵티마이저를 추가한다: 에이전트의 분기가 테스트를 통과한 후 두 번째 패스로 불필요한 변경을 트리밍한다. diff 크기 감소를 보고한다.

4. 세 번째 마이그레이션으로 확장: Node 18 to Node 22. 샌드박스 래핑을 재사용; 레시피 레이어를 커스텀 codemod로 교체한다.

5. 첫 번째 green 빌드까지 시간(TTFGB)을 UX 메트릭으로 측정한다. 목표: p50 10분 미만.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 결정론적 기판 | "Recipe engine" | OpenRewrite / libcst: 안전 보장이 있는 선언적 AST 재작성 |
| Codemod | "Code-modifying program" | 소스 코드를 기계적으로 변경하는 재작성 규칙 |
| 빌드 드리프트 | "Tool version skew" | 주요 버전 간의 Maven / Gradle / uv 동작의 미묘한 변경 |
| 실패 클래스 | "Taxonomy bucket" | repo가 마이그레이션되지 않은 레이블이 지정된 이유: dep, syntax, test, build-tool, budget |
| Coverage delta | "Coverage preservation" | 기본에서 마이그레이션된 분기로의 테스트 coverage % 변경 |
| 에이전트 턴 | "Tool-call round" | 에이전트 루프에서 하나의 plan -> act -> observe 사이클 |
| 예산 고갈 | "Hit the ceiling" | repo가 통과하지 않고 30분/$8/20턴 제한을 소비함 |

## 추가 자료

- [Amazon MigrationBench](https://aws.amazon.com/blogs/devops/amazon-introduces-two-benchmark-datasets-for-evaluating-ai-agents-ability-on-code-migration/) — 2026년 기준 벤치마크
- [Moderne.io OpenRewrite platform](https://www.moderne.io) — 결정론적 기판 기준
- [OpenRewrite documentation](https://docs.openrewrite.org) — 레시피 작성
- [Grit.io](https://www.grit.io) — 대체 codemod DSL
- [OpenAI sandboxed migration cookbook](https://developers.openai.com/cookbook/examples/agents_sdk/sandboxed-code-migration/sandboxed_code_migration_agent) — Agents SDK 기준
- [Google App Engine Py2 to Py3 migrator](https://cloud.google.com/appengine) — 대체 마이그레이션 벤치마크
- [libcst](https://github.com/Instagram/LibCST) — Python 결정론적 기판
- [Daytona sandboxes](https://daytona.io) — 분기당 샌드박스 기준