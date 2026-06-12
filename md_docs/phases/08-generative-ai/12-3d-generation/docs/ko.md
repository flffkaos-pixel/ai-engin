# 3D 생성

> 3D는 2D-to-3D 활용이 가장 강력한 모달리티입니다. 2023년 돌파구는 3D 가우시안 스플래팅이었습니다. 2024-2026년 생성형 AI는 단일 프롬프트나 사진에서 객체와 장면을 생성하기 위해 다중 뷰 확산 + 3D 재구성을 층으로 쌓아 올리고 있습니다.

**유형:** 학습
**언어:** Python
**선수 과목:** Phase 4 (Vision), Phase 8 · 07 (Latent Diffusion)
**소요 시간:** ~45분

## 문제

3D 콘텐츠는 고통스럽습니다:

- **표현 방식.** 메쉬, 포인트 클라우드, 복셀 그리드, 부호 거리장(signed distance fields, SDF), 신경 방사장(neural radiance fields, NeRF), 3D 가우시안. 각각 장단점이 있습니다.
- **데이터 부족.** ImageNet에는 1,400만 장의 이미지가 있습니다. 가장 큰 정제된 3D 데이터셋(Objaverse-XL, 2023)은 ~1,000만 개의 객체를 보유하고 있지만 대부분 품질이 낮습니다.
- **메모리.** 512³ 복셀 그리드는 1억 2,800만 복셀입니다. 유용한 장면 NeRF는 레이당 100만 샘플이 필요합니다. 생성은 재구성보다 어렵습니다.
- **감독.** 2D 이미지에는 픽셀이 있습니다. 3D의 경우通常是 몇 개의 2D 뷰만 있고 이를 3D로 올려야 합니다.

2026년 스택은 두 가지 문제를 분리합니다. 첫째, 확산 모델로 *2D 다중 뷰 이미지*를 생성합니다. 둘째, 해당 이미지에 *3D 표현*(일반적으로 가우시안 스플래팅)을 피팅합니다.

## 개념

![3D 생성: 다중 뷰 확산 + 3D 재구성](../assets/3d-generation.svg)

### 표현 방식: 3D 가우시안 스플래팅 (Kerbl et al., 2023)

~100만 개의 3D 가우시안 클라우드로 장면을 표현합니다. 각각 59개의 파라미터를 가집니다: 위치(3), 공분산(6, 또는 쿼터니언 4 + 스케일 3), 불투명도(1), 구면 조화 색상(3차원에서 48개, 0차원에서 3개).

렌더링 = 투영 + 알파 합성. 빠름(~4090에서 1080p @ 100fps). 미분 가능. 실사 사진에 대한 경사 하강법으로 피팅. 장면 피팅은 소비자용 GPU에서 5-30분 소요.

2023-2024년의 두 가지 혁신:

- **생성형 가우시안 스플랫.** LGM, LRM, InstantMesh와 같은 모델이 하나 또는 몇 개의 이미지에서 직접 가우시안 클라우드를 예측합니다.
- **4D 가우시안 스플래팅.** 동적 장면을 위한 프레임별 오프셋이 있는 가우시안.

### 다중 뷰 확산

미리 학습된 이미지 확산 모델을 미세 조정하여 텍스트 프롬프트나 단일 이미지에서 동일한 객체의 여러 일관된 뷰를 생성합니다. Zero123 (Liu et al., 2023), MVDream (Shi et al., 2023), SV3D (Stability, 2024), CAT3D (Google, 2024). 일반적으로 객체 주변 4-16개 뷰를 출력하며, 가우시안 스플래팅이나 NeRF를 통해 3D로 올립니다.

### 텍스트-3D 파이프라인

| 모델 | 입력 | 출력 | 시간 |
|------|------|------|------|
| DreamFusion (2022) | 텍스트 | SDS를 통한 NeRF | 에셋당 ~1시간 |
| Magic3D | 텍스트 | 메쉬 + 텍스처 | ~40분 |
| Shap-E (OpenAI, 2023) | 텍스트 | 암시적 3D | ~1분 |
| SJC / ProlificDreamer | 텍스트 | NeRF / 메쉬 | ~30분 |
| LRM (Meta, 2023) | 이미지 | 트라이플레인 | ~5초 |
| InstantMesh (2024) | 이미지 | 메쉬 | ~10초 |
| SV3D (Stability, 2024) | 이미지 | 새로운 뷰 | ~2분 |
| CAT3D (Google, 2024) | 1-64개 이미지 | 3D NeRF | ~1분 |
| TripoSR (2024) | 이미지 | 메쉬 | ~1초 |
| Meshy 4 (2025) | 텍스트 + 이미지 | PBR 메쉬 | ~30초 |
| Rodin Gen-1.5 (2025) | 텍스트 + 이미지 | PBR 메쉬 | ~60초 |
| Tencent Hunyuan3D 2.0 (2025) | 이미지 | 메쉬 | ~30초 |

