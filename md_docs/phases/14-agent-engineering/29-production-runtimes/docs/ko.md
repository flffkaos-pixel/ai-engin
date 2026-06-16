# 프로덕션 런타임: 큐, 이벤트, 크론

> 프로덕션 에이전트는 여섯 가지 런타임 형태로 실행됩니다: 요청-응답, 스트리밍, 지속적 실행(durable execution), 큐 기반 백그라운드, 이벤트 기반, 스케줄링. 프레임워크를 선택하기 전에 런타임 형태를 선택하세요. 모든 형태에서 관찰 가능성(observability)이 핵심입니다.

**Type:** Learn
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 13 (LangGraph), Phase 14 · 22 (Voice)
**Time:** ~60분

## 학습 목표

- 여섯 가지 프로덕션 런타임 형태를 명명하고 각각을 프레임워크 / 제품 패턴에 매칭합니다.
- 장기 작업에 지속적 실행(LangGraph)이 중요한 이유를 설명합니다.
- 이벤트 기반 런타임과 Claude Managed Agents가 적합한 경우를 설명합니다.
- 다중 단계 에이전트에 대한 관찰 가능성의 핵심 역할을 설명합니다.

## 문제

프로덕션 에이전트는 Jupyter 노트북이 드러내지 않는 방식으로 실패합니다: 37단계에서 네트워크 타임아웃, 음성 통화 중간에 사용자 연결 종료, 머신 재부팅으로 크론 작업 중단, 백그라운드 워커 메모리 부족. 런타임 형태가 어떤 실패가 생존 가능한지를 결정합니다.

## 개념

### 요청-응답

- 동기 HTTP. 사용자가 완료를 기다림.
- 짧은 작업(<30초)에만 실행 가능.
- 스택: Agno (Python + FastAPI), Mastra (TypeScript + Express/Hono/Fastify/Koa).
- 관찰 가능성: 표준 HTTP 액세스 로그 + OTel 스팬.

### 스트리밍

- SSE 또는 WebSocket을 통한 점진적 출력.
- LiveKit이 WebRTC를 통해 음성/비디오로 확장 (Lesson 22).
- 스택: 스트리밍 지원 프레임워크 + SSE/WS를 처리하는 프론트엔드.
- 관찰 가능성: 청크별 타이밍, 첫 토큰 지연 시간, 꼬리 지연 시간.

### 지속적 실행 (Durable execution)

- 모든 단계 후 상태 체크포인트; 실패 시 자동 재개.
- AutoGen v0.4 액터 모델이 하나의 에이전트로 실패 격리 (Lesson 14).
- LangGraph의 핵심 차별점 (Lesson 13).
- 단계 수를 모르고 복구 비용이 높을 때 필수적.

### 큐 기반 / 백그라운드

- 작업이 큐에 들어가고, 워커가 처리하며, 결과는 웹훅 또는 pub/sub을 통해 반환.
- 장기 에이전트에 필수 (Anthropic의 computer use 발표에 따르면 작업당 수십에서 수백 단계).
- 스택: Celery (Python), BullMQ (Node), SQS + Lambda (AWS), 커스텀.
- 관찰 가능성: 큐 깊이, 작업별 지연 시간 분포, DLQ 크기.

### 이벤트 기반

- 에이전트가 트리거에 구독: 새 이메일, PR 오픈, 크론 실행.
- Claude Managed Agents가 기본 지원 (Lesson 17).
- CrewAI Flows (Lesson 15)가 이벤트 기반 결정론적 워크플로우 구성.
- 관찰 가능성: 트리거 소스, 이벤트-시작 지연 시간, 에이전트 지연 시간.

### 스케줄링 (Scheduled)

- 주기적으로 실행되는 크론 형태 에이전트.
- 지속적 실행과 결합하여 실패하는 야간 실행이 다음 틱에서 재개되도록 함.
- 스택: Kubernetes CronJob + 지속적 프레임워크; 호스팅 (Render cron, Vercel cron).

### 2026년 배포 패턴

- **CrewAI Flows** — 이벤트 기반 프로덕션용.
- **Agno** 무상태 FastAPI — Python 마이크로서비스용.
- **Mastra** 서버 어댑터 (Express, Hono, Fastify, Koa) — 임베딩용.
- **Pipecat Cloud / LiveKit Cloud** — 관리형 음성 (Lesson 22).
- **Claude Managed Agents** — 호스팅 장기 실행 비동기 작업용.

