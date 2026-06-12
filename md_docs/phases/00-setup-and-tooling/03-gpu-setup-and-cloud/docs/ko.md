# GPU 설정 & 클라우드

> CPU로 학습하는 것은 학습용으로 괜찮습니다. 실제 훈련에는 GPU가 필요합니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 0, Lesson 01
**시간:** ~45분

## 학습 목표

- `nvidia-smi`와 PyTorch의 CUDA API를 사용하여 로컬 GPU 가용성 확인하기
- 무료 클라우드 기반 실험을 위해 T4 GPU로 Google Colab 구성하기
- CPU vs GPU에서 행렬 곱셈을 벤치마킹하고 속도 향상 측정하기
- fp16 경험 법칙을 사용하여 VRAM에 맞는 최대 모델 크기 추정하기

## 문제

Phase 1-3의 대부분 레슨은 CPU에서 잘 실행됩니다. 하지만 CNN, 트랜스포머, LLM을 훈련하기 시작하면(Phase 4+), GPU 가속이 필요합니다. CPU에서 8시간 걸리는 훈련이 GPU에서는 10분이면 됩니다.

세 가지 옵션이 있습니다: 로컬 GPU, 클라우드 GPU, Google Colab(무료).

## 개념

```
옵션:

1. 로컬 NVIDIA GPU
   비용: $0 (이미 보유 중)
   설정: CUDA + cuDNN 설치
   최적 용도: 정기적인 사용, 대규모 데이터셋

2. Google Colab (무료 티어)
   비용: $0
   설정: 없음
   최적 용도: 빠른 실험, 집에 GPU가 없는 경우

3. 클라우드 GPU (Lambda, RunPod, Vast.ai)
   비용: $0.20-2.00/시간
   설정: SSH + 설치
   최적 용도: 본격적인 훈련, 대규모 모델
```

## 빌드하기

### 옵션 1: 로컬 NVIDIA GPU

보유 여부 확인:

```bash
nvidia-smi
```

CUDA와 함께 PyTorch 설치:

```python
import torch

print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
print(f"CUDA 버전: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"메모리: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

### 옵션 2: Google Colab

1. [colab.research.google.com](https://colab.research.google.com)으로 이동
2. 런타임 > 런타임 유형 변경 > T4 GPU
3. `!nvidia-smi`를 실행하여 확인

이 과정의 노트북을 Colab에 직접 업로드하세요.

### 옵션 3: 클라우드 GPU

Lambda Labs, RunPod, Vast.ai의 경우:

```bash
ssh user@your-gpu-instance

pip install torch torchvision torchaudio
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### GPU가 없나요? 문제없습니다.

대부분의 레슨은 CPU에서 작동합니다. GPU가 필요한 레슨은 명시되어 있으며 Colab 링크가 포함됩니다.

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"사용 중: {device}")
```

## 빌드하기: GPU vs CPU 벤치마크

```python
import torch
import time

size = 5000

a_cpu = torch.randn(size, size)
b_cpu = torch.randn(size, size)

start = time.time()
c_cpu = a_cpu @ b_cpu
cpu_time = time.time() - start
print(f"CPU: {cpu_time:.3f}s")

if torch.cuda.is_available():
    a_gpu = a_cpu.to("cuda")
    b_gpu = b_cpu.to("cuda")

    torch.cuda.synchronize()
    start = time.time()
    c_gpu = a_gpu @ b_gpu
    torch.cuda.synchronize()
    gpu_time = time.time() - start
    print(f"GPU: {gpu_time:.3f}s")
    print(f"속도 향상: {cpu_time / gpu_time:.0f}x")
```

## 연습 문제

1. 위 벤치마크를 실행하고 CPU vs GPU 시간을 비교하세요
2. GPU가 없다면 Google Colab에서 실행하고 비교하세요
3. GPU 메모리가 얼마나 있는지 확인하고, 장착 가능한 최대 모델 크기를 추정하세요 (경험 법칙: fp16에서 파라미터당 2바이트)

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| CUDA | "GPU 프로그래밍" | GPU에서 코드를 실행할 수 있게 하는 NVIDIA의 병렬 컴퓨팅 플랫폼 |
| VRAM | "GPU 메모리" | GPU의 비디오 RAM, 시스템 RAM과 별개. 모델 크기를 제한함 |
| fp16 | "반정밀도" | 16비트 부동소수점, 최소한의 정확도 손실로 fp32 대비 절반의 메모리 사용 |
| 텐서 코어 | "빠른 행렬 하드웨어" | 행렬 곱셈을 위한 특수 GPU 코어, 일반 코어보다 4-8배 빠름 |