# 캡스톤 14 — 추측 디코딩 추론 서버

> vLLM 0.7의 EAGLE-3는 실제 트래픽에서 2.5~3배 처리량을 제공합니다. AWS의 P-EAGLE(2026)은 병렬 추측을 더욱 발전시켰습니다. SGLang의 SpecForge는 대규모로 드래프트 헤드를 학습시켰습니다. Red Hat의 Speculators 허브는 일반적인 오픈 모델에 대한 정렬된 드래프트를 게시했습니다. TensorRT-LLM은 NVIDIA에서 추측 디코딩을 일급 기능으로 만들었습니다. 2026년 프로덕션 서빙 스택은 vLLM 또는 SGLang에 EAGLE 계열 드래프트, FP8 또는 INT4 양자화, 큐 대기 시간 기반 HPA를 사용합니다. 이 캡스톤은 두 개의 오픈 모델을 기준선 대비 2.5배 이상의 처리량으로 서빙하고 전체 테일 레이턴시 보고서를 제공하는 것입니다.

**Type:** Capstone
**Languages:** Python (서빙), C++ / CUDA (커널 검사), YAML (설정)
**Prerequisites:** Phase 3 (딥러닝), Phase 7 (트랜스포머), Phase 10 (LLM 처음부터), Phase 17 (인프라)
**Phases exercised:** P3 · P7 · P10 · P17
**Time:** 30시간

## 문제

추측 디코딩은 2026년에 상용화되었습니다. EAGLE-3 드래프트 헤드는 타겟 모델의 은닉 상태에서 학습하여 N개의 토큰을 미리 예측하고, 타겟 모델은 단일 패스로 검증합니다. 60~80%의 수용률은 종단 간 2~3배의 처리량 향상으로 이어집니다. vLLM 0.7은 이를 기본적으로 통합합니다. SGLang + SpecForge는 학습 파이프라인을 제공합니다. Red Hat의 Speculators는 Llama 3.3 70B, Qwen3-Coder-30B MoE, GPT-OSS-120B에 대한 정렬된 드래프트를 게시합니다.

핵심 기술력은 모델이 아닌 서빙 운영에 있습니다. 수용률은 트래픽 분포(ShareGPT 대 코드 대 도메인 데이터)에 따라 달라집니다. 거부 시 테일 레이턴시는 추측이 없을 때보다 더 나쁩니다 — 안정 상태의 토큰/초뿐만 아니라 여러 배치 크기에서 p99를 보고해야 합니다. Anthropic / OpenAI API 대비 100만 토큰당 비용이 신뢰성의 지렛대입니다.

## 개념

추측 디코딩에는 두 개의 계층이 있습니다. **드래프트** 모델(EAGLE-3 헤드, 엔그램 또는 더 작은 타겟 정렬 모델)은 단계당 k개의 후보 토큰을 제안합니다. **타겟** 모델은 모든 k개를 한 번에 검증하고, 수용된 프리픽스가 탐욕적 경로를 대체합니다. 수용률은 드래프트-타겟 정렬도와 입력 분포에 따라 달라집니다.

EAGLE-3는 대부분의 트래픽에서 엔그램 드래프트를 능가합니다. P-EAGLE은 더 깊은 드래프트 트리를 위해 병렬 추측을 실행합니다. 트레이드오프: 거부 시 P99 레이턴시가 더 높아집니다(검증 패스가 더 크기 때문). 서빙 설정은 이를 표면화하기 위해 배치-크기-버킷별 레이턴시를 보고해야 합니다.

배포는 Kubernetes입니다. vLLM 0.7은 GPU 또는 텐서-병렬 샤드당 하나의 레플리카를 실행합니다. HPA는 CPU가 아닌 큐 대기 시간을 기준으로 오토스케일링합니다. FP8(Marlin) 및 INT4(AWQ) 양자화는 GPU 메모리를 H100/H200 한도 내로 유지합니다. 엔드투엔드 보고서는 처리량, 수용률, 배치 1/8/32에서의 p50/p99, 그리고 $/100만 토큰입니다.

