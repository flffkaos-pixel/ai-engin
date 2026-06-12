# 직접 선호도 최적화 계열

> Rafailov et al.(2023)은 RLHF의 optimum이 선호도 데이터의 관점에서 폐쇄형으로 존재함을 보여주었으므로, 명시적 보상 모델을 건너뛰고 정책을 직접 최적화할 수 있다. 그 통찰력은 계열을 만들었다 — IPO, KTO, SimPO, ORPO, BPO — 각각 DPO의 실패 모드를修正한다. 2026년, 직접 정렬 알고리즘이 PPO보다 더 많은 프론티어 사후 훈련 실행을 출시한다. 하지만 2과에서의 과최적화 곡선은 여전히 적용된다: DAA는 Goodhart를逃脱하지 않는다, 그저 그것이咬む 위치를移動할 뿐이다.

**유형:** 학습
**언어:** Python (stdlib, 6변형 선호도 손실 비교기)
**선수 과목:** Phase 18 · 01 (InstructGPT), Phase 18 · 02 (보상 해킹), Phase 10 · 08 (DPO 기초)
**소요 시간:** 약 75분

## 학습 목표

- RLHF optimum에서 DPO 폐쇄형을 도출한다.
- IPO, KTO, SimPO, ORPO, BPO가 DPO에서修正하는 실패 모드를陈述한다.
- "암시적 보상 격차"와 "선호도 강도"를 구분하고 IPO의 항등 매핑이 중요한 이유를 설명한다.
- Rafailov et al.(NeurIPS 2024)가 명시적 RM이 없음에도 DAA가 과최적화됨을증명하는 이유를 설명한다.

## 문제

RLHF 목적 함수(1과):

```
max_pi E_{x,y~pi} [ r(x, y) ] - beta * KL(pi || pi_ref)
```

알려진 optimum이 있다:

```
pi*(y|x) = (1/Z(x)) * pi_ref(y|x) * exp(r(x, y) / beta)
```

따라서 보상은 최적 정책과 레퍼런스의 비율로 암시적으로 정의된다:

```
r(x, y) = beta * log(pi*(y|x) / pi_ref(y|x)) + beta * log Z(x)
```

이를 Bradley-Terry 선호도 우도에 대입하고, partition 함수 `Z(x)`는 `x`에만 의존하므로 상쇄된다. 남은 것은 정책 매개변수만 있는 손실 — 보상 모델 불필요. 그것이 DPO이다.

주목: 도출은 optimum이 도달 가능하고, 선호도 데이터가 분포 내이고, 레퍼런스 정책이 참 모드 앵커라고 가정한다. 이것들 중 어느 것도 정확하게 유지되지 않는다. 모든 계열 멤버가 다른violated 가정을修正한다.

## 개념

### DPO (Rafailov et al., 2023)

```
L_DPO = -log sigmoid(
  beta * log(pi(y_w | x) / pi_ref(y_w | x))
  - beta * log(pi(y_l | x) / pi_ref(y_l | x))
)
```

什么问题:

- 암시적 보상 격차 `beta * (log(pi/pi_ref)_w - log(pi/pi_ref)_l`가 무겁다. 작은 선호도가 임의로 큰 격차를 생성할 수 있다.
- 손실은 선택된 것과拒绝된 로그 확률을 반대 방향으로驱动한다. 그것은 거부되는 것이 더 빨리 떨어지는 한 선택된 절대 로그 확률을 아래로 밀어낼 수 있다. 이것이 저하된 선택된 응답(Degraded Chosen Response) 현상이다.
- 분포 외 선호도(드문 쌍 대 드문 쌍)가 임의의 암시적 보상을 생성한다.

### IPO (Azar et al., 2024)

항등 선호도 최적화는 선호도 확률에 항등 매핑으로 로그-시그모이드를 대체한다. 손실이 bounded 대상에 대한 제곱 오차가 된다:

```
L_IPO = (log(pi(y_w | x) / pi_ref(y_w | x)) - log(pi(y_l | x) / pi_ref(y_l | x)) - 1/(2 beta))^2
```

여백은 `1/(2 beta)`로 bounded된다. 선호도 강도와 암시적 보상 격차가 비례한다. 폭발 없음.

