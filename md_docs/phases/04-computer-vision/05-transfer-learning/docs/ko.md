# 전이 학습 & 파인튜닝

> 누군가 백만 GPU 시간을 들여 에지, 텍스처, 객체 부분이 어떻게 생겼는지 네트워크에 가르쳤습니다. 자신의 것을 훈련하기 전에 그 특징을 빌리세요.

**유형:** 빌드  
**언어:** Python  
**선수 과목:** Phase 4  
**시간:** ~75분

## 개념

- **전이 학습**: 사전훈련된 모델을 특징 추출기로 사용. 분류 헤드만 새로 훈련
- **파인튜닝**: 전체 네트워크(또는 마지막 몇 층)를 작은 학습률로 재훈련
- **언제**: 데이터 적을 때 → 전이 학습만. 데이터 충분할 때 → 파인튜닝

## 빌드하기

```python
model = models.resnet50(pretrained=True)
# 특징 추출기로 고정
for param in model.parameters():
    param.requires_grad = False
# 분류 헤드 교체
model.fc = nn.Linear(2048, num_classes)

# 파인튜닝: 마지막 블록만 학습
for param in model.layer4.parameters():
    param.requires_grad = True
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 사전훈련 | ImageNet 등 대규모 데이터셋으로 훈련된 가중치 |
| 특징 추출 | CNN 백본 고정, 헤드만 학습 |
| 파인튜닝 | 작은 lr로 전체/일부 재학습 |