# AI 게이트웨이 — LiteLLM, Portkey, Kong AI Gateway, Bifrost

> 게이트웨이는 앱과 모델 공급업체 사이에 있습니다. 핵심 기능은 제공자 라우팅, 폴백, 재시도, 비율 제한, 시크릿 참조, 관찰 가능성, 가드레일입니다. 2026년 시장 분할: **LiteLLM**은 MIT OSS로 100+ 공급업체, OpenAI 호환이지만 ~2000 RPS에서 무너집니다 (8 GB 메모리, 게시된 벤치마크에서 연쇄적 실패); Python, <500 RPS, dev/prototyping에 가장 좋습니다. **Portkey**는 컨트롤 플레인 위치입니다 (가드레일, PII 수정, 탈출 감지, 감사 추적), 2026년 3월 Apache 2.0으로 오픈소스 전환, 20-40 ms 지연 시간 오버헤드, $49/월 프로덕션 계층. **Kong AI Gateway**는 Kong Gateway 기반으로 구축되었습니다 — Kong의 같은 12 CPU에서 자체 벤치마크: Portkey보다 228% 빠르고, LiteLLM보다 859% 빠릅니다; $100/모델/월 가격 (Plus 계층에서 최대 5개); 이미 Kong에 있으면 기업 적합. **Bifrost** (Maxim AI) — 구성 가능한 백오프가 있는 자동 재시도, OpenAI 429 시 Anthropic으로 폴백. **Cloudflare / Vercel AI Gateways** — 관리형, 제로 ops, 기본 재시도. 데이터 거주지가 자체 호스팅 결정을 주도합니다; Portkey와 Kong은 중간에 있으며 OSS + 선택적 관리됩니다.

**유형:** 학습
**언어:** Python (stdlib, toy gateway-routing 시뮬레이터)
**선수 과목:** Phase 17 · 01 (Managed LLM Platforms), Phase 17 · 16 (Model Routing)
**소요 시간:** ~60분

## 학습 목표

- 6가지 핵심 게이트웨이 기능을 열거합니다 (라우팅, 폴백, 재시도, 비율 제한, 시크릿, 관찰 가능성, 가드레일).
- 4가지 2026 게이트웨이 (LiteLLM, Portkey, Kong AI, Bifrost)를 규모 천장 및 사용 사례로 매핑합니다.
- Kong 벤치마크 (Portkey보다 228%, LiteLLM보다 859%)를 인용하고 >500 RPS에 중요한 이유를 설명합니다.
- 데이터 거주지 및 ops 예산 given으로 자체 호스팅 대 관리형을 선택합니다.

## 문제

제품이 OpenAI, Anthropic, 자체 호스팅 Llama를 호출합니다. 각 공급업체는 다른 SDK, 오류 모델, 비율 제한, 인증 체계를 가집니다. 장애 조치 (OpenAI 429이면 Anthropic 시도), 단일 자격 증명 저장소, 통합 관찰 가능성, 테넌트당 비율 제한을 원합니다.

앱 레이어에서 이것을 재발명하면 모든 서비스가 모든 공급업체에 결합됩니다. 게이트웨이 레이어는 하나 프로세스로 통합하여 (일반적으로 OpenAI 호환) 하나 API로 fans 공급업체로_out합니다.

## 개념

### 6가지 핵심 기능

1. **공급업체 라우팅** — 하나의 API 뒤에 OpenAI, Anthropic, Gemini, 자체 호스팅 등.
2. **폴백** — 429, 5xx 또는 품질 실패 시 다른 곳에서 재시도.
3. **재시도** — 지수 백오프, 제한된 시도.
4. **비율 제한** — 테넌트별, 키별, 모델별.
5. **시크릿 참조** — 런타임時に vault에서 자격 증명을 pull (앱에 절대 아님).
6. **관찰 가능성** — OTel + GenAI 属性 (Phase 17 · 13) + 비용 귀인.
7. **가드레일** — PII 수정, 탈출 감지, 허용된 항목 필터.

### LiteLLM — MIT OSS, Python

- 100+ 공급업체, OpenAI 호환, 라우터 구성, 폴백, 기본 관찰 가능성.
- Kong의 벤치마크에서 ~2000 RPS에서 무너집니다; 8 GB 메모리 발자국, 지속 부하에서 연쇄적 실패.
- 가장 적합: Python 앱, <500 RPS, dev/staging 게이트웨이, 실험적 라우팅.
- 비용: OSS는 $0; 클라우드 무료 계층이 있습니다.

### Portkey — 컨트롤 플레인 포지셔닝

- 2026년 3월 현재 Apache 2.0 OSS. 가드레일, PII 수정, 탈출 감지, 감사 추적.
- 요청당 20-40 ms 지연 시간 오버헤드.
- 유지 + SLA가 있는 프로덕션 계층에 대해 $49/월.
- 가장 적합: 가드레일 + 관찰 가능성이 번들된 규제 산업.

### Kong AI Gateway — 규모 플레이

- Kong Gateway (성숙한 API 게이트웨이 제품, lua+OpenResty) 위에 구축.
- Kong의 자체 벤치마크 (12-CPU 상당): Portkey보다 228% 빠르고, LiteLLM보다 859% 빠릅니다.
- 가격: $100/모델/월, Plus 계층에서 5개 최대.
- 가장 적합: 이미 Kong에 있음; >1000 RPS; 라이선스할 의지.

### Bifrost (Maxim AI)

- 구성 가능한 백오프가 있는 자동 재시도.
- OpenAI 429 시 Anthropic으로의 폴백이 정식 레시피입니다.
- 새로운 참가자; 상업용.

### Cloudflare AI Gateway / Vercel AI Gateway

