# 추론 플랫폼 경제학 — Fireworks, Together, Baseten, Modal, Replicate, Anyscale

> 2026년 추론 시장을 더 이상 GPU 시간 임대료가 아닙니다. 사용자 정의 실리콘 (Groq, Cerebras, SambaNova), GPU 플랫폼 (Baseten, Together, Fireworks, Modal), API 우선 마켓플레이스 (Replicate, DeepInfra)로 양분됩니다. Fireworks가 2026년 5월 1일 GPU당 $1/시간 가격을 올렸고 $4B 가치로 10T+ 토큰/일을 처리한다는 것은 볼륨 기반 모델이 작동한다는 것을 알려줍니다. Baseten은 2026년 1월 $5B로 $300M 시리즈 E를 마감했습니다. 경쟁 포지셔닝 규칙은 간단합니다: Fireworks는 지연 시간 최적화, Together는 카탈로그 폭 최적화, Baseten은 기업 완성도 최적화, Modal은 Python 네이티브 DX 최적화, Replicate는 멀티모달 리치 최적화, Anyscale은 분산 Python 최적화. 이 레슨은 창업자에게 건낼 수 있는 매트릭스를 제공합니다.

**유형:** 학습
**언어:** Python (stdlib, toy per-call economics 비교기)
**선수 과목:** Phase 17 · 01 (Managed LLM Platforms), Phase 17 · 04 (vLLM Serving Internals)
**소요 시간:** ~60분

## 학습 목표

- 세 가지 시장 세그먼트 (사용자 정의 실리콘, GPU 플랫폼, API 우선)를 이름 짓고 각 공급업체를 세그먼트에 매핑합니다.
- "토큰당" API 가격 책정 모델이 하드웨어의 것이 아니라 추론 엔진의 비용 곡선으로 수렴하는 이유를 설명합니다.
- 최소 세 가지 공급업체에서 요청당 유효 비용을 계산하고 per-minute (Baseten, Modal)가 per-token을 이기는 경우를 설명합니다.
- 주어진 작업 (서버리스 버스티, 안정적 고처리량, fine-tuned 변형, 멀티모달)에 올바른 기본 플랫폼을 식별합니다.

## 문제

관리형 하이퍼스케일러 플랫폼을 평가했습니다. 더 좁고 빠른 제공자가 필요하다고 결정했습니다 — 지연 시간에는 Fireworks, 폭에는 Together, fine-tuned 사용자 정의 모델에는 Baseten. 이제 6개의 실제 선택지가 있고 가격 페이지가 정렬되지 않습니다. Fireworks는 $/M 토큰을 표시합니다; Baseten은 $/분을 표시합니다; Modal은 $/초를 표시합니다; Replicate는 $/prediction을 표시합니다. 작업을 모델링하지 않고는它们를 직접 비교할 수 없습니다.

더 나쁘게는 각 가격 페이지 뒤의 사업 모델이 다릅니다. Fireworks는 자체 사용자 정의 엔진 (FireAttention)을 공유 GPU에서 실행합니다; 토큰당 요금은 利用률 곡선을 반영합니다. Baseten은 Truss + 전용 GPU를 제공합니다; per-minute은 독점성을 반영합니다. Modal은 진정한 Python 서버리스 — 하위 초 단위 콜드 스타트가 있는 초당 청구. 동일한 출력 (LLM 응답), 세 가지 다른 비용 함수.

이 레슨은 6개를 모델링하고 각각이 언제 이기는지 알려줍니다.

## 개념

### 세 가지 세그먼트

**사용자 정의 실리콘** — Groq (LPU), Cerebras (WSE), SambaNova (RDU). 일반적으로 동일한 모델의 GPU 기반 클러스터보다 5-10배 더 빠른 디코딩. 토큰당 가격更高 (Groq는 2025년 후반 Llama-70B에서 ~$0.99/M بود). 지연 시간 민감 사용 사례에서 비교할 수 없습니다. Groq는 음성 에이전트 및 실시간 번역의 프로덕션 선택입니다.

**GPU 플랫폼** — Baseten, Together, Fireworks, Modal, Anyscale. NVIDIA에서 실행 (2026년 H100, H200, B200) 또는 때때로 AMD. "raw GPU 임대" (RunPod, Lambda)와 "하이퍼스케일러 관리 서비스" (Bedrock) 사이의 경제적 계층.

