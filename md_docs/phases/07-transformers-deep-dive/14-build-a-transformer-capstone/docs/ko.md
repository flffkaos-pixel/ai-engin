# Scratch에서 Transformer 구축 — 최종 프로젝트

> 13개의 수업. 하나의 모델. 지름길 없음.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 7 · 01 through 13. 건너뛰지 마라.
**소요 시간:** ~120분

## 문제

모든 논문을 읽었다. Attention, multi-head 분할, 위치 인코딩, encoder 및 decoder 블록, BERT 및 GPT 손실, MoE, KV cache를 구현했다. 이제 그것들을 실제 작업에서 함께 작동하게 하라.

최종 프로젝트: 문자 수준 언어 모델링 작업에서 작은 decoder-only transformer를 종단 간 교육한다. Shakespeare를 읽는다. 새로운 Shakespeare를 생성한다. 10분 이내에 랩톱에서 교육할 수 있을 만큼 작다. 더 큰 데이터 세트와 더 긴 교육으로 교체하면 실제 LM이 될 만큼 정확하다.

이것은 코스의 "nanoGPT"이다. 독창적이지 않다 — Karpathy의 2023년 nanoGPT 튜토리얼은 모든 학생이 최소 한 번은 작성하는 참조 구현이다. 우리가 모양을 들어올리고 우리가 다룬 것을 중심으로 재구성한다.

## 개념

![Scratch에서 Transformer 블록 다이어그램](../assets/capstone.svg)

주석이 달린 아키텍처:

```
input tokens (B, N)
   │
   ▼
token embedding + positional embedding  ◀── Lesson 04 (RoPE 옵션)
   │
   ▼
┌──── block × L ────────────────────┐
│  RMSNorm                          │  ◀── Lesson 05
│  MultiHeadAttention (causal)      │  ◀── Lesson 03 + 07 (causal mask)
│  residual                         │
│  RMSNorm                          │
│  SwiGLU FFN                       │  ◀── Lesson 05
│  residual                         │
└────────────────────────────────── ┘
   │
   ▼
final RMSNorm
   │
   ▼
lm_head (token embedding에 바이어스)
   │
   ▼
logits (B, N, V)
   │
   ▼
shift-by-one cross-entropy            ◀── Lesson 07
```

### 우리가 출하하는 것

- `GPTConfig` — 모든 하이퍼파라미터를 구성하는 하나의 장소.
- `MultiHeadAttention` — causal, batched, 선택적 Flash 스타일 경로 (PyTorch의 `scaled_dot_product_attention`).
- `SwiGLUFFN` — 현대 FFN.
- `Block` — pre-norm, residual로 감싼 attention + FFN.
- `GPT` — 임베딩, 쌓인 블록, LM head, generate().
- AdamW, cosine LR, gradient clipping이 있는 교육 루프.
- Shakespeare 텍스트에 대한 문자 수준 토크나이저.

### 우리가 출하하지 않는 것

- RoPE — Lesson 04에서 개념적으로 구현됨. 여기서는 간단하게 학습된 위치 임베딩을 사용. 연습 문제에서 RoPE로 교체하도록 요청.
- 생성 중 KV cache — 각 생성 단계에서 전체 접두사에 대해 attention을 다시 계산. 더 느리지만 더 간단. 연습 문제에서 KV cache 추가를 요청.
- Flash Attention — PyTorch 2.0+는 입력이 일치하면 자동 디스패치; `F.scaled_dot_product_attention`을 사용.
- MoE — 블록당 단일 FFN. Lesson 11에서 MoE를 봄.

### 목표 메트릭

Mac M2 랩톱에서 4층, 4-head, d_model=128 GPT를 `tinyshakespeare.txt`에서 2,000단계 교육:

- 교육 손실이 약 4.2 (무작위)에서 ~1.5로 약 6분 만에 수렴.
- 샘플링된 출력은 Shakespeare 형태이다: 고어 단어, 줄 바꿈, "ROMEO:"와 같은 고유 이름이 나타남.
- Val 손실 (텍스트의 마지막 10% 보류)은 교육 손실과 밀접하게 추적; 이 크기/예산에서는 과적합 없음.

## 실습

이 수업은 PyTorch를 사용한다. `torch` 설치 (CPU 빌드로 충분). `code/main.py`를 참조. 스크립트 처리:

- 누락된 경우 `tinyshakespeare.txt` 다운로드 (또는 로컬 복사 읽기).
- 바이트 수준 문자 토크나이저.
- 90/10에서 train/val 분할.
- 지원 하드웨어에서 bf16 autocast가 있는 교육 루프.
- 교육 완료 후 샘플링.

### Step 1: 데이터

```python
text = open("tinyshakespeare.txt").read()
chars = sorted(set(text))
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for c, i in stoi.items()}
encode = lambda s: [stoi[c] for c in s]
decode = lambda xs: "".join(itos[x] for x in xs)
```