### 관찰 가능성은 핵심

OpenTelemetry GenAI 스팬 (Lesson 23)과 Langfuse/Phoenix/Opik 백엔드 (Lesson 24) 없이는 40단계에서 실패한 다중 단계 에이전트를 디버깅할 수 없습니다. 이는 프로덕션에서 선택 사항이 아닙니다. "빠르게 디버깅"과 "더 많은 로깅으로 처음부터 재실행"의 차이입니다.

### 프로덕션 런타임이 실패하는 경우

- **잘못된 형태 선택.** 5분 작업에 요청-응답 선택. 사용자가 연결 종료; 워커가 쌓임; 재시도가 복합됨.
- **DLQ 없음.** 데드 레터 없는 큐 워커. 실패한 작업이 사라짐.
- **불투명한 백그라운드 작업.** 트레이스 내보내기 없이 실행되는 백그라운드 에이전트. 사용자가 보고할 때까지 실패가 보이지 않음.
- **지속적 상태 생략.** 재시작을 감당할 수 없는 30초 이상 실행에는 지속적 실행이 필요.

## 빌드하기

`code/main.py`는 stdlib 다중 형태 데모입니다:

- 요청-응답 엔드포인트 (일반 함수).
- 스트리밍 핸들러 (제너레이터).
- DLQ가 있는 큐 기반 워커.
- 이벤트 트리거 레지스트리.
- 크론 형태 스케줄러.

실행:

```bash
python3 code/main.py
```

출력: 동일한 작업에 대한 각 형태의 동작을 보여주는 5개의 트레이스. 동일한 에이전트 로직, 다른 외부 셸. 지속적 실행(여섯 번째 형태)은 의도적으로 Lesson 13의 LangGraph 체크포인팅에서 다룹니다.

## 사용하기

- **요청-응답** — 채팅 스타일 UX용.
- **스트리밍** — 점진적 응답용.
- **지속적 실행** — 장기 작업용.
- **큐** — 배치 / 비동기 / 장기 실행용.
- **이벤트** — 에이전트 반응성용.
- **크론** — 하우스키핑용 (메모리 통합, 평가, 비용 보고서).

## 배포하기

`outputs/skill-runtime-shape.md`는 작업에 대한 런타임 형태를 선택하고 관찰 가능성 요구사항을 연결합니다.

## 연습 문제

1. Lesson 01 ReAct 루프를 스택의 여섯 가지 형태로 모두 포팅. 어떤 형태가 어떤 제품 표면에 적합한가?
2. 큐 기반 데모에 DLQ 추가. 10% 작업 실패 시뮬레이션; DLQ 크기 표시.
3. 크론 트리거 평가 에이전트 작성 — 그날의 상위 20개 트레이스에 대해 야간 실행.
4. 역압력이 있는 스트리밍 구현: 클라이언트가 느리면 에이전트 일시 중지. 턴 버짓과 어떻게 상호작용하는가?
5. Claude Managed Agents 문서 읽기. 자체 호스팅 장기 에이전트를 언제 관리형으로 전환하겠는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|------------------|-----------|
| Request-response | "동기" | 사용자가 대기; 짧은 작업만 |
| Streaming | "SSE / WS" | 점진적 출력; 더 나은 UX; 청크별 지연 시간 관찰 가능 |
| Durable execution | "실패에서 재개" | 체크포인트된 상태; 마지막 단계에서 재시작 |
| Queue-based | "백그라운드 작업" | 생산자 / 워커 풀 / DLQ |
| Event-driven | "트리거 기반" | 에이전트가 외부 이벤트에 반응 |
| DLQ | "데드 레터 큐" | 실패한 작업의 주차장 |
| Claude Managed Agents | "호스팅 하네스" | 캐싱 + 컴팩션이 있는 Anthropic 호스팅 장기 실행 비동기 |

## 추가 자료

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — 지속적 실행 상세
- [Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) — 호스팅 장기 실행 비동기
- [Anthropic, Introducing computer use](https://www.anthropic.com/news/3-5-models-and-computer-use) — "작업당 수십에서 수백 단계"
- [AutoGen v0.4 (Microsoft Research)](https://www.microsoft.com/en-us/research/articles/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/) — 액터-모델 장애 격리
