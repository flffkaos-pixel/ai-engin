# 에지 추론 — Apple Neural Engine, Qualcomm Hexagon, WebGPU/WebLLM, Jetson

> 핵심 에지 제약은 메모리 대역폭이지 컴퓨터가 아닙니다. 모바일 DRAM은 50-90 GB/s에 있습니다; 데이터센터 HBM3는 2-3 TB/s를 지웁니다 — 30-50배 격차. Decode는 메모리 바운드이므로 격차가 결정적입니다. 2026년 환경은 네 가지로 나뉩니다. Apple M4/A18 Neural Engine은 통합 메모리로 38 TOPS에서 정점을 찍습니다 (CPU↔NPU 복사 없음). Qualcomm Snapdragon X Elite / 8 Gen 4 Hexagon은 45 TOPS에 도달합니다. WebGPU + WebLLM은 M3 Max에서 Llama 3.1 8B (Q4)를 ~41 tok/s로 실행합니다 (기본 약 70-80%); 17.6k GitHub 스타, OpenAI 호환 API, ~70-75% 모바일 적용 범위. NVIDIA Jetson Orin Nano Super (8GB)는 Llama 3.2 3B / Phi-3에 맞습니다; AGX Orin은 vLLM에서 ~40 tok/s로 gpt-oss-20b를 실행합니다; Jetson T4000 (JetPack 7.1)은 AGX Orin의 2배입니다. TensorRT Edge-LLM은 EAGLE-3, NVFP4, chunked prefill을 지원합니다 — CES 2026에서 Bosch, ThunderSoft, MediaTek가展示했습니다.

**유형:** 학습
**언어:** Python (stdlib, toy bandwidth-bound decode 시뮬레이터)
**선수 과목:** Phase 17 · 04 (vLLM Serving Internals), Phase 17 · 09 (Production Quantization)
**소요 시간:** ~60분

## 학습 목표

- 모바일 LLM 추론이 메모리 대역폭 바운드이고 컴퓨터가 보조적 이유를 설명합니다.
- 4가지 에지 대상 (Apple ANE, Qualcomm Hexagon, WebGPU/WebLLM, NVIDIA Jetson)을 열거하고 각각을 사용 사례와 매칭합니다.
- 2026년 WebGPU 적용 범위 격차 (追いつく Firefox Android)와 Safari iOS 26 론칭을 이름 짓습니다.
- 대상당 양자화 형식을 선택합니다 (ANE용 Core ML INT4 + FP16, Hexagon용 QNN INT8/INT4, 브라우저용 WebGPU Q4, Jetson Thor용 NVFP4).

## 문제

고객이 온디바이스 챗봇을 원합니다: 음성 우선,デフォルトで 비공개, 오프라인으로 작동. MacBook Pro M3 Max에서 Llama 3.1 8B Q4는 ~55 tok/s로 실행됩니다 — 괜찮습니다. iPhone 16 Pro에서 같은 모델은 3 tok/s로 실행됩니다 — 괜찮지 않습니다. Snapdragon 8 Gen 3가 있는 미들레인지 Android에서 7 tok/s. Chrome Android v121+의 WebGPU를 통한 브라우저에서 4-8 tok/s, 장치에 따라 다릅니다.

처리량 분산은 포팅 문제가 아닙니다. 대역폭 격차 × 양자화 형식 × NPU가 사용자 공간에서 접근 가능한지 여부의 곱입니다. 2026년 에지 추론은 4가지 다른 문제와 4가지 다른 솔루션입니다.

## 개념

### 대역폭이 진정한 천장입니다

Decode는 모든 토큰에 대해 전체 가중치 세트를 읽습니다. Q4의 7B 모델 하나는 3.5 GB입니다. 50 GB/s에서 3.5 GB를 읽으려면 70 ms가 걸립니다 — ~14 tok/s의 이론적 천장. 90 GB/s (하이엔드 모바일 DRAM)에서 천장은 ~25 tok/s로 이동합니다. 이 숫자 아래에서는 컴퓨트가 도움이 되지 않습니다.

데이터센터 HBM3은 3 TB/s에서 같은 3.5 GB를 1.2 ms 만에 지웁니다 — 천장은 830 tok/s. 같은 모델, 같은 가중치. 다른 메모리 하위 시스템.

### Apple Neural Engine (M4 / A18)

