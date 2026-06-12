# 멀티 리전 LLM 제공 및 KV 캐시 지역성

> 라운드 로빈 부하 분산은 캐시된 LLM 추론에 적극적으로有害합니다. 접두사를 보유한 노드에_land하지 않는 요청은 전체 prefill 비용을 지불합니다 — 캐시 적중 시 ~80 ms에 비해 긴 프롬프트에서 P50에서 약 800 ms. 2026년 프로덕션 패턴은 KV-cache 이벤트를 소비하고 접두사-해시 match에서 라우팅하는 캐시 인식 라우터입니다 (vLLM Router in Rust, llm-d router). 최근 연구 (GORGO)는 교차 리전 네트워크 지연 시간을 라우팅 목표의 명시적 항목을 만듭니다. 상업적 "교차 리전 추론" 제공 (Bedrock cross-region inference, GKE multi-cluster gateways)은 추론을 불투명하게 처리합니다 — 가용성은 처리하지만 TTFT는 처리하지 않습니다. JPMorgan과 Mayo Clinic은 2024년 11월 us-east-1 장애 조치를 ~22분에 실행했습니다. DR 현실: LLM DR 실패의 32%가 가중치를 백업했지만 tokenizer 파일이나 양자화 구성을 잊은 것입니다.

**유형:** 학습
**언어:** Python (stdlib, toy prefix-cache-aware 라우터 시뮬레이터)
**선수 과목:** Phase 17 · 04 (vLLM Serving), Phase 17 · 06 (SGLang RadixAttention)
**소요 시간:** ~60분

## 학습 목표

- 라운드 로빈 부하 분산이 캐시된 추론을 깨뜨리는 이유를 설명하고 TTFT 페널티를 정량화합니다.
- 캐시 인식 라우터를 다이어그램으로 그립니다: 입력 (KV-cache 이벤트), 알고리즘 (접두사-해시 match), tie-breaker (GPU 利用률).
- LLM에 대한 32% DR 실패 드라이버 (누락된 tokenizer 파일 / 양자화 구성)를 이름 짓고 3파일 DR 체크리스트를 설명합니다.
- 상업적 교차 리전 제공 (Bedrock CRI, GKE Multi-Cluster Gateway)을 KV 인식 라우팅과区別합니다.

## 문제

서비스가 us-east-1, us-west-2, eu-west-1에서 실행됩니다. ALB를 앞에 두고 라운드 로빈을 사용합니다. 프로덕션의 접두사 캐시 적중율이 8%로 떨어집니다. TTFT P50이 세 배가 됩니다. vLLM 로그가 모든 요청이 전체 prefill 비용을 지불하고 있음을 보여줍니다.

라운드 로빈은 무상태 서비스에 최적입니다. LLM 추론은 본질적으로 상태 저장입니다 — KV 캐시가 모델이 본 모든 것을 인코딩합니다. 블라인드로 라우팅하면 잘못된 캐시로 라우팅됩니다.

개별적으로, 팀에 DR 계획이 있습니다. 가중치를 S3 교차 리전에 백업합니다. 지역 가동 중지가 발생합니다; 장애 조치를 시도합니다; 복제본이 시작을 거부합니다. tokenizer.json, 양자화 구성, RoPE 스케일링 구성을 별도 버킷에 두었음을 잊은 것입니다.

멀티 리전 LLM 서비스는 캐시 문제, 라우팅 문제, DR 위생 문제입니다 — 부하 분산 문제가 아닙니다.

## 개념

### 캐시 인식 라우팅

요청이 프롬프트와 함께 도착합니다. 라우터가 접두사를 해시합니다 (예: 처음 512 토큰); 각 복제본에 "이 접두사가 캐시되었습니까?"라고 물어봅니다. 복제본은 블록을 할당하고 제거할 때 KV-cache 이벤트를 pub/sub 채널에 게시합니다. 라우터가 일치하는 복제본을 선택하고, 일치하는 것이 없으면 GPU 利用률 기반 tie-breaker로 떨어집니다.

