# 자체 호스팅 서빙 선택 — llama.cpp, Ollama, TGI, vLLM, SGLang

> 2026년 자체 호스팅 추론에서 4가지 엔진이 지배합니다. 하드웨어, 규모, 생태계에 따라 선택합니다. **llama.cpp**는 CPU에서 가장 빠릅니다 — 가장 넓은 모델 지원, 양자화 및 스레딩에 대한 완전한 제어. **Ollama**는 dev-노트북 one-command 설치, llama.cpp보다 ~15-30% 느림 (Go + CGo + HTTP 직렬화), prod 유사 부하에서 3x 처리량 격차. **TGI는 2025년 12월 11일에 유지 관리 모드에 진입했습니다** — 버그 수정만, vLLM보다 원시 처리량에서 ~10% 느리지만Historically 최고 수준의 관찰 가능성과 HF 생태계 통합. 해당 유지 관리 상태가 장기적 내기에서 위험하게 만듭니다 — 새 프로젝트에는 SGLang 또는 vLLM이 더 안전한 기본값입니다. **vLLM**은 범용 프로덕션 기본값입니다 — v0.15.1 (2026년 2월) PyTorch 2.10, RTX Blackwell SM120, H200 최적화를 추가합니다. **SGLang**은 에이전틱 멀티터너 / 접두사 무거운 전문입니다 — 프로덕션에서 400,000개 이상의 GPU (xAI, LinkedIn, Cursor, Oracle, GCP, Azure, AWS). 하드웨어 제약: CPU만 → llama.cpp만. AMD / 비 NVIDIA → vLLM만 (TRT-LLM은 NVIDIA 잠금). 2026년 파이프라인 패턴: dev = Ollama, staging = llama.cpp, prod = vLLM 또는 SGLang. 동일한 GGUF/HF 가중치 throughout.

**유형:** 학습
**언어:** Python (stdlib, 엔진 결정 트리 워커)
**선수 과목:** 엔진涵盖的所有 Phase 17 수업 (04, 06, 07, 09, 18)
**소요 시간:** ~45분

## 학습 목표

- 하드웨어 (CPU / AMD / NVIDIA Hopper / Blackwell), 규모 (1 사용자 / 100 / 10,000), 워크로드 (일반 채팅 / 에이전트 / 긴 컨텍스트) given으로 엔진을 선택합니다.
- 2026년 TGI 유지 관리 모드 상태 (2025년 12월 11일)를 이름 짓고 새 프로젝트가 vLLM 또는 SGLang을 선호하는 이유를 설명합니다.
- 동일한 GGUF 또는 HF 가중치를 사용하여 throughout dev/staging/prod 파이프라인을 설명합니다.
- "CPU만"이 llama.cpp를 강제하고 "AMD"가 TRT-LLM을 제외하는 이유를 설명합니다.

## 문제

팀이 새로운 자체 호스팅 LLM 프로젝트를 시작합니다. 한 엔지니어가 Ollama라고 하고, 다른 하나가 vLLM이라고 하고, 세 번째가 "TGI가 작동하지 않습니까?"라고 합니다. 세 가지 모두 다양한 컨텍스트에서 맞습니다. 모두에게 맞는 것은 없습니다.

2026년 선택 트리가 중요합니다: 하드웨어 먼저, 규모 두 번째, 워크로드 세 번째. 그리고 하나의 특정 2025년 이벤트 — TGI가 2025년 12월 11일에 유지 관리 모드에 진입 — 새 프로젝트의 기본값을 변경합니다.

## 개념

### 5가지 엔진

| 엔진 | 최적의 경우 | 참고 |
|------|------------|------|
| **llama.cpp** | CPU / edge / 최소 의존성 / 가장 넓은 모델 지원 | CPU에서 가장 빠름, 완전한 제어 |
| **Ollama** | 개발 노트북, 단일 사용자, one-command 설치 | llama.cpp보다 15-30% 느림; prod 부하에서 3x 처리량 격차 |
| **TGI** | HF 생태계, 규제 산업 | **2025년 12월 11일 유지 관리 모드** |
| **vLLM** | 범용 프로덕션, 100+ 사용자 | 광범위한 프로덕션 기본값; v0.15.1 2026년 2월 |
| **SGLang** | 에이전틱 멀티터너, 접두사 무거운 워크로드 | 프로덕션에서 400,000개 이상의 GPU |

### 하드웨어 우선 결정

**CPU만** → llama.cpp. Ollama도 작동하지만 더 느립니다. 다른 엔진은 CPU에서 경쟁력이 없습니다.

**AMD GPU** → vLLM (AMD ROCm 지원). SGLang도 작동합니다. TRT-LLM은 NVIDIA 잠금장이므로 제외됩니다.

**NVIDIA Hopper (H100 / H200)** → vLLM 또는 SGLang 또는 TRT-LLM. 세 가지 모두 최고 수준.

**NVIDIA Blackwell (B200 / GB200)** → TRT-LLM이 처리량 리더입니다 (Phase 17 · 07). vLLM과 SGLang이 뒤따릅니다.

**Apple Silicon (M 시리즈)** → llama.cpp (Metal). Ollama가 이를 감쌉니다.

### 규모 우선 결정

**1 사용자 / 로컬 dev** → Ollama. 하나의 명령, 첫 번째 토큰이 몇 초 내에.

**10-100 사용자 / 소규모 팀** → vLLM 단일 GPU.

**100-10k 사용자 / 프로덕션** → vLLM 프로덕션 스택 (Phase 17 · 18) 또는 SGLang.

**10k+ 사용자 / 엔터프라이즈** → vLLM 프로덕션 스택 + 분리된 (Phase 17 · 17) + LMCache (Phase 17 · 18).

