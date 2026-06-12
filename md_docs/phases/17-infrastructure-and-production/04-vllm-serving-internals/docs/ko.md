# vLLM 제공 내부: PagedAttention, Continuous Batching, Chunked Prefill

> 2026년 vLLM의 지배는 세 가지 복합 기본값, 하나의 트릭이 아닙니다. PagedAttention은 항상 켜져 있습니다. Continuous batching은 디코딩 반복 사이에 활성 배치에 새 요청을 주입합니다. Chunked prefill은 긴 프롬프트를 슬라이스하여 디코딩 토큰이 결코 굶주리지 않도록 합니다. 세 가지를 모두 켜고 H100 SXM5 하나에서 Llama 3.3 70B FP8은 128 동시에서 2,200-2,400 tok/s를 밀어냅니다 — vLLM 자체 기본값보다 약 25% 높고 순진한 PyTorch 루프보다 3-4배 높습니다. 이 레슨은 다이어그램을 그릴 수 있는 수준으로 스케줄러와 어텐션 커널을 읽고, vLLM이 그렇게 하는 방식으로 prefill과 decode를 스케줄하는 toy continuous batcher가 있는 `code/main.py`에서 끝납니다.

**유형:** 학습
**언어:** Python (stdlib, toy continuous batching 스케줄러)
**선수 과목:** Phase 17 · 01 (Model Serving), Phase 11 (LLM Engineering)
**소요 시간:** ~75분

## 학습 목표

- PagedAttention을 KV 캐시 할당자로 설명합니다: 블록, 블록 테이블, 프로덕션 부하에서 분열이 4% 미만에 유지되는 이유.
- 반복 수준에서 continuous batching을 다이어그램으로 그립니다: 완료된 시퀀스가 배치를 어떻게 떠나고 새로운 것이 배수를 소진하지 않고 어떻게 합류하는지.
- chunked prefill을 한 문장으로 설명하고 어떤 지연 시간 메트릭을 보호하는지 이름 짓습니다 (힌트: TTFT tail이지 평균 처리량이 아닙니다).
- 한 번에 모든 최적화를 활성화하는 2026년 vLLM v0.18.0 함정의 이름을 붙입니다.

## 문제

순진한 PyTorch 서비스 루프는一度에 하나의 요청을 실행합니다: 토큰화, prefill, decode until EOS, 반환. 한 사용자에서 이것이 작동합니다. 백 명에서, 그것은 참을성 있는 사람들의 대기열입니다. 명확한 수정 — 정적 batching — 창에서 가장 긴 프롬프트로 모든 요청을 패드하고, 가장 긴 예상 출력으로 모든 decode를 패드하고, 가장 느린 시퀀스에서 전체 배치를 정지합니다. 사용하지 않는 패드에 지불하고, 빠른 요청이 느린 요청을 기다립니다.

vLLM은 세 가지 문제를 한 번에 해결합니다. PagedAttention은 클래식 연속 할당이 그렇게 하는 것처럼 KV 캐시 분열이 GPU 메모리의 60-80%를 먹는 것을 방지합니다. Continuous batching을 사용하면 요청이 각 디코딩 반복 사이에 배치를 결합하고 떠날 수 있으므로 배치는 항상 실제 작업으로 가득 차 있습니다. Chunked prefill은 긴 프롬프트를 ~512 토큰 슬라이스로 분할하여 디코딩과 interleaves하므로 긴 프롬프트가 GPU에서 모든 다른 디코딩 토큰을 freezing하지 않습니다.

2026년 프로덕션 기본값은 세 가지 모두 켜는 것입니다. 각 것이 하는 것을 이해해야 합니다, 왜냐하면 실패 모드는 모델이 아니라 스케줄러에 있기 때문입니다.

## 개념

### 가상 메모리 시스템としての PagedAttention

KV 캐시는 시퀀스당 `num_layers × 2 × num_heads × head_dim × seq_len × bytes_per_element`입니다. 8192 토큰에서 Llama 3.3 70B의 경우 BF16에서 시퀀스당 약 1.25 GB입니다. 모든 요청에 8192 슬롯을 사전 예약하지만 평균 요청이 1500 토큰만 사용하면 예약한 HBM의 약 82%를浪费합니다. 클래식 배칭은 이浪费를 지불합니다.

PagedAttention은 OS 가상 메모리에서 개념을 차용합니다. KV 캐시는 시퀀스별로 연속적이지 않습니다. 고정 크기 블록 (기본값 16 토큰)으로 할당됩니다. 각 시퀀스에는 논리적 토큰 위치를 물리적 블록 ID에 매핑하는 블록 테이블이 있습니다. 시퀀스가 할당된 블록을 넘어 성장하면 하나의 블록이 추가됩니다. 완료되면 블록이 풀로 돌아갑니다.

분열이 클래식의 60-80%에서 PagedAttention의 4% 미대로 떨어집니다. 플래그로 PagedAttention을 활성화하지 않습니다 — vLLM이 배송하는 유일한 할당자입니다. 노브는 `--gpu-memory-utilization` (기본값 0.9)으로, 가중치와 activations를 로드한 후 KV 블록에 예약할 HBM 양을 vLLM에 알려줍니다.