- 최대 38 TOPS. 통합 메모리 (CPU와 ANE가 같은 풀을 공유) — 복사 오버헤드 없음.
- Core ML + `.mlmodel` 컴파일된 모델을 통해 액세스하거나 Metal Performance Shaders (MPS)를 통해 PyTorch를 통해 액세스.
- Llama.cpp Metal 백엔드는 MPS를 사용합니다, 직접 ANE가 아닙니다; 네이티브 ANE는 Core ML 변환이 필요합니다.
- 2026년 iOS 앱을 위한 최선의 실제 경로: INT4 가중치 + FP16 activations가 있는 Core ML.

### Qualcomm Hexagon (Snapdragon X Elite / 8 Gen 4)

- 최대 45 TOPS. SoC에서 CPU 및 GPU와 통합되었지만 별도의 메모리 도메인.
- QNN (Qualcomm Neural Network) SDK 및 AI Hub가 PyTorch/ONNX로부터 변환을 제공합니다.
- 채팅 템플릿, Llama 3.2, Phi-3 모두 AI Hub에서 일등 시민 아티팩트로 shipping됩니다.

### Intel / AMD NPU (Lunar Lake, Ryzen AI 300)

- 40-50 TOPS. 소프트웨어가 Apple/Qualcomm 뒤처집니다; OpenVINO가 개선 중이지만 틈새.
- Windows ARM 코파일럿 앱에 가장 좋습니다; 로컬 우선을 위한 AMD/Intel 데스크탑에서 네이티브.

### WebGPU + WebLLM

- WebGPU 컴퓨트 셰이더를 통해 브라우저에서 모델을 실행합니다; 설치 없음.
- M3 Max에서 Llama 3.1 8B Q4 ~41 tok/s — 같은 백엔드를 통해 기본의 약 70-80%.
- WebLLM에서 17.6k GitHub 스타; OpenAI 호환 JS API; Apache 2.0.
- 2026년 적용 범위: Chrome Android v121+, Safari iOS 26 GA, Firefox Androidが追いつく中. 전체 ~70-75% 모바일 적용 범위.

### NVIDIA Jetson 제품군

- Orin Nano Super (8GB): Llama 3.2 3B, Phi-3에 좋은 tok/s로 맞습니다.
- AGX Orin: vLLM에서 ~40 tok/s로 gpt-oss-20b를 실행합니다.
- Thor / T4000 (JetPack 7.1): AGX Orin 성능의 2배, EAGLE-3 및 NVFP4 지원.
- TensorRT Edge-LLM (2026)은 EAGLE-3 스펙큘러티브 디코딩, NVFP4 가중치, chunked prefill을 지원합니다 — 에지로 포팅된 데이터센터 최적화.

### 대상별 양자화 선택

| 대상 | 형식 | 참고 |
|--------|--------|-------|
| Apple ANE | INT4 가중치 + FP16 activations | Core ML 변환 경로 |
| Qualcomm Hexagon | QNN INT8 / INT4 | AI Hub 변환기 |
| WebGPU / WebLLM | Q4 MLC (q4f16_1) | `mlc_llm convert_weight` + 컴파일된 `.wasm` 사용; GGUF는 지원되지 않음 |
| Jetson Orin Nano | Q4 GGUF 또는 TRT-LLM INT4 | 메모리 바운드 |
| Jetson AGX / Thor | NVFP4 + FP8 KV | Edge-LLM 경로 |

### 에지에서 긴 컨텍스트 함정

Llama 3.1의 128K 컨텍스트는 데이터센터 기능입니다. 8 GB RAM이 있는 폰에서 4 GB 모델 + 32K 토큰용 2 GB KV 캐시 + OS 오버헤드 = OOM. 에지 배포는 공격적 KV 양자화 (Q4 KV)를接受的이지 않는 한 컨텍스트를 4K-8K로 유지합니다.

### 음성이 킬러 앱입니다

음성 에이전트는 지연 시간에 민감합니다 (첫 번째 토큰 < 500 ms). 로컬 추론은 네트워크 지연 시간을 완전히 elimin합니다. 음성-텍스트 (에지에서 실행되는 Whisper Turbo 변형)와 결합하여 에지 추론이 프로덕션 품질 음성 루프가 됩니다.

### 기억해야 할 숫자