- 관리형, 제로 ops. 기본 재시도 및 관찰 가능성.
- 가장 적합: Cloudflare/Vercel의 Edge-서빙 JavaScript 앱.
- Kong/Portkey의 가드레일 및 비율 제한에 비해 제한적입니다.

### 자체 호스팅 대 관리형

데이터 거주지가 강제 함수입니다. 헬스케어와 금융은 자체 호스팅으로 기본 설정됩니다 (LiteLLM 또는 Portkey OSS 또는 Kong). 소비자 제품은 관리형 (Cloudflare AI Gateway) 또는 중간 계층 (Portkey 관리형)으로 기본 설정됩니다. 하이브리드: 규제 테넌트의 경우 자체 호스팅, 다른 경우 관리형.

### 지연 시간 예산

- LiteLLM: 일반적으로 5-15 ms 오버헤드.
- Portkey: 20-40 ms 오버헤드.
- Kong: 3-8 ms 오버헤드.
- Cloudflare/Vercel: Edge의 1-3 ms 오버헤드.

게이트웨이 지연 시간은 TTFT에 직접 추가됩니다. TTFT P99 < 100 ms SLA의 경우 Kong 또는 Cloudflare. P99 < 500 ms의 경우 아무 것이나.

### 비율 제한 의미론이 중요합니다

단순 토큰 버킷은 중간 규모까지 작동합니다. 멀티 테넌트는 sliding-window + 버스트 허용 + 테넌트별 계층화가 필요합니다. LiteLLM은 토큰 버킷을 제공하고; Kong은 sliding-window를 제공하고; Portkey는 계층화를 제공합니다.

### 게이트웨이 + 관찰 가능성 + 라우팅 구성

Phase 17 · 13 (관찰 가능성) + 16 (모델 라우팅) + 19 (게이트웨이)는 프로덕션에서 같은 레이어입니다. 세 가지 모두를Cover하는 하나의 도구를 선택하거나 carefully 它们를 연결하세요: 대부분의 2026년 배포는 분할 역할을 위해 (Helicone (관찰 가능성) 또는 Portkey (가드레일))와 (규모를 위해 Kong)를 결합합니다.

### 기억해야 할 숫자

- LiteLLM: ~2000 RPS에서 무너지고, 8 GB 메모리.
- Portkey: 20-40 ms 오버헤드; 2026년 3월부터 Apache 2.0.
- Kong: Portkey보다 228% 빠르고, LiteLLM보다 859% 빠릅니다.
- Kong 가격: $100/모델/월, Plus 계층에서 5개 최대.
- Cloudflare/Vercel: Edge에서 1-3 ms 오버헤드.

## 활용

`code/main.py`는 429/5xx 주입에서 3개 공급업체 전반의 폴백이 있는 게이트웨이 라우팅을 시뮬레이션합니다. 지연 시간, 재시도율, 폴백 적중율을 보고합니다.

## 결과물

이 레슨은 `outputs/skill-gateway-picker.md`를 산출합니다. 규모, ops 자세, 규정 준수, 지연 시간 예산이 주어지면 게이트웨이를 선택합니다.

## 연습문제

1. `code/main.py`를 실행하세요. OpenAI→Anthropic→자체 호스팅으로 폴백을 구성하세요. 공급업체 오류율 5%에서 예상 적중률은 얼마입니까?
2. SLA가 300 ms 기준에서 TTFT P99 < 200 ms입니다. 어떤 게이트웨이가 예산 내에 유지합니까?
3. 의료 고객이 자체 호스팅 + PII 수정 + 감사가 필요합니다. Portkey OSS 또는 Kong을 선택하세요.
4. LiteLLM 대 Kong 비교: 어느 RPS天花板에서 팀이 마이그레이션해야 합니까?
5. 멀티 테넌트 SaaS에 대한 비율 제한 정책을 디자인하세요: 무료 계층, 평가판 계층, 유료 계층. 토큰 버킷 또는 sliding-window?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| 게이트웨이 | "API 브로커" | 앱과 공급업체 사이에 있는 프로세스 |
| LiteLLM | "MIT 것" | Python OSS, 100+ 공급업체, 2K RPS에서 무너짐 |
| Portkey | "가드레일 게이트웨이" | 컨트롤 플레인 + 관찰 가능성, Apache 2.0 |
| Kong AI Gateway | "규모 것" | Kong Gateway 위에 구축, 벤치마크 리더 |
| Bifrost | "Maxim의 게이트웨이" | 재시도 + Anthropic 폴백 레시피 |
| Cloudflare AI Gateway | "edge 관리형" | Edge에 배포된 관리형 게이트웨이, 제로 ops |
| PII 수정 | "데이터 스크럽" | 모델로 보내기 전에 regex + NER 마스크 |
| 탈출 감지 | "프롬프트 주입 가드" | 사용자 입력의 분류기 |
| 감사 추적 | "규제 로그" | 모든 LLM 호출의 불변 기록 |
| 토큰 버킷 | "단순 비율 제한" | 리필 기반 비율 제한기 |
| Sliding-window | "정밀 비율 제한" | 시간 창 비율 제한기; 더 나은 공정성 |

## 추가 자료

- [Kong AI Gateway 벤치마크](https://konghq.com/blog/engineering/ai-gateway-benchmark-kong-ai-gateway-portkey-litellm)
- [TrueFoundry — AI 게이트웨이 2026 비교](https://www.truefoundry.com/blog/a-definitive-guide-to-ai-gateways-in-2026-competitive-landscape-comparison)
- [Techsy — 상위 LLM 게이트웨이 도구 2026](https://techsy.io/en/blog/best-llm-gateway-tools)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Portkey GitHub](https://github.com/Portkey-AI/gateway)
- [Kong AI Gateway 문서](https://docs.konghq.com/gateway/latest/ai-gateway/)