### 반복 수준에서의 Continuous Batching

오래된 "dynamic batching"은 배치를 채우기 위해 창 (예: 10 ms)을 기다린 다음 모든 시퀀스가 완료될 때까지 prefill + decode + decode + decode를 실행했습니다. 빠른 시퀀스가 일찍 떠나서 GPU가 느린 ones을Finished하는 동안 유휴 상태로 앉았습니다.

Continuous batching은 각 디코딩 단계마다 operating합니다. 실행 중인 시퀀스 세트를 `RUNNING` 목록이라고 부릅니다. 각 반복에서:

1. `RUNNING`에서 방금 EOS 또는 max_tokens에 도달한 시퀀스가 제거됩니다.
2. 스케줄러가 대기 큐를 봅니다. 빈 KV 블록이 있으면 새 시퀀스를 admitted합니다 (prefill 또는 재개된).
3. Forward pass가 `RUNNING`에 있는 무엇이든 실행되어 시퀀스당 하나의 새로운 토큰을.emit합니다.

배치 크기는 결코 고정 수로 패드되지 않습니다. 출력의 다른 위치에 있는 시퀀스가 하나의 fused forward를 공유합니다. 2026년 vLLM에서 이것은 `V1 스케줄러`라고 합니다. 주요 불변성: 스케줄러가 요청당 한 번이 아니라 디코딩 반복당 한 번 실행됩니다.

### Chunked Prefill이 TTFT tail을 보호합니다

Prefill은 계산 바운드입니다. 하나의 H100에서 Llama 3.3 70B에 대한 32k 토큰 프롬프트는 순수한 prefill에 ~800 ms가 걸립니다. Prefill이 실행되는 동안 배치의 모든 다른 시퀀스에 대해 디코딩 토큰이 기다립니다. 서비스 루프에서 하나의 긴 프롬프트의 첫 번째 토큰 지연 시간 (TTFT)은 다른 수십 명의 사용자에 대해 토큰 간 지연 시간 (ITL) blip이 됩니다.

Chunked prefill은 prefill을 고정 크기 청크 (기본값 512 토큰)로 분할하고 각 청크를 단위로 예약합니다. 청크 사이에서 스케줄러는 decode 시퀀스를 하나의 토큰으로 진행할 수 있습니다. 작은 절대 prefill 지연 시간 히트 (청크당 몇 ms)를 희생하여 훨씬 낮은 디코딩 시간 지터를 교환합니다. 게시된 벤치마크에서 혼합 부하에서 P99 ITL이 ~50 ms에서 ~15 ms로 떨어집니다.

### 세 가지 기본값이 상호 작용합니다

세 가지 기능이 서로를 가정합니다. PagedAttention은 스케줄러가 거래할 세분화된 KV 리소스를 제공합니다. Continuous batching은 새 시퀀스를 admittedすることが全局 reshuffle을 강제하지 않도록 그 세분화된 리소스가 필요합니다. Chunked prefill은 스케줄러가 같은 `RUNNING` 목록에서 만드는 결정입니다 — 별도의 시스템이 아니라 하나의 더 많은 스케줄러 정책입니다.

모든 플래그를 알 필요는 없습니다. 스케줄러가 최적화하는 것을 알아야 합니다: KV 블록 예산에서 좋은 처리량, chunked prefill 슬라이싱의 대상입니다.

### 2026년 v0.18.0 함정

vLLM v0.18.0에서 `--enable-chunked-prefill`을 draft 모델 스펙culative 디코딩 (`--speculative-model`)과 결합할 수 없습니다. 문서화된 예외는 V1 스케줄러의 N-gram GPU 스펙culative 디코딩입니다. 모든 플래그를 읽지 않고 켜는 팀은 부드러운 회귀가 아닌 시작 시 런타임 오류를 얻습니다. 스펙culative 이득이 chunked prefill을 활성화할 가치가 있었다면, 다시 확인하세요 — 2026년의 정답은 종종 chunked prefill 없이 EAGLE-3이며, 결합되지 않는 draft 모델 plus chunked prefill이 아닙니다.

### 기억해야 할 숫자

- Llama 3.3 70B FP8, H100 SXM5, 128 동시, 세 가지 모두 켜짐: 2,200-2,400 tok/s.
- 동일한 모델, 기본 vLLM (chunked prefill 없음): ~1,800 tok/s.
- 동일한 모델, 순진한 PyTorch forward 루프: ~600 tok/s.
- 프로덕션 부하에서 PagedAttention의 KV 분열浪费: <4%.
- 혼합 부하에서 P99 ITL: chunked prefill으로 ~15 ms, 없이 ~50 ms.

### 스케줄러 모양

