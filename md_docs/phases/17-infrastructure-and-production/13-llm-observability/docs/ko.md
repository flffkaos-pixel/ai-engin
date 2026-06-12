# LLM 감시 가능성 스택 선택

> 2026년 감시 가능성 시장을 두 가지 범주로 나뉩니다. 개발 플랫폼 (LangSmith, Langfuse, Comet Opik)은 모니터링을 평가, 프롬프트 관리, 세션 리플레이와 번들합니다. 게이트웨이/계측 도구 (Helicone, SigNoz, OpenLLMetry, Phoenix)는 원격 측정에 집중합니다. Langfuse는 강력한 OSS 균형 (월 50K 이벤트 무료 클라우드)이 있는 MIT 라이선스 핵심입니다. Phoenix는 Elastic License 2.0에서 OpenTelemetry 네이티브입니다 — 드리프트/RAG 시각화에 훌륭합니다, 지속적인 프로덕션 백엔드가 아닙니다. Arize AX는 100배 저렴하다고 주장하는 제로카피 Iceberg/Parquet 통합을 사용합니다. LangSmith는 LangChain/LangGraph에 주도적이며, 사용자당 $39/월, 기업에서만 자체 호스팅. Helicone은 프록시 기반이며 15-30분 설정, 월 100K req 무료이지만 에이전트 추적에서 깊이가 적습니다. 일반적인 프로덕션 패턴: OpenTelemetry로 접착된 게이트웨이 (Helicone/Portkey) + 평가 플랫폼 (Phoenix/TruLens).

**유형:** 학습
**언어:** Python (stdlib, toy trace-sampling 시뮬레이터)
**선수 과목:** Phase 17 · 08 (Inference Metrics), Phase 14 (Agent Engineering)
**소요 시간:** ~60분

## 학습 목표

- 개발 플랫폼 (번들: 평가 + 프롬프트 + 세션)과 게이트웨이/원격 측정 도구 (추적 + 메트릭만)를 구분합니다.
- 6가지 주요 도구 (Langfuse, LangSmith, Phoenix, Arize AX, Helicone, Opik)를 라이선스, 가격, 스위트 스팟 사용 사례로 매핑합니다.
- 게이트웨이 도구를 별도 평가 플랫폼과 결합하는 OpenTelemetry 접착 패턴을 설명합니다.
- 2026년 비용 차별화 요소 (Arize AX의 제로카피 접근 방식 대 모놀리식 ingest)를 이름 짓고 약 100배 곱셈을 설명합니다.

## 문제

LLM 기능을 shipping했습니다. 작동합니다. 프롬프트 실패, 도구 루프, 지연 시간 회귀, 비용 급등, 프롬프트 캐시 적중율에 대한 가시성이 없습니다. "LLM 감시 가능성"을 Google하면 세 가지 다른 가격점에서 같은 문제를 해결한다고 주장하는 8개 도구가 나옵니다.

그들은 같은 문제를 해결하지 않습니다. LangSmith는 "이 LangGraph 실행이 실패한 이유"를 answered합니다. Phoenix는 "내 RAG 파이프라인이 드리프트하고 있습니까?"를 answered합니다. Helicone은 "어떤 앱이 토큰을 burning하고 있습니까?"를 answered합니다. Langfuse는 "전체 것을 자체 호스팅할 수 있습니까?"를 answered합니다. 다른 도구, 다른 청중.

선택에는 4개의 축이 포함됩니다: 스택 (LangChain?裸 SDK? 멀티 벤더?), 라이선스 허용 (MIT만? Elastic OK? 상업용 fine?), 예산 (무료 계층? $100/월? $1000/월?), 자체 호스팅 (필수? nice-to-have? 절대로?).

## 개념

### 두 가지 범주

**개발 플랫폼**은 관찰 가능성을 평가, 프롬프트 관리, 데이터셋 버전 관리, 세션 리플레이와 번들합니다. 실험을 실행하고 어떤 프롬프트가 작동했는지 보고, 새 프롬프트를 이전 승자들에 대한 데이터셋 회귀. LangSmith, Langfuse, Comet Opik.

