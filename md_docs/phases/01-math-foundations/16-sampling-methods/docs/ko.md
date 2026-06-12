# 샘플링 방법

> 샘플링은 AI가 가능성의 공간을 탐색하는 방법입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lessons 06-07
**시간:** ~120분

## 학습 목표

- 균등 난수만 사용하여 역CDF, 기각, 중요도 샘플링을 처음부터 구현하기
- 언어 모델 토큰 생성을 위한 temperature, top-k, top-p(핵) 샘플링 구축하기
- 재매개변수화 트릭과 VAE에서 샘플링을 통한 역전파를 가능하게 하는 이유 설명하기
- 정규화되지 않은 목표 분포에서 샘플링하기 위해 Metropolis-Hastings MCMC 실행하기

## 문제

언어 모델이 프롬프트 처리를 마치고 50,000개 로짓의 벡터를 생성합니다. 이제 하나를 선택해야 합니다.

항상 최고 확률 토큰을 선택하면 모든 응답이 동일합니다 — 결정론적, 지루함. 균등 랜덤으로 선택하면 출력이 횡설수설입니다. 답은 이 극단 사이 어딘가에 있으며, 그 어딘가는 샘플링에 의해 제어됩니다.

모든 생성형 AI 시스템은 샘플링 시스템입니다. 샘플링 전략이 출력의 품질, 다양성, 제어 가능성을 결정합니다.

## 개념

### 샘플링이 중요한 네 가지 이유

1. **생성**: LLM, 확산 모델, GAN — 샘플링 알고리즘이 창의성과 일관성 제어
2. **훈련**: SGD는 미니배치 샘플링, 드롭아웃은 뉴런 샘플링
3. **추정**: 몬테카를로 — 폐쇄형 해가 없는 적분 근사
4. **탐색**: MCMC — 베이지안 추론의 사후분포 탐색

핵심 과제: 단순 분포(균등, 정규)에서만 직접 샘플링 가능. 다른 모든 것은 변환 방법 필요.

### 역CDF 방법

```
1. u ~ Uniform(0,1) 생성
2. F_inverse(u) 반환 — 목표 분포를 따름
```

CDF가 역함수를 가지면 언제나 작동. 지수분포에 적합.

### 기각 샘플링

```
1. 목표 분포 p(x)와 지배 분포 M·q(x) 선택 (M·q(x) >= p(x) 모든 x에 대해)
2. q에서 x 샘플링, u ~ Uniform(0,1) 생성
3. u < p(x)/(M·q(x))이면 x 수락, 아니면 기각 후 2단계로
```

### LLM 토큰 샘플링

```python
import numpy as np

def sample_token(logits, temperature=1.0, top_k=0, top_p=0.0):
    # Temperature 적용
    logits = np.array(logits) / temperature

    # Top-k: 상위 k개만 유지
    if top_k > 0:
        indices = np.argpartition(logits, -top_k)[-top_k:]
        mask = np.ones_like(logits, dtype=bool)
        mask[indices] = False
        logits[mask] = -np.inf

    # Top-p (nucleus): 누적 확률 p 초과 토큰 제거
    if top_p > 0.0:
        sorted_indices = np.argsort(logits)[::-1]
        sorted_probs = np.exp(logits[sorted_indices]) / np.sum(np.exp(logits))
        cumulative = np.cumsum(sorted_probs)
        cutoff_idx = np.searchsorted(cumulative, top_p)
        mask = np.ones_like(logits, dtype=bool)
        mask[sorted_indices[cutoff_idx+1:]] = False
        logits[mask] = -np.inf

    # 소프트맥스 + 샘플링
    probs = np.exp(logits) / np.sum(np.exp(logits))
    return np.random.choice(len(logits), p=probs)
```

### 재매개변수화 트릭

z ~ N(μ, σ²) 대신: z = μ + σ * ε, ε ~ N(0, 1)

무작위성을 입력(ε)으로 이동시켜 μ와 σ를 통한 역전파 가능.

### MCMC (Metropolis-Hastings)

```python
def metropolis_hastings(target_log_prob, initial, n_samples, proposal_std=0.5):
    samples = [initial]
    current = initial
    current_log_prob = target_log_prob(current)

    for _ in range(n_samples):
        # 제안
        proposal = current + np.random.normal(0, proposal_std, size=current.shape)
        proposal_log_prob = target_log_prob(proposal)

        # 수락 확률
        if np.log(np.random.random()) < proposal_log_prob - current_log_prob:
            current = proposal
            current_log_prob = proposal_log_prob

        samples.append(current.copy())

    return np.array(samples)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 역CDF | 균등 → 모든 분포. 해석적 CDF 필요 |
| 기각 샘플링 | 지배 분포로 샘플 감싸기. 비효율적일 수 있음 |
| Temperature | 0=결정론적, <1=더 집중, >1=더 무작위 |
| Top-k | 상위 k개 토큰으로 제한 |
| Top-p (nucleus) | 누적 확률 p까지 유지 — 더 적응적 |
| 재매개변수화 | 무작위성을 고정 입력으로 이동 — VAE에 필수 |
| MCMC | 마르코프 연쇄로 정규화되지 않은 분포 탐색 |