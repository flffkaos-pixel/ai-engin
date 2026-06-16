# Agno와 Mastra: 프로덕션 런타임

> Agno (Python)와 Mastra (TypeScript)는 2026년 프로덕션 런타임 페어링이다. Agno는 마이크로초 에이전트 인스턴스화와 상태 없는 FastAPI 백엔드를 목표로 한다. Mastra는 Vercel AI SDK 기반 위에 에이전트, 도구, 워크플로우, 통합 모델 라우팅 및 복합 저장소를 제공한다.

**Type:** Learn
**Languages:** Python, TypeScript
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 13 (LangGraph)
**Time:** ~45분

## 학습 목표

- Agno의 성능 목표와 그것이 중요한 때를 식별한다.
- Mastra의 세 가지 기본 요소(Agents, Tools, Workflows)와 지원되는 서버 어댑터를 명명한다.
- 상태 없는 세션 범위 FastAPI 백엔드가 권장되는 Agno 프로덕션 경로인 이유를 설명한다.
- 주어진 스택(Python-first vs TypeScript-first)에 대해 Agno와 Mastra 중에서 선택한다.

## 문제

LangGraph, AutoGen, CrewAI는 프레임워크 중심이다. "그냥 에이전트 루프, 빠르게, 내 런타임에서"를 원하는 팀은 Agno(Python) 또는 Mastra(TypeScript)를 사용한다. 둘 다 프레임워크 소유 기본 요소 중 일부를 원시 속도와 주변 스택에 대한 더 긴밀한 적합성과 교환한다.

## 개념

### Agno

- Python 런타임, 전신 Phi-data.
- "그래프, 체인 또는 복잡한 패턴 없음 — 순수 Python만."
- 문서의 성능 목표: ~2μs 에이전트 인스턴스화, 에이전트당 ~3.75 KiB 메모리, ~23개 모델 프로바이더.
- 프로덕션 경로: 상태 없는 세션 범위 FastAPI 백엔드. 각 요청은 새 에이전트를 시작; 세션 상태는 DB에 저장.
- 네이티브 멀티모달 (텍스트, 이미지, 오디오, 비디오, 파일) 및 agentic RAG.

속도 목표는 초당 수천 개의 단기 에이전트(채팅 팬인, 평가 파이프라인)가 있을 때 중요. 하나의 에이전트가 10분 동안 실행될 때는 덜 중요.

### Mastra

- TypeScript, Vercel AI SDK 기반.
- 세 가지 기본 요소: **Agents**, **Tools** (Zod-typed), **Workflows**.
- 통합 모델 라우터 — 94개 프로바이더의 3,300+ 모델 (2026년 3월).
- 복합 저장소: 메모리, 워크플로우, 관찰 가능성을 각각 다른 백엔드로; 대규모 관찰 가능성에는 ClickHouse 권장.
- Apache 2.0, `ee/` 디렉토리는 소스 사용 가능 엔터프라이즈 라이선스.
- Express, Hono, Fastify, Koa용 서버 어댑터; 일급 Next.js 및 Astro 통합.
- Mastra Studio (localhost:4111) for debugging.
- 22k+ GitHub stars, 300k+ weekly npm downloads at 1.0 (Jan 2026).

### 포지셔닝

둘 다 LangGraph가 되려고 하지 않는다. 다음에서 경쟁:

- **언어 적합성.** Python-first 팀용 Agno; TypeScript-first 팀용 Mastra.
- **런타임 인체공학.** Agno = 거의 제로 오버헤드; Mastra = Vercel 생태계와 통합.
- **관찰 가능성.** 둘 다 Langfuse/Phoenix/Opik과 통합 (레슨 24)하지만 Mastra Studio는 자사 기능.

### 각각을 선택할 때

