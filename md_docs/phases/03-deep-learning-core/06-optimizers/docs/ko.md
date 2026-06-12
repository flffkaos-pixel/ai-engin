# 옵티마이저

> 경사하강법은 걷기입니다. Adam은 스포츠카입니다. 같은 방향, 완전히 다른 속도.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 1, Lesson 03.03
**시간:** ~90분

## 개념

### SGD → 모멘텀 → Adam

- **SGD**: `w -= lr * g` — 순수 경사하강법
- **모멘텀**: `v=βv+g; w-=lr*v` — 관성, 지그재그 감소
- **Adam**: `m=β₁m+(1-β₁)g; v=β₂v+(1-β₂)g²; w-=lr*m̂/(√v̂+ε)` — 적응적 학습률

### Adam 파라미터

| 파라미터 | 기본값 | 역할 |
|---------|-------|------|
| lr | 0.001 | 기본 학습률 |
| β₁ | 0.9 | 모멘텀 붕괴 |
| β₂ | 0.999 | 속도 적응 붕괴 |
| ε | 1e-8 | 0 나누기 방지 |

### 선택 가이드

- **SGD**: 단순 문제, 커스텀 스케줄 필요
- **SGD+모멘텀**: 이미지 분류 (ResNet 기본)
- **Adam**: NLP/Transformer 기본 (95% 케이스)
- **AdamW**: Adam + 분리된 가중치 감쇠 — 최신 모델 표준

## 빌드하기

```python
class Adam:
    def __init__(self, lr=0.001, β₁=0.9, β₂=0.999, ε=1e-8):
        self.lr, self.β₁, self.β₂, self.ε = lr, β₁, β₂, ε
        self.m, self.v, self.t = {}, {}, 0

    def update(self, params, grads):
        self.t += 1
        for key in params:
            self.m[key] = self.β₁*self.m.get(key,0) + (1-self.β₁)*grads[key]
            self.v[key] = self.β₂*self.v.get(key,0) + (1-self.β₂)*grads[key]**2
            m̂ = self.m[key]/(1-self.β₁**self.t)
            v̂ = self.v[key]/(1-self.β₂**self.t)
            params[key] -= self.lr * m̂ / (v̂**0.5 + self.ε)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 모멘텀 | 과거 기울기 누적 → 더 부드러운 경로 |
| 적응적 lr | 파라미터별 학습률 — Adam의 핵심 |
| AdamW | Adam + 분리된 가중치 감쇠 |