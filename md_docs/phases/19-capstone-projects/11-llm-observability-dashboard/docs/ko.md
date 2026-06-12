# 캡스톤 11 — LLM 관찰 가능성 및 평가 대시보드

> Langfuse가 오픈 코어로 전환했다. Arize Phoenix가 2026 GenAI semconv 매핑을 게시했다. Helicone과 Braintrust 모두 사용자당 비용 귀속에 집중했다. Traceloop의 OpenLLMetry가 사실상의 SDK 계측이 되었다. 운영 형태는 traces용 ClickHouse, 메타데이터용 Postgres, UI용 Next.js, 샘플링된 traces에서 실행되는 다수의 평가 작업(DeepEval, RAGAS, LLM-judge)이다. 셀프 호스트를 구축하고 최소 4개의 SDK 제품군에서 수집하며 주입된 regression을 5분 이내에 포착하는 것을演示한다.

**유형:** 캡스톤
**언어:** TypeScript (UI), Python / TypeScript (수집 + 평가), SQL (ClickHouse)
**선수 과목:** Phase 11 (LLM 엔지니어링), Phase 13 (도구), Phase 17 (인프라), Phase 18 (안전)
**활용 phases:** P11 · P13 · P17 · P18
**소요 시간:** 25시간

## 문제

2026년 운영 트래픽을 실행하는 모든 AI 팀은 모델과 함께 관찰 가능성 평면을 유지한다. 비용 귀속. 환각 감지. 드리프트 모니터링. 탈옥 신호. SLO 대시보드. PII 유출 경고. 오픈소스 참조 — Langfuse, Phoenix, OpenLLMetry —는 수집 스키마로 OpenTelemetry GenAI 의미 규칙으로 수렴했다. 이제 하나의 SDK로 OpenAI, Anthropic, Google, LangChain, LlamaIndex, vLLM을 계측하고 호환 가능한 스팬을 shipped할 수 있다.

최소 4개의 SDK 제품군에서 수집하고, 샘플링된 traces에서 작은 평가 작업 세트를 실행하며, 드리프트를 감지하고 경고하는 셀프 호스트 대시보드를 구축한다. 측정 기준: 의도적으로 주입된 regression(PII를 생산하기 시작하는 프롬프트)이 주어지면 대시보드가 이를 포착하고 5분 이내에 경고를fire한다.

## 개념

수집은 OTLP HTTP이다. SDK는 GenAI-semconv 스팬을 생성한다: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.response.id`, `llm.prompts`, `llm.completions`. 스팬은 컬럼너 분석을 위해 ClickHouse에 도착한다; 메타데이터(사용자, 세션, 앱)는 Postgres에 도착한다.

평가는 샘플링된 traces에서 배치 작업으로 실행된다. DeepEval이 충실도, 독성, 답변 관련성을 채점한다. RAGAS가 추적에 검색 컨텍스트가 있을 때 검색 메트릭을 채점한다. 커스텀 LLM-judge가 도메인별 검사(PII 유출, 정책 외부 응답)를 실행한다. 평가는 부모 추적에 연결된 eval 스팬으로 다시 같은 ClickHouse에 쓴다.

드리프트 감지는 시간에 따른 임베딩 공간 분포(프롬프트 임베딩에서 PSI 또는 KL divergence)와 평가 점수 추세를監視한다. 경고는 Prometheus Alertmanager로 feeding된 다음 Slack / PagerDuty로 전달된다. UI는 Recharts가 있는 Next.js 15이다.

## 아키텍처

```
production apps:
  OpenAI SDK  +  Anthropic SDK  +  Google GenAI SDK
  LangChain + LlamaIndex + vLLM
       |
       v
  OpenTelemetry SDK with GenAI semconv
       |
       v  OTLP HTTP
  collector (ingest, sample, fan-out)
       |
       +-------------+-----------+
       v             v           v
   ClickHouse    Postgres    S3 archive
   (spans)       (metadata)  (raw events)
       |
       +---> eval jobs (DeepEval, RAGAS, LLM-judge)
       |     sampled or all-trace
       |     write eval spans back
       |
       +---> drift detector (PSI / KL on prompt embeddings)
       |
       +---> Prometheus metrics -> Alertmanager -> Slack / PagerDuty
       |
       v
   Next.js 15 dashboard (Recharts)
