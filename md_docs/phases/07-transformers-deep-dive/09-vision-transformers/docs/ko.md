# Vision Transformers (ViT)

> 이미지는 패치의 그리드이다. 문장은 토큰의 그리드이다. 동일한 transformer가 둘 다 먹는다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 05 (Full Transformer), Phase 4 · 03 (CNNs), Phase 4 · 14 (Vision Transformers intro)
**소요 시간:** ~45분

## 문제

2020년 이전에는 컴퓨터 비전이 컨볼루션을 의미했다. ImageNet, COCO 및 감지 벤치마크의 모든 SOTA는 CNN 백본을 사용했다. Transformers는 언어용이었다.

Dosovitskiy et al. (2020) — "An Image is Worth 16x16 Words" — 컨볼루션을 완전히 제거할 수 있음을 보여주었다. 이미지를 고정 크기 패치로 슬라이스하고, 각 패치를 선형으로 임베딩에 프로젝션하고, vanilla transformer encoder에 시퀀스를 공급한다. 충분한 규모에서 (ImageNet-21k 사전 교육 이상) ViT는 ResNet 기반 모델과 같거나 능가한다.

ViT는 2026년 더 넓은 패턴의 시작이었다: 하나의 아키텍처, 여러 양식. Whisper는 오디오를 토큰화한다. ViT는 이미지를 토큰화한다. 로봇 공학용 작업 토큰. 비디오용 픽셀 토큰. Transformer는 상관없다 — 시퀀스를 공급하면 학습한다.

2026년까지 ViT와 그 후손 (DeiT, Swin, DINOv2, ViT-22B, SAM 3)은 대부분의 비전을 소유한다. CNN은 여전히 에지 장치와 지연 시간에 민감한 작업에서 이긴다. 나머지에는 모두 ViT가 스택 어딘가에 있다.

## 개념

![이미지 → 패치 → 토큰 → transformer](../assets/vit.svg)

### Step 1 — patchify

`H × W × C` 이미지를 평면화된 패치의 `N × (P·P·C)` 시퀀스로 분할한다. 일반적인 설정: `224 × 224` 이미지, `16 × 16` 패치 → 각 768값의 196 패치.

```
image (224, 224, 3) → 16x16x3 패치의 14 × 14 그리드 → 길이 768의 196 벡터
```

패치 크기가 지렛대이다. 더 작은 패치 = 더 많은 토큰, 더 나은 해상도, 2차 attention 비용. 더 큰 패치 = 더 거칠고 저렴.

### Step 2 — 선형 임베딩

각 평면화된 패치를 `d_model`로 프로젝션하는 단일 학습 행렬. 커널 크기 `P`와 stride `P`의 컨볼루션과 동일. PyTorch에서 이것은 literally `nn.Conv2d(C, d_model, kernel_size=P, stride=P)`이다 — 2줄 구현.

### Step 3 — 앞에 `[CLS]` 토큰 추가, 위치 임베딩 추가

- 학습 가능한 `[CLS]` 토큰을 앞에 추가한다. Its 최종 숨겨진 상태는 분류에 사용되는 이미지 표현이다.
- 학습 가능한 위치 임베딩 (ViT-원본) 또는 정현파 2D (이후 변형)를 추가한다.
- 2024+에서 RoPE가 2D로 위치를 위해 확장되고, 때때로 명시적 임베딩 없이.

### Step 4 — 표준 transformer encoder

`LayerNorm → Self-Attention → + → LayerNorm → MLP → +`의 L 블록을 쌓는다. BERT와 동일. 비전 특정 레이어 없음. 이것이 논문의 교육적 결론이다.

### Step 5 — head

분류용: `[CLS]` 숨겨진 상태 → 선형 → softmax. DINOv2 또는 SAM용: `[CLS]`를 버리고 패치 임베딩을 직접 사용.

### 중요했던 변형

| 모델 | 연도 | 변경 사항 |
|-------|------|--------|
| ViT | 2020 | 원본. 고정 패치 크기, 전체 전역 attention. |
| DeiT | 2021 | 증류; ImageNet-1k에서만 교육 가능. |
| Swin | 2021 | Shifted windows가 있는 계층적. 고정 하위 2차 비용. |
| DINOv2 | 2023 | Self-supervised (레이블 없음). 최상의 범용 비전 특징. |
| ViT-22B | 2023 | 22B 매개변수; 스케일링 법칙이 적용됨. |
| SigLIP | 2023 | ViT + 언어 쌍, 시그모이드 대조 손실. 매칭된 계산에서 CLIP보다 나음. |
| SAM 3 | 2025 | Segment anything; ViT-Large + promptable mask decoder. |

### 왜 걸렸는지

ViT는 CNN보다 *훨씬 많은* 데이터를 필요로 한다 —它在视觉 inductive biases（翻译不变性、局部性）方面没有任何先验知识。Without >100M标记图像或强大的自我监督预训练，CNN在匹配计算时仍然获胜。DeiT在2021年用蒸馏技巧解决了这个问题；DINOv2在2023年用自我监督永久解决了这个问题。

## 실습

`code/main.py`를 참조. Pure-stdlib patchify + 선형 임베딩 + 정합성 검사. 교육 없음 — 현실적인 규모의 ViT는 PyTorch와 수時間の GPU 시간이 필요하다.

### Step 1: 가짜 이미지