2025-2026년 방향: 게임 엔진에 적합한 PBR 재질의 직접 텍스트-메쉬 모델. 다중 뷰 확산 중간 단계는 일반 객체에 대해 여전히 최고의 성능을 자랑하는 레시피입니다.

### NeRF (컨텍스트용)

Neural Radiance Field (Mildenhall et al., 2020). 작은 MLP가 `(x, y, z, 뷰 방향)`을 입력받아 `(색상, 밀도)`를 출력합니다. 레이를 따라 적분하여 렌더링합니다. 품질 면에서 메쉬 기반 새로운 뷰 합성을 능가하지만 렌더링 속도가 100-1000배 느립니다. 대부분의 실시간 사용에서 가우시안 스플래팅으로 대체되었지만 연구에서는 여전히 지배적입니다.

## 실습

`code/main.py`는 합성 대상 이미지(부드러운 그라데이션)를 2D 가우시안 스플랫의 합으로 표현하는toy 2D "가우시안 스플래팅" 피팅을 구현합니다. 위치, 색상, 공분산을 경사 하강법으로 최적화하여 대상과 일치시킵니다. 두 가지 핵심 연산을 볼 수 있습니다: 순방향 렌더링(스플랫 + 알파 합성)과 경사 하강법으로 피팅.

### Step 1: 2D 가우시안 스플랫

```python
def gaussian_at(x, y, gaussian):
    px, py = gaussian["pos"]
    sigma = gaussian["sigma"]
    d2 = (x - px) ** 2 + (y - py) ** 2
    return math.exp(-d2 / (2 * sigma * sigma))
```

### Step 2: 스플랫을 합산하여 렌더링

```python
def render(image_size, gaussians):
    img = [[0.0] * image_size for _ in range(image_size)]
    for g in gaussians:
        for y in range(image_size):
            for x in range(image_size):
                img[y][x] += g["color"] * gaussian_at(x, y, g)
    return img
```

실제 3D 가우시안 스플래팅은 깊이별로 가우시안을 정렬하고 순서대로 알파 합성합니다. 우리의 2D toy는 그냥 합산합니다.

### Step 3: 경사 하강법으로 피팅

```python
for step in range(steps):
    pred = render(size, gaussians)
    loss = mse(pred, target)
    gradients = compute_grads(pred, target, gaussians)
    update(gaussians, gradients, lr)
```

## 함정

- **뷰 불일치.** 4개의 뷰를 독립적으로 생성하고 객체 구조에 동의하지 않으면 3D 피팅이 흐릿해집니다. 해결: 공유 어텐션을 사용한 다중 뷰 확산.
- ** 뒷면 환각.** 단일 이미지 → 3D는 보이지 않는 쪽을 발명해야 합니다. 품질이 크게 달라집니다.
- **가우시안 스플래팅 폭발.** 무제약 학습은 1,000만 스플래트로 성장하여 과적합됩니다. 밀집화 +修剪启发式(3D-GS 원본 논문에서)이 필수적입니다.
- **토폴로지 문제.** 암시적 필드(SDF)의 메쉬는 종종 구멍이나 자기 교차를 가집니다. 배송 전에 리메셔(예: blender의 복셀 리메쉬)를 실행하세요.
- **학습 데이터 라이선스.** Objaverse는 다양한 라이선스를 가집니다; 상업적 사용은 모델마다 다릅니다.

## 활용

| 작업 | 2026년 선택 |
|------|-------------|
| 사진에서 장면 재구성 | 가우시안 스플래팅 (3DGS, Gsplat, Scaniverse) |
| 게임용 텍스트-3D 객체 | Meshy 4 또는 Rodin Gen-1.5 (PBR 출력) |
| 이미지-3D | Hunyuan3D 2.0, TripoSR, InstantMesh |
| 몇 개의 이미지에서 새로운 뷰 합성 | CAT3D, SV3D |
| 동적 장면 재구성 | 4D 가우시안 스플래팅 |
| 아바타 / 의복 입은 인간 | Gaussian Avatar, HUGS |
| 연구 / SOTA | 지난 주에 등장한 모델 |

게임이나 이커머스 파이프라인에서 프로덕션 3D를 배송하려면: Meshy 4 또는 Rodin Gen-1.5가 Unity / Unreal에 바로 들어가는 PBR 메쉬를 출력합니다.

## 결과물