### 워크로드 세 번째 결정

**일반 채팅 / Q&A** → vLLM이 광범위한 기본값에서 이깁니다.

**에이전틱 멀티터너 (도구, 계획, 메모리)** → SGLang의 RadixAttention (Phase 17 · 06)이 지배합니다.

**중단 접두사 재사용이 있는 RAG** → SGLang.

**코드 생성** → vLLM fine; SGLang이 캐시에서 약간 더 좋습니다.

**긴 컨텍스트 (128K+)** → vLLM + chunked prefill; SGLang + tiered KV.

### TGI 유지 관리 함정

Hugging Face TGI가 2025년 12월 11일에 유지 관리 모드에 진입했습니다 — 앞으로 버그 수정만 가능합니다. Historically: 최고 수준의 관찰 가능성, 최고 수준의 HF 생태계 통합 (모델 카드, 안전 도구), 원시 처리량에서 vLLM보다 약간 뒤처졌습니다.

2026년 새 프로젝트의 경우: TGI에서 멀어지는 것이 기본입니다. 기존 TGI 배포는 계속할 수 있지만 결국 마이그레이션해야 합니다. SGLang과 vLLM이 더 안전한 기본값입니다.

### 파이프라인 패턴

Dev (Ollama) → staging (llama.cpp) → prod (vLLM). 동일한 GGUF 또는 HF 가중치 throughout. 엔지니어들이 노트북에서 빠르게 반복; staging이 프로덕션 양자화를 미러; prod가 서빙 대상입니다.

### Ollama 주의사항

Ollama는 개발에 좋습니다. 공유 프로덕션에는 좋지 않습니다: Go HTTP 직렬화가 오버헤드를 추가하고, 동시성 관리가 vLLM보다 단순하며, OpenTelemetry 지원이 뒤처집니다. Ollama가 빛나는 곳 — 하나의 사용자, 하나의 명령 —에서 사용하고 공유를 위해 vLLM으로 전환하세요.

### 자체 호스팅 대 관리형은 별도의 결정입니다

Phase 17 · 01 (관리형 하이퍼스케일러), · 02 (추론 플랫폼)이 관리형을 다룹니다. 이 수업은 이미 자체 호스팅하기로 결정했다고 가정합니다. 자체 호스팅하는 이유: 데이터 거주지, 사용자 정의 fine-tune, 규모에서 총 비용 소유권, 호스팅에서 사용할 수 없는 도메인 모델.

### 기억해야 할 숫자

- TGI 유지 관리 모드: 2025년 12월 11일.
- vLLM v0.15.1: 2026년 2월; PyTorch 2.10; Blackwell SM120 지원.
- SGLang 프로덕션 발자국: 400,000개 이상의 GPU.
- Ollama 처리량 격차 vs llama.cpp: 15-30% 느림; prod 부하에서 3x.

## 활용

`code/main.py`는 결정 트리 워커입니다: 하드웨어 + 규모 + 워크로드가 주어지면 엔진을 선택하고 이유를 설명합니다.

## 결과물

이 레슨은 `outputs/skill-engine-picker.md`를 산출합니다. 제약 조건이 주어지면 엔진을 선택하고 마이그레이션 계획을 작성합니다.

## 연습문제

1. `code/main.py`를 하드웨어 / 규모 / 워크로드로 실행합니다. 출력이 직관과 일치합니까?
2. 인프라가 12개의 H100과 8개의 MI300X AMD입니다. 어떤 엔진? TRT-LLM이 테이블에서 벗어난 이유?
3. 팀이 "우리가 아는 것이니까"라는 이유로 2026년에 TGI를 사용하기를 원합니다. 마이그레이션 사례를 주장하세요.
4. Ollama dev에서 vLLM prod로: 양자화, 구성, 관찰 가능성에서 무엇이 변경됩니다?
5. P99 접두사 길이가 8K이고 테넌트 간 높은 재사용이 있는 RAG 제품입니다. 엔진을 선택하고 Phase 17 · 11 + 18과 함께 스택합니다.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| llama.cpp | "CPU 것" | 가장 넓은 모델 지원, CPU에서 가장 빠름 |
| Ollama | "노트북 것" | one-command 설치, 개발 등급 처리량 |
| TGI | "HF의 서빙" | 2025년 12월부터 유지 관리 모드 |
| vLLM | "기본값" | 2026년 광범위한 프로덕션 기준선 |
| SGLang | "에이전틱 것" | 접두사 무거운, RadixAttention |
| TRT-LLM | "NVIDIA 잠금" | Blackwell 처리량 리더, NVIDIA만 |
| GGUF | "llama.cpp 형식" | 번들된 K-quant 변형 |
| Production-stack | "vLLM K8s" | Phase 17 · 18 참조 배포 |
| 파이프라인 패턴 | "dev→stage→prod" | 동일한 가중치에서 Ollama → llama.cpp → vLLM |

## 추가 자료

- [AI Made Tools — vLLM vs Ollama vs llama.cpp vs TGI 2026](https://www.aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi/)
- [Morph — llama.cpp vs Ollama 2026](https://www.morphllm.com/comparisons/llama-cpp-vs-ollama)
- [n1n.ai — 포괄적인 LLM 추론 엔진 비교](https://explore.n1n.ai/blog/llm-inference-engine-comparison-vllm-tgi-tensorrt-sglang-2026-03-13)
- [PremAI — 2026년 최고의 vLLM 대안 10가지](https://blog.premai.io/10-best-vllm-alternatives-for-llm-inference-in-production-2026/)
- [TGI 유지 관리 공지](https://github.com/huggingface/text-generation-inference) — 릴리스 노트.
- [vLLM v0.15.1 릴리스 노트](https://github.com/vllm-project/vllm/releases)