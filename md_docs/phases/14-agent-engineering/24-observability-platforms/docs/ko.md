# 관찰 가능성 플랫폼: Langfuse, Phoenix, Opik

> 관찰 가능성 플랫폼은 OTel GenAI 스팬을 사람이 읽을 수 있는 UI로 전환한다. 이것들은 비슷해 보이지만 — 트레이스, 평가기, LLM-as-judge, 프롬프트 버전 관리 — 각각 다른 형성 원리를 가지고 있다. Langfuse는 에이전트 운영을 중심으로 설계되었다. Phoenix는 실험 중심이다. Opik은 버전 관리 및 규정 준수에 중점을 둔다.

**Type:** Learn
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 23 (Observability OTel GenAI)
**Time:** ~45분

## 학습 목표

- Langfuse가 에이전트 추적, 평가기, 프롬프트 관리를 단일 제품으로 결합하는 이유를 설명한다.
- Phoenix의 폭포형 스팬 뷰와 노트북 UI가 무엇에 가장 적합한지 설명한다.
- Opik의 프롬프트 버전 관리, CVE 검사, 평가 대시보드를 Opik의 형성 원리와 연결한다.
- 특정 팀 구성(에이전트 운영 vs 연구 vs 규정 준수)에 대한 플랫폼 선택을 권장한다.

## 문제

플랫폼은 비슷해 보이지만 (트레이스, 평가기, 프롬프트 관리, LLM-as-judge), 약속과 생태계가 다르다. 플랫폼을 선택하는 것은 벤더 잠금을 선택하는 것이다. 프로젝트의 궤적에 맞게 선택하라.

## 개념

### Langfuse

- 형성 원리: **프로덕션 에이전트 운영.**
- 기능: 트레이스 추적, LLM-as-judge 평가기, 프롬프트 버전 관리, AI Python SDK.
- 자체 호스팅과 클라우드 모두.
- 에이전트 워크플로우(레슨 12)에 기본적으로 적용됨: 대시보드는 에이전트 단계를 추적하고, 평가기를 연결하고, 프롬프트 변경을 추적.
- 다른 기능(IM)보다 운영 우선 순위를 두므로 현장 데일리 탐정 작업에 적합.

### Phoenix (Arize)

- 형성 원리: **실험 및 발견.**
- 기능: OTel 네이티브 폭포형 스팬 뷰, LLM-as-judge 예제, 대시보드에 포함되지 않은 노트북 UI.
- 열기: Python 노트북, Databricks, SageMaker에서 실행; 벡터 검색 시각화.
- 운영보다 연구에 적합. 폭포형 뷰는 단일 추적에 집중; 에이전트 워크플로우 대시보드는 Langfuse가 우선 순위로 가지고 있지 않음.

### Opik (Comet)

- 형성 원리: **버전 관리 및 규정 준수.**
- 기능: LLM 평가, 프롬프트 버전 관리 (Comet Experiment Management와 유사한 Diff UI), 하이라인 CVEs, 게이트된 프롬프트 레지스트리.
- "프롬프트를 Git처럼 버전 관리하고, 알려진 취약점에 대해 검사" — 버전 관리 + 규정 준수에 유용.
- 무엇보다도 재현성과 감사 추적을 중요시하는 팀에 적합.

### 오버랩

세 가지 모두:

- **OTel GenAI** (2025 이후) — 모두 표준화된 LLM 스팬 이해.
- **LLM-as-judge** — 한 모델이 다른 모델의 출력을 평가할 때.
- **평가기** — LLM 호출에 점수를 매기는 스코어 카드.

### 유지보수

세 가지 모두 적극적으로 유지보수되며, GitHub에서 분기별 릴리스와 수천 개의 별표를 받고 있음. 세 가지 모두 안전합니다. 현재 에이전트 플랫폼 선택은 호환성이 아닌 기능 우선 순위에 따라 결정됨.

### 이 패턴이 잘못되는 경우

- **기능 우선 순위 오해.** Langfuse를 실험에 사용하면 Langfuse의 운영 중심 대시보드가 불편하게 느껴질 수 있음. 평가만 원한다면 Opik은 너무 무거울 수 있음.
- **확장 계획 없음.** 무료/허용 계층에서 시작했지만 나중에 자체 호스팅, 사용자 관리, 또는 규정 준수 보고 제어 필요. UI에서 확인.
- **OTel GenAI만으로 충분하다고 가정.** 원시 OTel은 스팬을 제공하지만 평가기, 프롬프트 버전 관리, 또는 LLM-as-judge는 제공하지 않음. 이러한 플랫폼은 운영 추상화를 추가함.

## 직접 구현하기

`code/main.py`는 세 가지 플랫폼 각각에 대해 스텁 연결 계층을 구현:

- OTel 내보내기용 `ObservabilityClient` (레슨 23의 스팬을 가져옴).
- 세 가지 싱크에 대한 커넥터.
- LLM-as-judge 평가기: "출력이 짧다" / "출력이 도구 호출을 포함한다" / "출력이 유해하다".
- 프롬프트 버전 Diff: 두 프롬프트를 비교하고 토큰 차이 표시.

실행:

```
python3 code/main.py
```

출력: 각 싱크에 대한 스팬 배치 (즉시 표시) + 평가기 점수 + Diff.

## 활용하기

- **Langfuse** for prod operations — agents, workflows, daily debugging.
- **Phoenix** for research — experiments, notebooks, ad-hoc evals.
- **Opik** for regulated teams — versioned prompts, CVE scanning, audit trails.
- **Datadog / Grafana** if your AIOps is already there — add LLM dashboards to your existing stack.

## 배포하기

`outputs/skill-platform-picker.md` picks a primary observability platform (and a backup) based on team structure.

## 연습 문제

1. 세 가지 플랫폼 각각의 OTel GenAI 구현 문서 읽기. 표면 아래에서 무엇이 다른가?
2. LLM-as-judge 평가기를 실제 배치로 포팅: 10개의 에이전트 실행에서 출력 점수 매기기. 점수는 어떻게 보이는가?
3. 프롬프트 버전 Diff 시스템 확장: 입력 예제가 포함된 프롬프트 템플릿 비교. "(이름)"과 "(사용자)"의 차이는 무엇인가?
4. 세 가지 플랫폼의 자체 호스팅 지침 읽기. 어떤 것이 인프라에 가장 적합한가?
5. 팀 구조 매핑: 어떤 팀 구성이 어떤 플랫폼에 적합한가? "프롬프트를 Git처럼 버전 관리"가 사례에 맞는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| LLM-as-judge | "모델이 모델 평가" | 평가자가 LLM에 점수를 요청함 |
| Trace | "요청 경로" | 사용자 입력에서 출력까지의 전체 에이전트 추적 |
| Span | "단계" | 단일 LLM 호출, 도구 호출, DB 쿼리 |
| Evaluator | "스코어 카드" | LLM 호출에 점수를 매기는 함수 |
| Prompt registry | "감사 프롬프트" | 게이트 및 기록이 있는 버전 관리된 프롬프트 저장소 |
| Waterfall view | "단계별 추적" | 각 스팬을 중첩된 행으로 보여주는 UI |

## 추가 자료

- [Langfuse docs](https://langfuse.com/docs) — traces, evals, prompt management
- [Arize Phoenix docs](https://docs.arize.com/phoenix) — notebook-first, OTel-native
- [Comet Opik](https://www.comet.com/site/products/opik/) — versioned prompts, CVE scanning
- [OTel GenAI conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — underlying standard all three implement
