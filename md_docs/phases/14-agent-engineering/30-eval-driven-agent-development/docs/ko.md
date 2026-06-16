# 평가 주도 에이전트 개발

> Anthropic의 조언: "간단한 프롬프트로 시작하고, 포괄적인 평가로 최적화하며, 필요할 때만 다중 단계 에이전틱 시스템을 추가하세요." 평가는 마지막 단계가 아닙니다. Phase 14의 모든 다른 선택을 이끄는 외부 루프입니다.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 전체
**Time:** ~60분

## 학습 목표

- 세 가지 평가 계층(정적 벤치마크, 커스텀 오프라인, 온라인 프로덕션)과 각각의 목적을 명명합니다.
- 평가자-최적화자(evaluator-optimizer)의 긴밀한 루프를 설명합니다.
- 2026년 모범 사례를 설명합니다: 평가는 코드 옆에 있고, CI에서 실행되며, PR을 게이트합니다.
- 모든 Phase 14 레슨을 그것이 생성하는 평가 케이스에 연결합니다.

## 문제

에이전트는 데모를 통과합니다. 데모가 예측할 수 없는 방식으로 프로덕션에서 실패합니다. 벤치마크는 "이 모델이 광범위하게 유능한가?"에 답할 뿐, "이 에이전트가 내 제품에 올바른 패치를 제공하는가?"에는 답하지 않습니다. 해결책: 세 계층의 평가를 지속적으로 실행하고, 모든 가드레일과 학습된 규칙을 평가 케이스에 매핑합니다.

## 개념

### 세 가지 평가 계층

1. **정적 벤치마크** — 코드용 SWE-bench Verified (Lesson 19), 브라우징/데스크탑용 WebArena/OSWorld (Lesson 20), 제너럴리스트용 GAIA (Lesson 19), 도구 사용용 BFCL V4 (Lesson 06). 교차 모델 비교 및 회귀 게이팅에 사용. 오염은 실제 문제: SWE-bench+에서 32.67% 솔루션 누출 발견. 항상 Verified / +-audited 점수 보고.

2. **커스텀 오프라인 평가** — 제품의 형태:
   - LLM-as-judge (Langfuse, Phoenix, Opik — Lesson 24).
   - 실행 기반 (패치 실행, 테스트 확인).
   - 궤적 기반 (골드와 작업 시퀀스 비교; OSWorld-Human은 최고 에이전트가 골드 대비 1.4-2.7배).

3. **온라인 평가** — 프로덕션:
   - 세션 재생 (Langfuse).
   - 가드레일 트리거 알림 (Lesson 16, 21).
   - 단계별 비용 / 지연 시간 추적 (Lesson 23 OTel 스팬).

### 평가자-최적화자 (Anthropic)

긴밀한 루프:

1. 제안자가 출력 생성.
2. 평가자가 판단.
3. 평가자가 통과할 때까지 개선.

이는 일반화된 Self-Refine (Lesson 05)입니다. 관심 있는 모든 에이전트 흐름은 신뢰성을 위해 evaluator-optimizer로 감쌀 수 있습니다.

### 2026년 모범 사례

- 평가는 코드 옆에 위치.
- 모든 PR에서 CI 실행.
- 평가 점수로 병합 게이트 (예: "main 대비 5% 이상 회귀 없음").
- 모든 가드레일이 평가 케이스에 매핑.
- 모든 학습된 규칙 (Reflexion, pro-workflow learn-rule)이 실패 케이스에 매핑.

### Phase 14 통합

Phase 14의 모든 레슨이 평가 케이스를 생성합니다:

