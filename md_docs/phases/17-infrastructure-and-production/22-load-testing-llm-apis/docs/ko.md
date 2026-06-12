# LLM API 부하 테스트 — k6와 Locust가 거짓말하는 이유

> 전통적인 부하 테스터는 스트리밍 응답, 가변 출력 길이, 토큰 수준 메트릭 또는 GPU 포화를 위해 설계되지 않았습니다. 대부분의 팀이 빠지는 두 가지 함정. GIL 함정: Locust의 토큰 수준 측정은 무거운 동시성에서 요청 생성과 경쟁하는 Python GIL 아래에서 토큰화를 실행합니다; 토큰화 백로그가 then reported 토큰 간 지연 시간을膨胀 — 고객이 병목이며 서버가 아닙니다. 프롬프트 균일성 함정: 루프의 동일한 프롬프트는 토큰 분포의 한 지점만 테스트합니다; 실제 트래픽은 가변 길이 및 다양한 접두사 일치를 가집니다. LLMPerf는 `--mean-input-tokens` + `--stddev-input-tokens`로 이를 수정합니다. 2026년 도구 매핑: LLM 전문화 (GenAI-Perf, LLMPerf, LLM-Locust, guidellm) — 토큰 수준 정확도; **k6 v2026.1.0** + **k6 Operator 1.0 GA (2025년 9월)** — 스트리밍 인식, TestRun/PrivateLoadZone CRD를 통한 Kubernetes 네이티브 분산, CI/CD 게이트에 최적; Vegeta — Go 상수 속도 포화; Locust 2.43.3은 스트리밍용 LLM-Locust 확장 없이는 only. 부하 패턴: 정상 상태, 램프, 스파이크 (오토스케일링 테스트), 소크 (메모리 누수).

**유형:** 빌드
**언어:** Python (stdlib, toy 현실적 프롬프트 생성기 + 지연 시간 수집기)
**선수 과목:** Phase 17 · 08 (추론 메트릭), Phase 17 · 03 (GPU 오토스케일링)
**소요 시간:** ~75분

## 학습 목표

- 일반 부하 테스터가 LLM API에 대해 거짓말하는 두 가지 안티패턴 (GIL 함정, 프롬프트 균일성 함정)을 설명합니다.
- 주어진 목적에 대한 도구를 선택합니다: LLMPerf (벤치마크 실행), k6 + 스트리밍 확장 (CI 게이트), guidellm (대규모 합성), GenAI-Perf (NVIDIA 참조).
- 네 가지 부하 패턴 (정상, 램프, 스파이크, 소크)을 설계하고 각각이 catches하는 실패 모드를 이름 짓습니다.
- 고정 길이 대신 입력 토큰의 평균 + 표준 편차를 사용하여 현실적인 프롬프트 분포를 구축합니다.

## 문제

500명의 동시 사용자로 LLM 엔드포인트를 k6 테스트했습니다. 버텄습니다. shipping했습니다. 프로덕션에서 200명의 실제 사용자에게 서비스가 멈춥니다 — P99 TTFT이 폭발하고, GPU가 pinned됩니다.

두 가지 일이 발생했습니다. 첫째, k6가 500개의 동일한 프롬프트를 보냈습니다 — 요청 병합 및 접두사 캐싱으로 인해 500개의 동시 디코드를 처리하는 것처럼 보였지만 실제로는 하나를 처리하고 있었습니다. 둘째, k6는 스트리밍 응답에서 토큰 간 지연 시간을 사용자가 경험하는 방식대로 추적하지 않습니다; 하나의 HTTP 연결을 보지, 다양한 간격으로 도착하는 500개의 토큰을 보지 않습니다.

LLM의 부하 테스트는 그 자체의 дис플리너입니다.

## 개념

### GIL 함정 (Locust)

Locust는 Python을 사용하고 GIL 아래에서 클라이언트 측 토큰화를 실행합니다. 높은 동시성에서 토큰화가 요청 생성 뒤에 대기합니다. 보고된 토큰 간 지연 시간에는 클라이언트 측 토큰화 백로그가 포함됩니다. 서버가 느리다고 생각합니다; 테스트 하네스가 그것입니다.

수정: LLM-Locust 확장이 토큰화를 별도의 프로세스로 이동하거나, 컴파일된 언어 하네스 (k6, tokenizers.rs를 사용하는 LLMPerf)를 사용합니다.

### 프롬프트 균일성 함정

모든 알려진 부하 테스터가 하나의 프롬프트를 구성하도록 허용합니다. 10,000 iterations의 루프 테스트에서 동일한 프롬프트가 매번 전송됩니다. 서버가 매번 동일한 접두사를 saw — 접두사 캐시 히트가 100%에 접근하고, 처리량이 훌륭해 보입니다.

수정: 프롬프트 분포에서 샘플링합니다. LLMPerf는 `--mean-input-tokens 500 --stddev-input-tokens 150`을 사용합니다 — 다양한 길이, 다양한 콘텐츠.

### 네 가지 부하 패턴

1. **정상 상태** — 30-60분 동안 일정한 RPS. 포착: 기준 성능 회귀.
2. **램프** — 15분 동안 0에서 목표까지 선형적으로 RPS를 증가시킵니다. 포착: 용량 분기점, 워밍업 이상.
3. **스파이크** — 2분 동안 갑자기 3-10x RPS를 했다가 돌아옵니다. 포착: 오토스케일링 지연, 대기열 포화, 콜드 스타트 영향.
4. **소크** — 4-8시간 동안 정상 상태. 포착: 메모리 누수, 연결 풀 드리프트, 관찰 가능성 오버플로.

