# ControlNet, LoRA & 조건

> 텍스트만으로는 控制 신호가 어색하다. ControlNet을 사용하면 사전 교육된 diffusion 모델을 복제하고 깊이 맵, 포즈 스켈레톤, 스케이블 또는 가장자리 이미지로 steering할 수 있다. LoRA를 사용하면 2B 매개변수 모델을 10억 개의 매개변수를 교육하여 미세 조정할 수 있다. 함께它们는 Stable Diffusion을 장난감에서 2026년 모든 에이전시에서出货하는 이미지 파이프라인으로 만들었다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 8 · 07 (Latent Diffusion), Phase 10 (LLMs from Scratch — LoRA 기반용)
**소요 시간:** ~75분

## 문제

"번화한 거리에서 개를 산책하는 빨간 드레스를 입은 여성"과 같은 프롬프트는 개가 *어디에* 있는지, 여성의 *포즈*가 어떤지, 거리의 *관점*이 어떤지에 대한 정보를 모델에 제공하지 않는다. 텍스트는 이미지를 지정하는 데 필요한 것의 약 10%만 고정한다. 나머지는 시각적이며 단어로 효율적으로 설명할 수 없다.

모든 신호 (포즈, 깊이, canny, 세그멘테이션)에 대해 처음부터 새로운 조건부 모델을 교육하는 것은 금지이다. 2.6B-param SDXL 백본을 동결 상태로 유지하고, 조건을 읽는 작은 측면 네트워크를 부착하고, 백본의 중간 특징을 nudge하게 하고 싶다. 그것이 ControlNet이다.

모델에 새로운 개념 (얼굴, 제품, 스타일)을 가르치고 싶지만 전체 모델을 재교육하지 않고. 100x 더 작은 delta를 원한다. 그것이 LoRA이다 — 기존 attention 가중치에 플러그인되는 낮은 순위 어댑터.

ControlNet + LoRA + 텍스트 = 2026년 실무자의 도구 키트. 대부분의 production 이미지 파이프라인은 SDXL / SD3 / Flux base 위에 2-5개의 LoRA, 1-3개의 ControlNet, IP-Adapter를 Layer한다.

## 개념

![ControlNet은 encoder를 복제; LoRA는 낮은 순위 delta를 추가](../assets/controlnet-lora.svg)

### ControlNet (Zhang et al., 2023)

사전 교육된 SD를 가져온다. U-Net의 encoder 절반을 *복제*한다. 원본을 동결한다. 복제본을 교육하여 추가 조건 입력 (에지, 깊이, 포즈)을 수락하도록 한다. *zero-convolution* 스킵 연결 (1×1 conv, 0으로 초기화 — 시작 시 no-op, delta를 학습)을 통해 복제본을 원본의 decoder 절반에 다시 연결한다.

```
SD U-Net decoder:   ... ← orig_enc_features + zero_conv(controlnet_enc(condition))
```

Zero-conv init은 ControlNet이 교육 전에도 해를 끼치지 않는 신원체로 시작함을 의미한다. 표준 diffusion 손실로 (프롬프트, 조건, 이미지) 트리플 1M개에서 교육한다.

Per-modality ControlNets는 작은 측면 모델로出货된다 (SDXL의 경우 ~360M, SD 1.5의 경우 ~70M). 추론時にそれらを 구성할 수 있다:

```
features += weight_a * control_a(depth) + weight_b * control_b(pose)
```

### LoRA (Hu et al., 2021)

모델의 любой 선형 레이어 `W ∈ R^{d×d}`에 대해 `W`를 동결하고 낮은 순위 delta를 추가한다:

```
W' = W + ΔW,  ΔW = B @ A,  A ∈ R^{r×d},  B ∈ R^{d×r}
```

`r << d`. 순위 4-16은 attention의 표준, 순위 64-128은 무거운 fine-tune용. 새 매개변수 수: `d²` 대신 `2 · d · r`. `d=640` 및 `r=16`의 SDXL attention의 경우: 어댑터당 20k params 대신 410k — 20x 감소. 전체 모델에서: LoRA는通常 20-200MB 대 기본 5GB.

