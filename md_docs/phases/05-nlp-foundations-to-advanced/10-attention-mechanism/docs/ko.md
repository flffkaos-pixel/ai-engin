# 어텐션 메커니즘 — 혁신

> 디코더는 압축된 요약을 응시하는 것을 멈추고 전체 소스를 보기 시작한다. 이후의 모든 것은 어텐션과 엔지니어링이다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 09 (Sequence-to-Sequence Models)
**Time:** ~45분

## 문제

레슨 09는 측정된 실패로 끝났다. 장난감 복사 작업에서 GRU 인코더-디코더는 길이 5에서 89% 정확도에서 길이 80에서 우연 수준으로 떨어진다. 이유는 구조적이며 학습 버그가 아니다: 인코더가 수집한 모든 정보가 하나의 고정 크기 은닉 상태에 들어가야 하며 디코더는 그 외에는 아무것도 볼 수 없다.

Bahdanau, Cho, Bengio는 2014년에 세 줄짜리 수정을 발표했다. 디코더에 마지막 인코더 상태만 주는 대신 모든 인코더 상태를 유지한다. 각 디코더 단계에서 인코더 상태의 가중 평균을 계산하며, 가중치는 "디코더가 지금 인코더 위치 `i`를 얼마나 봐야 하는가"를 나타낸다. 이 가중 평균이 컨텍스트이며 디코더 단계마다 변경된다.

## 개념

각 디코더 단계 `t`에서:

1. 이전 디코더 은닉 상태 `s_{t-1}`를 **쿼리**로 사용한다.
2. 모든 인코더 은닉 상태 `h_1, ..., h_T`에 대해 점수를 계산한다.
3. 소프트맥스로 어텐션 가중치 `α_{t,1}, ..., α_{t,T}`를 얻는다(합 = 1).
4. 컨텍스트 벡터 `c_t = Σ α_{t,i} * h_i`. 인코더 상태의 가중 평균.
5. 디코더가 `c_t`와 이전 출력 토큰을 사용하여 다음 토큰을 생성한다.

## 직접 구현하기

## 사용하기

PyTorch와 TensorFlow가 어텐션을 직접 제공한다.

```python
import torch
import torch.nn as nn

mha = nn.MultiheadAttention(embed_dim=128, num_heads=8, batch_first=True)
query = torch.randn(2, 5, 128)
key = torch.randn(2, 10, 128)
value = torch.randn(2, 10, 128)

output, weights = mha(query, key, value)
print(output.shape, weights.shape)
```

## 최종 결과물

`outputs/prompt-attention-shapes.md`로 저장:

```markdown
---
name: attention-shapes
description: 어텐션 구현의 shape 버그를 디버깅한다.
phase: 5
lesson: 10
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Attention | 값 시퀀스의 가중 평균, 쿼리-키 유사도에서 가중치 계산. |
| Query, Key, Value | QKV. 세 가지 투영. |
| Additive attention | Bahdanau. 피드포워드 점수. |
| Multiplicative attention | Luong dot/general. 점수 = `q^T k`. |
| Alignment matrix | 시각화용 어텐션 가중치 격자. |

## 추가 자료

- [Bahdanau, Cho, Bengio (2014). Neural Machine Translation by Jointly Learning to Align and Translate](https://arxiv.org/abs/1409.0473)
- [Luong, Pham, Manning (2015). Effective Approaches to Attention-based Neural MT](https://arxiv.org/abs/1508.04025)
- [Jain and Wallace (2019). Attention is not Explanation](https://arxiv.org/abs/1902.10186)
- [Dive into Deep Learning — Bahdanau Attention](https://d2l.ai/chapter_attention-mechanisms-and-transformers/bahdanau-attention.html)