```
while True:
    finished = [s for s in RUNNING if s.is_done()]
    for s in finished: release_blocks(s); RUNNING.remove(s)

    while WAITING and have_free_blocks_for(WAITING[0]):
        s = WAITING.pop(0)
        allocate_initial_blocks(s)
        RUNNING.append(s)

    # schedule prefill chunks + decode in one batch
    batch = []
    for s in RUNNING:
        if s.in_prefill:
            batch.append(next_prefill_chunk(s))   # e.g. 512 tokens
        else:
            batch.append(decode_one_token(s))     # 1 token

    run_forward(batch)                            # one fused GPU call
```

`code/main.py`는 정확한 이 루프를 가짜 토큰 수와 가짜 forward 지연으로 stdlib Python에서 구현합니다. 실행하면 chunked prefill이 긴 prefill 동안 decode 시퀀스를 생존시키는 방법을 보여줍니다.

## 활용

`code/main.py`는 토글 가능한 기능으로 vLLM 스타일 스케줄러를 시뮬레이션합니다. 실행하여 다음을 확인하세요:

- `NAIVE` 모드: 한 번에 하나의 요청, 배칭 없음.
- `STATIC` 모드: 패드 및 대기, 클래식 배칭.
- `CONTINUOUS` 모드: 반복 수준 admitting 및 releasing.
- `CONTINUOUS + CHUNKED` 모드: decode와 interleaved prefill 슬라이스.

출력은 총 처리량 (가상 초당 토큰), TTFT 평균, P99 ITL을 보여줍니다. `CONTINUOUS + CHUNKED` 행이 혼합 트래픽에서 지배해야 합니다.

## 결과물

이 레슨은 `outputs/skill-vllm-scheduler-reader.md`를 산출합니다. 제공 구성 (배치 크기, KV 메모리 利用률, chunked prefill 크기, 스펙culative 구성)이 주어지면 세 가지 기본값 중哪一个가 병목인지 이름짓고 튜닝할 것을 권장하는 스케줄러 진단을 산출합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 짧고 긴 요청이 혼합된 작업에서 `STATIC`을 `CONTINUOUS`와 비교하세요. 처리량 격차가 어디서 오는지 — prefill 효율, decode 효율, tail 지연 시간?
2. `--max-num-batched-tokens`를 추가하도록 toy 스케줄러를 수정하세요. H100에서 Llama 3.3 70B FP8을 실행하는 데 올바른 값은 무엇입니까? (힌트:它是 KV 블록 크기 및 빈 블록 수의 함수이지 raw HBM이 아닙니다.)
3. vLLM v0.18.0 릴리스 노트를 다시 읽으세요. 어떤 플래그 조합이 상호 배타적입니까? 나열하세요.
4. 평균 1,500 출력 토큰, 표준 600 토큰인 1,000개 요청의 추적에서 8192 최대에서 연속적인 요청당 할당과 (b) 16 토큰 블록의 PagedAttention에서 KV 캐시 분열浪费를 계산하세요.
5. 한 문장으로 chunked prefill이 P99 ITL을 돕지만 고유하게 처리량이 아닌 이유를 설명하세요. 실제로 처리량 이득이 어디서 오는지 설명하세요.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| PagedAttention | "KV 트릭" | KV 캐시용 고정 크기 블록 할당자; 분열 <4% |
| 블록 테이블 | "페이지 테이블" | 논리적 토큰 위치에서 물리적 KV 블록으로의 시퀀스별 맵 |
| Continuous Batching | "올바른 dynamic batching" | 디코딩 반복마다 made admitting/releasing 결정 |
| Chunked Prefill | "prefill 분할" | 디코딩과 interleaved 512 토큰 슬라이스로 긴 prefill 분할 |
| TTFT | "첫 번째 토큰 시간" | Prefill + 큐 + 네트워크; 긴 프롬프트에서 prefill이 지배함 |
| ITL | "토큰 간 지연 시간" | 연속 디코딩 토큰 사이의 시간; 배치 크기가 지배함 |
| Goodput | "SLO를 충족하는 처리량" | 모든 요청이 여전히 TTFT 및 ITL 목표에 도달한 토큰/초 |
| V1 스케줄러 | "새 스케줄러" | vLLM의 2026년 스케줄러; N-gram spec decode는 chunked-prefill 호환 경로입니다 |
| `--gpu-memory-utilization` | "메모리 노브" | 가중치 및 activations 후 KV 블록에 예약된 HBM 비율 |

## 추가 자료

- [vLLM documentation — Speculative Decoding](https://docs.vllm.ai/en/latest/features/spec_decode/) — chunked-prefill 및 speculative-decoding 호환성에 대한 공식 출처.
- [vLLM Release Notes (NVIDIA)](https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/index.html) — 2026년 릴리스 주기 및 버전 특정 동작.
- [vLLM Blog — PagedAttention](https://blog.vllm.ai/2023/06/20/vllm.html) — 할당자에 대해 생각하는 방법을 여전히 정의하는 원래 작성.
- [PagedAttention 논문 (arXiv:2309.06180)](https://arxiv.org/abs/2309.06180) — 분열 분석 및 스케줄러 디자인.
- [Aleksa Gordic — Inside vLLM](https://www.aleksagordic.com/blog/vllm) — 플레임 그래프로 상세한 V1 스케줄러 walkthrough.