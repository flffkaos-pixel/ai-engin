# 평가 — FID, CLIP 점수, 인간 선호도

> 모든 생성형 모델 리더보드는 FID, CLIP 점수, 인간 선호도 아레나의 승률을 인용합니다. 각 숫자는 Determined 연구자가 게임할 수 있는 실패 모드를 가집니다. 실패 모드를 모르면 실제 개선과 게임 실행을 구별할 수 없습니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 8 · 01 (Taxonomy), Phase 2 · 04 (Evaluation Metrics)
**소요 시간:** ~45분

## 문제

생성형 모델은 *샘플 품질*과 *조건 준수*로 판단됩니다. 둘 다 닫힌 형식의 측정이 없습니다. 모델이 10,000개의 이미지를 렌더링해야 합니다; 무언가가 그들에게 숫자를 할당해야 합니다; 모델 제품군, 해상도, 아키텍처에 걸친 숫자를 신뢰해야 합니다. 2014-2026년 관문을 통과한 세 가지 지표:

- **FID (Fréchet Inception Distance).** 실제와 생성의 두 분포 사이의 거리 — Inception 네트워크의 특성 공간에서. 낮을수록 좋습니다.
- **CLIP 점수.** 생성된 이미지의 CLIP-이미지 임베딩과 프롬프트의 CLIP-텍스트 임베딩 사이의 코사인 유사성. 높을수록 좋습니다. 프롬프트 준수를 측정합니다.
- **인간 선호도.** 동일한 프롬프트에서 두 모델을 정면으로 대결시키고, 인간(GPT-4급 모델)이 더 나은 것을 선택하고, Elo 점수로 집계합니다.

또한 다음을 보게 됩니다: IS (inception score, largely retired), KID, CMMD, ImageReward, PickScore, HPSv2, MJHQ-30k. 각각이 이전의 하나의 실패를 수정합니다.

## 개념

![FID, CLIP, 선호도: 세 개의 축, 다른 실패 모드](../assets/evaluation.svg)

### FID — 샘플 품질

Heusel et al. (2017). 단계:

1. N개의 실제 이미지와 N개의 생성된 이미지에 대해 Inception-v3 특성(2048-D)을 추출합니다.
2. 각 풀에 가우시안을 피팅합니다: 평균 `μ_r, μ_g`와 공분산 `Σ_r, Σ_g`를 계산합니다.
3. FID = `||μ_r - μ_g||² + Tr(Σ_r + Σ_g - 2 · (Σ_r · Σ_g)^0.5)`.

해석: 특성 공간에서 두 다변량 가우시안 사이의 Fréchet 거리. 낮을수록 더 유사한 분포.

실패 모드:
- **작은 N에 대한 편향.** FID는 특성 분포에 대한 평균 제곱입니다 — 작은 N은 공분산을 과소 추정하여 허위로 낮은 FID를 제공합니다. 항상 N ≥ 10,000을 사용하세요.
- **Inception 의존.** Inception-v3는 ImageNet에서 학습되었습니다. ImageNet과 먼 도메인(얼굴, 예술, 텍스트 이미지)은 의미 없는 FID를 생성합니다. 도메인 특정 특성 추출기를 사용하세요.
- **게aming.** 시각적 품질 개선 없이 Inception 사전에 과적합하면 낮은 FID가 됩니다. CMMD로 극복하세요(아래 참조).

### CLIP 점수 — 프롬프트 준수

Radford et al. (2021). 생성된 이미지 + 프롬프트의 경우:

```
clip_score = cos_sim( CLIP_image(x_gen), CLIP_text(prompt) )
```

30k 생성된 이미지에 대해 평균 → 모델 간 비교 가능한 스칼라.

실패 모드:
- **CLIP 자체의 블라인드 스팟.** CLIP는 약한 조합적 추론을 가집니다("빨간 큐브가青い 구슬 위에"는 종종 실패). 모델은 복잡한 프롬프트를 실제로 따르지 않고도 CLIP 점수에서 잘 순위할 수 있습니다.
- **짧은 프롬프트 편향.** 짧은 프롬프트는 추가로 CLIP-이미지 일치가 더 많습니다. 긴 프롬프트는 기계적으로 더 낮은 CLIP 점수를 가집니다.
- **프롬프트 게임.** 프롬프트에 "high quality, 4k, masterpiece"를 포함하면 이미지-텍스트 바인딩 개선 없이 CLIP 점수가膨胀합니다.

CMMD (Jayasumana et al., 2024)가 이를 일부 수정합니다: Inception 대신 CLIP 특성을 사용하고, Fréchet 대신 최대 평균 편차(MMD)를 사용합니다. 미묘한 품질 차이 감지에 더 좋습니다.

### 인간 선호도 — 근거 진실

프롬프트 풀을 선택합니다. 모델 A와 모델 B로 생성합니다. 인간(또는 강력한 LLM 판정관)에게 쌍을 보여줍니다. 승리를 Bradley-Terry 또는 Elo 점수로 집계합니다. 벤치마크:

