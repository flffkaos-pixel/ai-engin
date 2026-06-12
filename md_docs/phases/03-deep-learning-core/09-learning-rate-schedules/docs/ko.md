# 학습률 스케줄

> 시작은 크게 탐험하고, 나중에는 작게 정밀 조정하세요. 학습률 스케줄이 바로 그 일을 합니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Lesson 03.06
**시간:** ~60분

## 개념

### 스케줄 유형

- **단계 감소**: N 에폭마다 γ 곱하기
- **지수 감소**: `lr = lr₀ * γ^epoch`
- **코사인**: `lr = lr_min + 0.5*(lr₀-lr_min)*(1+cos(π*epoch/T))`
- **선형 웜업**: 처음 K 에폭 동안 0→lr₀
- **1cycle**: 한 주기 내에 올라갔다 내려오기

### 선택 가이드

| 스케줄 | 용도 |
|--------|------|
| 코사인 | Transformer, ViT 기본값 |
| 단계 감소 | ResNet, CNN |
| 웜업 + 코사인 | 대형 언어 모델 (GPT, LLaMA) |
| 1cycle | 빠른 실험, 작은 데이터셋 |

## 빌드하기

```python
def cosine_schedule(epoch, total_epochs, lr_max=0.1, lr_min=0.0):
    return lr_min + 0.5*(lr_max-lr_min)*(1+np.cos(np.pi*epoch/total_epochs))

def warmup_cosine(epoch, warmup_epochs, total_epochs):
    if epoch < warmup_epochs:
        return epoch / warmup_epochs  # 0→1
    return cosine_schedule(epoch-warmup_epochs, total_epochs-warmup_epochs)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 웜업 | 점진적 증가 — 초기 불안정 방지 |
| 코사인 | 부드러운 감소 — Transformer 표준 |
| 1cycle | 한 주기 — 빠른 수렴 |