**API 우선 마켓플레이스** — Replicate, DeepInfra, OpenRouter, Fal. 광범위한 카탈로그, 예측당 또는 초당 지불, 첫 번째 호출까지의 시간 강조.

### Fireworks — 지연 시간 최적화 GPU 플랫폼

- FireAttention 엔진 (사용자 정의); 동등한 구성에서 vLLM보다 4배 낮은 지연 시간으로 마케팅됩니다.
- 非対話적 작업용 배치 계층: 서버리스 요금의 ~50%.
- Fine-tuned 모델이 기본 모델과 동일한 요금으로 제공됩니다 — LoRA에 프리미엄을 부과하는 제공자와 비교한 실제 차별화.
- 2026년 중반: 2026년 5월 1일 온디맨드 GPU 임대가 시간당 $1 효과적으로 인상. 규모에서 볼륨 가격 협상 가능.
- 재무 신호: $4B 가치, 10T+ 토큰/일 처리.

### Together — 폭 최적화

- 상류 게시 후 며칠 내에 오픈소스 릴리스를 포함하여 200+ 모델.
- 동등한 LLM 모델에서 Replicate보다 50-70% 저렴 — "AI Native Cloud" 포지셔닝은 볼륨과 카탈로그입니다.
- 하나의 API에서 추론 + fine-tuning + 훈련.

### Baseten — 기업 완성도 최적화

- Truss 프레임워크: 종속성, 시크릿, 제공 구성在一个 manifest에서 모델 패키징.
- T4에서 B200까지의 GPU 범위. 합리적인 콜드 스타트 완화를 통한 분당 과금.
- SOC 2 Type II, HIPAA 준비. 일반적인 핀테크 및 의료 선택.
- $5B 가치, 2026년 1월 시리즈 E ($300M CapitalG, IVP, NVIDIA에서).

### Modal — Python 네이티브 최적화

- 순수 Python에서 인프라-as-code. `@modal.function(gpu="A100")`로 함수를 장식하고 하나의 명령으로 배포.
- 초당 청구. 작은 모델에서 2-4s 콜드 스타트; <1s.
- $87M 시리즈 B, $1.1B 가치 (2025). 독립 조사에서 가장 강한 개발자 경험 점수.

### Replicate — 멀티모달 폭

- 예측당 지불. 이미지, 비디오, 오디오 모델의 기본 플랫폼.
- 통합 에코시스템 (Zapier, Vercel, CMS 플러그인).
- LLM 토큰당 요금에서 경쟁력이 낮지만 멀티모달 다양성에서 이깁니다.

### Anyscale — Ray 네이티브

- Ray 위에 구축; RayTurbo는 Anyscale의 전용 추론 엔진입니다 (vLLM과 경쟁).
- 추론 단계가 더 큰 그래프의 하나의 노드인 분산 Python 작업에 가장 적합.
- 관리형 Ray 클러스터; Ray AIR 및 Ray Serve와 긴밀한 통합.

### 토큰당 대 분당 — 각각이 이기는 경우

토큰당 작업이 지연 시간에 민감하지 않고 버스티할 때 합리적입니다 — 사용한 만큼만 지불합니다. 분당 작업 이용률이 높고 예측 가능한 경우 합리적입니다 — GPU를 포화시키기 시작하면 토큰당을 이깁니다.

的经验적 규칙: 전용 GPU의 지속적인 利用률 ~30% 이상인 작업의 경우, 분당 (Baseten, Modal)이 토큰당 (Fireworks, Together)을 이기기 시작합니다. 그 아래에서는 토큰당이 이깁니다, 왜냐하면 유휴에 지불하는 것을 피하기 때문입니다.

### 사용자 정의 엔진이 실제 방어막입니다

vLLM과 SGLang 위에서 사용자 정의 엔진을 주장하는 모든 플랫폼. FireAttention, RayTurbo, Baseten의 추론 스택. 사용자 정의 엔진 주장은 마케팅을 어둡게 합니다 — 정직한 프레이밍은 vLLM + SGLang이 생산용 오픈소스 추론의 약 80%를代表하고, 플랫폼 레이어의 차별화는 DX, 귀인, SLA입니다.

### 기억해야 할 숫자

