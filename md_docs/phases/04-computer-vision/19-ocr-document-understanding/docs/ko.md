# OCR & 문서 이해

> OCR은 세 단계 파이프라인이다 — 텍스트 상자 검출, 문자 인식, 그 다음 배치. 모든 최신 OCR 시스템은 이 단계들을 재정렬하거나 병합한다.

**유형:** 학습 + 사용
**언어:** Python
**사전 요구사항:** 4단계 06과(검출), 7단계 02과(셀프 어텐션)
**시간:** ~45분

## 학습 목표

- 고전적 OCR 파이프라인(검출 -> 인식 -> 배치)과 최신 종단간 대안(Donut, Qwen-VL-OCR)을 추적한다
- 시퀀스-투-시퀀스 OCR 훈련을 위한 CTC(Connectionist Temporal Classification) 손실을 구현한다
- 훈련 없이 프로덕션 문서 파싱을 위해 PaddleOCR 또는 EasyOCR을 사용한다
- OCR, 레이아웃 파싱, 문서 이해를 구별하고 작업별로 올바른 도구를 선택한다

## 문제

텍스트가 가득한 이미지는 어디에나 있다: 영수증, 인보이스, 신분증, 스캔된 책, 양식, 화이트보드, 표지판, 스크린샷. 이들로부터 구조화된 데이터를 추출하는 것 — 단순한 문자가 아니라 "이게 총 금액이다" — 는 가장 가치가 높은 응용 비전 문제 중 하나이다.

이 분야는 세 가지 기술 계층으로 나뉜다:

1. **OCR 본연**: 픽셀을 텍스트로 변환한다.
2. **레이아웃 파싱**: OCR 출력을 영역(제목, 본문, 표, 헤더)으로 그룹화한다.
3. **문서 이해**: 레이아웃에서 구조화된 필드("invoice_total = $42.50")를 추출한다.

각 계층에는 고전적 및 현대적 접근법이 있으며, "이미지에서 텍스트를 원한다"와 "이 영수증에서 총 금액이 필요하다" 사이의 간격은 대부분의 팀이 생각하는 것보다 크다.

## 개념

### 고전적 파이프라인

```mermaid
flowchart LR
    IMG["이미지"] --> DET["텍스트 검출<br/>(DB, EAST, CRAFT)"]
    DET --> BOX["단어/줄<br/>경계 상자"]
    BOX --> CROP["각 영역 크롭"]
    CROP --> REC["인식<br/>(CRNN + CTC)"]
    REC --> TXT["텍스트 문자열"]
    TXT --> LAY["레이아웃<br/>정렬"]
    LAY --> OUT["읽기 순서 텍스트"]

    style DET fill:#dbeafe,stroke:#2563eb
    style REC fill:#fef3c7,stroke:#d97706
    style OUT fill:#dcfce7,stroke:#16a34a
```

- **텍스트 검출**은 줄별 또는 단어별 사각형을 생성한다.
- **인식**은 각 영역을 고정 높이로 크롭하고, CNN + BiLSTM + CTC를 실행하여 문자 시퀀스를 생성한다.
- **레이아웃**은 읽기 순서를 재구성한다(라틴어는 위-아래, 왼-오른쪽; 아랍어, 일본어는 다름).

### CTC를 한 단락으로

OCR 인식은 고정 길이 특징 맵에서 가변 길이 시퀀스를 생성한다. CTC(Graves et al., 2006)는 문자 수준 정렬 없이 이를 훈련할 수 있게 한다. 모델은 모든 시간 단계에서 (어휘 + 공백)에 대한 분포를 출력한다; CTC 손실은 반복 병합과 공백 제거 후 타겟 텍스트로 축소되는 모든 정렬에 대해 주변화한다.

```
raw output: "h h h _ _ e e l l _ l l o _ _"
반복 병합 및 공백 제거 후: "hello"
```

CTC는 CRNN이 2015년에 작동했고 2026년에도 여전히 대부분의 프로덕션 OCR 모델을 훈련시키는 이유이다.

### 최신 종단간 모델

- **Donut** (Kim et al., 2022) — ViT 인코더 + 텍스트 디코더; 이미지를 읽고 직접 JSON을 출력한다. 텍스트 검출기, 레이아웃 모듈이 없다.
- **TrOCR** — ViT + 트랜스포머 디코더를 위한 라인 수준 OCR.
- **Qwen-VL-OCR / InternVL** — OCR 작업에 미세조정된 완전한 비전-언어 모델; 2026년 복잡한 문서에 대한 최고 정확도.
- **PaddleOCR** — 성숙한 프로덕션 패키지의 고전적 DB + CRNN 파이프라인; 여전히 오픈소스 작업마.

종단간 모델은 더 많은 데이터와 컴퓨팅이 필요하지만 다단계 파이프라인의 오류 누적을 건너뛴다.

### 레이아웃 파싱

