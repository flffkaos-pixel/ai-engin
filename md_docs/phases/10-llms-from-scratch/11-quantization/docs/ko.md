# 양자화

> FP16/FP32→INT8/INT4. 메모리 2~8배 절약.

**유형:** 빌드 | **시간:** ~75min

## 기법
- GPTQ: 레이어별 양자화, Hessian 기반
- AWQ: 중요 채널 보호
- GGUF: llama.cpp 형식, CPU 추론
- BitsandBytes: QLoRA용 4-bit