- **Agno** — Python 백엔드, 많은 단기 에이전트, 강력한 성능 요구사항, FastAPI 샵.
- **Mastra** — TypeScript 백엔드, Next.js / Vercel 배포, 통합 멀티 프로바이더 모델 라우팅, Zod-typed 도구.
- **LangGraph** (레슨 13) — 내구성 있는 상태와 명시적 그래프 추론이 원시 속도보다 더 중요할 때.
- **OpenAI / Claude Agent SDK** — 프로바이더의 제품화된 형태를 원할 때 (레슨 16-17).

### 이 패턴이 잘못되는 경우

- **성능을 위한 성능.** 워크로드가 요청당 하나의 느린 에이전트 호출일 때 "2μs"가 좋게 들려서 Agno 선택. 오버헤드가 병목이 아님.
- **생태계 종속.** Mastra의 Vercel 풍미 통합은 Vercel에서는 장점, 다른 곳에서는 단점.
- **엔터프라이즈 라이선스 혼동.** Mastra의 `ee/` 디렉토리는 소스 사용 가능이며 Apache 2.0이 아님. 포크할 계획이라면 라이선스를 읽어라.

## 직접 구현하기

이 레슨은 주로 비교 중심 — 단일 코드 아티팩트로 두 프레임워크를 모두 다루기는 어려움. `code/main.py`는 나란히 장난감을 참조: "에이전트 실행, 출력 스트리밍, 세션 지속" 흐름을 두 번 구현 (한 번은 Agno 형태, 한 번은 Mastra 형태).

실행:

```
python3 code/main.py
```

구조적으로는 다르지만 기능적으로 동등한 두 트레이스.

## 활용하기

- **Agno** — Python 백엔드, 속도와 FastAPI 형태 필요.
- **Mastra** — TypeScript 백엔드, 많은 프로바이더와 워크플로우 기본 요소.
- 둘 다 자사 관찰 가능성 훅 제공. 둘 다 Langfuse와 통합.

## 배포하기

`outputs/skill-runtime-picker.md` picks Agno, Mastra, LangGraph, or a provider SDK based on stack, latency budget, and operational shape.

## 연습 문제

1. Agno 문서 읽기. stdlib ReAct 루프 (레슨 01)를 Agno로 포팅. 무엇이 사라졌는가? 무엇이 남았는가?
2. Mastra 문서 읽기. 동일한 루프를 Mastra로 포팅. 도구 타이핑에서 무엇이 바뀌었는가 (Zod vs nothing)?
3. 벤치마크: 스택에서 에이전트 인스턴스화 지연 시간 측정. Agno의 2μs가 워크로드에 중요한가?
4. 마이그레이션 설계: Python에서 CrewAI를 실행 중이라면 Agno로 이동할 때 무엇이 깨지는가?
5. Mastra의 `ee/` 라이선스 조건 읽기. 어떤 제한이 오픈소스 포크에 영향을 미치는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Agno | "빠른 Python 에이전트" | 상태 없는 세션 범위 에이전트 런타임 |
| Mastra | "Vercel AI SDK의 TypeScript 에이전트" | Agents + Tools + Workflows + Model Router |
| Unified Model Router | "멀티 프로바이더 액세스" | 94개 프로바이더의 3,300+ 모델을 위한 단일 클라이언트 |
| Composite storage | "다중 백엔드" | 메모리/워크플로우/관찰 가능성을 각각 다른 저장소로 |
| Mastra Studio | "로컬 디버거" | localhost:4111 UI for introspecting agents |
| Source-available | "OSS 아님" | 라이선스가 소스 읽기는 허용하지만 상업적 사용 제한 |

## 추가 자료

- [Agno Agent Framework docs](https://www.agno.com/agent-framework) — performance targets, FastAPI integration
- [Mastra docs](https://mastra.ai/docs) — primitives, server adapters, Model Router
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — the stateful-graph alternative
- [Comet Opik](https://www.comet.com/site/products/opik/) — observability comparisons cited by Mastra integrations
