# 프로덕션 양자화 — AWQ, GPTQ, GGUF K-quants, FP8, MXFP4/NVFP4

> 양자화 형식은 범용 선택이 아닙니다 — 하드웨어, 서비스 엔진, 작업의 함수입니다. GGUF Q4_K_M 또는 Q5_K_M은 CPU와 에지를 소유하며 llama.cpp와 Ollama를 통해 제공됩니다. GPTQ는 같은 베이스에 멀티 LoRA가 필요할 때 vLLM 내부에서 이깁니다. Marlin-AWQ 커널이 있는 AWQ는 INT4에서 최상의 Pass@1으로 7B 클래스 모델에서 약 741 tok/s를 제공합니다 — 2026년 데이터센터 프로덕션의 기본값입니다. FP8은 Hopper, Ada, Blackwell에서 중간 지형으로 유지됩니다 — near-lossless이며 널리 지원됩니다. NVFP4 및 MXFP4 (Blackwell 마이크로스케일링)는 공격적이며 블록별 검증이 필요합니다. 두 가지 함정이 팀을 문지릅니다: 캘리브레이션 데이터셋이 배포 도메인과 일치해야 하고, KV 캐시는 가중치 양자화와 분리되어 있습니다 — AWQ 교훈 "내 모델이 이제 4 GB"는 프로덕션 배치 크기에서 10-30 GB KV 캐시를 잊습니다.

**유형:** 학습
**언어:** Python (stdlib, toy 포맷 전반의 메모리 및 처리량 비교)
**선수 과목:** Phase 10 · 13 (Quantization foundations), Phase 17 · 04 (vLLM Serving Internals)
**소요 시간:** ~75분

## 학습 목표

- 2026년 6가지 프로덕션 양자화 형식과 각자의 스위트 스팟을 이름 짓습니다.
- 하드웨어 (CPU 대 GPU, Hopper 대 Blackwell), 엔진 (vLLM, TRT-LLM, llama.cpp), 작업 (rutine 채팅, 추론, 멀티 LoRA)이 주어지면 형식을 선택합니다.
- 선택한 형식에 대해 가중치 메모리 절감과 영향을받지 않는 KV 캐시를 계산합니다.
- 도메인 트래픽에서 양자화된 모델의 품질을 저하시키는 캘리브레이션 데이터셋 함정을 이름 짓습니다.

## 문제

양자화는 메모리와 HBM 대역폭을 줄입니다 — 그것이 정확히 decode가 필요한 것입니다. FP16 70B 모델은 140 GB의 가중치입니다. 가중치를 INT4 (AWQ 또는 GPTQ)로 양자화하면 모델이 35 GB가 됩니다 — KV 캐시 공간을 위해 H100 하나에 맞으며, 128개의 동시 시퀀스에서 2k 컨텍스트로 KV 캐시만 20-30 GB이기 때문에 중요합니다.

하지만 양자화는 무료가 아닙니다. 공격적 양자화는 품질을 저하시키며, 특히 추론 무거운 작업에서 그렇습니다. 다른 형식은 다른 엔진에서 작동합니다. 다른 하드웨어는 다른 정밀도를 기본적으로 지원합니다. 2026년 형식 동물원은 실제이며 다른 사람의 선택을 복사할 수 없습니다 — 스택에 따라 선택해야 합니다.

## 개념

### 여섯 가지 형식

| 형식 | 비트 | 스위트 스팟 | 엔진 |
|--------|------|-----------|---------|
| GGUF Q4_K_M / Q5_K_M | 4-5 | CPU, 에지, 노트북 | llama.cpp, Ollama |
| GPTQ | 4-8 | vLLM의 멀티 LoRA | vLLM, TGI |
| AWQ | 4 | 데이터센터 GPU 프로덕션 | vLLM (Marlin-AWQ), TGI |
| FP8 | 8 | Hopper/Ada/Blackwell 데이터센터 | vLLM, TRT-LLM, SGLang |
| MXFP4 | 4 | Blackwell 멀티 사용자 | TRT-LLM |
| NVFP4 | 4 | Blackwell 멀티 사용자 | TRT-LLM |

### GGUF — CPU/에지 기본값

GGUF는 본질적으로 양자화 체계가 아닌 파일 형식입니다 — 하나의 컨테이너에 K-quant 변형 (Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0)을 번들합니다. Q4_K_M과 Q5_K_M이 프로덕션 기본값입니다 — 4-5비트에서 BF16에 가까운 품질. llama.cpp가 압도적으로 가장 빠른 CPU 추론 엔진이기 때문에 CPU 또는 에지 서비스에 가장 좋습니다.