**vLLM Router** (Rust, 2026 프로덕션 스택): `kv.cache.block_added` 이벤트에 구독하고, prefix-hash → replica 인덱스를 유지하며, O(1) 조회의 라우팅. 일치하는 것이 없을 때 least-queue-depth로 떨어집니다.

**llm-d 라우터**: 동일한 패턴, Kubernetes 네이티브. ControlPlane API를 통해 이벤트를 게시합니다.

**SGLang RadixAttention** (Phase 17 · 06)은 노드 내 배포에 해당합니다. 교차 복제 라우팅은 엄밀히上游입니다.

### 숫자

2K 토큰 프롬프트에서 TTFT P50, Llama 3.3 70B FP8, H100:
- 캐시 적중 (같은 복제본, 접두사 상주): ~80 ms.
- 캐시 미스 (cold prefill): ~800 ms.

10배 격차. 라우터가 복제본 전반에서 접두사 캐시의 60-80%에 hit하면 N-복제본 용량에서 단일 복제본 성능을近似합니다. 10%에 hit하면 순진한 확장을近似합니다.

### 교차 리전에 새로운 제약이 있습니다 — 네트워크 지연 시간

지역 간 RTT:
- us-east-1 ↔ us-west-2: ~65 ms.
- us-east-1 ↔ eu-west-1: ~75 ms.
- us-east-1 ↔ ap-southeast-1: ~220 ms.

라우팅이 요청을 us-east-1에서 ap-southeast-1의 핫 접두사로 보내면, 절감된 prefill (800 → 80 ms)이 440 ms 왕복으로 압도됩니다. GORGO (2026 연구)는 이것을 명시적으로 만듭니다 — prefill만 아닌 `prefill_time + network_latency`를 공동으로 최소화하세요. 종종 답은 prefill이 지배하는 거대한 멀티 MB 접두사를 제외하고는 지역 라우팅을 유지하는 것입니다.

### 상업적 "교차 리전 추론"은 여기서 도움이 되지 않습니다

AWS Bedrock cross-region inference는 용량 압박 시 다른 지역으로 자동으로 요청을 라우팅합니다. 가용성을 최적화하지 TTFT를 최적화하지 않으며 추론을 불투명하게 처리합니다. GKE Multi-Cluster Gateway도 동일합니다 — 서비스 수준 장애 조치, KV 캐시 인식 없음.

여전히 이러한 것을 사용할 때에도 앱 레이어 캐시 인식 라우터가 필요합니다. 그들은 "us-east-1이 불타고 있다" 경우를 처리합니다. 캐시 인식 라우팅은 TTFT 경우를 처리합니다.

### DR 위생 — 32% 누락 파일 문제

널리 인용되는 2026년 통계: LLM DR 실패의 32%가 팀이 가중치를 백업했지만 다음을 잊은場合に 발생합니다:

- `tokenizer.json` 또는 `tokenizer.model`
- 양자화 구성 (`quantize_config.json`, AWQ 스케일, GPTQ 제로포인트)
- 모델 특정 구성 (RoPE 스케일링, 어텐션 마스크, 채팅 템플릿)
- 엔진 구성 (`vllm_config.yaml`, 샘플링 기본값, LoRA 어댑터 manifests)

수정은 3파일 최소 DR manifest입니다:

1. HF 모델 repo의 모든 파일 (가중치 + 구성 + tokenizer).
2. 엔진별 제공 구성.
3. 배포 manifest (K8s YAML, Dockerfile, 종속성 잠금).

plus: 분기별로 DR 드릴을 실행하세요. JPMorgan us-east-1 드릴은 플레이북이 리허설되었기 때문에 2024년 11월 22분 복구를 달성했습니다.

### 데이터 거주지는 별개입니다