- Fireworks GPU 임대: 2026년 5월 1일 효과적인 시간당 $1 인상.
- Fireworks 주장: 동등한 구성에서 vLLM보다 4배 낮은 지연 시간.
- Together: LLM에서 Replicate보다 50-70% 저렴.
- Baseten 가치: $5B (2026년 1월 시리즈 E, $300M 라운드).
- Modal 가치: $1.1B (2025년 시리즈 B).
- 지속적인 利用률 ~30% 이상에서 분당이 토큰당을 이깁니다.

## 활용

`code/main.py`는 합성 작업에서 6개 공급업체를 가격 책정 모델에서 비교합니다. $/일 및 유효 $/M 토큰을 보고합니다. 토큰당과 분당의 균형점을 찾기 위해 실행하세요.

## 결과물

이 레슨은 `outputs/skill-inference-platform-picker.md`를 산출합니다. 작업 프로필, SLA, 예산이 주어지면 기본 추론 플랫폼을 선택하고 runner-up의 이름을 지정합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 하나의 H100에서 70B 모델에 대해 Baseten (분당)이 Fireworks (토큰당)를 이기는 지속적인 利用률은 어느 정도입니까? crossover를 직접 유도하고 경험적 규칙과 비교하세요.
2. 제품이 이미지 생성 plus 채팅 plus 음성-텍스트를 제공합니다. 각 양식에 플랫폼을 선택하고 그것들을 통합하는 게이트웨이 패턴의 이름을 지정하세요.
3. Fireworks가 기본 모델에서 시간당 $1 가격을 올립니다. 트래픽의 40%가 배치 계층 (50% 할인)으로 이동하면 혼합 비용 영향을 모델링하세요.
4. 규제받는 고객이 SOC 2 Type II + HIPAA + 전용 GPU를 요구합니다. 세 플랫폼이 이행 가능하고哪一个이 FinOps에서 이기는지指定하세요.
5. Fireworks 서버리스, Together 온디맨드, Baseten 전용, Replicate API에서 Llama 3.1 70B의 1,000 예측당 비용을 비교하세요. 10 예측/일에서哪一个가 가장 저렴합니까? 10,000에서?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| 사용자 정의 실리콘 | "non-GPU 칩" | Groq LPU, Cerebras WSE, SambaNova RDU — 디코딩 최적화 |
| FireAttention | "Fireworks 엔진" | 사용자 정의 어텐션 커널; vLLM보다 4배 낮은 지연 시간으로 마케팅 |
| Truss | "Baseten의 형식" | 종속성 + 시크릿 + 제공 구성이 있는 모델 패키징 manifest |
| 토큰당 | "API 가격 책정" | 소비된 토큰별로 청구; 유휴에 지불하지 않음 |
| 분당 | "전용 가격 책정" | wall-clock GPU 시간별로 청구; 높은 利用률에서 이김 |
| 예측당 | "Replicate 가격 책정" | 모델 호출당 청구; 이미지/비디오에 일반적 |
| RayTurbo | "Anyscale 엔진" | Ray 클러스터에서 vLLM과 경쟁하는 Ray 전용 추론 |
| 배치 계층 | "50% 할인" | 할인된 요금의 非対話적 대기열; Fireworks, OpenAI에서 일반적 |
| 기본 요금으로 fine-tuned | "Fireworks LoRA" | LoRA 제공 요청을 기본 모델 요금으로 청구 (차별화) |

## 추가 자료

- [Fireworks Pricing](https://fireworks.ai/pricing) — 토큰당 요금, 배치 계층, GPU 임대.
- [Baseten Pricing](https://www.baseten.co/pricing/) — 분당 요금, 커밋된 용량, 기업 등급.
- [Modal Pricing](https://modal.com/pricing) — 초당 GPU 요금 및 무료 계층.
- [Together AI Pricing](https://www.together.ai/pricing) — 모델 카탈로그 및 토큰당 요금.
- [Anyscale Pricing](https://www.anyscale.com/pricing) — RayTurbo 및 관리형 Ray 가격 책정.
- [Northflank — Fireworks AI Alternatives](https://northflank.com/blog/7-best-fireworks-ai-alternatives-for-inference) — 비교 평가.
- [Infrabase — AI Inference API Providers 2026](https://infrabase.ai/blog/ai-inference-api-providers-compared) — 공급업체 환경.