- Apple M4 / A18 ANE: 38 TOPS.
- Qualcomm Hexagon SD X Elite: 45 TOPS.
- WebLLM M3 Max: Llama 3.1 8B Q4에서 ~41 tok/s.
- AGX Orin: vLLM에서 gpt-oss-20b에서 ~40 tok/s.
- 데이터센터-에지 대역폭 격차: 30-50x.
- WebGPU 모바일 적용 범위: ~70-75% (Firefox Android 뒤처짐).

## 활용

`code/main.py`는 에지 대상 전반의 대역폭 바운드 수학에서 이론적 decode 처리량 천장을 계산합니다. 관찰된 벤치마크와 비교하고 대역폭而非 컴퓨터가 병목인 곳을 강조합니다.

## 결과물

이 레슨은 `outputs/skill-edge-target-picker.md`를 산출합니다. 플랫폼 (iOS/Android/browser/Jetson), 모델, 지연 시간/메모리 예산이 주어지면 양자화 형식과 변환 파이프라인을 선택합니다.

## 연습문제

1. `code/main.py`를 실행하세요. Snapdragon 8 Gen 3 (~77 GB/s 대역폭)에서 Q4의 7B 모델에 대해 decode 천장을 계산하세요. 관찰된 6-8 tok/s와 비교 — 런타임이 효율적입니까?
2. Android의 WebGPU는 Chrome v121+가 필요합니다. 이전 브라우저에 대한 대체제를 디자인하세요 — 같은 OpenAI 호환 API를 통한 서버 측.
3. iOS 앱에 4K 컨텍스트 스트리밍이 필요합니다. iPhone 16에서 4 GB 활성 메모리 이하로 유지하는 모델/형식 조합은 무엇입니까?
4. Jetson AGX Orin은 40 tok/s에서 gpt-oss-20b를 실행합니다. Jetson Nano는 3B만 맞습니다. 제품이 둘 다를 대상으로 하면 추론 스택을 어떻게 통합합니까?
5. "2026년 WebLLM이 프로덕션 준비 완료"인지 주장하세요. 적용 범위, 성능, Firefox Android 격차를 인용하세요.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| ANE | "Apple neural engine" | M 시리즈 및 A 시리즈의 온디바이스 NPU; 통합 메모리 |
| Hexagon | "Qualcomm NPU" | Snapdragon NPU; 액세스를 위한 QNN SDK |
| WebGPU | "브라우저 GPU" | W3C 표준화 브라우저 GPU API; Chrome/Safari 2026 |
| WebLLM | "브라우저 LLM 런타임" | MLC-LLM 프로젝트; Apache 2.0; OpenAI 호환 JS |
| Jetson | "NVIDIA 에지" | Orin Nano / AGX / Thor / T4000 제품군 |
| TRT Edge-LLM | "에지 TensorRT" | 2026년 에지 포팅 TensorRT-LLM; EAGLE-3 + NVFP4 |
| 통합 메모리 | "공유 풀" | CPU와 NPU가 같은 RAM을 봅니다; 복사 오버헤드 없음 |
| 대역폭 바운드 | "메모리 제한" | 가중치를 읽는 bytes/sec로 게이트된 Decode |
| Core ML | "Apple 변환" | ANE 네이티브 모델용 Apple 프레임워크 |
| QNN | "Qualcomm 스택" | Qualcomm Neural Network SDK |

## 추가 자료

- [On-Device LLMs State of the Union 2026](https://v-chandra.github.io/on-device-llms/) — 환경 및 벤치마크.
- [NVIDIA Jetson Edge AI](https://developer.nvidia.com/blog/getting-started-with-edge-ai-on-nvidia-jetson-llms-vlms-and-foundation-models-for-robotics/) — Orin / AGX / Thor.
- [NVIDIA TensorRT Edge-LLM](https://developer.nvidia.com/blog/accelerating-llm-and-vlm-inference-for-automotive-and-robotics-with-nvidia-tensorrt-edge-llm/) — 2026년 에지 포팅 발표.
- [WebLLM (arXiv:2412.15803)](https://arxiv.org/html/2412.15803v2) — 디자인 및 벤치마크.
- [Apple Core ML](https://developer.apple.com/documentation/coreml) — ANE 네이티브 변환.
- [Qualcomm AI Hub](https://aihub.qualcomm.com/) — Hexagon용 사전 변환된 모델.