**게이트웨이/원격 측정 도구**는 추론 호출을 계측합니다 — 프롬프트, 응답, 토큰, 지연 시간, 모델, 비용. Helicone, SigNoz, OpenLLMetry, Phoenix. 미니멀리스트. OpenTelemetry를 통해 별도의 평가 도구와 결합할 수 있습니다.

### Langfuse — OSS 균형

- 코어 Apache / MIT 라이선스; Docker를 통한 자체 호스팅.
- 클라우드 무료 계층: 월 50K 이벤트. 유료: 팀당 $29/월.
- 평가, 프롬프트 관리, 추적, 데이터셋. 4가지 개발 플랫폼 기능의 합리적 적용 범위.
- 스위트 스팟: LangSmith 클래스 기능이 필요하지만 자체 호스팅하거나 OSS 라이선스에 머물러야 하는 경우.

### Phoenix (Arize) — 원격 측정 우선, OpenTelemetry 네이티브

- Elastic License 2.0; 자체 호스팅 간단.
- RAG 및 드리프트 시각화에 뛰어납니다. 임베딩 공간 산점도가 일등 시민으로 제공됩니다.
- 지속적인 프로덕션 백엔드로 설계되지 않았습니다 — primarily 개발 시간 관찰 가능성.
- 스위트 스팟: RAG 파이프라인 개발, 드리프트 디버깅, 프로덕션용 별도의 게이트웨이와 페어링.

### Arize AX — 규모 플레이

- 상업용. Iceberg/Parquet를 통한 제로카피 데이터 레이크 통합.
- 규모에서 모놀리식 관찰 가능성 (Datadog 클래스)보다 ~100배 저렴하다고 주장합니다. 수학: 추적을 자체 Parquet on S3에 저장합니다; Arize가 직접 읽습니다.
- 스위트 스팟: 일 10M+ 추적, 기존 데이터 레이크, Datadog 가격 없이 LLM 특정 대시보드 원하는 경우.

### LangSmith — LangChain/LangGraph 우선

- 상업용, 사용자당 $39/월. 기업에서만 자체 호스팅.
- LangChain 및 LangGraph 스택에 최상위. 둘 다 사용하지 않으면 덜 설득력 있습니다.
- 스위트 스팟: LangChain에 헌신된 팀, 지불할 의지.

### Helicone — 프록시 기반 최소 기능

- `OPENAI_API_BASE`를 Helicone 프록시로 교체하여 15-30분 설정.
- MIT 라이선스; 월 100K req 무료, 유료 $20/월+.
- 장애 조치, 캐싱, 비율 제한 포함 — 게이트웨이으로도 작동합니다.
- 에이전트/멀티 스텝 추적에서 깊이가 적습니다.
- 스위트 스팟: 빠른 시작, 단일 스택 앱, 게이트웨이 + 관찰 가능성을 하나로 필요로 하는 경우.

### Opik (Comet) — OSS 개발 플랫폼

- Apache 2.0, 완전 OSS.
- Comet heritage가 있는 Langfuse와 유사한 기능 세트.
- 스위트 스팟: 이미 Comet에 있는 ML 팀, 같은 창에서 LLM 관찰 가능성을 원하는 경우.

### SigNoz — OpenTelemetry 우선 완전 APM

- Apache 2.0. OpenTelemetry를 통해 일반 APM plus LLM을 처리합니다.
- 스위트 스팟: 서비스 및 LLM 호출 전반의 통합 관찰 가능성.

### 접착제: OpenTelemetry + GenAI 의미론 규칙