### 2026 도구 매핑

**LLMPerf** (Anyscale) — Python이지만 Rust 백엔드 토큰화. 평균/표준 편차 프롬프트. 스트리밍 인식. 성능 실행의 최선의 기본값.

**NVIDIA GenAI-Perf** — NVIDIA의 참조. Triton 클라이언트 사용; 포괄적인 메트릭 적용 범위. 주의: ITL이 TTFT를 제외함; LLMPerf의 것은 포함함. 두 도구가 동일한 서버에서 다른 TPOT을 생성합니다.

**LLM-Locust** (TrueFoundry) — GIL 함정을 수정하는 Locust 확장. 익숙한 Locust DSL + 스트리밍 메트릭.

**guidellm** — 대규모 합성 벤치마킹.

**k6 v2026.1.0** + **k6 Operator 1.0 GA (2025년 9월)**:
- k6 자체 (Go, 컴파일됨, GIL 없음)가 스트리밍 인식 메트릭을 추가했습니다.
- k6 Operator는 Kubernetes 네이티브 분산 테스트를 위한 TestRun / PrivateLoadZone CRD를 사용합니다.
- CI/CD 게이트 및 SLA 테스트에 최적.

**Vegeta** — Go, k6보다 간단합니다. 상수 속도 HTTP 포화. LLM 인식은 아니지만 게이트웨이 / 비율 제한 테스트에 적합합니다.

**Locust 2.43.3 스톡** — LLM에 대해 GIL 함정이 있습니다. LLM-Locust 확장만 해당.

### CI의 SLA 게이트

PR에서 k6 실행:

- 기준 RPS에서 30-50 iterations.
- 게이트: P50/P95 TTFT, 5xx < 5%, 임계값 이하의 TPOT.
- 위반 시 빌드를 중단합니다.

### 현실적인 프롬프트 분포

실제 트래픽 샘플에서 구축 (있는 경우) 또는 게시된 분포에서 (예: 채팅용 ShareGPT 프롬프트, 코드용 HumanEval). 평균 + stddev를 LLMPerf에 제공합니다. 어떤 경우든 하나의 프롬프트로 루프하지 마세요.

### 기억해야 할 숫자

- k6 Operator 1.0 GA: 2025년 9월.
- k6 v2026.1.0: 스트리밍 인식 메트릭.
- 일반적인 LLMPerf 실행: 동시성 X에서 100-1000개 요청.
- 일반적인 CI 게이트: PR당 30-50 iterations.
- 네 가지 패턴: 정상, 램프, 스파이크, 소크.

## 활용

`code/main.py`는 현실적인 프롬프트 분포로 부하 테스트를 시뮬레이션하고, 효과적인 TPOT를 측정하며, 균일 프롬프트 함정을演示합니다.

## 결과물

이 레슨은 `outputs/skill-load-test-plan.md`를 산출합니다. 작업 및 SLA가 주어지면 도구를 선택하고 네 가지 부하 패턴을 설계합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 균일 vs 현실적 분포 — 격차가 어디에습니까?
2. CI 게이트용 k6 스크립트 작성: 100명의 동시 사용자로 800ms 미만의 TTFT P95, 런타임 5분.
3. 소크 테스트가 시간당 50MB 증가하는 메모리를 보여줍니다. 세 가지 원인을 이름 짓고它们 사이에서 선택하는 계측을 지정하세요.
4. 10 RPS에서 100 RPS로 스파이크 테스트. Karpenter + vLLM 프로덕션 스택이 있는 경우 예상 복구 시간은 얼마입니까 (Phase 17 · 03 + 18)?
5. GenAI-Perf가 TPOT=6ms를 보고합니다; LLMPerf가 동일한 서버에서 TPOT=11ms를 보고합니다. 설명하세요.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| LLMPerf | "LLM 하네스" | Anyscale 벤치마크 도구, 스트리밍 인식 |
| GenAI-Perf | "NVIDIA 도구" | NVIDIA 참조 하네스 |
| LLM-Locust | "LLM용 Locust" | GIL 함정을 수정하는 Locust 확장 |
| guidellm | "합성 벤치마크" | 대규모 합성 도구 |
| k6 Operator | "K8s k6" | CRD 기반 분산 k6 |
| GIL 함정 | "Python 클라이언트 오버헤드" | 토큰화 백로그가 보고된 지연 시간을膨胀 |
| 프롬프트 균일성 함정 | "단일 프롬프트 거짓말" | 동일한 프롬프트로 루프하면 캐시가 히트하고 처리량이膨胀 |
| 정상 상태 | "일정한 부하" | N분 동안 평탄한 RPS |
| 램프 | "선형 증가" | 기간 동안 0에서 목표까지 |
| 스파이크 | "버스트 테스트" | 갑작스러운 승수 후 회귀 |
| 소크 | "장기 테스트" | 누수 감지를 위한 시간 |

## 추가 자료

- [TianPan — LLM 애플리케이션 부하 테스트](https://tianpan.co/blog/2026-03-19-load-testing-llm-applications)
- [PremAI — 2026년 LLM 부하 테스트](https://blog.premai.io/load-testing-llms-tools-metrics-realistic-traffic-simulation-2026/)
- [NVIDIA NIM — LLM 추론 벤치마킹 소개](https://docs.nvidia.com/nim/large-language-models/1.0.0/benchmarking.html)
- [TrueFoundry — LLM-Locust](https://www.truefoundry.com/blog/llm-locust-a-tool-for-benchmarking-llm-performance)
- [LLMPerf](https://github.com/ray-project/llmperf)
- [k6 Operator](https://github.com/grafana/k6-operator)