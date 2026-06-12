# 이미지 분류

> 분류기는 픽셀을 클래스 확률 분포로 매핑하는 함수입니다. 나머지는 배관입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 2, 3, 4
**시간:** ~75분

## 개념

### 파이프라인

```
이미지 → 전처리 → CNN → GlobalPool → FC → Softmax → 클래스
```

### 데이터셋

- **CIFAR-10/100**: 32×32, 10/100 클래스 — 빠른 실험
- **ImageNet**: 224×224, 1000 클래스 — 사실상의 벤치마크
- **자체 데이터셋**: `torchvision.datasets.ImageFolder`

### 훈련 레시피

```python
# 증강
transforms = Compose([
    RandomResizedCrop(224),
    RandomHorizontalFlip(),
    ColorJitter(0.4, 0.4, 0.4),
    ToTensor(),
    Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])

# 모델
model = models.resnet50(pretrained=True)
model.fc = nn.Linear(2048, num_classes)

# 훈련
optimizer = AdamW(model.parameters(), lr=1e-4)
scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
```

### 평가

Top-1 정확도, Top-5 정확도, 혼동 행렬, 클래스별 정밀도/재현율.

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| ImageFolder | 디렉토리 구조 → 데이터셋 |
| GlobalPool | 공간 차원 평균화 → FC에 공급 |
| Top-5 | 정답이 상위 5개에 포함 = 정확 |