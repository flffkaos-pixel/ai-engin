# CNN — LeNet에서 ResNet까지

> 지난 30년간의 모든 주요 CNN은 하나의 새로운 아이디어가 추가된 동일한 conv-비선형-다운샘플 레시피입니다.

**유형:** 학습+빌드
**언어:** Python
**선수 과목:** Phase 3, Phase 4
**시간:** ~75분

## 개념

### CNN 진화

| 모델 | 연도 | 핵심 아이디어 | 파라미터 |
|------|------|-------------|---------|
| LeNet-5 | 1998 | Conv→Pool→FC | 60K |
| AlexNet | 2012 | ReLU, Dropout, GPU | 60M |
| VGG | 2014 | 3×3 스택, 단순 깊이 | 138M |
| GoogLeNet | 2014 | Inception 모듈 | 5M |
| ResNet | 2015 | 잔차 연결 (스킵 연결) | 25M |
| DenseNet | 2017 | 모든 레이어 연결 | 8M |
| EfficientNet | 2019 | 너비/깊이/해상도 스케일링 | 5M |

### ResNet의 핵심: 잔차 연결

`output = F(x) + x` (입력을 출력에 더함)

기울기 소실 없이 152개 레이어 가능. 현대 모든 CNN의 기초.

### 표준 CNN 블록

```python
class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
        )
        self.relu = nn.ReLU()

    def forward(self, x):
        return self.relu(self.conv(x) + x)  # 잔차
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 잔차 연결 | 입력을 출력에 더함 — 깊이 가능하게 함 |
| Inception | 병렬 다양한 커널 크기 |
| 배치 정규화 | 훈련 안정화 — 더 빠른 수렴 |