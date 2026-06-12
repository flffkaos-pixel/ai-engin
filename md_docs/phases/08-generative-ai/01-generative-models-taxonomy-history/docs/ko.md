# 생성 모델 — 분류와 역사

> 모든 이미지 모델, 텍스트 모델, 비디오 모델, 3D 모델은 다섯 개의 버킷 중 하나에 속한다. 잘못된 버킷을 선택하면 수학적 논리로 몇 주를 싸울 것이다. 올바른 버킷을 선택하면 지난 12년간의 발전이 머릿속에 깔끔하게 쌓인다.

**유형:** 학습
**언어:** Python
**선수 과목:** Phase 2 (ML Fundamentals), Phase 3 (Deep Learning Core), Phase 7 · 14 (Transformers)
**소요 시간:** ~45분

## 문제

생성 모델은 하나의 작업을 수행한다: 어떤 알려지지 않은 분포 `p_data(x)`에서 추출한 교육 샘플이 주어지면, 동일한 분포에서 온 것처럼 보이는 새로운 샘플을 출력한다. 얼굴, 문장, MIDI 파일, 단백질 구조 — 모두 같은 문제로 볼 수 있다.

문제는 `p_data`가 수백만 차원의 공간에 존재한다는 것이다 (512x512 RGB 이미지는 ~786k 차원). 샘플은 그 공간 내 얇은 매니폴드에 있고, 예는 ~10M개뿐이다. 밀도를 무식하게 접근하는 것은 희망 없다. 모든 생성 모델은 하나의 힘든 문제를 조금 덜 힘든 것으로 trade하는妥协이다.

5개의 패밀리가 지난 12년간 살아남았다. 각 패밀리가 어떤妥协을 하는지 알면 왜 일부 작업에서 이기고 다른 작업에서 붕괴하는지 이해할 수 있다.

## 개념

![생성 모델의 다섯 패밀리 — 무엇을 모델링하는지에 따른 분류](../assets/taxonomy.svg)

**1. 명시적 밀도,tractable.** 실제로 평가할 수 있는 합으로 `log p(x)`를 작성한다. Autoregressive 모델 (PixelCNN, WaveNet, GPT)는 `p(x) = ∏ p(x_i | x_<i)`로 인수분해한다. Normalizing flows (RealNVP, Glow)는 단순한 기본 분포의 可逆 변환으로 `p(x)`를 구축한다. 장점: 정확한 우도, 깨끗한 교육 손실. 단점: autoregressive 추론은 순차적 (긴 시퀀스에 느림), flows는 可逆 아키텍처 필요 (아키텍처 제한).

**2. 명시적 밀도, 근사.** `log p(x)`를 아래에서 제한 (ELBO)하고 제한을 최적화한다. VAE (Kingma 2013)는 변분 사후 분포가 있는 encoder-decoder를 사용한다. Diffusion 모델 (DDPM, Ho 2020)은 암묵적으로 가중 ELBO를 최적화하는 denoiser를 교육한다. Diffusion은 2026년 지배적인 이미지, 비디오 및 3D 백본이다.

**3. 암묵적 밀도.** 밀도를 완전히 건너뛰고; 샘플을 생성하는 생성기 `G(z)`와 진짜에서 가짜를 구분하는 판별기 `D(x)`를 학습한다. GAN (Goodfellow 2014). 추론 시 빠름 (한 번의 forward 통과) 하지만 교육 중에는 유명하게 불안정. StyleGAN 1/2/3는 2026년에도 고정 도메인 포토리얼리즘 (얼굴, 침실)에 대해 최첨단으로 남아 있다.

**4. Score-based / 연속 시간.** log-밀도의 gradient `∇_x log p(x)` (score)를 직접 학습한다. Song & Ermon (2019)은 score matching이 diffusion을 SDE로 일반화함을 보여주었다. Flow matching (Lipman 2023)은 2024-2026년 유행: 시뮬레이션 자유 교육, 더 곧은 경로, DDPM보다 4-10x 더 빠른 샘플링. Stable Diffusion 3, Flux, AudioCraft 2 모두 flow matching을 사용한다.

**5. 이산 코드의Token-based autoregressive.** VQ-VAE 또는 잔류 quantizer로 고차원 데이터를 짧은 이산 토큰 시퀀스로 압축한 다음 Transformer를 사용하여 토큰 시퀀스를 모델링한다. Parti, MuseNet, AudioLM, VALL-E, Sora의 patch tokenizer가 모두 이것을 사용한다. 이것은 학습된 토크나이저 plus_bucket 1이다.

