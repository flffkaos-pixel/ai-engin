# AI 게이트웨이와 MLflow 추적

> AI 게이트웨이는 호출을 라우팅한다(LiteLLM, Portkey, MLflow). MLflow 추적은 계측한다. 2026년 표준은 LiteLLM으로 라우팅하고 MLflow로 자동 추적하는 것이다. LiteLLM의 MLflow 콜백(mlflow.<provider>.autolog())은 비용, 지연 시간, 토큰 사용을 게이트웨이 로그에 중앙 집중화한다.

**Type:** Learn
**Build:** Python (stdlib)
**Prerequisites:** Phase 14 · 23 (Telemetry & Observability)
**Time:** ~60분

## 학습 목표

- AI 게이트웨이가 하는 세 가지 일을 명명한다 (모델 라우팅, 로깅, 가드레일 적용).
- LiteLLM(500개 모델)과 Portkey(멀티 프로바이더 폴백)의 차이점을 요약한다.
- MLflow 게이트웨이와 Tracing API를 설명한다.
- LiteLLM의 `mlflow.<provider>.autolog()`가 모든 호출을 추적하기 위해 하는 일을 설명한다.

## 문제

에이전트가 LLM을 호출한다. 어디로 갈까? 비용은? 가드레일이 적용되었는가? 실패할 때 폴백은? AI 게이트웨이는 이 계층이다. OTel GenAI(레슨 23-24)는 추적을 표준화한다. 게이트웨이는 실행을 라우팅한다. 2026년의 가장 깨끗한 조합: LiteLLM + MLflow 추적.

## 개념

### AI 게이트웨이

앙트리포인트 → 게이트웨이 → LLM 공급자. 게이트웨이가 하는 것:

1. **라우팅.** 프록시가 모델을 매핑. LiteLLM 스타일: `gpt-4o` → OpenAI, `claude-4` → Anthropic, `gemini-2.5-pro` → Google.
2. **로깅.** 모든 호출 기록: 프롬프트, 완료, 타임스탬프, 지연 시간, 토큰.
3. **가드레일.** 게이트웨이 수준에서 호출 전 검사 (부적절한 콘텐츠에 대한 프롬프트 검사, 속도 제한, 예산 검사).

### LiteLLM

- Python 패키지, OpenAI 형식을 모든 주요 LLM 공급자로 라우팅. 500개 이상의 모델 지원.
- OpenAI SDK 래퍼(import openai 대신 import litellm)로 사용하거나 프록시 서버로 배포 가능.
- 런타임 폴백(오류 시 공급자 전환).

### Portkey

- 자체 호스팅 또는 클라우드 AI 게이트웨이.
- 멀티 프로바이더 폴백: 공급자가 실패하면 Portkey가 다른 공급자로 요청을 보냄. 가드레일, 캐싱, AI 비용 통제.
- 에이전트 대상 기능: 속도 제한, 예산 캡, 사용자당 한도.
- 게이트웨이 계층을 위한 완전한 운영 솔루션.

둘 다 실용적이다. LiteLLM은 라우팅이 가볍지만 로깅이 거의 없는 팀에게. Portkey는 게이트웨이를 운영 인프라로 운영해야 하는 팀에게.

### MLflow 게이트웨이

- MLflow의 통합 AI 게이트웨이. 프록시 서버로 배포; OpenAI 호환 API로 라우팅.
- MLflow의 추적 UI에 자동 로깅.
- 에이전트를 실행하고 모든 호출이 MLflow에 들어가는 것을 원한다면 좋음.

### MLflow 추적

MLflow의 Tracing API는 자동으로 계측:

- 모든 LLM 호출을 OTel GenAI 스팬으로.
- 비용, 지연 시간, 토큰 사용, 프롬프트, 응답을 캡처.
- MLflow UI에서.
- LiteLLM의 `mlflow.<provider>.autolog()`는 모든 LiteLLM 호출을 MLflow 추적에 연결.
- 일반적인 사용 사례: LiteLLM을 통해 라우팅하고, 모든 호출을 MLflow 추적으로 자동 기록.