`outputs/skill-3d-pipeline.md`를 저장하세요. Skill은 3D 브리프(입력: 텍스트 / 한 이미지 / 몇 개의 이미지; 출력: 메쉬 / 스플랫 / NeRF; 사용: 렌더링 / 게임 / VR)를 가져와서 출력합니다: 파이프라인(다중 뷰 확산 + 피팅, 또는 직접 메쉬 모델), 기본 모델, 반복 예산, 토폴로지 사후 처리, 필요한 재질 채널.

## 연습 문제

1. **쉬움.** `code/main.py`를 4, 16, 64개의 가우시안으로 실행하세요. 최종 MSE vs 대상을 보고하세요.
2. **보통.** 색상 가우시안(RGB)으로 확장하세요. 재구성이 대상 색상 패턴과 일치하는지 확인하세요.
3. **어려움.** gsplat 또는 Nerfstudio를 사용하여 50장 사진 캡처에서 실제 객체를 재구성하세요. 피팅 시간과 held-out 뷰에 대한 최종 SSIM을 보고하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 3D 가우시안 스플래팅 | "3DGS" | 3D 가우시안 클라우드의 장면; 미분 가능한 알파 합성 렌더링. |
| NeRF | "Neural radiance field" | 3D 점에서 색상 + 밀도를 출력하는 MLP; 레이 적분을 통해 렌더링. |
| 트라이플레인 | "세 개의 2D 평면" | 3D를 세 개의 2D 축 정렬 특성 그리드로 분해; 체적 방식보다 저렴. |
| SDS | "Score distillation sampling" | 2D 확산 점수를 의사 경사로 사용하여 3D 모델을 학습. |
| 다중 뷰 확산 | "한 번에 여러 뷰" | 일관된 카메라 뷰 배치를 출력하는 확산 모델. |
| PBR | "Physically-based rendering" | 알베도, 러프니스, 메탈릭, 노말 채널이 있는 재질. |
| 밀집화 | "스플래팅 성장" | 3DGS 학습启发식: 높은 경사 영역에서 스플래팅을 분할/복제. |

## 프로덕션 노트: 3D는 아직 공유 기지가 없습니다

이미지(latent diffusion + DiT)와 비디오(시공간 DiT)와 달리, 3D는 2026년에 단일 지배적 런타임이 없습니다. 프로덕션 결정 트리는 표현 방식에서 분기됩니다:

- **NeRF / 트라이플레인.** 추론은 레이 마칭 + 샘플당 MLP 순방향입니다. 512² 렌더링은 수백만 개의 MLP 순방향을 요구합니다. 레이 샘플을 적극적으로 배치하세요; SDPA/xformers가 적용됩니다.
- **다중 뷰 확산 + LRM 재구성.** 2단계 파이프라인. Stage 1(다중 뷰 DiT)은 Lesson 07과 똑같은 확산 서버입니다. Stage 2(LRM 트랜스포머)는 뷰에 대한 원샷 순방향 패스입니다. 전체 지연 프로파일은 "확산 + 원샷"입니다 — 단계별 서빙 기본 요소를 적절히 선택하세요.
- **SDS / DreamFusion.** 에셋별 최적화, 추론이 아닙니다. 빌드 작업이지 요청 핸들러가 아닙니다.

2026년 대부분의 제품에 올바른 답은 "요청 시 다중 뷰 확산 모델을 실행하고, 3DGS로 비동기적으로 재구성하고, 실시간 뷰잉를 위해 3DGS를 서빙하는 것"입니다. 이것은 GPU 추론 서버(빠름)와 오프라인 옵티마이저(느림) 사이의 작업을 깔끔하게 분리합니다.

## 추가 자료

- [Mildenhall et al. (2020). NeRF: Representing Scenes as Neural Radiance Fields](https://arxiv.org/abs/2003.08934) — NeRF.
- [Kerbl et al. (2023). 3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://arxiv.org/abs/2308.04079) — 3DGS.
- [Poole et al. (2022). DreamFusion: Text-to-3D using 2D Diffusion](https://arxiv.org/abs/2209.14988) — SDS.
- [Liu et al. (2023). Zero-1-to-3: Zero-shot One Image to 3D Object](https://arxiv.org/abs/2303.11328) — Zero123.
- [Shi et al. (2023). MVDream](https://arxiv.org/abs/2308.16512) — 다중 뷰 확산.
- [Hong et al. (2023). LRM: Large Reconstruction Model for Single Image to 3D](https://arxiv.org/abs/2311.04400) — LRM.
- [Gao et al. (2024). CAT3D: Create Anything in 3D with Multi-View Diffusion Models](https://arxiv.org/abs/2405.10314) — CAT3D.
- [Stability AI (2024). Stable Video 3D (SV3D)](https://stability.ai/research/sv3d) — SV3D.