# Video 생성

> 이미지는 2-D 텐서이다. 비디오는 3-D이다. 이론은 동일하다; 계산은 10-100x 더 어렵다. OpenAI의 Sora (2024년 2월)는 가능함을 증명했다. 2026년까지 Veo 2, Kling 1.5, Runway Gen-3, Pika 2.0 및 WAN 2.2는 1080p에서 텍스트에서 production 비디오를 shipments한다 — 그리고 오픈 가중치 스택 (CogVideoX, HunyuanVideo, Mochi-1, WAN 2.2)은 12개월 뒤처져 있다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 8 · 07 (Latent Diffusion), Phase 7 · 09 (ViT), Phase 8 · 06 (DDPM)
**소요 시간:** ~45분

## 문제

24fps에서 10초 1080p 비디오는 1920×1080×3 픽셀의 240 프레임이다. 이는 클립당 ~1.5GB의 원시 데이터이다. 픽셀 공간 diffusion은実行 불가능하다. 필요하다:

1. **시공간 압축.** 프레임이 아닌 비디오를 인코딩하는 VAE, 시공간 패치 시퀀스로.
2. **시간적 일관성.** 프레임은 초에 걸쳐 콘텐츠, 조명 및 개체 정체성을 공유해야 한다. Net은 모션을 모델링해야 한다.
3. **계산 예산.** 동일한 모델 크기에서 비디오 교육은 이미지보다 10-100x 더 비싸다.
4. **조건.** 텍스트, 이미지 (첫 번째 프레임), 오디오 또는 다른 비디오. 대부분의 production 모델은 네 가지를 모두 accept한다.

이것을 해결한 아키텍처는 시공간 패치에 적용된 **Diffusion Transformer (DiT)**이며, 대규모 (프롬프트, 캡션, 비디오) 데이터 세트에서 교육된다. Lesson 06과 동일한 diffusion 손실.

## 개념

![비디오 diffusion: 패치화, DiT, 디코딩](../assets/video-generation.svg)

### 패치화

3D VAE로 비디오를 인코딩한다 (학습된 시공간 압축). 잠재는 shape `[T_latent, H_latent, W_latent, C_latent]`이다. Size `[t_p, h_p, w_p]`의 패치로 분할한다. Sora 스타일 모델의 경우 `t_p = 1` (프레임당 패치) 또는 `t_p = 2` (매 두 프레임). 10초 1080p 비디오는 ~20,000-100,000 패치로 압축된다.

### 시공간 DiT

Transformer가 패치의 плоский 시퀀스를 처리한다. 각 패치에는 3D 위치 임베딩 (시간 + y + x)이 있다. Attention은 usually factorized:

- **공간 attention** 각 프레임의 패치 내.
- **시간적 attention** 동일한 공간 위치에서 프레임 간.
- **전체 3D attention**은 16-100x 더 비싸다; 저해상도에서만 또는 연구에서 사용.

### 텍스트 조건

대规模 텍스트 인코더 (Sora의 경우 T5-XXL, CogVideoX-5B는 T5-XXL 사용)와의 cross-attention. 긴 프롬프트가 중요하다 — Sora의 교육 데이터 세트에는 클립당 평균 200토큰의 GPT 생성 dense re-captions이 있었다.

### 교육

시공간 잠재에 대한 표준 diffusion 손실 (ε 또는 v 예측). 데이터: 웹 비디오 + ~100M 큐레이션된 클립 + 합성 텍스트 캡션. 계산: 소규모 연구 실행에도 10,000+ GPU 시간; Sora 규모는 100,000+.

## 2026년 production 환경

| 모델 | 날짜 | 최대 기간 | 최대 해상도 | 오픈 가중치? | notable |
|-------|------|--------------|---------|---------------|---------|
| Sora (OpenAI) | 2024-02 | 60초 | 1080p | 아니오 | 규모에서 세계 시뮬레이터 속성을 보여준 첫 번째 모델 |
| Sora Turbo | 2024-12 | 20초 | 1080p | 아니오 | 5x 더 빠른 추론에서 Production Sora |
| Veo 2 (Google) | 2024-12 | 8초 | 4K | 아니오 | 2025년 최고 품질 + 물리 |
| Veo 3 | 2025 Q3 | 15초 | 4K | 아니오 | 네이티브 오디오 및更强한 카메라 제어 |
| Kling 1.5 / 2.1 (Kuaishou) | 2024-2025 | 10초 | 1080p | 아니오 | 2025 Q1에서 가장 좋은 인간 동작 |
| Runway Gen-3 Alpha | 2024-06 | 10초 | 768p | 아니오 | 상단에 professional 비디오 도구 |
| Pika 2.0 | 2024-10 | 5초 | 1080p | 아니오 | 가장 강한 캐릭터 일관성 |
| CogVideoX (THUDM) | 2024 | 10초 | 720p | 예 (2B, 5B) | 첫 번째 오픈 5B 규모 비디오 |
| HunyuanVideo (Tencent) | 2024-12 | 5초 | 720p | 예 (13B) | 2024년 말 공개 SOTA |
| Mochi-1 (Genmo) | 2024-10 | 5.4초 | 480p | 예 (10B) | 가장 관대한 라이선스 |
| WAN 2.2 (Alibaba) | 2025-07 | 5초 | 720p | 예 | 2025년 중반 最強 오픈 모델 |

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| DiT | "Diffusion Transformer" | 비디오 패치용 transformer 기반 diffusion. |
| Spatiotemporal | "시간 + 공간" | 비디오의 시간적 차원과 공간적 차원을 모두 고려. |
| Temporal attention | "프레임 간 일관성" | 동일한 공간 위치에서 여러 프레임 간 attention. |
| VAE (video) | "비디오 압축" | 시공간 패치로 비디오를 저차원 잠재로 인코딩. |
| Token AR | "이산 토큰 생성" | 오디오/비디오 토큰의 autoregressive 생성. |

## 추가 자료

- [Balaji et al. (2022). eDiffi: Text-to-Image Diffusion Models with Ensemble of Expert Denoisers](https://arxiv.org/abs/2211.01324) — 다양한 비디오 생성 모델 분석.
- [Chen et al. (2024). CogVideoX: Large-Scale Open-Source Video Diffusion Models](https://arxiv.org/abs/2408.06069) — CogVideoX.