## 아키텍처

```
요청 수신
    |
    v
vLLM 서버 (0.7) 또는 SGLang (0.4)
    |
    +-- 드래프트: EAGLE-3 헤드 | P-EAGLE 병렬 | 엔그램 폴백
    +-- 타겟: Llama 3.3 70B | Qwen3-Coder-30B | GPT-OSS-120B
    |     양자화: FP8-Marlin 또는 INT4-AWQ
    |
    v
검증 패스: k개 드래프트 토큰을 타겟으로 배치 처리
    |
    v (프리픽스 수용, 거부된 접미사는 리샘플링)
    v
클라이언트로 토큰 스트림 반환
    |
    v
Prometheus 메트릭: 처리량, 수용률, 큐 대기 시간, 레이턴시 p50/p99
    |
    v
큐 대기 시간 메트릭 기반 HPA
```

## 스택

- 서빙: vLLM 0.7 또는 SGLang 0.4
- 추측 방법: EAGLE-3 드래프트 헤드, P-EAGLE 병렬 추측, 엔그램 폴백
- 드래프트 학습: SpecForge (SGLang) 또는 Red Hat Speculators
- 타겟 모델: Llama 3.3 70B, Qwen3-Coder-30B MoE, GPT-OSS-120B
- 양자화: FP8 (Marlin), INT4 AWQ
- 배포: Kubernetes + NVIDIA 디바이스 플러그인; 큐 대기 시간 메트릭 기반 HPA
- 평가: ShareGPT, MT-Bench-v2, GSM8K, HumanEval (도메인별 수용률 측정)
- 참조: TensorRT-LLM 추측 디코딩 (벤더 기준선)

## 구축하기

1. **타겟 모델 준비.** Llama 3.3 70B를 선택합니다. Marlin을 통해 FP8로 양자화합니다. 1xH100(또는 2x 텐서-병렬)에서 vLLM 0.7로 배포합니다.

2. **드래프트 소스.** Red Hat Speculators에서 정렬된 EAGLE-3 드래프트 헤드를 가져오거나 SpecForge를 통해 학습시킵니다. vLLM의 추측 디코딩 설정에 로드합니다.

3. **기준선 수치.** 추측 전: 배치 1/8/32에서 토큰/초, p50/p99 레이턴시, GPU 사용률. 게시합니다.

4. **EAGLE-3 활성화.** 설정을 전환하고 동일한 벤치마크를 재실행합니다. 속도 향상, 수용률, p99 테일 레이턴시 변화를 보고합니다.

5. **P-EAGLE.** 병렬 추측을 활성화하고 직렬 EAGLE-3 대비 더 깊은 드래프트 트리를 측정합니다. P-EAGLE이 도움이 되는 지점과 해가 되는 지점을 보고합니다.

6. **도메인 트래픽.** 동일한 서버를 통해 ShareGPT, HumanEval, 도메인별 트래픽을 실행합니다. 분포별 수용률을 측정합니다. 드래프트가 드리프트하는 시점을 식별합니다.

7. **두 번째 타겟 모델.** Qwen3-Coder-30B MoE에 대해 동일한 파이프라인을 실행합니다. 드래프트가 더 까다롭습니다(MoE 라우팅 노이즈). 보고합니다.

8. **K8s HPA.** `queue_wait_ms`를 추적하는 HPA와 함께 K8s에 배포합니다. 부하가 3배 증가할 때 스케일 아웃을 시연합니다.

9. **비용 비교.** 동일한 평가에서 Anthropic Claude Sonnet 4.7 및 OpenAI GPT-5.4와 $/100만 토큰을 비교 계산합니다. 게시합니다.

## 사용하기

```
$ curl https://infer.example.com/v1/chat/completions -d '{"messages":[...]}'
[serve]     vLLM 0.7, Llama 3.3 70B FP8, EAGLE-3 활성
[decode]    bs=8, 수용된_토큰_단계당=3.2, 수용률=0.76
[latency]   첫-토큰 42ms, 전체-응답 980ms (620 토큰)
[cost]      지속 처리량 기준 출력 토큰 100만 개당 $0.34
```