vLLM의 처리량 페널티: 7B에서 ~93 tok/s — 형식이 GPU 커널에 최적화되지 않았습니다. 배포 대상이 CPU/에지일 때 GGUF를 사용하세요. 그렇지 않으면 아닙니다.

### GPTQ — vLLM의 멀티 LoRA

GPTQ는 캘리브레이션 패스가 있는 사후 훈련 양자화 알고리즘입니다. Marlin 커널이 GPU에서 빠르게 만듭니다 (비 Marlin GPTQ 대비 2.6x 스피드업). 7B에서 ~712 tok/s.

고유한 이점: GPTQ-Int4는 vLLM에서 LoRA 어댑터를 지원합니다. 베이스 모델 plus 10-50개의 fine-tuned 변형 (각각 LoRA로)을 제공 중이면 GPTQ가 당신의 길입니다. NVFP4는 2026년 초까지 LoRA를 아직 지원하지 않습니다.

### AWQ — 데이터센터 GPU 기본값

Activation-aware Weight Quantization. 양자화 중에 ~1% 가장 관련된 가중치를 보호합니다. Marlin-AWK 커널: 순진한 것 대비 10.9x 스피드업. 7B에서 ~741 tok/s, INT4 형식 중 최상의 Pass@1.

멀티 LoRA (GPTQ) 또는 공격적인 Blackwell FP4 (NVFP4)가 필요하지 않는 한 새 GPU 서비스에 AWQ를 선택하세요.

### FP8 — 신뢰할 수 있는 중간

8비트 부동 소수점. Near-lossless. 널리 지원됩니다. Hopper Tensor Cores는 FP8을 기본으로 가속합니다. Blackwell이 상속합니다. 품질이 협상 불가능할 때 (추론, 의료, 코드-gen) FP8이 2026년 안전한 기본값입니다. 메모리 절감은 INT4의 절반이지만 품질 위험이 훨씬 낮습니다.

### MXFP4 / NVFP4 — Blackwell 공격적

마이크로스케일링 FP4. 가중치의 각 블록에는 자체 스케일 인자가 있습니다. 공격적이지만 Blackwell Tensor Cores에서 하드웨어 가속됩니다. FP8 대비 토큰당 바이트를 절반으로 줄입니다 — Phase 17 · 07의 경제적 이점.

주의사항:
- LoRA 지원 아직 없음 (2026년 초).
- 추론 무거운 작업에서可视적 품질 하락.
- 모델당 평가 집합에서 검증하세요.

### 캘리브레이션 함정

AWQ와 GPTQ는 캘리브레이션 데이터셋이 필요합니다 — 일반적으로 C4 또는 WikiText입니다. 도메인 모델 (코드, 의료, 법률)의 경우 일반 웹 텍스트에서 캘리브레이션하면 알고리즘이 보호할 가중치에 대해 잘못된 결정을 내립니다. HumanEval에서 Pass@1이 몇 포인트 떨어질 수 있습니다.

수정: 도메인 내 데이터로 캘리브레이션하세요. 보통 수백 개의 도메인 샘플로 충분합니다. 배송 전에 평가 집합에서 테스트하세요.

### KV 캐시 함정

AWQ는 가중치를 4비트로 줄입니다. KV 캐시는 별도이며 FP16/FP8로 유지됩니다. AWQ가 있는 70B 모델의 경우:

- 가중치: ~35 GB (140 GB에서 INT4).
- 128 동시 × 2k 컨텍스트의 KV 캐시: ~20 GB.
- Activations: ~5 GB.
- 전체: ~60 GB — H100 80GB에 맞습니다.

순진하게 "모델을 4 GB로 양자화했다"고 말하면 다른 30-50 GB를 잊습니다. HBM을 총체적으로 예산을 잡으세요.

개별적으로, KV 캐시 양자화 (FP8 KV 또는 INT8 KV)는 어텐션 정확도에 직접 영향을 미치고 무료 이안이 아닌 자체 트레이드오프가 있는 다른 선택입니다.

### 추론에 AWQ INT4는 위험합니다

사슬-of-though, 수학, 긴 컨텍스트가 있는 코드-gen — 이들은 공격적 양자화에서明显적으로 고통합니다. AWQ INT4는 MATH에서 ~3-5포인트를 잃습니다. 추론 무거운 작업의 경우 FP8 또는 BF16으로 배송하세요; 메모리 비용을受け入れ하세요.

