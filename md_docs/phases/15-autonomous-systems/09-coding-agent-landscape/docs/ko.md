# 자율 코딩 에이전트 현황 (2026)

> SWE-bench Verified가 3년도 안 되어 4%에서 80.9%로 상승했다. 동일한 Claude Sonnet 4.5가 SWE-agent v1에서 43.2%, Cline 자율에서 59.8%를 기록했다 — 모델을 둘러싼 스캐폴딩이 이제 모델 자체만큼 중요하다. OpenHands(이전 OpenDevin)는 가장 활동적인 MIT 라이선스 플랫폼이며, 그 CodeAct 루프는 JSON 도구 호출 대신 샌드박스에서 직접 Python 작업을 실행한다. 헤드라인 수치는 방법론적 문제를 숨긴다: 500개 SWE-bench Verified 작업 중 161개는 1-2줄 변경만 필요하며, SWE-bench Pro(10줄 이상 작업)는 동일한 프론티어 모델에 대해 23-59%에 머물러 있다.

**Type:** 학습
**Languages:** Python (stdlib, CodeAct vs JSON tool-call comparison)
**Prerequisites:** Phase 14 · 07 (도구 사용), Phase 15 · 01 (장기 실행 에이전트)
**Time:** ~45분

## 문제

"어떤 코딩 에이전트가 최고인가"는 잘못된 질문이다. 올바른 질문은: 내 작업과 일치하는 작업 분포에서, 프로덕션에서 실행할 스캐폴딩으로, 어떤 종단간 신뢰도를 얻는가?

2022년과 2026년 사이에 현장은 스캐폴딩(검색 계층, 플래너, 샌드박스, 편집-확인 루프, 피드백 형식)이 하중을 지탱한다는 것을 배웠다. Claude Sonnet 4.5가 SWE-agent v1에서 43.2%를 기록했다; 동일한 모델이 Cline의 자율 스캐폴드 내에서 59.8%를 기록했다. 16.6%포인트 차이, 동일한 가중치. 기본 모델은 구성 요소이고, 루프가 제품이다.

동반 문제는 벤치마크 포화가 회귀를 숨긴다는 것이다. SWE-bench Verified는 포화에 가깝고, 쉬운 작업 꼬리(500개 작업 중 161개가 ≤2줄 필요)가 최고 점수를 끌어올린다. 실제 품질은 SWE-bench Pro(10줄 이상 변경)와 같은 분포에서 더 잘 측정되며, 동일한 선두주자가 여전히 23-59%에 머물러 있다.

## 개념

### SWE-bench, 한 문단

SWE-bench(Jimenez et al.)는 실제 GitHub 이슈와 실제 패치를 가져와 에이전트가 테스트 스위트를 통과하는 패치를 생성하도록 요청한다. SWE-bench Verified(OpenAI, 2024)는 모호하고 깨진 작업이 제거된 인간이 선별한 500개 작업 하위 집합이다. SWE-bench Pro는 더 어려운 후속 작업이다 — 10줄 이상의 변경이 필요한 작업으로, 현재 프론티어 에이전트가 23-59%에 머물러 있다.

### 2022년 → 2026년 곡선이 실제로 보여주는 것

- **2022년**: 연구 모델이 원시 SWE-bench에서 ~4%.
- **2024년**: GPT-4 + Devin 스타일 스캐폴딩이 ~14%; SWE-agent가 ~12%.
- **2025년**: Aider와 SWE-agent 내부의 Claude 3.5/3.7 Sonnet이 40-55% 범위로 진입.
- **2026년**: Claude Sonnet 4.5 및 경쟁사가 SWE-bench Verified에서 70-80%+. Epoch AI의 리더보드가 이를 실시간 추적한다.

기울기는 세 가지 복합 소스에서 비롯되었다: 더 나은 기본 모델, 더 나은 스캐폴딩(CodeAct, 반성, 검증기 루프), 더 나은 벤치마크(Verified가 노이즈 제거).

### CodeAct vs JSON 도구 호출

