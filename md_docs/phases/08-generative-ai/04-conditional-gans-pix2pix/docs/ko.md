# Conditional GANs & Pix2Pix

> 2014-2017의 첫 번째 큰 unlock은 GAN이 만드는 것을 제어하는 것이었다. 라벨, 또는 이미지, 또는 문장을 연결한다. Pix2Pix는 이미지 버전을 전문화했고, 여전히 모든 범용 텍스트-이미지 모델보다狭い 이미지-이미지 작업에서 이긴다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 8 · 03 (GANs), Phase 4 · 06 (U-Net), Phase 3 · 07 (CNNs)
**소요 시간:** ~75분

## 문제

비조건부 GAN은 임의의 얼굴을 샘플링한다. 데모에 유용하고 production에서 쓸모없다. 원하는 것: *스케치에서 사진으로*, *지도에서 항공 사진으로*, *주간 장면에서 야간으로*, *회색조 이미지를 색상으로*. 이 모든에서 입력 이미지 `x`가 주어지고 의미론적 대응이 있는 `y`를 출력해야 한다. 각 `x`당 많은 그럴듯한 `y`가 있다. 평균제곱오차는 그것들을 뭉개어 버린다. 적대적 손실은 그렇지 않다 — "실제처럼 보인다는 것"은 날카롭다.

Conditional GAN (Mirza & Osindero, 2014)은 조건 `c`를 `G`와 `D` 모두에 입력으로 추가한다. Pix2Pix (Isola et al., 2017)는 이것을 전문화했다: 조건은 전체 입력 이미지, 생성기는 U-Net, 판별기는 *패치 기반* 분류기 (PatchGAN), 손실은 적대적 + L1. 그 레시피는paired 데이터로 교육되기 때문에 정확한 신호를 갖기 때문에 2026년에도狭い 이미지-이미지 도메인에서 처음부터 텍스트-이미지 모델을 능가한다.

## 개념

![Pix2Pix: U-Net 생성기, PatchGAN 판별기](../assets/pix2pix.svg)

**Conditional G.** `G(x, z) → y`. Pix2Pix에서 `z`는 G 내부의 dropout이다 (입력 노이즈 없음 — Isola는 명시적 노이즈가 무시됨을 발견).

**Conditional D.** `D(x, y) → [0, 1]`. 입력을 *쌍* (조건, 출력)으로 한다. 이것이 핵심 차이: D는 `y`가 실제처럼 보이는지 여부가 아니라 `y`가 `x`와 일관성이 있는지 판단해야 한다.

**U-Net 생성기.** 봇틀neck을 가로지르는 스킵 연결이 있는 encoder-decoder. 입력과 출력이 저수준 구조 (에지, 실루엣)를 공유하는 작업에 중요. 스킵 없이는 고주파 detail이 사라진다.

**PatchGAN 판별기.** 단일 real/fake 점수 대신 출력하는 대신 D는 각 셀이 ~70×70 픽셀의 수용 필드를 판단하는 `N×N` 그리드를 출력한다. 평균. 이것은 Markov random field 가정이다: 사실성은 지역적이다. 훈련이 훨씬 빠르고 매개변수가 적으며 출력이 더 선명하다.

**손실.**

```
loss_G = -log D(x, G(x)) + λ · ||y - G(x)||_1
loss_D = -log D(x, y) - log (1 - D(x, G(x)))
```

L1 항은 교육을 안정화하고 G를 알려진 대상に向かって 밀어붙인다. L1은 L2 (중앙값, 평균이 아닌)보다 더 날카로운 에지를 제공한다. `λ = 100`이 Pix2Pix 기본값이었다.

## CycleGAN — 쌍이 없을 때

Pix2Pix는 paired `(x, y)` 데이터가 필요하다. CycleGAN (Zhu et al., 2017)은 추가 손실의 비용으로 이 요구사항을 삭제한다: *cycle consistency* 손실. 두 생성기 `G: X → Y`와 `F: Y → X`. `F(G(x)) ≈ x`와 `G(F(y)) ≈ y`가 되도록 교육한다. 이를 통해 paired 예제 없이 말을 얼룩말로, 여름을 겨울로 변환할 수 있다.