### KTO (Ethayarajh et al., 2024)

Kahneman-Tversky 최적화는 쌍별 구조를 entirely 삭제한다. 단일 레이블이 지정된 출력과 이진 "권장" 또는 "비권장" 신호가 주어지면,prospect-theory 유틸리티로 매핑한다:

```
v(x, y) = sigma(beta * log(pi(y|x) / pi_ref(y|x)) - z_ref)
```

이득과 손실에 대해 다른 가중치(손실 회피). 이점: 쌍을 이루지 않은 데이터를 사용할 수 있다, 이는 훨씬 더 풍부하다.

### SimPO (Meng et al., 2024)

단순 선호도 최적화는 생성과 훈련 신호를对齐시킨다. 레퍼런스 정책을 entirely 제거하고 길이로 로그 우도를 정규화한다:

```
L_SimPO = -log sigmoid(
  (beta / |y_w|) * log pi(y_w | x)
  - (beta / |y_l|) * log pi(y_l | x)
  - gamma
)
```

안정화를 위한 여백 `gamma`. 길이 정규화는 DPO의 길이 편향 실패 모드를활용하는 인센티브를 제거한다(길수록 `y_w`가 construction에 의해 더 큰 로그 확률 격차를 얻는다).

### ORPO (Hong et al., 2024)

Odds-Ratio 선호도 최적화는 표준 SFT 음의 로그 우도에 선호도 항을 추가한다:

```
L_ORPO = L_NLL(y_w) + lambda * L_OR
L_OR = -log sigmoid(log(odds(y_w) / odds(y_l)))
```

레퍼런스 정책 없음 — SFT 항이 정규화기이다. 기본 모델에서 정렬된 모델로 단일 단계로 훈련한다. 별도의 SFT 체크포인트 없음.

### BPO (ICLR 2026 제출, OpenReview id=b97EwMUWu7)

저하된 선택된 응답 문제를 식별한다: DPO는 순위 `y_w > y_l`를 보존하지만 `y_w`의 절대 로그 확률이 하락할 수 있다. BPO는 선택된 응답의 하향 이동을penalize하는 한 줄 수정을 추가한다. 수학 추론에서 DPO보다 Llama-3.1-8B-Instruct에서 10.1% 정확도 향상을 보고했다.

### 보편적 결과: DAA는 여전히 과최적화된다

Rafailov et al. "직접 정렬 알고리즘에서 보상 모델 과최적화의 스케일링 법칙"(NeurIPS 2024)은 여러 데이터 세트에서 DPO, IPO, SLiC로 정책을 훈련했다. KL 전반에 걸친 골드-보상 대 KL 곡선이 동일한 Gao et al. 정점-그리고-붕괴 모양을 가진다. 암시적 보상 쿼리가 훈련 중 분포 외 샘플을查询한다; KL 정규화가 이것을 안정화하지 않는다.

DAA는 Goodhart를逃脱하지 않는다. "보상 모델 과최적화"에서 "레퍼런스 정책 비율 과최적화"로咬む 표면을 변경한다. 보편적修正 — 더 나은 데이터, 앙상블, 초기 중지 — 둘 다에 적용된다.

### 그들 사이 선택 (2026)

- 큰 쌍 선호도 데이터가 있는 경우:Conserv 베타로 DPO, 길이 편향이 evident하면 SimPO.
- 쌍을 이루지 않은 이진 피드백이 있는 경우: KTO.
- 기본 모델에서 단일 단계 파이프라인을 원하는 경우: ORPO.
- DPO 로그에서 저하된 선택 로그 확률을보는 경우: BPO.
- 선호도 강도가 다양하고 DPO가 포화되는 경우: IPO.

모든 실험실에서 5개 모두를 배터리로 실행하고 태스크별로 우승자를 선택한다. 수학 추론과 안전성에 대한 optimum이 같을 이유가 없다.

## 활용

`code/main.py`는 선호도 강도가 다양한toy 선호도 데이터 세트에서 6개의 손실(DPO, IPO, KTO, SimPO, ORPO, BPO)를 비교한다. 각 손실은 동일한 500쌍 표본에 대해 작은 softmax 정책에 대해 최적화된다. 방법별 최종 승률, 선택-로그-확률偏离, 암시적-보상 스프레드를 플롯한다.