```

## 기술 스택

- 수집: OpenTelemetry SDK + GenAI 의미 규칙; OTLP HTTP 전송
- 수집기: tail-샘플링 프로세서(비용 관리를 위한)가 있는 OpenTelemetry Collector
- 스토리지: 스팬용 ClickHouse, 메타데이터용 Postgres, 원본 이벤트 아카이브용 S3
- Eval: DeepEval, RAGAS 0.2, Arize Phoenix evaluator 팩, 커스텀 LLM-judge
- 드리프트: 매주 pooled 프롬프트 임베딩에서 PSI / KL (sentence-transformers)
- 경고: Prometheus Alertmanager -> Slack / PagerDuty
- UI: Next.js 15 App Router + Recharts + 서버 액션
- 즉시 지원되는 SDK: OpenAI, Anthropic, Google GenAI, LangChain, LlamaIndex, vLLM

## 실습

1. **수집기 구성.** OTLP HTTP 수신기, 실패한 traces 100% 및 성공의 10%를 유지하는 tail-샘플러, ClickHouse 및 S3로의 내보내기가 있는 OpenTelemetry Collector.

2. **ClickHouse 스키마.** GenAI semconv를 반영하는 열이 있는 `spans` 테이블: `gen_ai_system`, `gen_ai_request_model`, `input_tokens`, `output_tokens`, `latency_ms`, `prompt_hash`, `trace_id`, `parent_span_id`, 긴 페이로드용 JSON 백. user_id 및 app_id로 보조 인덱스 추가.

3. **SDK 적용 범위 테스트.** 각 SDK(OpenAI, Anthropic, Google, LangChain, LlamaIndex, vLLM)를 사용하는 작은 클라이언트 앱을 OpenLLMetry 자동 계측으로 작성한다. 각 SDK가 ClickHouse에 도착하는 표준 GenAI 스팬을 생성하는지 확인한다.

4. **평가 작업.** 예약된 작업이 마지막 15분 샘플링된 traces를 읽고 DeepEval 충실도, 독성, 답변 관련성을 실행한다. 출력이 부모 추적에 연결된 eval 스팬이다.

5. **커스텀 LLM-judge.** PII 유출 심사위원: 응답이 주어지면 가드 LLM을 호출하여 PII 유출 가능성을 채점한다. 높은 점수의 응답은 트라이지 대기열에 도착한다.

6. **드리프트 감지.** 매주 작업이 이주의 pooled 프롬프트 임베딩과 뒤처지는 4주 기준선 간의 PSI를 계산한다. PSI가 임계값 이상이면 경고.

7. **대시보드.** 페이지가 있는 Next.js 15: 개요(spans/sec, cost/user, p95 지연), traces(검색 + 워터폴), 평가(충실도 추세, 독성), 드리프트(PSI 추이), 경고.

8. **경고 체인.** Prometheus 내보내기가 평가 점수 집계 및 지연 백분위수를 읽는다; Alertmanager가 경고에 대해 Slack으로, 중요한 위반에 대해 PagerDuty로 라우팅한다.

9. **회귀 프로브.** 버그 주입: 평가된 챗봇이 1%的时间内 가짜 SSN을 유출하기 시작한다. MTTR 측정: 버그 배포에서 Slack 경고까지.

## 활용

```
$ curl -X POST https://my-otel-collector/v1/traces -d @trace.json
[collector]  accepted 1 trace, 3 spans
[clickhouse] inserted 3 spans (app=chat, user=u_42)
[eval]       DeepEval faithfulness 0.82, toxicity 0.03
[drift]      weekly PSI 0.08 (below 0.2 threshold)
[ui]         live at https://obs.example.com
```

## 결과물

`outputs/skill-llm-observability.md`가 결과물이다. LLM 애플리케이션이 주어지면 대시보드가 traces를 수집하고, 평가를 실행하고, 드리프트에 경고하고, Next.js에서 사용자당 비용 분류를 제공한다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 추적 스키마 적용 범위 | 표준 GenAI 스팬을 생성하는 SDK 제품군 수(대상: 6+) |
| 20 | 평가 정확도 | 수동 레이블 세트 대비 DeepEval / RAGAS 점수 |
| 20 | 대시보드 UX | 주입된 regression에 대한 MTTR(5분 미만 목표) |
| 20 | 비용/규모 | 백로그 없이 1k spans/sec에서 지속 수집 |
| 15 | 경고 + 드리프트 감지 | Prometheus/Alertmanager 체인이 종단 간 연습됨 |
| **100** | | |

## 연습 문제

1. Haystack 프레임워크에 사용자 지정 계측을 추가한다. 표준 스팬이 충실한 `gen_ai.*` 속성으로 ClickHouse에 도착하는지 확인한다.

2. 동일한 traces에서 DeepEval을 Phoenix evaluators로 교체한다. 두 평가 엔진 간의 점수 드리프트를 측정한다.

3. 드리프트 감지 강화: 전역이 아닌 앱별로 PSI를 계산한다. 앱별 드리프트 트레일을 표시한다.

4. "사용자 영향" 페이지 추가:sparklines가 있는 사용자당 비용 및 사용자당 실패율.

5. 독성 > 0.5인 traces 100%와 나머지의 10% 계층화 샘플을 유지하는 tail-샘플링 정책을 구축한다. 도입된 샘플링 편향을 측정한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| GenAI semconv | "OTel LLM attributes" | 2025 OpenTelemetry LLM 스팬 属性 사양(system, model, tokens) |
| Tail 샘플링 | "Post-trace sample" | 수집기가 완료 후 추적을 유지하거나 삭제할지决定(오류를 볼 수 있음) |
| PSI | "Population stability index" | 두 분포를 비교하는 드리프트 메트릭; > 0.2는 일반적으로 의미 있는 드리프트를 나타냄 |
| LLM-judge | "Eval as model" | 루브릭에서 다른 LLM의 출력을 채점하는 LLM(충실도, 독성, PII) |
| Tail-샘플링 정책 | "Keep-rule" | 지속 vs 삭제할 traces를 결정하는 규칙; 오류 + 샘플 속도 |
| Eval 스팬 | "Linked eval trace" | 원본 LLM 호출 스팬에 연결된 평가 점수를携带하는 하위 스팬 |
| 사용자당 비용 | "Unit economics" | 기간 동안 user_id에 귀속되는 달러 비용; 주요 제품 메트릭 |

## 추가 자료

- [Langfuse](https://github.com/langfuse/langfuse) — 기준 오픈 코어 관찰 가능성 플랫폼
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) — 강한 드리프트 지원이 있는 대체 기준
- [OpenLLMetry (Traceloop)](https://github.com/traceloop/openllmetry) — 자동 계측 SDK 제품군
- [OpenTelemetry GenAI 의미 규칙](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 수집 스키마
- [Helicone](https://www.helicone.ai) — 대체 호스티드 관찰 가능성
- [Braintrust](https://www.braintrust.dev) — 대체 평가 우선 플랫폼
- [ClickHouse documentation](https://clickhouse.com/docs) — 컬럼너 스팬 저장소
- [DeepEval](https://github.com/confident-ai/deepeval) — 평가기 라이브러리