EU 고객 PHI는 EU를 벗어날 수 없습니다. 캐시 인식 라우터가 파리에서 온 요청을 us-east-1의 접두사 일치를 위해 보내면 TTFT 이득에 관계없이 GDPR을 위반했습니다. TTFT를 최적화하기 전에 거주지 경계별로 라우터를 분할하세요.

### 기억해야 할 숫자

- 캐시 적중 대 미스 TTFT 격차: 2K 프롬프트에서 ~10배 (80 ms 대 800 ms).
- 지역 간 RTT US-EU: ~75 ms.
- DR 실패: 32%가 tokenizer/quant 구성을 누락했습니다.
- JPMorgan us-east-1 장애 조치 2024년 11월: 22분 (30분 SLA).

## 활용

`code/main.py`는 멀티 리전 작업에서 세 가지 라우팅 전략 (라운드 로빈, 캐시 인식 지역, 캐시 인식 전역)을 시뮬레이션합니다. 캐시 적중율, TTFT P50/P99, 교차 리전 청구서를 보고합니다.

## 결과물

이 레슨은 `outputs/skill-multi-region-router.md`를 산출합니다. 지역, 거주지 제약, SLA가 주어지면 라우팅 계획을 디자인합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 75 ms RTT가 주어지면 교차 지역 라우팅이 로컬 전용 라우팅을 이기는 프롬프트 길이는 어느 것입니까?
2. 캐시 적중율이 70%에서 12%로 떨어집니다. 세 가지 가능한 원인을 진단하고 각각을 확인하는 관찰 가능성을 설명하세요.
3. vLLM에서 5개의 LoRA 어댑터가 있는 70B AWQ 양자화 모델에 대한 DR manifest를 디자인하세요. 모든 파일과 구성을 나열하세요.
4. Bedrock cross-region inference가 엄격한 TTFT SLA가 있는 핀테크에 "충분한"지 주장하세요. specific 동작을 인용하세요.
5. 파리 출처 요청이 us-east-1의 접두사와 일치합니다. 라우팅합니까? 정책을 작성하세요.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| 캐시 인식 라우팅 | "스마트 LB" | KV-cache 보유 복제본으로의 접두사-해시 match에서 라우팅 |
| KV-cache 이벤트 | "캐시 pub-sub" | 복제본이 블록 추가/제거를 게시합니다; 라우터가 인덱싱 |
| 접두사 해시 | "캐시 키" | 라우터 조회를 위해 처음 N 토큰의 해시 |
| GORGO | "교차 지역 라우팅 연구" | arXiv 2602.11688; 명시적 네트워크 지연 시간 항목 |
| 교차 지역 추론 | "Bedrock CRI" | AWS 제품; 가용성 장애 조치, TTFT 인식 없음 |
| DR manifest | "백업 목록" | 복원에 필요한 모든 파일 — 가중치만 아닌 |
| 데이터 거주지 | "GDPR 경계" | 사용자 데이터가 보는 지역에 대한 법적 제약 |
| RTT | "왕복 시간" | 네트워크 지연 시간; US-EU 75 ms, US-APAC 220 ms |
| LLM 인식 LB | "캐시 적중 LB" | 제품 범주로서의 캐시 인식 라우터 |

## 추가 자료

- [BentoML — 멀티 클라우드 및 교차 지역 추론](https://bentoml.com/llm/infrastructure-and-operations/multi-cloud-and-cross-region-inference)
- [arXiv — GORGO (2602.11688)](https://arxiv.org/html/2602.11688v1) — 네트워크 지연 시간 항목을 사용한 교차 지역 KV-cache 재사용.
- [TianPan — 멀티 리전 LLM 서비스 캐시 지역성](https://tianpan.co/blog/2026-04-17-multi-region-llm-serving-data-residency-routing)
- [AWS Bedrock Cross-Region Inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html) — 가용성 장애 조치 문서.
- [vLLM 프로덕션 스택 라우터](https://github.com/vllm-project/production-stack) — 캐시 인식 라우터 소스.