추론 시 LoRA를 스케일할 수 있다: `W' = W + α · B @ A`. `α = 0.5-1.5`가 정상이다. 여러 LoRA가 추가적으로 스택된다 (비선형 방식으로 상호 작용한다는 usual caveat와 함께).

### IP-Adapter (Ye et al., 2023)

텍스트 alongside 이미지를 조건으로 수락하는 작은 어댑터 (약 20MB per base model). CLIP 이미지 인코더를 사용하여 이미지 토큰을 생성하고, 텍스트 토큰 alongside cross-attention에 주입한다. "이 레퍼런스의 스타일로 이미지 생성"을 LoRA 없이 할 수 있다.

## 구성 가능성 매트릭스

| 도구 | 제어하는 것 | 크기 | 사용하는 경우 |
|------|------------------|------|-------------|
| ControlNet | 공간 구조 (포즈, 깊이, 에지) | 70-360MB | 정확한 레이아웃, 구도 |
| LoRA | 스타일, 주체, 개념 | 20-200MB | 개인화, 스타일 |
| IP-Adapter | 레퍼런스 이미지에서 스타일 또는 주체 | 20MB | 텍스트가 룩을 설명할 수 없음 |
| Textual Inversion | 새 토큰으로 단일 개념 | 10KB | Legacy, 대부분 LoRA로 대체됨 |
| DreamBooth | 주제에 대한 전체 fine-tune | 2-5GB | 강한 정체성, 높은 계산 |
| T2I-Adapter | 더 가벼운 ControlNet 대안 | 70MB | 에지 장치, 추론 예산 |

ControlNet ≈ 공간. LoRA ≈ 의미론. 둘 다 사용한다.

## 실습

`code/main.py`는 1-D에서 두 가지 메커니즘을 시뮬레이션한다:

1. **LoRA.** 사전 교육된 선형 레이어 `W`. 동결. `W + BA`가 대상 선형 레이어와 일치하도록 낮은 순위 `B @ A`를 교육. `r = 1`이 순위 1 수정을 완벽하게 학습하는 데 충분함을 보여준다.

2. **ControlNet-lite.** 추가 신호를 읽는 "frozen base" predictor와 "side network". 측면 네트워크 출력은 0으로 초기화된 학습 가능한 스칼라에 의해 게이트됨 (zero-conv 버전). 교육하고 게이트가 램프업되는 것을 본다.

### Step 1: LoRA 수학

```python
def lora(W, A, B, x, alpha=1.0):
    return W @ x + alpha * (B @ A) @ x
```

### Step 2: ControlNet gate

```python
def controlnet_gate(frozen_features, side_features, gate):
    return frozen_features + gate * side_features
```

게이트가 0에서 시작하면 ControlNet은 identity이다.

## 활용

2026년 production 이미지 생성:

| 조합 | 용도 |
|------|------|
| SDXL + ControlNet-Depth + ControlNet-Pose | 정확한 공간 구도 |
| SDXL + LoRA(스타일) + LoRA(얼굴) | 개인화된 출력 |
| Flux + IP-Adapter | 레퍼런스 이미지 스타일을 사용하여 생성 |
| SDXL + 다중 LoRA | 특정 미학 또는 브랜드 스타일 |

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|-----------------------|
| ControlNet | "조건부 스톱" | 사전 교육된 모델의 encoder를 복제하여 조건을 주입. |
| Zero-convolution | "0으로 초기화된 conv" | 학습 가능한 delta를 위한Identity에서 시작. |
| LoRA | "저순위 적응" | 전체 가중치 대신 작은 행렬 쌍을 교육. |
| Rank | "r" | LoRA 행렬의 순위; 낮을수록 작고 효율적. |
| IP-Adapter | "이미지 조건" | 텍스트 alongside 이미지를 조건으로 사용. |
| Fine-tune | "사전 교육된 모델 조정" | 새로운 작업이나 도메인에 적응. |

## 추가 자료

- [Zhang et al. (2023). Adding Conditional Control to Text-to-Image Diffusion Models](https://arxiv.org/abs/2302.05543) — ControlNet.
- [Hu et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) — LoRA.
- [Ye et al. (2023). IP-Adapter: Text Compatible Image Prompt Adapter](https://arxiv.org/abs/2308.06721) — IP-Adapter.