## 간략한 역사

| 연도 | 모델 | 중요 이유 |
|------|-------|-----------------|
| 2013 | VAE (Kingma) | 사용 가능한 교육 손실을 가진 첫 번째 deep 생성 모델. |
| 2014 | GAN (Goodfellow) | 암묵적 밀도, 우도 없음 — 놀라울 정도로 선명한 샘플. |
| 2015 | DRAW, PixelCNN | 순차적 이미지 생성. |
| 2017 | Glow, RealNVP | 可逆 flows; 깊이에서 정확한 우도. |
| 2017 | Progressive GAN | 첫 메가픽셀 얼굴. |
| 2019 | StyleGAN / StyleGAN2 | 한 도메인에 대해 아직도 이기기 어려운 포토리얼 얼굴. |
| 2020 | DDPM (Ho) | Diffusion이 실용적자가 됨. |
| 2021 | CLIP, DALL-E 1, VQGAN | 텍스트-이미지가 주류가 됨. |
| 2022 | Imagen, Stable Diffusion 1, DALL-E 2 | 잠재 diffusion + 텍스트 조건 = 상품. |
| 2022 | ControlNet, LoRA | 사전 교육된 diffusion에 대한 세밀한 제어. |
| 2023 | SDXL, Midjourney v5, Flow matching | 규모 + 더 나은 교육 역학. |
| 2024 | Sora, Stable Diffusion 3, Flux.1 | 비디오 diffusion; flow matching이 승리. |
| 2025 | Veo 2, Kling 1.5, Runway Gen-3, Nano Banana | 프로덕션급 비디오. |
| 2026 | Consistency + Rectified Flow | diffusion 백본からの 1단계 샘플링. |

## 다섯 가지 질문 트라이아지

새로운 생성 모델 논문이 나오면 방법 섹션을 읽기 전에 다음 다섯 가지 질문에 답하라.

1. **무엇이 모델링되는가?** 픽셀, 잠재, 이산 토큰, 3D 가우시안, 메시, 파형?
2. **밀도가 명시적인가 암묵적인가?** `log p(x)`를 서술하는가?
3. **샘플링: 원샷인가 반복인가?** Iterative는 더 느린 추론을 의미; 원샷은通常是 적대적 또는 증류됨을 의미.
4. **조건: 무조건, 클래스, 텍스트, 이미지, 포즈?** 이것이 손실과 아키텍처 스캐폴딩을 결정.
5. **평가: FID, CLIP 점수, IS, 인간 선호도, 작업 정확도?** 각각 알려진 실패 양상이 있다 (Lesson 14 참조).

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Explicit density | "우도를 계산할 수 있음" | `log p(x)`를 평가할 수 있음; VAE, diffusion, normalizing flow. |
| Implicit density | "우도 없음" | 밀도를 명시적으로 계산하지 않음; GAN처럼 샘플링을 통해 학습. |
| ELBO | "아래쪽 경계" | 변분 하한; VAE와 diffusion의 교육 손실. |
| Autoregressive | "순차적 생성" | 각 토큰이 이전 토큰에 조건부로 생성; 정확하지만 느림. |
| Latent diffusion | "压缩 공간에서diffusion" | VAE로压缩된潜伏空間でdiffusion; 더 효율적. |
| Flow matching | "확률 흐름 경로" | 시작 분포에서 목표 분포로의 常微分方程式経路; 시뮬레이션 자유. |
| Score-based | "score 함수 학습" | `∇_x log p(x)`를 직접 추정; SDE로扩散. |
| Token-based AR | "이산 토큰의 transformer" | VQ-VAE로 압축된 토큰을 GPT처럼 모델링. |

## 추가 자료

- [Goodfellow et al. (2014). Generative Adversarial Networks](https://arxiv.org/abs/1406.2661) — GAN 논문.
- [Kingma & Welling (2013). Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114) — VAE 논문.
- [Ho et al. (2020). Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) — DDPM 논문.
- [Song et al. (2019). Generative Modeling by Estimating Gradients of the Data Distribution](https://arxiv.org/abs/1907.05600) — score matching.
- [Lipman et al. (2023). Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747) — flow matching.