## 배포하기

`outputs/skill-inference-server.md`가 결과물입니다. 추측 디코딩, 전체 벤치마크 보고서, K8s 배포를 갖춘 측정된 서빙 스택입니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 기준선 대비 측정된 속도 향상 | 두 모델에서 일치하는 품질로 2.5배+ 처리량 |
| 20 | 실제 트래픽에서의 수용률 | 분포별 수용률 보고서 |
| 20 | P99 테일 레이턴시 규율 | 배치 1/8/32에서 추측 유무에 따른 p99 |
| 20 | 운영 | K8s 배포, 큐 대기 시간 기반 HPA, 원활한 롤아웃 |
| 15 | 문서 및 방법론 | 변경 사항과 이유에 대한 명확한 설명 |
| **100** | | |

## 실습

1. 드래프트가 타겟보다 한 버전 뒤쳐질 때(예: Llama 3.3 -> 3.4 드리프트) 수용률 저하를 측정합니다. 모니터링 알림을 구축합니다.

2. 엔그램 폴백을 구현합니다: EAGLE-3 수용률이 임계값 아래로 떨어지면 엔그램 드래프트로 전환합니다. 신뢰성 개선을 보고합니다.

3. 제어된 MoE 실험을 실행합니다: 라우팅 노이즈를 주입한 Qwen3-Coder-30B와 없는 경우를 비교합니다. 드래프트 수용 민감도를 측정합니다.

4. H200(141GB)으로 확장합니다. 레플리카당 확보된 모델 크기 헤드룸과 양자화되지 않은 Llama 3.3 70B를 서빙할 수 있는지 보고합니다.

5. 동일한 H100 하드웨어에서 TensorRT-LLM 추측 디코딩을 벤치마킹합니다. vLLM 대비 우위를 보이는 부분을 보고합니다.

## 주요 용어

| 용어 | 일반적인 사용법 | 정확한 의미 |
|------|----------------|-------------|
| 드래프트 모델 | "추측기" | 타겟이 검증할 N개의 토큰을 제안하는 작은 모델 |
| EAGLE-3 | "2026 드래프트 아키텍처" | 타겟 은닉 상태에서 학습된 드래프트 헤드; 약 75% 수용률 |
| P-EAGLE | "병렬 추측" | 하나의 타겟 패스로 검증되는 드래프트 브랜치 트리 |
| 수용률 | "적중률" | 리샘플링 없이 수용된 드래프트 토큰의 비율 |
| 양자화 | "FP8 / INT4" | GPU 메모리에 더 많은 모델을 담기 위한 저정밀 가중치 |
| 큐 대기 시간 | "HPA 메트릭" | 추론 시작 전에 요청이 대기 큐에서 기다리는 시간 |
| Speculators 허브 | "정렬된 드래프트" | 일반적인 오픈 모델용 EAGLE 드래프트의 Red Hat Neural Magic 허브 |

## 추가 자료

- [vLLM EAGLE 및 P-EAGLE 문서](https://docs.vllm.ai) — 참조 서빙 스택
- [P-EAGLE (AWS 2026)](https://aws.amazon.com/blogs/machine-learning/p-eagle-faster-llm-inference-with-parallel-speculative-decoding-in-vllm/) — 병렬 추측 디코딩 논문 + 통합
- [SGLang SpecForge](https://github.com/sgl-project/SpecForge) — 드래프트 헤드 학습 파이프라인
- [Red Hat Speculators](https://github.com/neuralmagic/speculators) — 정렬된 드래프트 허브
- [TensorRT-LLM 추측 디코딩](https://nvidia.github.io/TensorRT-LLM/) — 벤더 대안
- [Fireworks.ai 서빙 아키텍처](https://fireworks.ai/blog) — 상용 참조
- [EAGLE-3 논문 (arXiv:2503.01840)](https://arxiv.org/abs/2503.01840) — 방법 논문
- [vLLM 저장소](https://github.com/vllm-project/vllm) — 코드 및 벤치마크
