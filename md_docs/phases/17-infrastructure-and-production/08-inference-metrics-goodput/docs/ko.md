# 추론 메트릭 — TTFT, TPOT, ITL, Goodput, P99

> 네 가지 메트릭이 추론 배포가 작동하는지 결정합니다. TTFT는 prefill plus 큐 plus 네트워크입니다. TPOT (ITL과 동등)는 토큰당 메모리 바운드 decode 비용입니다. 종단 간 지연 시간은 TTFT plus TPOT times 출력 길이입니다. 처리량은 플릿 전체에서 초당 토큰입니다. 그러나 제품에 중요한 것은 goodput — 모든 SLO를 동시에 충족한 요청 비율입니다. 낮은 goodput에서 높은 처리량은 제때 사용자에게 도달하지 않는 토큰을 처리하고 있다는 의미입니다. 2026년 TRT-LLM에서 Llama-3.1-8B-Instruct에 대한 참조 숫자: 평균 TTFT 162 ms, 평균 TPOT 7.33 ms, 평균 E2E 1,093 ms. 항상 P50, P90, P99를 보고하세요 — 평균만 아닙니다. 그리고 측정 함정을監視하세요: GenAI-Perf는 ITL 계산에서 TTFT를 제외하고, LLMPerf는 그것을 포함합니다; 두 도구가 동일한 실행에서 TPOT에 대해不同意합니다.

**유형:** 학습
**언어:** Python (stdlib, toy 백분위 수 계산기 및 goodput 리포터)
**선수 과목:** Phase 17 · 04 (vLLM Serving Internals)
**소요 시간:** ~60분

## 학습 목표

- TTFT, TPOT, ITL, E2E, 처리량, goodput을 정확하게 정의하고 각 구성 요소를 측정하는 메트릭의 이름을 붙입니다.
- 평균이 LLM 서비스에 대한 잘못된 통계인 이유를 설명하고 P50/P90/P99를 읽는 방법을 설명합니다.
- SLO 다중 제약 (예: TTFT<500 ms AND TPOT<15 ms AND E2E<2 s)을 구성하고 그것에 대해 goodput을 계산합니다.
- 동일한 실행에서 TPOT에 대해不同意하는 두 가지 벤치마크 도구의 이름을 붙이고 그 이유를 설명합니다.

## 문제

"처리량이 초당 15,000 토큰입니다." 그래서 어떡합니까? 요청의 40%가 2초를 넘었다면 사용자가 세션을 abandoning했습니다. 처리량만으로는 제품이 작동하는지 알 수 없습니다.

추론에는 여러 축의 지연 시간이 있으며 각각이 다르게 실패합니다. Prefill은 계산 바운드이며 프롬프트 길이와 함께 확장됩니다. Decode는 메모리 바운드이며 배치 크기와 함께 확장됩니다. 큐 지연은 운영 문제입니다. 네트워크는 물리적 거리 문제입니다. 각 것에 대해 별도의 메트릭이 필요하며 백분위가 필요하며 사용자가 예상한 것을 얻었는지 сказа하는 단일 composite이 필요합니다 — 그것이 goodput입니다.

## 개념

### TTFT — 첫 번째 토큰까지의 시간

`TTFT = queue_time + network_request + prefill_time`

프롬프트가 길 때 prefill이 지배합니다. H100에서 Llama-3.3-70B FP8에서 32k 프롬프트는 순수한 prefill에 ~800 ms가 걸립니다. 큐 시간은 부하 아래 스케줄러 동작입니다. 네트워크 요청은 TLS를 포함한 와이어 시간입니다. TTFT는 사용자가 아무것도 스트리밍되기 전에 saw는 지연 시간입니다.

### TPOT / ITL — 토큰 간 지연 시간

하나의 수량에 여러 이름. `TPOT` (토큰당 출력 시간), `ITL` (토큰 간 지연 시간), `토큰당 디코딩 지연 시간` — 모두 동일합니다. 첫 번째 후 연속 스트리밍 토큰 사이의 시간입니다.

