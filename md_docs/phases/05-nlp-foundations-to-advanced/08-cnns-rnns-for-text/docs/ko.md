# 텍스트를 위한 CNN과 RNN

> 합성곱은 n-그램을 학습한다. 순환은 기억한다. 둘 다 어텐션에 의해 대체되었지만 제한된 하드웨어에서는 여전히 중요하다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 3 · 11 (PyTorch Intro), Phase 5 · 03 (Word Embeddings), Phase 4 · 02 (Convolutions from Scratch)
**Time:** ~75분

## 문제

TF-IDF와 Word2Vec은 단어 순서를 무시하는 평탄한 벡터를 생성했다. 이 벡터로 만든 분류기는 `dog bites man`과 `man bites dog`를 구별할 수 없었다. 단어 순서가 때로는 신호를 전달한다.

트랜스포머 이전에 두 가지 아키텍처 계열이 이 격차를 메웠다.

**텍스트를 위한 합성곱 신경망(TextCNN).** 단어 임베딩 시퀀스에 1D 합성곱을 적용한다. 너비 3의 필터는 학습 가능한 삼중그램 감지기다. 2, 3, 4, 5 등 다양한 너비를 쌓아 다중 스케일 패턴을 감지한다. 최대 풀링으로 고정 크기 표현을 만든다. 평탄하고, 병렬적이며, 빠르다.

**순환 신경망(RNN, LSTM, GRU).** 토큰을 하나씩 처리하며 정보를 전달하는 은닉 상태를 유지한다. 순차적이고, 메모리를 가지며, 입력 길이가 유연하다. 2014년부터 2017년까지 시퀀스 모델링을 지배했다.

## 개념

**TextCNN** (Kim, 2014). 토큰이 임베딩된다. 너비-`k` 1D 합성곱이 연속된 `k`-그램 임베딩 위로 슬라이드하여 특징 맵을 생성한다. 전역 최대 풀링이 가장 강한 활성화를 선택한다. 여러 필터 너비의 최대 풀링 출력을 연결한다. 분류기 헤드로 전달한다.

**RNN.** 각 시간 단계 `t`에서 은닉 상태 `h_t = f(W * x_t + U * h_{t-1} + b)`.

## 직접 구현하기

## 사용하기

```python
from transformers import AutoModel

encoder = AutoModel.from_pretrained("bert-base-uncased")
for param in encoder.parameters():
    param.requires_grad = False


class BertCNN(nn.Module):
    def __init__(self, n_classes, filter_widths=(2, 3, 4), n_filters=64):
        super().__init__()
        self.encoder = encoder
        self.convs = nn.ModuleList([nn.Conv1d(768, n_filters, kernel_size=k) for k in filter_widths])
        self.fc = nn.Linear(n_filters * len(filter_widths), n_classes)
    ...
```

## 최종 결과물

`outputs/prompt-text-encoder-picker.md`로 저장:

```markdown
---
name: text-encoder-picker
description: 주어진 제약 조건 집합에 대한 텍스트 인코더 아키텍처를 선택한다.
phase: 5
lesson: 08
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| TextCNN | 텍스트용 CNN. 단어 임베딩 위의 1D 합성곱 스택. |
| RNN | 순환 신경망. 각 시간 단계에서 은닉 상태 업데이트. |
| LSTM | 게이트형 RNN. 입력/망각/출력 게이트 + 셀 상태 추가. |
| GRU | 단순화된 LSTM. 유사한 정확도, 더 적은 파라미터. |
| Bidirectional | 양방향. 앞+뒤 RNN 연결. |
| Vanishing gradient | 학습 신호 소멸. 단순 RNN의 <1 가중치 반복 곱셈. |

## 추가 자료

- [Kim, Y. (2014). Convolutional Neural Networks for Sentence Classification](https://arxiv.org/abs/1408.5882)
- [Hochreiter, S. and Schmidhuber, J. (1997). Long Short-Term Memory](https://www.bioinf.jku.at/publications/older/2604.pdf)
- [Olah, C. (2015). Understanding LSTM Networks](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