OpenHands(All-Hands-AI, arXiv:2407.16741, 이전 OpenDevin)는 특정 아키텍처 선택을 했다: 모델이 호스트가 디코딩하고 실행하는 JSON 도구 호출을 출력하는 대신, 모델이 Python 코드를 출력하고 Jupyter 스타일 커널이 샌드박스에서 실행한다. 에이전트는 파일을 반복하고, 도구를 체이닝하며, 하나의 작업 내에서 자체 예외를 잡을 수 있다.

트레이드오프:

- **JSON 도구 호출**: 모든 작업은 하나의 턴; 감사하기 쉬움; 제한된 구성성; 각 호출이 명시적 검증기를 통과하므로 기본적으로 안전.
- **CodeAct**: 하나의 작업이 전체 프로그램이 될 수 있음; 구성 가능; 강화된 샌드박스 필요(OpenHands는 Docker 격리 사용); 실패 모드는 샌드박스 런타임이 허용하는 모든 것을 포함.

두 아키텍처 모두 프로덕션에 있다. CodeAct는 오픈 플랫폼(OpenHands, smolagents)에서 지배적이다. JSON 도구 호출은 제공자가 실행자를 제어하는 관리형 서비스(Anthropic Managed Agents, OpenAI Assistants)에서 지배적이다.

### 2026년 현황의 스캐폴드

| 스캐폴드 | 라이선스 | 실행 모델 | 주목할 속성 |
|---|---|---|---|
| OpenHands (OpenDevin) | MIT | Docker의 CodeAct | 가장 활동적인 오픈 플랫폼; 이벤트 스트림 재생 가능 |
| SWE-agent | MIT | 에이전트-컴퓨터 인터페이스 (ACI) | 최초 종단간 SWE-bench 스캐폴드 |
| Aider | Apache-2 | 로컬 저장소에서 diff 통한 편집 | 최소 스캐폴드, 강력한 회귀 안정성 |
| Cline | Apache-2 | 도구 정책이 있는 VS Code 에이전트 | Sonnet 4.5에서 가장 높은 점수의 오픈 스캐폴드 |
| Devin (Cognition) | 독점 | 관리형 VM + 플래너 | 첫 "AI 소프트웨어 엔지니어" 제품 카테고리 |
| Claude Code | 독점 | 권한 모드 + 루틴 | 레슨 10이 에이전트 루프를 상세히 다룸 |

### 스캐폴딩이 지배하는 이유

코딩 실행은 장기 실행 궤적이다(레슨 1). 신뢰도는 단계를 거쳐 복합된다. 스캐폴딩이 점수를 얻는 세 곳:

1. **검색**: 올바른 파일을 찾는 것이 침묵하는 병목이다. SWE-agent의 ACI, OpenHands의 파일 인덱스, Aider의 저장소 맵이 모두 이를 공격한다.
2. **검증기 루프**: 테스트 실행, 스택 추적 읽기, 재시도는 SWE-bench에서 10+포인트 차이다.
3. **실패 격리**: 오류 시 롤백되는 샌드박스는 복합 손상을 방지한다. 검증기 루프가 있는 모델과 없는 모델은 두 가지 다른 제품처럼 보인다.

### 벤치마크 포화와 실제 분포

OpenHands 저자와 Epoch AI는 모두 SWE-bench Verified가 쉬운 꼬리를 가지고 있다고 지적한다: 500개 작업 중 161개가 1-2줄 변경만 필요하다. 높은 점수는 부분적으로 이 꼬리에 의해 주도된다. SWE-bench Pro는 10줄 이상 변경으로 제한하며 프론티어 시스템조차 23-59% 범위의 점수를 반환한다. 당신의 프로덕션 분포는 거의 확실히 Verified보다 Pro에 더 가깝다.

에이전트 선택에 대한 함의: 자신의 버그 백로그에서 Pro와 유사한 하위 집합을 실행하라. 중요한 점수는 당신이 출시하는 것을 대표하는 작업에 대한 점수다.

## 사용하기

`code/main.py`는 고정된 미니 작업 분포에서 두 장난감 에이전트 스캐폴드를 비교한다:

