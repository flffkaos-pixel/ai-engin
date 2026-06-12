# Stable Diffusion

> 텍스트 → U-Net에서 노이즈 예측 → 이미지. 그게 핵심입니다.

**유형:** 빌드  
**언어:** Python  
**시간:** ~90분

## 개념

- **VAE**: 이미지 ↔ 잠재 공간 압축/복원
- **U-Net**: 잠재 공간에서 노이즈 예측 (텍스트 조건부)
- **CLIP 텍스트 인코더**: 프롬프트 → 임베딩 → U-Net 유도
- **스케줄러**: 노이즈 제거 단계 제어

## 주요 구성 요소

```
텍스트 → CLIP 인코더 → 임베딩
                            ↓
노이즈 → U-Net(잠재 공간) → 예측 노이즈
                            ↓
                    VAE 디코더 → 이미지
```

## 빌드하기

```python
from diffusers import StableDiffusionPipeline
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
pipe.to("cuda")
image = pipe("a cat wearing a hat").images[0]
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| 잠재 공간 | 압축된 표현 — 메모리/속도 효율 |
| 조건부 생성 | 텍스트/이미지로 출력 제어 |
| CFG (분류기 없는 안내) | 프롬프트 충실도 향상 |