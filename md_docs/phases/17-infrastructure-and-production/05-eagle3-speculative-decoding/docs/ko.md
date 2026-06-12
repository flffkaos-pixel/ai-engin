# 프로덕션의 EAGLE-3 스펙큘러티브 디코딩

> 스펙큘러티브 디코딩은 빠른 draft 모델과 대상 모델을 페어로 묶습니다. Draft가 K 토큰을 제안합니다; 대상이 하나의 포워드에서 검증합니다; 수락된 토큰은 무료입니다. 2026년 EAGLE-3이 프로덕션 등급 변형입니다 — 대상 모델의 숨겨진 상태에서 draft 헤드를 훈련하여 일반 채팅에서 acceptance rate alpha를 0.6-0.8 대역으로 밀어냅니다. 올바른 질문은 "draft가 얼마나 빠른가"가 아니라 "내 트래픽에서 alpha가 무엇인가"입니다. Alpha가 ~0.55 아래로 떨어지면 모든 거부된 draft가 두 번째 대상 포워드 패스를 cost하므로 높은 동시성에서 스펙큘러티브 디코딩이 순 부정입니다. 이 레슨은 먼저 alpha를 측정하고 두 번째로 플래그를 뒤집도록 가르칩니다.

**유형:** 학습
**언어:** Python (stdlib, toy acceptance-rate 시뮬레이터)
**선수 과목:** Phase 17 · 04 (vLLM Serving Internals), Phase 10 · 18 (Multi-Token Prediction)
**소요 시간:** ~60분

## 학습 목표

- 스펙큘러티브 디코딩의 세 세대를 이름 짓고 EAGLE-3이 EAGLE-2와 클래식 draft 모델에서 무엇을 변경하는지 설명합니다.
- Acceptance rate alpha를 정의하고 alpha와 K (draft 길이)에서 예상되는 스피드업을 계산하며 대상 동시성에 대한 균형 alpha를 식별합니다.
- 스펙큘러티브 디코딩이 vLLM 2026에서 opt-in (기본값 아님)인 이유와 alpha를 측정하지 않고 켜는 것이 프로덕션 안티패턴인 이유를 설명합니다.
- 측정 계획을 작성합니다: 벤치마크, 프롬프트 분포, 동시성 지점, 게이트할 메트릭.

## 문제

Decode는 메모리 바운드입니다. H100에서 Llama 3.3 70B FP8을 실행할 때 각 디코딩된 토큰은 ~140 GB/s의 가중치를 읽고 하나의 토큰을 방출합니다. GPU 계산은 decode 동안 거의 유휴합니다 — 병목은 HBM 대역폭이지 행렬곱 처리량이 아닙니다.

스펙큘러티브 디코딩은 그 간격을 이용합니다. 저렴한 draft 모델로 K개의 후보 토큰을 생성한 다음 대상 모델에게 하나의 포워드 패스에서 K개를 모두 검증하도록 요청합니다. 각 검증된 토큰은 효과적으로 무료입니다 (대상이 어쨌든 해야 했던 K-포워드의 배치에 분산됩니다).

클래식 draft 모델 접근 방식은 같은 제품군의 더 작은 모델을 사용합니다 (Llama 3.2 1B가 Llama 3.3 70B를 draft). 작동하지만 acceptance rate가 평범합니다 — 더 작은 모델 분포가 대상에서 벗어납니다. EAGLE, then EAGLE-2, then EAGLE-3는 대상 모델의 내부 상태에서 직접 가벼운 draft 헤드를 훈련하여 draft의 분포가 대상을 훨씬 더 밀접하게 추적합니다. 그것이 alpha가 draft 모델의 0.4에서 EAGLE-3의 0.6-0.8으로가는 이유입니다.

단점: EAGLE-3는 vLLM 2026에서 opt-in입니다. `speculative_config`를 명시적으로 설정해야 합니다. 플래그 없음, 가속 없음. 실제 트래픽에서 alpha를 측정하지 않고 켜는 팀은 종종 tail 지연이 더 나빠지는 것을 saw습니다, 더 나쁘지 않습니다.

## 개념

### 스펙큘러티브 디코딩이 실제로 사는 것

스펙 디코딩 없이는 토큰당 비용이 하나의 대상 포워드입니다. Draft 길이 K와 acceptance alpha에서 스펙 디코딩으로 예상되는 토큰당 대상 포워드는 `1 + K * alpha`입니다. 스피드업은 `(1 + K * alpha) / (1 + epsilon)`이며 epsilon은 draft-plus-verify 오버헤드입니다. K=5, alpha=0.7: `(1 + 5*0.7) / (1 + 0.1) = 4.5 / 1.1 = 4.1x`. 실제 숫자는 alpha가 프로덕션 트래픽에서 거의 그만큼 높지 않고 epsilon이 높은 배치 크기에서 증가하기 때문에 2-3x 주위에 모입니다.