구조화된 문서의 경우 각 영역에 레이블을 지정하는 레이아웃 검출기(LayoutLMv3, DocLayNet)를 실행한다: 제목, 단락, 그림, 표, 각주. 읽기 순서는 "레이아웃 순서로 영역을 반복하며 연결"이 된다.

양식의 경우 **키-값 추출** 모델(시각적으로 풍부한 문서용 Donut, 일반 스캔용 LayoutLMv3)을 사용한다. 이들은 이미지 + 검출된 텍스트 + 위치를 받아 구조화된 키-값 쌍을 예측한다.

### 평가 지표

- **CER(문자 오류율)** — Levenshtein 거리 / 참조 길이. 낮을수록 좋다. 프로덕션 목표: 깨끗한 스캔에서 < 2%.
- **WER(단어 오류율)** — 단어 수준에서 동일.
- **구조화된 필드의 F1** — 키-값 작업의 경우; `{invoice_total: 42.50}`가 올바르게 나타나는지 측정.
- **JSON 편집 거리** — 종단간 문서 파싱의 경우; Donut 논문이 정규화된 트리 편집 거리를 도입했다.

## 빌드 It

### 단계 1: CTC 손실 + 탐욕적 디코더

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


def ctc_loss(log_probs, targets, input_lengths, target_lengths, blank=0):
    """
    log_probs:      (T, N, C) 인덱스 0에 공백을 포함한 어휘에 대한 log-softmax
    targets:        (N, S) int 타겟 (공백 없음)
    input_lengths:  (N,) 샘플별 사용된 시간 단계
    target_lengths: (N,) 샘플별 타겟 길이
    """
    return F.ctc_loss(log_probs, targets, input_lengths, target_lengths,
                      blank=blank, reduction="mean", zero_infinity=True)


def greedy_ctc_decode(log_probs, blank=0):
    """
    log_probs: (T, N, C) log-softmax
    returns: 인덱스 시퀀스 리스트 (공백 제거, 반복 병합)
    """
    preds = log_probs.argmax(dim=-1).transpose(0, 1).cpu().tolist()
    out = []
    for seq in preds:
        decoded = []
        prev = None
        for idx in seq:
            if idx != prev and idx != blank:
                decoded.append(idx)
            prev = idx
        out.append(decoded)
    return out
```

`F.ctc_loss`는 가능할 때 효율적인 CuDNN 구현을 사용한다. 탐욕적 디코더는 빔 서치보다 간단하며 일반적으로 CER 1% 이내이다.

### 단계 2: Tiny CRNN 인식기

최소 CNN + BiLSTM을 위한 라인 OCR.

```python
class TinyCRNN(nn.Module):
    def __init__(self, vocab_size=40, hidden=128, feat=32):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, feat, 3, 1, 1), nn.BatchNorm2d(feat), nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(feat, feat * 2, 3, 1, 1), nn.BatchNorm2d(feat * 2), nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(feat * 2, feat * 4, 3, 1, 1), nn.BatchNorm2d(feat * 4), nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),
            nn.Conv2d(feat * 4, feat * 4, 3, 1, 1), nn.BatchNorm2d(feat * 4), nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),
        )
        self.rnn = nn.LSTM(feat * 4, hidden, bidirectional=True, batch_first=True)
        self.head = nn.Linear(hidden * 2, vocab_size)

    def forward(self, x):
        # x: (N, 1, H, W)
        f = self.cnn(x)                # (N, C, H', W')
        f = f.mean(dim=2).transpose(1, 2)  # (N, W', C)
        h, _ = self.rnn(f)
        return F.log_softmax(self.head(h).transpose(0, 1), dim=-1)  # (W', N, vocab)
```

고정 높이 입력(CNN이 높이를 1로 max-pool). 너비는 CTC의 시간 차원이다.

### 단계 3: 합성 OCR

종단간 연기 테스트를 위한 흰색 배경의 검은 숫자 문자열 생성.

```python
import numpy as np

def synthetic_line(text, height=32, char_width=16):
    W = char_width * len(text)
    img = np.ones((height, W), dtype=np.float32)
    for i, c in enumerate(text):
        x = i * char_width
        shade = 0.0 if c.isalnum() else 0.5
        img[6:height - 6, x + 2:x + char_width - 2] = shade
    return img


def build_batch(strings, vocab):
    H = 32
    W = 16 * max(len(s) for s in strings)
    imgs = np.ones((len(strings), 1, H, W), dtype=np.float32)
    target_lengths = []
    targets = []
    for i, s in enumerate(strings):
        imgs[i, 0, :, :16 * len(s)] = synthetic_line(s)
        ids = [vocab.index(c) for c in s]
        targets.extend(ids)
        target_lengths.append(len(ids))
    return torch.from_numpy(imgs), torch.tensor(targets), torch.tensor(target_lengths)