### 2026 선택 가이드

- CPU/에지 서비스: GGUF Q4_K_M. 끝.
- GPU 서비스, rutin 채팅, LoRA 없음: AWQ.
- GPU 서비스, 멀티 LoRA: Marlin이 있는 GPTQ.
- 추론 작업: FP8.
- Blackwell 데이터센터, 검증된 품질: NVFP4 + FP8 KV.
- 모호함: 각 후보 형식에서 1,000샘플 평가를 실행하세요.

## 활용

`code/main.py`는 다양한 모델 크기에서 6가지 형식 전반의 메모리 공간 (가중치 + KV + activations)과 상대적 처리량을 계산합니다. KV 캐시가 지배하는 곳, 가중치 압축이 payoff하는 곳, FP8이 안전한 선택인 곳을 보여줍니다.

## 결과물

이 레슨은 `outputs/skill-quantization-picker.md`를 산출합니다. 하드웨어, 모델 크기, 작업 유형, 품질 허용 범위가 주어지면 형식을 선택하고 캘리브레이션/검증 계획을 산출합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 2k 컨텍스트에서 128개의 동시로 70B 모델에 대해 각 형식의 총 HBM을 계산하세요. 어떤 형식이 H100 80GB 하나에 맞습니까?
2. 7B 코딩 모델이 있습니다. 형식을 선택하고 정당화하세요. 품질許容범위에서 잘못했다면 복구 경로는 무엇입니까?
3. 의료 도메인 모델에 대해 AWQ를 캘리브레이션하는 데 필요한 캘리브레이션 데이터셋 크기를 계산하세요. 더 많은 데이터가 항상 더 나쁜 이유는 무엇입니까?
4. Marlin-AWQ 커널 논문 또는 릴리스 노트를 읽으세요. 세 문장으로 AWQ가 순진한 GPTQ가 ~712를 hits하는 동안 7B에서 741 tok/s에 도달하는 이유를 설명하세요.
5. AWQ 가중치와 FP8 KV 캐시를 결합하는 것이 KV를 BF16으로 유지하는 것과，什么时候 sensible합니까?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| GGUF | "llama.cpp 형식" | K-quant 변형을 번들하는 파일 형식; CPU/에지 기본값 |
| Q4_K_M | "Q4 K M" | 4비트 K-quant 중형; 프로덕션 GGUF 기본값 |
| GPTQ | "지 피 티 큐" | 캘리브레이션이 있는 포스트트레이닝 INT4; vLLM에서 LoRA 지원 |
| AWQ | "에이 더블유 큐" | Activation-aware INT4; Marlin 커널; INT4에서 최상의 Pass@1 |
| Marlin 커널 | "빠른 INT4 커널" | Hopper에서 INT4용 사용자 정의 CUDA 커널; 10x 스피드업 |
| FP8 | "8비트 부동 소수점" | Hopper/Ada/Blackwell에서 안전한 정밀도 기본값 |
| MXFP4 / NVFP4 | "마이크로스케일링 4" | 블록별 스케일 인자가 있는 Blackwell 4비트 FP |
| 캘리브레이션 데이터셋 | "캘 데이터" | 양자화 매개변수를 선택하는 데 사용되는 입력 텍스트; 도메인과 일치해야 함 |
| KV 캐시 양자화 | "KV INT8" | 가중치와 별개의 선택; 어텐션 정확도에 직접 영향 |

## 추가 자료

- [VRLA Tech — LLM Quantization 2026](https://vrlatech.com/llm-quantization-explained-int4-int8-fp8-awq-and-gptq-in-2026/) — 비교 벤치마크.
- [Jarvis Labs — vLLM Quantization Complete Guide](https://jarvislabs.ai/blog/vllm-quantization-complete-guide-benchmarks) — 형식별 처리량 숫자.
- [PremAI — GGUF vs AWQ vs GPTQ vs bitsandbytes 2026](https://blog.premai.io/llm-quantization-guide-gguf-vs-awq-vs-gptq-vs-bitsandbytes-compared-2026/) — 형식별 선택.
- [vLLM 문서 — 양자화](https://docs.vllm.ai/en/latest/features/quantization/index.html) — 지원되는 형식 및 플래그.
- [AWQ 논문 (arXiv:2306.00978)](https://arxiv.org/abs/2306.00978) — 원래 AWQ 공식.
- [GPTQ 논문 (arXiv:2210.17323)](https://arxiv.org/abs/2210.17323) — 원래 GPTQ 공식.