### alpha가 유일하게 중요한 메트릭인 이유

거부된 토큰은 사라지지 않습니다 —它们는 첫 번째 거부된 토큰에 대해 두 번째 대상 포워드를 강제합니다. Alpha가 0.4로 떨어지는 작업에서 draft 오버헤드 plus 검증 plus 재실행에 지불합니다. 높은 동시성 (256 동시라고 말하면)에서는 decode 배치가 이미 충분히 커서 "대상 alone"과 "대상 plus 검증" 사이의 메모리 대역폭 격차가 줄어듭니다. 대부분의 2026년 하드웨어에서 alpha 0.55 아래에서 스펙 디코딩은 순 부정입니다.

Alpha는 작업에 따라 다릅니다. ShareGPT 스타일 일반 채팅에서 ShareGPT에서 훈련된 EAGLE-3는 0.6-0.8을 hits합니다. 도메인 특정 트래픽 (코드, 의료, 법률)에서 일반 데이터에서 훈련된 draft 헤드는 0.4-0.6으로 떨어집니다. 도메인 특정 EAGLE-3 draft를 훈련하면 alpha를 회복합니다 — 대상 finetuning에 비해 가볍고 빠른 훈련 작업입니다.

### 한눈에 보는 EAGLE 세대

- **클래식 draft 모델**: 같은 제품군의 작은 모델. Alpha 0.3-0.5. 인프라 간단 — 두 모델 로드, draft가 대상 포워드당 K 포워드를 실행합니다.
- **EAGLE-1 (2024)**: 대상 숨겨진 상태 (마지막 레이어)에서 훈련된 단일 draft 헤드. Alpha ~0.5-0.6. 대상之上的 작은 매개변수 오버헤드.
- **EAGLE-2 (2025)**: 적응형 draft 길이 및 트리 기반 drafts (하나의 대상 패스에서 여러 분기 검증). Alpha ~0.6-0.7. 더 복잡한 draft 스케줄러.
- **EAGLE-3 (2025-2026)**: 여러 대상 레이어 (마지막만 bukan)에서 훈련된 draft 헤드, 더 나은 정렬. 일반 채팅에서 Alpha ~0.6-0.8.

### 2026년 프로덕션 레시피

1. 대상 모델을 그대로 배송합니다. 대상 동시성에서 기본 TTFT, ITL, 처리량을 측정합니다.
2. vLLM `speculative_config`를 통해 EAGLE-3 draft를 활성화합니다. 벤치마크를 다시 실행합니다.
3. Acceptance rate alpha를 로그합니다. vLLM V1은 이것을 `spec_decode_metrics.accepted_tokens_per_request`로 보고합니다. alpha를 얻으려면 요청된 draft 길이로 나눕니다.
4. 프로덕션 트래픽 분포에서 alpha < 0.55이면 스펙 디코딩을 비활성화하거나 도메인 특정 EAGLE-3 draft를 훈련합니다.
5. 프로덕션 동시성에서 다시 실행합니다. P99 ITL이 더 나빠지지 않았음을 확인합니다.

### 프로덕션 함정: P99 tail

평균 ITL은 스펙 디코딩으로 떨어집니다. 튜닝하지 않으면 P99가 더 나빠질 수 있습니다. 거부된 drafts는 2패스 시퀀스를 트리거합니다 (draft + verify-fail + 재실행). 전체 배치에서 those 두 패스가 직렬화됩니다. P50이 아닌 P99 ITL을监视하세요.

### EAGLE-3가 이미 배포된 곳

Google은 2025년 AI Overviews에 스펙큘러티브 디코딩을 배포했습니다 (동일한 품질, 더 빠른 응답). vLLM V1은 문서화된 인터페이스로 `speculative_config`를 배송합니다; V1의 N-gram GPU 스펙큘러티브 디코딩은 chunked prefill과 호환되는 변형입니다. SGLang은 접두사 무거운 작업에 권장되는 draft 경로로 EAGLE-3를 지원합니다.

### 한 줄의 균형 수학

예상 스피드업: `S(alpha, K) = (1 + K*alpha) / (1 + verify_overhead)`. `S = 1`로 설정하면 alpha를求解합니다: `alpha_breakeven = verify_overhead / K`. 일반적인 verify_overhead ~0.15 및 K=5의 경우: `alpha_breakeven = 0.03`. 그러나 그것은 원시 decode 수학입니다. 높은 동시성에서 verify 오버헤드가 증가하고 decode 배치가 이미 시퀀스 전반에 걸쳐 메모리 읽기를 상각하므로 실효 alpha_breakeven이 실제로 ~0.45-0.55로攀升합니다.

### 스펙큘러티브 디코딩을 사용하지 말 때