`TPOT = (decode_forward_time + scheduler_overhead) / tokens_produced`

chunked prefill이 있는 동일한 Llama-3.3-70B H100 스택에서 TPOT 평균 ~7 ms. chunked prefill 없이는 이웃 시퀀스의 긴 prefill 동안 TPOT이 50 ms로 치솟을 수 있습니다. P99를监视하고, 평균이 아닌.

### E2E 지연 시간

`E2E = TTFT + TPOT * output_tokens + network_response`

긴 출력 (>500 토큰)에서 E2E는 TPOT 지배입니다. 긴 프롬프트가 있는 짧은 출력에서 E2E는 TTFT 지배입니다. 출력 길이 조건부 E2E를 보고하세요.

### 처리량

`throughput = total_output_tokens / elapsed_time`

집계 메트릭. 플릿 효율성을 알려줍니다. 개별 요청 헬스를 알려주지 않습니다.

### Goodput — 실제로 신경 쓰는 메트릭

`goodput = (TTFT <= a) AND (TPOT <= b) AND (E2E <= c)를 충족하는 요청 비율`

SLO는 다중 제약입니다. 모든 제약이 유지될 때만 요청이 "좋습니다". Goodput은 비율입니다. 60% goodput에서 높은 처리량은 실패입니다. 99% goodput에서 낮은 처리량이 목표입니다.

2026년 goodput은 MLPerf Inference v6.0 제출과 AI 플랫폼 제공자의 내부 SLA 추적에 사용되는 메트릭입니다.

### 평균이 잘못된 통계인 이유

LLM 지연 시간 분포는 오른쪽으로 치우칩니다. 하나의 긴 prefill 이웃이 있는 decode 배치는 TPOT ~7 ms로 500 토큰을 shipped하고 TPOT ~60 ms로 20 토큰을 shipped할 수 있습니다. 평균 TPOT는 9 ms입니다. P99 TPOT는 65 ms입니다. 사용자는 정기적으로 P99를 hit합니다 — 그것이 그들이 떠나는 이유입니다.

항상 triple (P50, P90, P99)를 보고하세요. 사용자 경험의 경우 P99가 최적화하는 것입니다.

### 참조 숫자 — 2026년 TRT-LLM에서 Llama-3.1-8B-Instruct

- 평균 TTFT: 162 ms
- 평균 TPOT: 7.33 ms
- 평균 E2E: 1,093 ms
- P99 TPOT: chunked-prefill 구성에 따라 10-25 ms 변동.

이것들은 게시된 NVIDIA 참조 지점입니다. 모델 크기 (70B는 3-5배를 보여줌), 하드웨어 (H100 대 B200 ~3배), 부하에 따라 변경됩니다.

### 측정 함정

2026년 가장 사용되는 두 벤치마크 도구가 동일한 실행에서 TPOT에 대해不同意합니다:

- **NVIDIA GenAI-Perf**: ITL 계산에서 TTFT를 제외합니다. ITL은 토큰 2에서 시작합니다.
- **LLMPerf**: TTFT를 포함합니다. ITL은 토큰 1에서 시작합니다.

TTFT 500 ms이고 총 decode에서 100개의 출력 토큰이 700 ms에서 있는 요청의 경우 GenAI-Perf는 `ITL = 700/99 = 7.07 ms`를 보고하고, LLMPerf는 `ITL = 1200/100 = 12.00 ms`를 보고합니다. 도구 선택이 숫자를 변경합니다.

항상 도구 이름을陈述하세요. 항상 정의를 게시하세요.

### SLO 구성

2026년 70B 채팅 모델에 대한 합리적인 소비자 노출 SLO:

- TTFT P99 <= 800 ms.
- TPOT P99 <= 25 ms.
- <300 토큰 출력에 대한 E2E P99 <= 3초.
- Goodput 목표 >= 99%.

기업 SLO는 TTFT (200-400 ms)를加紧하고 E2E를緩めます. 요점은 그것들을 서면으로 작성하고, 세 가지를 모두 측정하고, 단일 composite으로 goodput을 추적하는 것입니다.