| 레슨 | 생성하는 평가 케이스 |
|------|-------------------|
| 01 Agent Loop | 예산 소진, 무한 루프 가드 |
| 02 ReWOO | 도구 실패 시 플래너가 올바르게 재계획 |
| 03 Reflexion | 재시도 시 학습된 반영 적용 |
| 05 Self-Refine/CRITIC | 판사가 개선된 출력 통과 |
| 06 Tool Use | 인수 강제 변환 작동; 알 수 없는 도구 거부 |
| 07-10 Memory | 검색 인용이 소스와 일치; 오래된 사실 무효화 |
| 12 Workflow Patterns | 각 패턴이 올바른 출력 생성 |
| 13 LangGraph | 재개가 상태를 정확히 복원 |
| 14 AutoGen Actors | DLQ가 충돌한 핸들러 포착 |
| 16 OpenAI Agents SDK | 가드레일이 올바른 입력에서 작동 |
| 17 Claude Agent SDK | 하위 에이전트 결과가 오케스트레이터로 반환 |
| 19-20 Benchmarks | SWE-bench Verified 점수, WebArena 성공률, OSWorld 효율성 |
| 21 Computer Use | 단계별 안전이 주입된 DOM 포착 |
| 23 OTel | 스팬이 필수 속성 생성 |
| 26 Failure Modes | 탐지기가 알려진 실패 태깅 |
| 27 Prompt Injection | PVE가 중독된 검색 거부 |
| 28 Orchestration | Supervisor가 올바른 전문가에게 라우팅 |
| 29 Runtime Shapes | DLQ가 N% 실패 처리 |

각각에 대한 평가 케이스가 있다면 Phase 14를 모두 다룬 것입니다.

### 평가 주도 개발이 실패하는 경우

- **기준선 없음.** 마지막으로 알려진 정상 상태가 없는 평가는 읽을 수 없음. 기준선 저장.
- **근거 없는 LLM 판사.** 판사도 환각함. CRITIC 패턴 (Lesson 05) — 판사가 외부 도구에 근거.
- **평가에 과적합.** 평가에 최적화하면 프로덕션 유용성과 괴리. 케이스 순환.
- **불안정한 평가.** 비결정론적 케이스가 오경보 유발. 시드 고정, 상태 스냅샷.

## 빌드하기

`code/main.py`는 stdlib 평가 하네스입니다:

- 범주(벤치마크, 커스텀, 온라인)가 있는 케이스 레지스트리.
- 테스트 중인 스크립트형 에이전트.
- Evaluator-optimizer 루프: 제안, 판단, 통과 또는 최대 라운드까지 개선.
- CI 게이트: 기준선 대비 전체 통과율 + 회귀.

실행:

```
python3 code/main.py
```

출력: 케이스별 통과/실패, 회귀 플래그, CI 게이트 판정.

## 사용하기

- 에이전트 코드와 동일한 저장소에 평가 케이스 작성.
- CI를 통해 모든 PR에서 실행.
- 회귀 시 빌드 실패.
- 시간 경과에 따른 통과율 추적.
- 모든 프로덕션 실패를 새 케이스에 연결.

## 배포하기

`outputs/skill-eval-suite.md`는 CI 게이트와 회귀 추적 기능이 있는 에이전트 제품용 3계층 평가 스위트를 구축합니다.

## 연습 문제

1. 프로덕션 실패 중 하나를 선택. 이를 재현하는 평가 케이스 작성. 에이전트가 지금 통과하는가?
2. 도메인에 대한 3차원(사실성, 어조, 범위) LLM-as-judge 루브릭 구축. 50개 세션 점수화.
3. 평가 스위트를 CI에 연결. 5% 이상 회귀 시 빌드 실패.
4. 궤적 효율성 메트릭 추가: 에이전트가 골드 궤적 대비 몇 단계를 거쳤는가?
5. 모든 Phase 14 레슨을 스위트의 평가 케이스에 매핑. 누락된 것이 있다면? 그것은 메꿔야 할 격차.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|------------------|-----------|
| Static benchmark | "기성 평가" | SWE-bench, GAIA, AgentBench, WebArena, OSWorld |
| Custom offline eval | "도메인 평가" | 제품 형태에 대한 LLM-as-judge / 실행 / 궤적 |
| Online eval | "프로덕션 평가" | 세션 재생, 가드레일 알림, 비용/지연 시간 추적 |
| Evaluator-optimizer | "제안-판단-개선" | 판사가 통과할 때까지 반복 |
| CI gate | "병합 차단기" | 평가 회귀 시 빌드 실패 |
| Baseline | "마지막으로 알려진 정상" | 회귀 탐지를 위한 참조 점수 |
| Trajectory efficiency | "골드 대비 단계" | 에이전트 단계 수를 인간 전문가 최소값으로 나눈 값 |

## 추가 자료

- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — "간단하게 시작, 평가로 최적화"
- [OpenAI, SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) — 큐레이티드 벤치마크
- [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) — 도구 사용 벤치마크
- [Langfuse docs](https://langfuse.com/) — 실제 평가 + 세션 재생