- **PartiPrompts (Google)**: 1,600개의 다양한 프롬프트, 12개 카테고리.
- **HPSv2**: 107k개의 인간 주석, 자동 프록시로 널리 사용됩니다.
- **ImageReward**: 137k개의 프롬프트-이미지 선호도 쌍, MIT 라이선스.
- **PickScore**: Pick-a-Pic 2.6M 선호도에서 학습되었습니다.
- **Chatbot-Arena 스타일 이미지 아레나**: https://imagearena.ai/ 및 기타.

실패 모드:
- **판정관 분산.** 비전문가는 전문가와 다른 선호도를 가집니다. 둘 다 사용하세요.
- **프롬프트 분포.** 체리 피킹된 프롬프트는 한 제품군에 유리합니다. 항상 문서화하세요.
- **LLM-판정관 보상 해킹.** GPT-4-판정관은 아름답지만 Wrong인 출력에 속습니다. 인간으로 삼각측량하세요.

## 함께 사용

프로덕션 평가 보고서에는 다음이 포함되어야 합니다:

1. held-out 실제 분포에 대해 10-30k 샘플에서 FID(샘플 품질).
2. 동일한 샘플에 대해 프롬프트 대비 CLIP 점수 / CMMD(준수).
3. 이전 모델 대비 블라인드 아레나에서의 승률(전체 선호도).
4. 실패 모드 분석: 알려진 문제(손 해부학, 텍스트 렌더링, 일관된 객체 수)로 플래그된 50개 무작위 샘플 출력.

단일 지표는 거짓말입니다. 세 가지 corroborating 지표 + 정성적 검토가 주장입니다.

## 실습

`code/main.py`는 합성 "특성 벡터"(Inception 특성에 대한 대용으로 4-D 벡터 사용)에서 FID, CLIP 점수 유사, Elo 집계를 구현합니다. 다음을 볼 수 있습니다:

- 작은 N과 큰 N에서 FID 계산 — 편향.
- 특성 풀 간 코사인 유사성으로 "CLIP 점수".
- 합성 선호도 스트림에서 Elo 업데이트 규칙.

### Step 1: FID 4줄 구현

```python
def fid(real_features, gen_features):
    mu_r, cov_r = mean_and_cov(real_features)
    mu_g, cov_g = mean_and_cov(gen_features)
    mean_diff = sum((a - b) ** 2 for a, b in zip(mu_r, mu_g))
    trace_term = trace(cov_r) + trace(cov_g) - 2 * sqrt_cov_product(cov_r, cov_g)
    return mean_diff + trace_term
```

### Step 2: CLIP 스타일 코사인 유사성

```python
def clip_like(image_feat, text_feat):
    dot = sum(a * b for a, b in zip(image_feat, text_feat))
    norm = math.sqrt(dot_self(image_feat) * dot_self(text_feat))
    return dot / max(norm, 1e-8)
```

### Step 3: Elo 집계

```python
def elo_update(r_a, r_b, winner, k=32):
    expected_a = 1 / (1 + 10 ** ((r_b - r_a) / 400))
    actual_a = 1.0 if winner == "a" else 0.0
    r_a_new = r_a + k * (actual_a - expected_a)
    r_b_new = r_b - k * (actual_a - expected_a)
    return r_a_new, r_b_new
```

## 함정

- **N=1000에서의 FID.** 발견적 방법은 N<10k에서 신뢰할 수 없습니다. 낮은 N FID를 보고하는 논문은 게임입니다.
- **해상도 간 FID 비교.** Inception의 299×299 리사이즈는 특성 분포를 변경합니다. 일치된 해상도에서만 비교하세요.
- **하나의 시드 보고.** 최소 3개의 시드를 실행하세요. 표준 편차를 보고하세요.
- **부정 프롬프트를 통한 CLIP 점수 inflation.** 일부 파이프라인은 과적합으로 CLIP를 부스트합니다. 시각적 포화에 대해 확인하세요.
- **프롬프트 중첩으로 인한 Elo 편향.** 두 모델 모두 학습 중 벤치마크 프롬프트를 보았다면 Elo는 의미가 없습니다.-held-out 프롬프트 세트를 사용하세요.
- **유료 크라우드 인간 평가 왜곡.** Prolific, MTurk 주석자는 더 젊음 / 기술 친화적입니다. 모은 예술/디자인 전문가와 혼합하세요.

## 활용

2026년 프로덕션 평가 프로토콜:

| 기둥 | 최소 | 권장 |
|------|------|------|
| 샘플 품질 | held-out 실제 대비 10k에서 FID | + 5k에서 CMMD + 카테고리별 하위 집합에서 FID |
| 프롬프트 준수 | 30k에서 CLIP 점수 | + HPSv2 + ImageReward + VQA 스타일 질문 답변 |
| 선호도 | baseline 대비 200개의 블라인드 쌍 | + 2000개의 페어드 인간 + LLM-판정관 + Chatbot Arena |
| 실패 분석 | 50개의 손으로 플래그된 | 500개의 손으로 플래그된 + 자동 안전 분류기 |

