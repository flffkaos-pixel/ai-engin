# Inpainting, Outpainting & 이미지 편집

> 텍스트-이미지가 새로운 것을 만든다. Inpainting은旧的 것을 수정한다. Production에서 청구 가능한 이미지 작업의 70%는 편집이다 — 배경을 교체하고, 로고를 제거하고, 캔버스를 확장하고, 손을 다시 생성한다. Inpainting은 diffusion이 그 값을稼ぐ 곳이다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 8 · 07 (Latent Diffusion), Phase 8 · 08 (ControlNet & LoRA)
**소요 시간:** ~75분

## 문제

클라이언트가 배경에 방해가 되는 표지판이 있는 완벽한 제품 사진을 보낸다. 표지판을 지우고 나머지는 모두 픽셀-identical로 남두고 싶다. 처음부터 텍스트-이미지를 실행할 수 없다 — 결과는 다른 색상, 다른 조명, 다른 제품 각도를 갖게 된다. *마스킹된 영역만* 다시 생성하고, 재생성이 주변 컨텍스트를 존중하게 하고 싶다.

그것이 inpainting이다. 변형:

- **Inpainting.** 마스크 내에서 다시 생성, 외부 픽셀 유지.
- **Outpainting.** 마스크 외부에서 다시 생성 (또는 캔버스 beyond), 내부 유지.
- **이미지 편집.** 전체 이미지를 다시 생성하지만 원본에 대한 의미론적 또는 구조적 충실도 유지 (SDEdit, InstructPix2Pix).

2026년 모든 diffusion 파이프라인은 inpainting 모드를 shipments한다. Flux.1-Fill, Stable Diffusion Inpaint, SDXL-Inpaint, DALL-E 3 Edit. 그들은 동일한 원리에서 작동한다.

## 개념

![Inpainting: 컨텍스트 보존 재주입으로 마스킹 인식 denoising](../assets/inpainting.svg)

### 순진한 접근 (그리고 왜 틀린가)

마스크로 표준 텍스트-이미지를 실행한다. 각 샘플링 단계에서 노이즈가 있는 잠재의 마스킹되지 않은 영역을 순방향 확산된 클린 이미지로 대체한다. 그것은 작동한다... 잘못. 모델이 마스킹된 영역에 무엇이 있는지 정보가 없기 때문에 경계 아티팩트가 스며든다.

### 적절한 inpainting 모델

9개의 입력 채널을 대신接受的 수정된 U-Net을 교육한다:

```
input = concat([ noisy_latent (4ch), encoded_image (4ch), mask (1ch) ], dim=channel)
```

추가 채널은 VAE 인코딩된 소스 이미지의 복사본 plus 단일 채널 마스크이다. 교육 시간에 이미지의 영역을 무작위로 마스킹하고 마스킹되지 않은 영역이 클린 조건 신호로 주어지는 동안 마스킹된 영역만 denoise하도록 모델을 교육한다. 추론 시 모델은 마스킹된 영역을 둘러싸는 것을 "볼" 수 있고 일관된 완성물을 생성한다.

SD-Inpaint, SDXL-Inpaint, Flux-Fill 모두 이 9채널 (또는 유사) 입력을 사용한다. Diffusers `StableDiffusionInpaintPipeline`, `FluxFillPipeline`.

### SDEdit (Meng et al., 2022) — 무료 편집

일부 중간 `t`까지 소스 이미지에 노이즈를 추가한 다음 새 프롬프트로 `t`에서 0까지 역방향 체인을 실행한다. 재교육 없음. 시작 `t`의 선택은 충실도와 창작 자유 사이를 trade한다:

- `t/T = 0.3` → 소스와 거의 동일, 작은 스타일 변경
- `t/T = 0.6` → 중간 편집, 대략적 구조 보존
- `t/T = 0.9` → near-noise에서 생성, 최소 소스 보존

### InstructPix2Pix (Brooks et al., 2023)

`(input_image, instruction, output_image)` 트리플에서 diffusion 모델을 미세 조정한다. 추론 시 입력 이미지와 텍스트 지시 모두 조건화한다 ("sunset으로 만들어", "용을 추가해"). 두 CFG 척도: 이미지 척도와 텍스트 척도.

### RePaint (Lugmayr et al., 2022)

표준 무조건 diffusion 모델을 유지한다. 각 역방향 단계에서resample — 가끔 더 노이즈가 있는 상태로 되돌아가서 다시 생성한다. 경계 아티팩트를 피한다. 훈련된 inpainting 모델이 없을 때 사용.

## 실습

`code/main.py`는 5차원 데이터에서 5차원 mixture에 대한 toy 1-D inpainting 방식을 구현한다. 각 샘플이 두 클러스터 중 하나의 5개 float인 5-D mixture 데이터에서 DDPM을 교육한다. 추론 시 5개 중 2개를 "마스킹"하고, 각 단계에서 마스킹되지 않은 3개의 노이즈가 있는 버전을 주입하고, 마스킹된 차원만 다시 생성한다.

### Step 1: 마스킹 및 주입

```python
def inpaint_step(x_noisy, x_clean_masked, mask, model, t):
    x_combined = x_noisy * mask + x_clean_masked * (1 - mask)
    return model(x_combined, t)
```

마스크 영역은 노이즈가 있는 버전으로 유지되고, 마스킹되지 않은 영역은 클린 버전으로 대체된다.

### Step 2: Iterative refinement

표준 DDPM 역방향 단계를 사용하되, 노이즈가 아닌 마스킹되지 않은 영역을 각 단계에서 다시 주입한다.

## 활용

2026년 inpainting 파이프라인:

| 도구 | 사용 사례 |
|------|---------------|
| SDXL-Inpaint | 일반적인 개체 제거 및 교체 |
| Flux.1-Fill | 고품질 컨텍스트 인식 채우기 |
| DALL-E 3 Edit | 텍스트 프롬프트로 세밀한 제어 |
| ControlNet-Inpaint | 공간 제어로 정교한 채우기 |

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Inpainting | "영역 다시 생성" | 마스크 내에서 콘텐츠를 대체하고 외부 픽셀을 보존. |
| Outpainting | "캔버스 확장" | 기존 이미지 beyond에서 콘텐츠 생성. |
| SDEdit | "노이즈 기반 편집" | 소스 이미지에 노이즈를 추가하고 역방향 실행. |
| Mask | "대상 영역" | 다시 생성할 영역을 정의하는 바이너리 맵. |
| Latent inpainting | "잠재 공간에서 처리" | 픽셀보다 잠재에서 마스킹 및 denoising. |

## 추가 자료

- [Tarun et al. (2023). FreeDoM: Training-Free Energy-Guided Diffusion Model](https://arxiv.org/abs/2311.16298) — zero-shot 편집.
- [Avrahami et al. (2023). Spatio-temporal Decoupling for Image Editing](https://arxiv.org/abs/2311.16460) — InstructPix2Pix.