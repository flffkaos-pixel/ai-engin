# 텔레메트리: OpenTelemetry와 GenAI 스팬

> OTel GenAI는 LLM 호출을 표준화된 첫 번째 토큰, 입력/출력 토큰, 프롬프트 템플릿, 벡터 검색 스팬으로 계측한다. 2026년에는 Langfuse, Phoenix, Opik, Datadog, Grafana가 모두 동일한 의미 체계를 채택했다. 선택은 기능이 아닌 AIOps/Vendor 선호도에 달려 있다.

**Type:** Learn
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 07 (MCP Servers — Transport)
**Time:** ~60분

## 학습 목표

- OTel GenAI의 여섯 가지 스팬 유형 (llm, chat, embed, vector, retrieve, rerank)을 명명한다.
- 스팬 속성(gen_ai.request.model, gen_ai.response.id, gen_ai.usage.completion_tokens)을 설명한다.
- Langfuse, Phoenix, Opik의 차이점과 오버랩을 요약한다.
- 에이전트 루프를 위한 세 가지 계측 전략(래퍼, 미들웨어, MLflow)을 설명한다.

## 문제

에이전트가 실패할 때 원인을 알 수 없다. 잘못된 도구 선택? 프롬프트 인젝션? 공급자 중단? 높은 지연 시간? 계측은 디버깅, 감사 및 비용 통제를 위해 모든 LLM 호출, 도구 사용 및 토큰 사용을 캡처하는 에이전트 인프라의 계층이다.

## 개념

### OTel GenAI (OpenTelemetry Semantic Conventions for Generative AI)

여섯 가지 스팬 유형:

| 스팬 유형 | 대상 | 예시 속성 |
|-----------|---------|-----------|
| `llm` | 임의 LLM 호출 | `gen_ai.request.model`, `gen_ai.response.id`, `gen_ai.usage.completion_tokens` |
| `chat` | 채팅 완료 | `gen_ai.system`, `gen_ai.request.max_tokens`, 메시지 이벤트 |
| `embed` | 임베딩 | `gen_ai.request.model`, 임베딩 차원 |
| `vector` | 벡터 DB 검색 | 밀집 vs 희소, 결과 점수, 하이브리드 검색 |
| `retrieve` | 에이전트 검색 | 검색 전략, 리랜커 호출 |
| `rerank` | 리랭킹 | 입력 점수, 출력 점수, 리랭킹 설명 |

각 스팬은 형제 OTEL 스팬(DB 호출, HTTP 요청 내부)을 포함하고 LLM 호출 트레이스에 연결된다.

### 플랫폼

| 플랫폼 | 하이라이트 |
|---------|-----------|
| **Langfuse** | 에이전트 전용 관찰 가능성; 자가 호스팅 또는 클라우드; LLM-as-judge 평가기 |
| **Phoenix (Arize)** | OTel 네이티브; 폭포형 스팬; LLM-as-judge 예제; 노트북 UI |
| **Opik (Comet)** | LLM 평가; 프롬프트 버전 관리; 하이라인 CVEs |
| **Datadog** | LLM Observability 퀵 스타트; APM에 연결 |
| **Grafana** | OTel 파이프라인; 기존 AIOps 대시보드에 연결 |

Datadog, Grafana, Langfuse: OTel 네이티브. Opik과 Phoenix도 OTel을 지원하지만 자사 SDK도 있음. 선택 결정은: "우리가 이미 사용하고 있는 AIOps 스택이 무엇인가?"

### 에이전트 계측 전략

1. **래퍼.** LLM 클라이언트 호출을 OTel 스팬으로 래핑. 간단하지만 불완전 (툴링 누락).
2. **미들웨어.** LLM 호출을 가로채고 도구 사용을 추적하는 미들웨어 계층. SDk에 더 가깝지만 래퍼보다 더 많은 코드.
3. **MLflow Tracing** (레슨 25) — MLflow의 자동 Tracing API. AI Gateway와 통합되는 공급자 중립적 접근 방식.

### 커리큘럼 통합