### 측정 방법

- 실제 트래픽 또는 현실적인 합성 실행 (평균 입력 토큰 800, 표준 편차 입력 토큰 300, 평균 출력 토큰 150으로 LLMPerf).
- 벤치마크 실행에 대해 피크 동시성의 2배를 목표로 합니다.
- 30-50 iteration 실행, 결합된 샘플의 백분위수 취합니다.
- 도구 이름, 도구 버전, 모델, 하드웨어, 동시성, 프롬프트 분포로 게시합니다.

## 활용

`code/main.py`는 toy goodput 계산기입니다. 합성 지연 시간 분포를 생성하고, SLO를 적용하고, goodput을 계산합니다. 또한 동일한 추적에서 GenAI-Perf 대 LLMPerf TPOT 차이를 보여줍니다.

## 결과물

이 레슨은 `outputs/skill-slo-goodput-gate.md`를 산출합니다. 작업과 SLO가 주어지면 처리량이 아닌 goodput에서 게이트하는 CI/CD 준비 벤치마크 레시피를 산출합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 1% tail 스파이크로 분포를 생성합니다. P99 TPOT을 30 ms에서 15 ms로 tigthening할 때 goodput이 어떻게 변경됨니까?
2. 벤더가 "Llama 3.3 70B H100에서 15,000 tok/s"라고 인용합니다. 신뢰하기 전에 물어볼 세 가지 질문을 이름 짓으세요.
3. chunked prefill이 P99 TPOT을 보호하지만 평균 TPOT을 보호하지 않는 이유는 무엇입니까?
4. 음성 비서 (첫 번째 토큰이 읽혀지는而非 들리는)를 위한 소비자 SLO를 구성하세요. 어떤 메트릭이 사용자에게 가장可视적입니까?
5. LLMPerf README와 GenAI-Perf 문서를 읽으세요. 도구가不同意하는 세 가지 다른 메트릭을 식별하세요.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| TTFT | "첫 번째 토큰까지의 시간" | 큐 + 네트워크 + prefill; 긴 프롬프트에서 prefill이 지배함 |
| TPOT | "토큰당 출력 시간" | 첫 번째 후 토큰당 메모리 바운드 decode 비용 |
| ITL | "토큰 간 지연 시간" | 대부분의 도구에서 TPOT과 동일 (전부는 아님 — GenAI-Perf 참조) |
| E2E | "종단 간" | TTFT + TPOT * output_len; 위에 응답 측면 네트워크 |
| 처리량 | "tok/s" | 플릿 효율성; 지연 시간 백분위 없이는 무용지물 |
| Goodput | "SLO 충족률" | 모든 SLO 제약을 동시에 충족하는 요청 비율 |
| P99 | "tail" | 100 중 1 최악의 지연 시간; 사용자 경험 메트릭 |
| SLO 다중 제약 | "결합" | 세 지연 시간 범위의 AND;任何一个가 위반되면 요청이 실패함 |
| GenAI-Perf 대 LLMPerf | "도구 함정" | ITL에 TTFT를 포함하는지에 대한 도구不同意 |

## 추가 자료

- [NVIDIA NIM — LLM 벤치마킹 메트릭](https://docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html) — TTFT, ITL, TPOT의 정식 정의.
- [Anyscale — LLM 서비스 벤치마킹 메트릭](https://docs.anyscale.com/llm/serving/benchmarking/metrics) — 대체 정의 및 측정 레시피.
- [BentoML — LLM 추론 메트릭](https://bentoml.com/llm/inference-optimization/llm-inference-metrics) — 실제 배포에 적용된 측정.
- [LLMPerf](https://github.com/ray-project/llmperf) — Ray 기반 오픈소스 벤치마크.
- [GenAI-Perf](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/client/src/c++/perf_analyzer/genai-perf/README.html) — NVIDIA의 벤치마크 도구.
- [MLPerf Inference](https://mlcommons.org/benchmarks/inference-datacenter/) — 업계接受的 goodput 기반 벤치마크.