네 가지 기둥이 모두 하나의 보고서에 = 주장. 하나만 = 마케팅.

## 결과물

`outputs/skill-eval-report.md`를 저장하세요. Skill은 새 모델 체크포인트 + baseline을 가져와서 완전한 평가 플랜을 출력합니다: 샘플 크기, 지표, 실패 모드 프로브, 서명 기준.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행하세요. 동일한 합성 분포에서 N=100 vs N=1000에서 FID를 비교하세요. 편향 크기를 보고하세요.
2. **보통.** 합성 CLIP 스타일 특성에서 CMMD를 구현하세요(Jayasumana et al., 2024의 공식 참조). FID 대비 품질 차이에 대한 민감도를 비교하세요.
3. **어려움.** HPSv2 설정을 복제하세요: Pick-a-Pic의 하위 집합에서 1000개의 이미지-프롬프트 쌍을 가져와서, 선호도에서 작은 CLIP 기반 점수자를 미세 조정하고, held-out 세트에서 일치도를 측정하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| FID | "Fréchet Inception Distance" | 실제 vs 생성 Inception 특성에 대한 가우시안 피팅의 Fréchet 거리. |
| CLIP 점수 | "텍스트-이미지 유사성" | CLIP 이미지 및 텍스트 임베딩 사이의 코사인 유사성. |
| CMMD | "FID의 대안" | CLIP-특성 MMD; 덜 편향되고 가우시안 가정이 없습니다. |
| IS | "Inception score" | Exp KL(p(y|x) || p(y)); 최신 모델에서 Poor하게 상관되며, 폐기됨. |
| HPSv2 / ImageReward / PickScore | "학습된 선호도 프록시" | 인간 선호도에서 학습된 작은 모델; 자동 판정관으로 사용됩니다. |
| Elo | "체스 레이팅" | 페어드 승리의 Bradley-Terry 집계. |
| PartiPrompts | "벤치마크 프롬프트 세트" | 12개 카테고리에 걸친 1,600개의 Google 관리 프롬프트. |
| FD-DINO | "자기 감독 대안" | 자기_supervised 대안인 DINOv2 특성을 사용한 FD; ImageNet 외 도메인에 더 좋습니다. |

## 프로덕션 노트: 평가는 또한 추론 워크로드입니다

10k 샘플에서 FID를 실행한다는 것은 10k 이미지를 생성한다는 의미입니다. L4의 단일 L4에서 1024²의 50단계 SDXL 기본에 대해, 이는 ~11시간의 단일 요청 추론입니다. 평가 예산은 실제이며, 프레이밍은 정확히 오프라인 추론 시나리오입니다(처리량 극대화, TTFT 무시):

- **배치 하드, 지연 시간 잊은.** 오프라인 평가 = 메모리에 맞는 가장 큰 크기에서 정적 배칭. 80GB H100에서 `pipe(...).images`와 `num_images_per_prompt=8`은 단일 요청보다 벽시계 4-6× 빠릅니다.
- **실제 특성 캐시.** 실제 레퍼런스 세트에 대한 Inception(FID) 또는 CLIP(CLIP 점수, CMMD) 특성 추출은 *한 번*만 실행되어 `.npz`로 저장됩니다. 평가마다 다시 계산하지 마세요.

CI / 회귀 게이트용: PR당 500샘플 하위 집합에서 FID + CLIP 점수(~30분 실행); 전체 10k FID + HPSv2 + Elo는 매일 밤 실행.

## 추가 자료

- [Heusel et al. (2017). GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium (FID)](https://arxiv.org/abs/1706.08500) — FID 논문.
- [Jayasumana et al. (2024). Rethinking FID: Towards a Better Evaluation Metric for Image Generation (CMMD)](https://arxiv.org/abs/2401.09603) — CMMD.
- [Radford et al. (2021). Learning Transferable Visual Models from Natural Language Supervision (CLIP)](https://arxiv.org/abs/2103.00020) — CLIP.
- [Wu et al. (2023). HPSv2: A Comprehensive Human Preference Score](https://arxiv.org/abs/2306.09341) — HPSv2.
- [Xu et al. (2023). ImageReward: Learning and Evaluating Human Preferences for Text-to-Image Generation](https://arxiv.org/abs/2304.05977) — ImageReward.
- [Yu et al. (2023). Scaling Autoregressive Models for Content-Rich Text-to-Image Generation (Parti + PartiPrompts)](https://arxiv.org/abs/2206.10789) — PartiPrompts.
- [Stein et al. (2023). Exposing flaws of generative model evaluation metrics](https://arxiv.org/abs/2306.04675) — 실패 모드 조사.