vocab = ["_"] + list("0123456789abcdefghijklmnopqrstuvwxyz")
imgs, targets, lengths = build_batch(["hello", "world"], vocab)
print(f"images: {imgs.shape}   targets: {targets.shape}   lengths: {lengths.tolist()}")
```

실제 OCR 데이터셋은 폰트, 노이즈, 회전, 블러, 색상을 추가한다. 위의 파이프라인은 동일하다.

### 단계 4: 훈련 스케치

```python
model = TinyCRNN(vocab_size=len(vocab))
opt = torch.optim.Adam(model.parameters(), lr=1e-3)

for step in range(200):
    strings = ["abc" + str(step % 10)] * 4 + ["xyz" + str((step + 1) % 10)] * 4
    imgs, targets, target_lens = build_batch(strings, vocab)
    log_probs = model(imgs)  # (W', 8, vocab)
    input_lens = torch.full((8,), log_probs.size(0), dtype=torch.long)
    loss = ctc_loss(log_probs, targets, input_lens, target_lens, blank=0)
    opt.zero_grad(); loss.backward(); opt.step()
```

이 단순한 합성 데이터에서 손실은 200단계에 걸쳐 ~3에서 ~0.2로 감소해야 한다.

## 사용 It

세 가지 프로덕션 경로:

- **PaddleOCR** — 성숙, 빠름, 다국어. 한 줄 사용: `paddleocr.PaddleOCR(lang="en").ocr(image_path)`.
- **EasyOCR** — Python 네이티브, 다국어, PyTorch 백본.
- **Tesseract** — 고전적; 모델이 어려움을 겪을 때 오래된 스캔 문서에 여전히 유용.

종단간 문서 파싱의 경우 Donut 또는 VLM을 사용한다:

```python
from transformers import DonutProcessor, VisionEncoderDecoderModel

processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")
model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")
```

반복 가능한 구조의 영수증, 인보이스, 양식의 경우 Donut을 미세조정한다. 임의 문서 또는 추론이 필요한 OCR의 경우 Qwen-VL-OCR과 같은 VLM이 현재 기본값이다.

## 배송 It

이 과목은 다음을 제공한다:

- `outputs/prompt-ocr-stack-picker.md` — 문서 유형, 언어, 구조에 따라 Tesseract / PaddleOCR / Donut / VLM-OCR을 선택하는 프롬프트.
- `outputs/skill-ctc-decoder.md` — 탐욕적 및 빔 서치 CTC 디코더를 처음부터, 길이 정규화를 포함하여 작성하는 스킬.

## 연습 문제

1. **(쉬움)** TinyCRNN을 5자리 무작위 숫자 문자열로 500단계 훈련한다. 보류 세트에서 CER을 보고한다.
2. **(중간)** 탐욕적 디코딩을 빔 서치(beam_width=5)로 대체한다. CER 델타를 보고한다. 어떤 입력에서 빔 서치가 승리하는가?
3. **(어려움)** PaddleOCR을 20개의 영수증 세트에 사용하고, 라인 항목을 추출하며, {item_name, price} 쌍에 대해 수동 레이블링된 정답과의 F1을 계산한다.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| OCR | "픽셀에서 텍스트로" | 이미지 영역을 문자 시퀀스로 변환 |
| CTC | "정렬 프리 손실" | 시간 단계별 레이블 없이 시퀀스 모델을 훈련하는 손실; 정렬에 대해 주변화 |
| CRNN | "고전적 OCR 모델" | Conv 특징 추출기 + BiLSTM + CTC; 프로덕션에서 여전히 사용되는 2015 기준선 |
| Donut | "종단간 OCR" | ViT 인코더 + 텍스트 디코더; 이미지에서 직접 JSON 출력 |
| 레이아웃 파싱 | "영역 찾기" | 문서에서 제목/표/그림/단락 영역을 검출하고 레이블링 |
| 읽기 순서 | "텍스트 시퀀스" | 인식된 영역을 문장으로 정렬; 라틴어는 간단, 혼합 레이아웃은 복잡 |
| CER / WER | "오류율" | 문자 또는 단어 세분성의 Levenshtein 거리 / 참조 길이 |
| VLM-OCR | "읽는 LLM" | OCR 작업에 훈련되거나 프롬프트된 비전-언어 모델; 복잡한 문서에 대한 현재 SOTA |

## 추가 읽기

- [CRNN (Shi et al., 2015)](https://arxiv.org/abs/1507.05717) — 원본 CNN+RNN+CTC 아키텍처
- [CTC (Graves et al., 2006)](https://www.cs.toronto.edu/~graves/icml_2006.pdf) — 원본 CTC 논문; 알고리즘 아이디어로 가득 차 있음
- [Donut (Kim et al., 2022)](https://arxiv.org/abs/2111.15664) — OCR 없는 문서 이해 트랜스포머
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) — 오픈소스 프로덕션 OCR 스택