1. 턴당 하나의 작업을 수행하는 **JSON 도구 호출** 스캐폴드.
2. 작업당 작은 Python 스니펫을 출력할 수 있는 **CodeAct** 스캐폴드.

둘 다 스텁 "모델"(결정적 규칙)을 사용하여 비교가 모델 품질에서 스캐폴드를 분리한다. 출력은 CodeAct 스캐폴드가 더 적은 턴으로 더 많은 작업을 해결하지만 작업당 더 큰 폭발 반경의 비용이 든다는 것을 보여준다.

## 출시하기

`outputs/skill-scaffold-audit.md`는 채택 전에 제안된 코딩 에이전트 스캐폴드를 감사하는 데 도움을 준다: 검색 품질, 검증기 존재, 샌드박스 격리, 벤치마크-대-분포 적합.

## 연습문제

1. `code/main.py`를 실행하라. 각 스캐폴드가 동일한 작업 세트에 대해 몇 턴을 사용하는가? 각각의 작업당 폭발 반경은 무엇인가?

2. OpenHands 논문(arXiv:2407.16741)을 읽어라. 논문은 CodeAct가 복잡한 작업에서 JSON 도구 호출을 이긴다고 주장한다. 논문이 인정하는 하나의 실패 모드를 식별하고, 그 모드가 프로덕션에서 지배할 때를 한 문장으로 설명하라.

3. 버그 백로그에서 두 파일에 걸쳐 10줄 이상의 변경이 필요한 작업 하나를 골라라. (a) JSON 도구 호출 및 (b) CodeAct 하에서 프론티어 모델의 종단간 성공 확률을 추정하라. 격차를 정당화하라.

4. SWE-bench Verified에는 161개의 단일 파일, 1-2줄 작업이 있다. 이를 제외하는 점수를 구성하라. 리더보드가 어떻게 재구성되는가?

5. "Introducing SWE-bench Verified"(OpenAI)를 읽어라. 모호한 작업을 제거하는 데 사용된 특정 방법론을 설명하고, 선별이 놓칠 하나의 범주를 말하라.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|---|---|---|
| SWE-bench | "코딩 벤치마크" | 실제 패치와 테스트 스위트가 있는 실제 GitHub 이슈 |
| SWE-bench Verified | "정리된 하위 집합" | 500개 인간 선별 작업, 쉬운 꼬리 존재 |
| SWE-bench Pro | "더 어려운 하위 집합" | 10줄 이상 변경; 프론티어가 23-59%에 머뭄 |
| CodeAct | "코드-로서-작업" | 에이전트가 Python 출력; Jupyter 스타일 커널이 샌드박스에서 실행 |
| JSON 도구 호출 (JSON tool call) | "함수 호출" | 각 작업은 실행 전 검증된 구조화된 JSON 페이로드 |
| 스캐폴드 (Scaffold) | "에이전트 프레임워크" | 기본 모델 주변의 검색 + 플래너 + 실행기 + 검증기 루프 |
| ACI (Agent-Computer Interface) | "SWE-agent의 형식" | 인간 셸이 아닌 LLM 사용성을 위해 설계된 명령어 세트 |
| 검증기 루프 (Verifier loop) | "테스트-및-재시도" | 테스트 실행, 출력 읽기, 패치 수정; 가장 큰 비모델 신뢰도 이득 |

## 추가 읽을거리

- [Jimenez et al. — SWE-bench](https://www.swebench.com/) — 원본 벤치마크 및 방법론.
- [OpenAI — Introducing SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) — 선별된 하위 집합 구축 방법.
- [Wang et al. — OpenHands: An Open Platform for AI Software Developers](https://arxiv.org/abs/2407.16741) — CodeAct 아키텍처 및 이벤트 스트림 설계.
- [Epoch AI — SWE-bench leaderboard](https://epoch.ai/benchmarks) — 실시간 추적 점수.
- [Anthropic — Measuring agent autonomy](https://www.anthropic.com/research/measuring-agent-autonomy) — 장기 실행 코딩 에이전트 신뢰도 프레이밍.