2026년, unpaired 이미지-이미지는 주로 CycleGAN보다 diffusion (ControlNet, IP-Adapter)을 통해 수행되지만, cycle-consistency 아이디어는 거의 모든 unpaired 도메인 적응 논문에서 생존한다.

## 실습

`code/main.py`는 1-D 데이터에서 tiny conditional GAN을 구현한다. 조건 `c`는 클래스 레이블 (0 또는 1)이다. 작업: 주어진 클래스에 대한 조건부 분포에서 샘플을 생성한다.

### Step 1: 조건을 G와 D 입력 모두에 추가

```python
def G(z, c, params):
    return mlp(concat([z, one_hot(c)]), params)

def D(x, c, params):
    return mlp(concat([x, one_hot(c)]), params)
```

원핫 인코딩이 가장 간단한 방법이다. 더 큰 모델은 학습된 임베딩, FiLM 변조 또는 cross-attention을 사용한다.

### Step 2: 조건부 교육

```python
for step in range(steps):
    x, c = sample_real_conditional()
    noise = sample_noise()
    update_D(x_real=x, x_fake=G(noise, c), c=c)
    update_G(noise, c)
```

생성기는 주어진 조건에 대한 실제 분포와 일치해야 한다 — 한계가 아니라.

### Step 3: 클래스별 출력 확인

```python
for c in [0, 1]:
    samples = [G(noise, c) for noise in batch]
    mean_c = mean(samples)
    assert_near(mean_c, real_mean_for_class_c)
```

## 함정

- **조건이 무시됨.** G가 주변화를 학습하고 D는 조건 신호가 약하기 때문에 Penelize하지 않는다. 수정: 조건을 더 적극적으로 (后期的 레이어가 아닌 초기 레이어), 투영 판별기 사용 (Miyato & Koyama 2018).
- **L1 가중치가 너무 낮음.** G가 실제처럼 보이는 임의의 출력으로 drift하고忠实한 것이 아니다. Pix2Pix 스타일 작업에 대해 λ≈100으로 시작한다.
- **L1 가중치가 너무 높음.** L1은 여전히 L_p norm이기 때문에 G가 blurry 출력을 생성한다. 교육이 안정되면 annealing down.
- **D의 ground-truth leakage.** `(x, y)`를 D 입력으로 연결하고 `y`만 아니라. 이것이 없으면 D는 일관성을 확인할 수 없다.
- **클래스별 mode collapse.** 각 클래스가 독립적으로 붕괴될 수 있다. 클래스 조건 diversity 검사를 실행한다.

## 활용

2026년 이미지-이미지 작업의 상태:

| 작업 | 최선 접근 |
|------|---------------|
| 스케치 → 사진, 동일한 도메인, paired 데이터 | Pix2Pix / Pix2PixHD (여전히 빠르고 여전히 선명) |
| 스케치 → 사진, unpaired | ControlNet과 Scribble 조건 모델 |
| 시맨틱 seg → 사진 | SPADE / GauGAN2 또는 SD + ControlNet-Seg |
| 스타일 전송 | IP-Adapter 또는 LoRA가 있는 diffusion; GAN 방법은 legacy |
| 깊이 → 사진 | Stable Diffusion 위의 ControlNet-Depth |
| 초해상도 | Real-ESRGAN (GAN), ESRGAN-Plus, 또는 SD-Upscale (diffusion) |
| 색상화 | ColTran, diffusion 기반 색상화 도구, 또는 Pix2Pix-색상 |
| 주간 → 야간, 계절, 날씨 | CycleGAN 또는 ControlNet 기반 |

Pix2Pix는 (a) 수천 개의 paired 예시가 있고, (b) 작업이 좁고 반복 가능하며, (c) 빠른 추론이 필요한 경우 올바른 도구로 유지된다. 범용 개방형 작업에서 diffusion이 이긴다.

## 결과물