65개의 고유 문자. 작은 어휘. 4바이트 vocab_size에 적합. BPE 없음, 토크나이저 drama 없음.

### Step 2: 모델

`code/main.py`를 참조. 블록은 Lesson 05의 교과서 — pre-norm, RMSNorm, SwiGLU, causal MHA. 4/4/128의 매개변수 수: ~800K.

### Step 3: 교육 루프

길이-256 토큰 윈도우의 무작위 배치를 가져온다. Forward. Shift-by-one cross-entropy. Backward. AdamW 단계. 로그. 반복.

```python
for step in range(max_steps):
    x, y = get_batch("train")
    logits = model(x)
    loss = F.cross_entropy(logits.view(-1, vocab_size), y.view(-1))
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    opt.zero_grad()
```

### Step 4: 샘플

프롬프트를 받으면, 반복적으로 forward하고, top-p 로짓에서 샘플링하고, 추가하고, 계속한다. 500 토큰 후 중지.

### Step 5: 출력 읽기

2,000단계 후:

```
ROMEO:
Away and mild will not thy friend, that thou shalt wit:
The chief that well shame and hath been his friends,
...
```

Shakespeare가 아니다. 하지만 Shakespeare 형태. ~800K 매개변수와 랩톱에서 6분에 대한 명확한 승리.

## 활용

이 최종 프로젝트는 참조 아키텍처이다. Something real로 출하하기 위한 세 가지 확장:

1. **토크나이저 교체.** BPE 사용 (예: `tiktoken.get_encoding("cl100k_base")`). 어휘 크기가 65에서 ~50,000으로 점프. 모델 용량이 그에 따라 스케일업해야 한다.
2. **더 큰 코퍼스에서 교육.** `OpenWebText` 또는 `fineweb-edu` 사용 (HuggingFace). 125M-param GPT에서 단일 A100에서 10B 토큰에 ~24시간 소요.
3. **RoPE + KV cache + Flash Attention 추가.** 아래 연습 문제가 각 문제를 안내.

결과적으로 流暢한 영어를 생성하는 125M 매개변수 GPT가 된다. 프론티어 모델이 아니다. 하지만 동일한 코드 경로 — 그냥 더 큰 — 가 Karpathy, EleutherAI 및 Allen Institute가 2026년 연구 체크포인트를 교육하는 데 사용하는 것이다.

## 결과물

`outputs/skill-transformer-review.md`를 참조. 이 skill는 13개의 이전 수업을 걸쳐 정확성을 위해 scratch에서 transformer 구현을 검토한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행한다. 교육된 모델의 최종 단계 검증 손실이 2.0 미만인지 확인. `max_steps`를 2,000에서 5,000으로 변경 — val 손실이 계속 개선되는가?
2. **보통.** 학습된 위치 임베딩을 RoPE로 교체. `MultiHeadAttention` 내부에서 Q와 K에 회전을 적용. 교육하고 val 손실이 적어도同等하게 낮은지 확인.
3. **보통.** 샘플링 루프에 KV cache를 구현. 캐시 유무로 500 토큰 생성. 랩톱에서 벽시계가 5–20× 개선되어야 한다.
4. **어려움.** 모델에 다음+1 토큰을 예측하는 두 번째 head 추가 (DeepSeek-V3의 MTP — Multi-Token Prediction). 공동 교육. 도움이 되는가?
5. **어려움.** 블록당 단일 FFN을 4-expert MoE로 교체. Router + top-2 라우팅. 일치하는 활성 매개변수에서 val 손실이 어떻게 변하는지 확인.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| nanoGPT | "Karpathy의 튜토리얼 리포" | 최소 decoder-only transformer 교육 코드, ~300 LOC; 표준 참조. |
| tinyshakespeare | "표준 토이 코퍼스" | ~1.1 MB 텍스트; 2015년以来的 모든 문자-LM 튜토리얼이 사용. |
| Tied embeddings | "입력/출력 행렬 공유" | LM head 가중치 = 토큰 임베딩 행렬의 전치; 매개변수 절약, 품질 향상. |
| bf16 autocast | "교육 정밀도 트릭" | forward/back를 bf16로 실행, 옵티마이저 상태를 fp32로 유지; 2021년以来的 표준. |
| Gradient clipping | "스파이크 중지" | 글로벌 grad norm을 1.0에서 캡; 교육 폭발 방지. |
| Cosine LR schedule | "2020+ 기본값" | LR이 선형으로 상승 (warmup) then 코사인 형태로 최고치의 10%로 감소. |
| MFU | "Model FLOP Utilization" | 달성된 FLOP / 이론적 피크; 2026년 strong 40% dense, 30% MoE. |
| Val loss | "보류 손실" | 모델이 본 적 없는 데이터에 대한 cross-entropy; 과적합 탐지기. |

## 추가 자료

- [The Annotated Transformer (Harvard NLP)](https://nlp.seas.harvard.edu/annotated-transformer/) — 주석이 달린 클래식 구현.