`(R, G, B)` 튜플의 행 목록으로 24 × 24 RGB 이미지. 6×6 패치 사용 → 16 패치, 각각 108-d 임베딩 벡터.

### Step 2: patchify

```python
def patchify(image, P):
    H = len(image)
    W = len(image[0])
    patches = []
    for i in range(0, H, P):
        for j in range(0, W, P):
            patch = []
            for di in range(P):
                for dj in range(P):
                    patch.extend(image[i + di][j + dj])
            patches.append(patch)
    return patches
```

래스터 순서: 그리드를 따라 행 우선. 모든 ViT가 이 순서를 사용한다.

### Step 3: 선형 임베딩

각 평면화된 패치에 무작위 `(patch_flat_size, d_model)` 행렬을 곱한다. `[CLS]`를 앞에 추가한 후 출력 shape가 `(N_patches + 1, d_model)`인지 확인한다.

### Step 4: 현실적인 ViT에 대한 매개변수 수 계산

ViT-Base에 대한 매개변수 수 인쇄: 12 레이어, 12 heads, d=768, patch=16. ResNet-50 (~25M)과 비교. ViT-Base는 ~86M에 있다. ViT-Large ~307M. ViT-Huge ~632M.

## 활용

```python
from transformers import ViTImageProcessor, ViTModel
import torch
from PIL import Image

processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
model = ViTModel.from_pretrained("google/vit-base-patch16-224-in21k")

img = Image.open("cat.jpg")
inputs = processor(img, return_tensors="pt")
out = model(**inputs).last_hidden_state   # (1, 197, 768): [CLS] + 196 패치
cls_emb = out[:, 0]                       # 이미지 표현
```

**DINOv2 임베딩은 2026년 이미지 특징의 기본값이다.** 백본을 동결하고 작은 head를 교육한다. 분류, 검색, 감지, 캡셔닝에 작동한다. Meta의 DINOv2 체크포인트는 모든 비텍스트 비전 작업에서 CLIP보다 우수하다.

**패치 크기 선택.** 작은 모델은 16×16 사용 (ViT-B/16). 밀도 예측 (세그멘테이션)은 8×8 또는 14×14 사용 (SAM, DINOv2). 매우 큰 모델은 14×14 사용.

## 결과물

`outputs/skill-vit-configurator.md`를 참조. 이 skill는 데이터 세트 크기, 해상도 및 계산 예산을 고려하여 새 비전 작업에 대한 ViT 변형과 패치 크기를 선택한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행한다. 패치 수가 `(H/P) * (W/P)`와 같고 평면화된 패치 차원이 `P*P*C`와 같은지 확인한다.
2. **보통.** 2D 정현파 위치 임베딩 구현 — 패치의 `row`와 `col` 각각에 대해 두 개의 독립적인 정현파 코드, 연결됨. Tiny PyTorch ViT에 공급하고 CIFAR-10에서 학습 가능한 위치 임베딩과 정확도를 비교한다.
3. **어려움.** 3층 ViT (PyTorch)를 구축하고 4×4 패치로 1,000개의 MNIST 이미지로 교육한다. 테스트 정확도를 측정한다. 이제 동일한 1,000개 이미지로 DINOv2 사전 교육 추가 (간단화: 마스킹된 패치에서 패치 임베딩을 예측하도록 encoder 교육). 정확도가 향상되는가?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Patch | "비전-transformer 토큰" | 이미지의 `P × P × C` 영역에 대한 픽셀 값의 평면 벡터. |
| Patchify | "잘라서 평면화" | 이미지를 겹치지 않는 패치로 분할하고, 각각을 벡터로 평면화. |
| `[CLS]` token | "이미지 요약" | 모든 시퀀스 앞에 추가된 학습 가능한 토큰; Its 최종 임베딩은 이미지 표현. |
| Inductive bias | "모델이 가정하는 것" | ViT는 CNN보다 더 적은 사전 지식이 있다; 격차를 메우기 위해 더 많은 데이터가 필요. |
| DINOv2 | "Self-supervised ViT" | 이미지 증강 + 모멘텀 teacher를 사용하여 레이블 없이 교육. 2026년 최상의 범용 이미지 특징. |
| SigLIP | "CLIP의 후계자" | 시그모이드 대조 손실로 교육된 ViT + 텍스트 인코더; 매칭된 계산에서 CLIP보다 나음. |
| Swin | "Windowed ViT" | 로컬 attention + shifted windows가 있는 계층적 ViT; 하위 2차. |
| Register tokens | "2023 트릭" | attention sinks를 흡수하는 몇 가지 추가 학습 가능한 토큰; DINOv2 특징을 개선. |

## 추가 자료

- [Dosovitskiy et al. (2020). An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale](https://arxiv.org/abs/2010.11929) — ViT 논문.
- [Touvron et al. (2021). Training data-efficient image transformers & distillation through attention](https://arxiv.org/abs/2012.12877) — DeiT.
- [Liu et al. (2021). Swin Transformer: Hierarchical Vision Transformer using Shifted Windows](https://arxiv.org/abs/2103.14030) — Swin.
- [Oquab et al. (2023). DINOv2: Learning Robust Visual Features without Supervision](https://arxiv.org/abs/2304.07193) — DINOv2.
- [Darcet et al. (2023). Vision Transformers Need Registers](https://arxiv.org/abs/2309.16588) — DINOv2용 register-token 수정.