OpenTelemetry는 2025년 말에 GenAI 의미론 규칙을 게시했습니다 (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`). OTel을 소비하는 도구는 상호 운용할 수 있습니다. 출현하는 프로덕션 패턴:

1. 모든 LLM 호출에서 GenAI 규칙으로 OTel을 방출합니다.
2. 일상적으로 게이트웨이 (Helicone / Portkey)로 라우팅합니다.
3. 회귀를 위해 평가 플랫폼 (Phoenix / Langfuse)으로 이중 shipping합니다.
4. 장기 분석을 위해 데이터 레이크 (Iceberg)에 보관 — Arize AX 또는 DuckDB를 통해.

### 함정: 잘못된 레이어에서 계측

에이전트 프레임워크 내부에서 계측 (예: LangSmith 추적 추가)은 해당 프레임워크에 결합합니다. HTTP/OpenAI-SDK 레이어에서 계측 (OpenLLMetry 또는 게이트웨이 통해)은 이식 가능합니다.

### 샘플링 — 모든 것을 유지할 수 없습니다

일 100만 요청 이상에서 전체 추적 유지 비용이 LLM 호출보다 비쌉니다. 규칙으로 샘플링: 100% 오류, 100% 고비용, 5% 성공. 항상 aggregate를 유지합니다; 긴 tail에 대해서는 원시를 유지합니다.

### 기억해야 할 숫자

- Langfuse 무료 클라우드: 월 50K 이벤트.
- LangSmith: 사용자당 $39/월.
- Helicone 무료: 월 100K req.
- Arize AX 주장: 규모에서 모놀리식 대비 ~100배 저렴.
- OpenTelemetry GenAI 규칙: 2025년 shipping, 2026년 널리 채택.

## 활용

`code/main.py`는 유지 전략 전반에서 1M-추적일을 시뮬레이션합니다 (100% ingest, 샘플링, 샘플링 + 오류). 각에서 저장소 비용과 손실된 것을 보고합니다.

## 결과물

이 레슨은 `outputs/skill-observability-stack.md`를 산출합니다. 스택, 규모, 예산, 라이선스 자세를 감안하여 도구를 선택합니다.

## 연습문제

1. LangChain의 팀이 OSS 자체 호스팅 관찰 가능성을 원합니다. Langfuse 또는 Opik을 선택하고 정당화하세요.
2. 일 5M 추적에서 Datadog 견적이 $150K/월인 경우 Arize AX의 균형을 계산하세요.
3. 조직의 지침이 모든 LLM 호출에서 의무화해야 하는 OpenTelemetry GenAI 属性 세트를 디자인하세요.
4. Phoenix만으로 프로덕션에 충분한지 주장하세요. 언제 충분하지 않습니까?
5. Helicone은 20ms 프록시 오버헤드입니다. P99 TTFT 300 ms에서 그것을接受的합니까? SLA가 100 ms이면 어떻습니까?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| OpenLLMetry | "LLM용 OTel" | LLM용 오픈소스 OpenTelemetry 계측 |
| GenAI 규칙 | "OTel 属性" | LLM 호출을 위한 표준 OTel 属性 이름 |
| LangSmith | "LangChain 관찰 가능성" | LangChain 에코시스템과 번들된 상업용 플랫폼 |
| Langfuse | "OSS LangSmith" | 유사한 기능 세트가 있는 MIT OSS |
| Phoenix | "Arize 개발 도구" | OpenTelemetry 네이티브 개발/평가 플랫폼 |
| Arize AX | "규모 관찰 가능성" | Iceberg/Parquet 제로카피 상업용 관찰 가능성 |
| Helicone | "프록시 관찰 가능성" | LLM 원격 측정 + 게이트웨이 기능을 수집하는 HTTP 프록시 |
| Opik | "Comet LLM" | Comet의 Apache 2.0 OSS 개발 플랫폼 |
| 세션 리플레이 | "추적 재실행" | 도구 호출로 전체 에이전트 세션을 재실행 |
| 평가 | "오프라인 테스트" | 레이블된 데이터셋에서 후보 모델/프롬프트 실행 |

## 추가 자료

- [SigNoz — 상위 LLM 관찰 가능성 도구 2026](https://signoz.io/comparisons/llm-observability-tools/)
- [Langfuse — Arize AX 대안 분석](https://langfuse.com/faq/all/best-phoenix-arize-alternatives)
- [PremAI — Langfuse, LangSmith, Helicone, Phoenix 설정](https://blog.premai.io/llm-observability-setting-up-langfuse-langsmith-helicone-phoenix/)
- [OpenTelemetry GenAI 의미론 규칙](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Arize Phoenix 문서](https://docs.arize.com/phoenix)
- [Helicone 문서](https://docs.helicone.ai/)