OTel GenAI는 각 레슨을 연결한다: 도구 사용(레슨 06), MCP 전송(레슨 07), 에이전트 루프(레슨 01), 평가(레슨 30). 추적되지 않은 에이전트는 운영될 수 없다.

### 이 패턴이 잘못되는 경우

- **추적 과부하.** 모든 단일 LLM 호출을 추적. 저장 비용이 실행 비용을 초과. 중요 프로덕션 흐름에 헤드 기반 샘플링 사용.
- **원시 OTel에만 의존.** 원시 OTel은 낮은 수준. Langfuse 또는 Phoenix 계층이 UI, LLM-as-judge 평가기, 감사 로그 테이블을 추가.
- **민감한 데이터 기록.** 프롬프트와 응답을 추적에 포함. PII/비밀이 있는 경우 마스킹 훅 추가.

## 직접 구현하기

`code/main.py`는 OTel GenAI 계층을 구현한다:

- 6가지 스팬 유형 모두에 대한 스팬 생성기 및 속성 매퍼.
- `llm` 스팬을 생성하는 LLM 클라이언트 래퍼.
- 스팬을 stdout JSON 라인으로 출력하는 간단한 내보내기.
- 추적 헤더를 연결하는 컨텍스트 전파(Phase 14 · 07의 트레이스 컨텍스트).

실행:

```
python3 code/main.py
```

출력: LLM 호출, 벡터 검색, 리랭킹을 단일 전체 추적으로 보여주는 연결된 JSON 스팬 그룹.

## 활용하기

- 모든 프로덕션 에이전트에 대해 Langfuse 자체 호스팅. 가장 빠른 설정.
- Phoenix/Opik이 여기에 있음을 테스트 또는 노트북 작업에서 사용.
- Datadog/Grafana은 해당 스택에 이미 투자한 팀에게.
- AI Gateway(레슨 25) + MLflow 추적이 저장소/감사/비용을 게이트웨이로 중앙 집중화.

## 배포하기

`outputs/skill-observability-setup.md` scaffolds an OpenTelemetry GenAI instrumented agent with:
- Span generation and export
- Langfuse / Phoenix connectors
- Step-by-step trace propagation
- Token accounting

## 연습 문제

1. 장난감 OTel 계층을 실제 LLM 호출 래퍼로 포팅. 스팬 내에 캡처된 속성은 무엇인가?
2. 헤드 기반 샘플링 추가: 에이전트 루프 스팬의 10%만 저장. 5회 실행에서 어떤 스팬이 손실되는가?
3. 마스킹 훅 구현: 프롬프트에서 역할="user"인 메시지의 콘텐츠 필드 제로화. 동작 검증.
4. 래퍼 전략을 미들웨어 전략으로 교체. 미들웨어가 LLM 호출 전후에 무엇을 추가로 잡는가?
5. Langfuse 자체 호스팅 시작. 장난감 에이전트의 추적을 Langfuse UI에 연결.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| OTel GenAI | "LLM용 텔레메트리 스키마" | LLM, 채팅, 임베딩, 벡터 검색, 검색, 리랭킹을 위한 표준화된 스팬 유형 |
| Trace | "전체 요청 경로" | 단일 사용자 요청에 연결된 모든 스팬 |
| Span | "단일 작업" | 단일 LLM 호출, 도구 호출 또는 DB 쿼리 |
| Exporter | "내보내기 대상" | 스팬이 전송되는 곳 (stdout, Langfuse, Datadog) |
| Sampling | "저장 비용 제어" | 기록할 요청의 일부 선택 기준 |
| Head-based sampling | "첫 번째 스팬 결정" | 트레이스 수준에서 샘플링 결정; 요청 진행 중에 변경되지 않음 |

## 추가 자료

- [OTel GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — official spec for GenAI spans
- [Langfuse docs](https://langfuse.com/docs) — agent-native observability
- [Arize Phoenix docs](https://docs.arize.com/phoenix) — OTel-native LLM observability
- [Comet Opik docs](https://www.comet.com/docs/opik/) — evaluation + observability