`outputs/skill-img2img-chooser.md`를 저장한다. Skill은 작업 설명, 데이터 가용성 (paired vs unpaired, N 샘플), 지연 시간/품질 예산을 가져와서: 접근 방식 (Pix2Pix, CycleGAN, ControlNet 변형, SDXL + IP-Adapter), 교육 데이터 요구 사항, 추론 비용, 평가 프로토콜 (LPIPS, FID, 작업 특정)을 출력한다.

## 연습 문제

1. **쉬움.** 세 번째 클래스를 추가하도록 `code/main.py`를 수정한다. G가 각 클래스의 노이즈를 여전히 정확한 모드로 매핑하는지 확인한다.
2. **보통.** 1-D 설정에서 perceptual-style 손실로 L1을 교체한다 (예: 작은 동결 D가 특징 추출기로Acting). 조건부 분포의 선명도가 변경되는가?
3. **어려움.** 1-D 설정에서 CycleGAN을 스케치: 두 분포, 두 생성기, cycle 손실. paired 데이터 없이 그들 사이를 매핑하는 것을 학습함을 보여준다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|-----------------------|
| Conditional GAN | "라벨이 있는 GAN" | G(z, c), D(x, c). 두 네트워크 모두 조건을 본다. |
| Pix2Pix | "이미지-이미지 GAN" | U-Net G와 PatchGAN D + L1 손실이 있는 paired cGAN. |
| U-Net | "스킵이 있는 encoder-decoder" | 대칭conv 네트워크; 스킵은 고주파를 보존. |
| PatchGAN | "국부 사실성 분류기" | D는 글로벌 점수 대신 패치당 점수를 출력. |
| CycleGAN | "Unpaired 이미지 번역" | 두 G + cycle-consistency 손실; paired 데이터 없음. |
| SPADE | "GauGAN" | 시맨틱 맵으로 중간 활성화 정규화; 세그멘테이션-이미지. |
| FiLM | "Feature-wise linear modulation" | 조건에서 per-feature affine 변환; 저렴한 조건. |

## Production note: Pix2Pix를 지연 시간 경계 기준으로

paired 데이터와 좁은 작업 (스케치 → 렌더, 시맨틱 맵 → 사진, 낮 → 밤)이 있을 때 Pix2Pix의 원샷 추론은 지연 시간에서 diffusion보다 한 자릿수 빠르다. Production 비교는通常 다음과 같다:

| 경로 | 단계 | 단일 L4에서 512²의典型 지연 |
|------|-------|----------------------------------------|
| Pix2Pix (U-Net forward) | 1 | ~30 ms |
| SD-Inpaint 또는 SD-Img2Img | 20 | ~1.2 s |
| SDXL-Turbo Img2Img | 1-4 | ~0.15-0.35 s |
| ControlNet + SDXL base | 20-30 | ~3-5 s |

Pix2Pix는 정적 배치에서 처리량 측면에서 이긴다 (모든 요청이 동일한 FLOP). Diffusion은 품질과 일반화에서 이긴다. 현대적인 플레이는 часто 좁은 작업에 대해 Pix2Pix 스타일 증류 모델을出货하고 tail 입력에 대해 diffusion fallback을出货하는 것이다.

## 추가 자료

- [Mirza & Osindero (2014). Conditional Generative Adversarial Nets](https://arxiv.org/abs/1411.1784) — cGAN 논문.
- [Isola et al. (2017). Image-to-Image Translation with Conditional Adversarial Networks](https://arxiv.org/abs/1611.07004) — Pix2Pix.
- [Zhu et al. (2017). Unpaired Image-to-Image Translation using Cycle-Consistent Adversarial Networks](https://arxiv.org/abs/1703.10593) — CycleGAN.
- [Wang et al. (2018). High-Resolution Image Synthesis with Conditional GANs](https://arxiv.org/abs/1711.11585) — Pix2PixHD.
- [Park et al. (2019). Semantic Image Synthesis with Spatially-Adaptive Normalization](https://arxiv.org/abs/1903.07291) — SPADE / GauGAN.
- [Miyato & Koyama (2018). cGANs with Projection Discriminator](https://arxiv.org/abs/1802.05637) — 투영 D.