- 지연 시간이 중요하지 않은 배치-1 오프라인 생성. 일반 대상을 사용하세요.
- 매우 짧은 출력 (50 토큰 미만). Draft 오버헤드와 검증 비용이 지배합니다.
- 도메인 훈련 draft 헤드 없이 특수화된 도메인. Alpha 너무 낮습니다.
- vLLM v0.18.0 plus draft 모델 스펙 디코딩 plus `--enable-chunked-prefill`. 이 조합은 컴파일되지 않습니다. 문서화된 예외는 V1의 N-gram GPU 스펙 디코딩입니다.

## 활용

`code/main.py`는 다양한 alpha 값과 draft 길이 K에서 스펙큘러티브 디코딩과 without를 시뮬레이션합니다. 균형 alpha, 측정된 스피드업, tail 동작을 인쇄합니다. 여러 (alpha, K) 조합에서 실행하여 스펙큘러티브 디코딩이 멈추는 곳을 정확히 확인하세요.

## 결과물

이 레슨은 `outputs/skill-eagle3-rollout.md`를 산출합니다. 대상 모델, 트래픽 분포 설명, 동시성 대상이 주어지면 단계적 EAGLE-3 rollout 계획을 산출합니다 — 기본값 벤치마크, enable 구성, alpha 측정, alpha >= 0.55에서 게이트, P99 ITL監視.

## 연습문제

1. `code/main.py`를 실행하세요. K=5에서 2x 스피드업을 위해 어떤 alpha가 필요합니까? 3x를 위해? 그것이 verify_overhead에 얼마나 민감합니까?
2. 프로덕션 트래픽이 70% 일반 채팅, 30% 코드로 분할된다고 상상하세요. 일반 채팅은 ShareGPT에서 훈련된 EAGLE-3로 alpha 0.7에 도달합니다; 코드는 alpha 0.4에 도달합니다. 혼합 alpha가 무엇이며 스펙 디코딩이 순肯定적입니까?
3. vLLM `speculative_config` 문서를 읽으세요. 세 가지 모드 (draft 모델, EAGLE, N-gram)의 이름을 지정하고 chunked prefill과 호환되는 것을 指定하세요.
4. EAGLE-3 활성화 후 평균 ITL이 25% 감소했지만 P99 ITL이 15% 증가한 것을 saw습니다. 진단하고 완화를 제안하세요.
5. Llama 3.3 70B에 대한 EAGLE-3 draft 헤드의 메모리 비용을 계산하세요. 클래식 draft로 Llama 3.2 1B를 실행하는 것과 어떻게 비교합니까?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| 스펙큘러티브 디코딩 | "draft plus verify" | 저렴한 모델로 K 토큰을 제안, 하나의 대상 포워드에서 K 모두 검증 |
| Acceptance rate alpha | "spec accept rate" | 대상이 수락한 draft 토큰 비율; 유일하게 중요한 메트릭 |
| Draft 길이 K | "spec k" | 대상 포워드당 draft가 제안하는 토큰 수; 일반적 4-8 |
| Verify 오버헤드 epsilon | "spec overhead" | 일반 대상 포워드 대비 검증-재실행의 추가 비용; 배치와 함께 증가 |
| EAGLE-3 | "최신 EAGLE" | 2025-2026년 변형; 여러 대상 레이어에서 draft 헤드를 훈련; 일반 채팅에서 alpha 0.6-0.8 |
| `speculative_config` | "vLLM spec config" | vLLM V1의 명시적 opt-in; 기본값 없음意味着 없음 가속 |
| N-gram spec decode | "N-gram draft" | 프롬프트에서 N-gram 조회를 사용하는 GPU 측 draft; chunked-prefill 호환 |
| 균형 alpha | "no-op alpha" | 스펙 디코딩이零 스피드업을 제공하는 alpha; 프로덕션 동시성에서 이것을監視하세요 |
| 거부-draft 2패스 | "재실행 비용" | draft가 거부될 때 두 개의 대상 포워드; P99 tail을 주도함 |

## 추가 자료

- [vLLM — Speculative Decoding docs](https://docs.vllm.ai/en/latest/features/spec_decode/) — `speculative_config` 및 V1의 chunked-prefill 호환성에 대한 공식 출처.
- [vLLM Speculative Config API](https://docs.vllm.ai/en/latest/api/vllm/config/speculative/) — 정확한 필드 세트.
- [EAGLE 논문 (arXiv:2401.15077)](https://arxiv.org/abs/2401.15077) — 원래 EAGLE draft-헤드 공식.
- [EAGLE-2 논문 (arXiv:2406.16858)](https://arxiv.org/abs/2406.16858) — 적응형 drafts 및 트리.
- [UC Berkeley EECS-2025-224](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2025/EECS-2025-224.html) — 스펙큘러티브 디코딩을 갖춘 효율적인 LLM 시스템.
- [BentoML — 스펙큘러티브 디코딩](https://bentoml.com/llm/inference-optimization/speculative-decoding) — 프로덕션 rollout 체크리스트.