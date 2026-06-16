# 트랜스포머 이전의 텍스트 생성 — N-그램 언어 모델

> 단어가 놀랍다면 모델이 나쁜 것이다. 퍼플렉시티는 놀라움을 숫자로 만든다. 스무딩은 그것을 유한하게 유지한다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 01 (Text Processing), Phase 2 · 14 (Naive Bayes)
**Time:** ~45분

## 문제

트랜스포머, RNN, 단어 임베딩 이전에 언어 모델은 이전 `n-1`개 단어 뒤에 얼마나 자주 오는지 세어 다음 단어를 예측했다. 그것이 n-그램 언어 모델이다. 1980년부터 2015년까지 모든 음성 인식기, 맞춤법 검사기, 구문 기반 기계 번역 시스템을 구동했다.

흥미로운 문제는 보지 못한 n-그램을 어떻게 처리할 것인가다. 원시 카운트 기반 모델은 보지 못한 것에 0 확률을 할당하며, 이는 치명적이다.

## 개념

**스무딩 접근법:**

1. **Laplace (add-one).** 모든 카운트에 1을 더함.
2. **Good-Turing.** 빈도-빈도에 기반하여 확률 질량 재할당.
3. **보간.** n-그램, (n-1)-그램 추정치 결합.
4. **백오프.** n-그램 카운트가 0이면 (n-1)-그램으로 폴백.
5. **절대 할인.** 모든 카운트에서 고정 할인 `D` 차감.
6. **Kneser-Ney.** 절대 할인 + 하위 차수 모델에 대한 연속 확률.

## 직접 구현하기

## 사용하기

- **고전적 NLP 교육.** 스무딩, MLE, 퍼플렉시티에 대한 가장 명확한 노출.
- **KenLM.** 프로덕션 n-그램 라이브러리.
- **온디바이스 자동완성.** 키보드의 삼중그램 모델.
- **기준선.** 신경망 LM을 선언하기 전에 항상 n-그램 LM 퍼플렉시티 계산.

## 최종 결과물

`outputs/prompt-lm-baseline.md`로 저장:

```markdown
---
name: lm-baseline
description: 신경망 LM을 학습시키기 전에 재현 가능한 n-그램 언어 모델 기준선을 구축한다.
phase: 5
lesson: 16
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| N-gram | `n`개 연속 토큰의 시퀀스. |
| Smoothing | 보지 못한 이벤트에 0이 아닌 확률 할당. |
| Perplexity | `exp(-평균 log-확률)`. 낮을수록 좋음. |
| Backoff | 더 짧은 컨텍스트로 폴백. |
| Kneser-Ney | 절대 할인 + 연속 확률. |
| Continuation probability | 단어가 나타나는 컨텍스트 수로 가중치 부여. |

## 추가 자료

- [Jurafsky and Martin — Chapter 3](https://web.stanford.edu/~jurafsky/slp3/3.pdf)
- [Chen and Goodman (1998). An Empirical Study of Smoothing](https://dash.harvard.edu/handle/1/25104739)
- [Kneser and Ney (1995). Improved Backing-off](https://ieeexplore.ieee.org/document/479394)
- [KenLM](https://kheafield.com/code/kenlm/)