### 조합 사용

LiteLLM을 프록시로 배포 → 프록시가 호출을 라우팅 → `mlflow.autolog()`가 모든 호출을 추적 → MLflow 추적 UI가 실행 모니터링 → Portkey 복잡성이 필요하지 않으면 중단. LiteLLM + MLflow = 가장 빠른 생산 경로.

### 이 패턴이 잘못되는 경우

- **게이트웨이 과잉.** 게이트웨이가 하나의 모델을 하나의 공급자로 라우팅만 하는 경우 불필요한 복잡성.
- **로깅 과부하.** 500k 호출/일; 게이트웨이 로그만으로 50GB/일. 샘플링 또는 보존 정책 설정.
- **MLflow 과잉.** 이미 Datadog/Grafana가 있다면 MLflow 추적을 추가하는 것은 다른 계층으로 다른 곳으로 보내야 함. 먼저 단일성을 확립하라.

## 직접 구현하기

`code/main.py`는 게이트웨이와 추적 계층을 구현:

- `GatewayRouter`: 요청을 공급자로 라우팅, 실패 시 폴백.
- `SpanCapture`: 모든 호출을 추적하는 추적 래퍼 (비용, 지연 시간, 토큰).
- 구성 형식: `{"model": "gpt-4o", "fallbacks": ["claude-4", "gemini-2.5-pro"]}`.
- 데모: 게이트웨이를 통해 3개 라우팅, 하나의 공급자가 실패하는 시뮬레이션, 폴백이 작동하는 모습을 보여줌.

실행:

```
python3 code/main.py
```

출력: 라우팅 결정이 포함된 추적된 호출과 폴백 공급자로의 지연 시간 증가.

## 활용하기

- **LiteLLM + MLflow 추적** for fast setup with basic routing needs.
- **Portkey** for full gateway ops: rate limiting, budget caps, multi-provider fallback with fine-grained control.
- **MLflow Gateway** if you're already deep in MLflow (MLflow-native models, registered model versioning).
- **No gateway** for single-provider projects — raw LLM calls are fine.

## 배포하기

`outputs/skill-gateway-setup.md` scaffolds a LiteLLM proxy + MLflow autolog configuration with fallback policies.

## 연습 문제

1. 장난감 게이트웨이를 LiteLLM으로 포팅. python에서 LiteLLM 프록시 시작. 라우트 3개 모델.
2. `mlflow.autolog()` 추가 / LiteLLM 호출에 대한 LiteLLM 콜백. MLflow UI에서 자동 추적 확인.
3. Portkey 자체 호스팅 시작. LiteLLM MLflow 조합과 비교: 설정 복잡성, 기능 차이.
4. 구성 기반 폴백 정책 추가: 기본 gpt-4o, 폴백 claude-4, 2차 폴백 gemini-2.5-pro.
5. 부하 테스트: 게이트웨이를 통해 100개 호출을 벤치마킹. 추가된 지연 시간은 얼마인가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| AI Gateway | "LLM 프록시" | LLM 호출을 라우팅, 로깅, 게이트하는 계층 |
| Model routing | "프록시" | 요청을 공급자에게 전달 |
| Fallback | "백업 공급자" | 기본 공급자가 실패할 때 전환 |
| MLflow Tracing | "자동 계측" | 모든 호출을 OTel 스팬으로 래핑 |
| autolog | "1-라인 계측" | LiteLLM 호출의 자동 MLflow 추적 |

## 추가 자료

- [LiteLLM docs](https://docs.litellm.ai/docs/) — 500+ models, proxy, fallbacks
- [Portkey docs](https://portkey.ai/docs) — self-hosted/cloud AI gateway
- [MLflow Gateway docs](https://mlflow.org/docs/latest/llm/gateway/index.html) — MLflow-native gateway
- [MLflow Tracing docs](https://mlflow.org/docs/latest/llm/tracing/index.html) — automated APM-style tracking
