# 에이전트 워크벤치: 캡스톤

> 캡스톤은 전체 Phase 14를 종합한다. 에이전트 워크벤치는 다단계 도구 사용, 하위 에이전트 생성, 평가, 관찰 가능성, 방어 UX 및 안전을 결합한다.

**Type:** Build (Capstone)
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01–41 (Complete Phase 14)
**Time:** ~120분

## 학습 목표

- 에이전트 워크벤치를 구현하여 Phase 14의 모든 패턴을 통합한다.
- 벤치마크에 대해 워크벤치를 평가하고 결과를 관찰 가능성에 게시한다.
- 워크벤치에 방어 UX와 가드레일을 추가한다.
- 벤치마크에 대해 배포한다.

## 문제

42개의 레슨을 마쳤다. 이제 하나의 완전한 기능을 갖춘 에이전트 워크벤치에서 모든 것을 종합해야 한다. 캡스톤은 Phase 14가 가르친 모든 패턴을 포함한다:

- 도구 등록 및 실행 (레슨 06, 10)
- 하위 에이전트 병렬화 및 격리 (레슨 17)
- 평가 (레슨 19-20, 30)
- 관찰 가능성 (레슨 23-24)
- 방어 UX와 HITL (레슨 28)
- 가드레일 (레슨 27, 39)
- 프롬프트 캐싱 (레슨 40)

## 사양

다음이 포함된 에이전트 워크벤치 구축:

**1. 에이전트 런타임.** 도구를 등록하고 하위 에이전트를 실행하는 에이전트 루프. 에이전트 루프 패턴(레슨 01)에 도구 실행(레슨 06) 및 하위 에이전트(레슨 17)가 추가됨.

**2. 도구 세트.** 장난감 평가를 위한 최소 5개 도구: `search_web`(시뮬레이션), `read_file`, `write_file`, `run_code`, `summarize`.

**3. 평가.** SWE-bench 스타일 작업에 대해 워크벤치를 평가하는 평가기: FAIL_TO_PASS + PASS_TO_PASS(레슨 19). GAIA 스타일 난이도(레슨 19). 라운드당 추가된 단계 측정(OSWorld-Human 스타일 효율성, 레슨 20).

**4. 관찰 가능성.** OTel GenAI 계측은 모든 도구 호출 및 LLM 호출을 추적합니다(레슨 23-24).

**5. 방어 UX.** 확인 게이트, 거절 설명, 실행 취소(레슨 28).

**6. 가드레일.** 프롬프트 인젝션 분류기, HITL 게이트, 레드팀 공격 시뮬레이션(레슨 27, 39).

**7. 프롬프트 캐싱.** 반복되는 프롬프트 접두사 캐시(레슨 40).

## 직접 구현하기

`code/main.py`는 에이전트 워크벤치를 구현한다:

- **`run_agent(task)`** — 작업을 가져와 도구 실행, 하위 에이전트 생성, 관찰 가능성에 게시.
- **`evaluate(benchmark)`** — 작업에 대해 워크벤치 실행, FAIL_TO_PASS + PASS_TO_PASS + 단계 효율성 점수 생성.
- **`add_defensive_ux()`** — 확인 게이트, 거절 설명, 실행 취소로 워크벤치 래핑.
- **`add_guardrails()`** — 프롬프트 인젝션 분류기와 레드팀 공격 시뮬레이션으로 워크벤치 래핑.
- **`run_red_team()`** — 가드레일에 대한 공격 실행, 결과 보고.

실행:

```
python3 code/main.py
```

출력: 작업 결과, 평가 점수, 방어 UX 로그, 가드레일 결과, 관찰 가능성 추적.

## 활용하기

- 이 워크벤치를 새 에이전트 프로젝트의 템플릿으로 사용.
- Phase 14 레슨을 참조하여 각 구성 요소를 심층 학습.
- 평가 및 관찰 가능성을 프로덕션 파이프라인에 통합.

## 배포하기

`outputs/skill-agent-workbench.md` scaffolds the complete Agent Workbench with all components.

## 연습 문제

1. 워크벤치에 5개의 도구를 더 추가: 총 10개 도구. 추가 도구가 평가 점수에 어떤 영향을 미치는가?
2. 새로운 벤치마크(자체 선택)에 대해 워크벤치 평가. 추가된 벤치마크는 무엇을 드러내는가?
3. 방어 UX를 우회하는 시나리오 테스트: 확인 게이트 없이 "데이터베이스 삭제". 무슨 일이 발생하는가?
4. 가드레일을 우회하는 시나리오 테스트: 인젝션 페이로드. 분류기가 차단하는가?
5. 관찰 가능성 추적을 Langfuse, Phoenix 또는 MLflow로 내보내기: 프로덕션 관찰 가능성이 어떻게 보이는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Agent Workbench | "Phase 14 캡스톤" | 모든 Phase 14 패턴을 결합하는 완전한 기능의 에이전트 |
| Capstone | "종합" | 42개 레슨의 패턴을 하나의 애플리케이션으로 통합 |
| FAIL_TO_PASS | "수정 게이트" | 이전에 실패했으며 패치 후 통과해야 하는 테스트 |
| PASS_TO_PASS | "회귀 방지 게이트" | 이전에 통과했으며 여전히 통과해야 하는 테스트 |
| OTel GenAI | "LLM 텔레메트리" | LLM 호출 및 도구 사용을 위한 표준화된 스팬 |

## 추가 자료

- Phase 14 · 01 (Agent Loop) — core runtime
- Phase 14 · 06 (Tool Use) — tool registration
- Phase 14 · 17 (Claude Agent SDK) — subagents
- Phase 14 · 19-20 (Benchmarks) — evaluation methodology
- Phase 14 · 23-24 (Observability) — telemetry
- Phase 14 · 27-28 (Safety + UX) — guardrails and defensive UX
- Phase 14 · 39 (Red Teaming) — adversarial testing
- Phase 14 · 40 (Caching) — prompt caching