## 결과물

이 수업은 `outputs/skill-preference-loss-selector.md`를 생성한다. 데이터 집합 통계(쌍 대 비쌍, 가변 대 균일 선호도 강도, 길이 분포)와 대상(단일 단계 또는 SFT-then-선호도)이 주어지면, 선호도 손실을 권장하고 그것이 защищает하는 실패 모드를 보고한다.

## 연습 문제

1. `code/main.py`를 실행한다. DPO와 BPO에 대한 최종 선택-로그-확률 하락을 보고한다. BPO가 더 높은 선택 절대 확률을 유지해야 한다 — 이것을 확인한다.

2. 모든 쌍이 동일한 강도를 가지도록 선호도 데이터를 수정한다. 6개 방법 중 어느 것이 가장 robust한가? 어느 것이 저하되는가? IPO의 이점을 설명한다.

3. 거부된 응답이 평균적으로 선택보다 2배 길게 만든다. 다른 것을 변경하지 않고 DPO의 길이 활용을 숫자로 보여주고 SimPO의修正을 보여준다.

4. Rafailov et al.(NeurIPS 2024)은 DAA가 과최적화된다고 주장한다. 단일 포인트 버전을 재현한다: 선택-마이너스-거부 KL 발산을 플롯하고 큰 베타에서 DPO의 과최적화를 관찰한다.

5. BPO 논문 초록(OpenReview b97EwMUWu7)을 읽는다. BPO가 DPO에 추가하는 한 줄 수정을 적어준다. `code/main.py`의 구현과 확인한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| DPO | "보상 모델 없는 RLHF" | 폐쇄형 RLHF optimum에서 파생된 손실; 정책 매개변수만 |
| 암시적 보상 | "로그 비율" | `beta * log(pi(y\|x) / pi_ref(y\|x))` — DPO-의미 보상 |
| IPO | "bounded DPO" | 항등 매핑으로 로그-시그모이드를 대체; 암시적 보상 격차가 `1/(2 beta)`로 bounded |
| KTO | "비쌍 DPO" | 손실 회피가 있는 단일 레이블에 대한 기대 이론적 유틸리티 |
| SimPO | "레퍼런스 없는 DPO" | 길이 정규화된 로그 우도 + 여백; 레퍼런스 정책 없음 |
| ORPO | "단일 단계 DPO" | NLL + odds-ratio 선호도 항; 한 패스에서 기본 모델에서 훈련 |
| BPO | "선택 보존 DPO" | 선택된 응답의 절대 로그 확률 하강을penalize하는 DPO 플러스 |
| 저하된 선택 | "선택이 하락함" | DPO는 거부되는 것이 더 빨리 떨어지는 한 선택 로그 확률을 감소시킨다 |
| DAA | "직접 정렬 알고리즘" | 명시적 RM을 건너뛰는 선호도-손실 방법 |

## 추가 자료

- [Rafailov et al. — Direct Preference Optimization (NeurIPS 2023, arXiv:2305.18290)](https://arxiv.org/abs/2305.18290)
- [Azar et al. — A General Theoretical Paradigm to Understand Learning from Human Preferences (AISTATS 2024, arXiv:2310.12036)](https://arxiv.org/abs/2310.12036) — IPO
- [Ethayarajh et al. — KTO: Model Alignment as Prospect Theoretic Optimization (arXiv:2402.01306)](https://arxiv.org/abs/2402.01306)
- [Meng, Xia, Chen — SimPO (NeurIPS 2024, arXiv:2405.14734)](https://arxiv.org/abs/2405.14734)
- [Hong, Lee, Thorne — ORPO (EMNLP 2024, arXiv:2403.07691)](https://arxiv.org/abs/2403.07691)
- [BPO — Behavior Preservation Optimization (ICLR 2026 OpenReview b97EwMUWu7)](https://openreview.net/forum?id=b97EwMUWu7)
- [Rafailov et al. — Scaling Laws for RM Overoptimization in DAAs (NeurIPS 2024, arXiv:2406.02900)](https://arxiv.org/abs/2406.02900)