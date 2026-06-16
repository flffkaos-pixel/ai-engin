# 긴 컨텍스트 평가 — NIAH, RULER, LongBench, MRCR

> Gemini 3 Pro는 1천만 토큰 컨텍스트를 광고한다. 1백만 토큰에서 8-니들 MRCR은 26.3%로 떨어진다. 광고된 것 ≠ 사용 가능한 것. 긴 컨텍스트 평가는 실제 용량을 알려준다.

**Type:** Learn
**Languages:** Python
**Prerequisites:** Phase 5 · 13 (Question Answering), Phase 5 · 23 (Chunking Strategies)
**Time:** ~60분

## 문제

200페이지 계약서가 있다. 모델이 1백만 토큰 컨텍스트를 주장한다. 계약서를 붙여넣고 "해지 조항이 무엇인가요?"라고 묻는다. 모델이 표지에서 답변한다 — 해지 조항이 120k 토큰 깊이에 있기 때문이다.

이것이 2026년 컨텍스트 용량 격차다.

## 개념

**NIAH (Needle-in-a-Haystack, 2023).** 긴 컨텍스트의 제어된 깊이에 사실을 배치하고 검색 요청.

**RULER (Nvidia, 2024).** 13개 작업 유형, 4개 카테고리.

**LongBench v2 (2024).** 503개 객관식 질문.

**MRCR.** 대규모 다중 라운드 상호참조 해결.

## 직접 구현하기

## 사용하기

```python
def score_niah(model, haystack, question, expected):
    answer = model.complete(f"Context: {haystack}\nQ: {question}\nA:", max_tokens=50)
    return 1 if expected.lower() in answer.lower() else 0
```

## 최종 결과물

`outputs/skill-long-context-eval.md`로 저장:

```markdown
---
name: long-context-eval
description: 주어진 모델과 사용 사례에 대한 긴 컨텍스트 평가 배터리를 설계한다.
version: 1.0.0
phase: 5
lesson: 28
tags: [nlp, long-context, evaluation]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| NIAH | 건초 더미 속의 바늘. 필러에 사실을 심고 검색 요청. |
| RULER | 13개 작업 유형의 NIAH 강화판. |
| Effective context | 정확도가 임계값 이상을 유지하는 길이. |
| Lost in the middle | 모델이 긴 입력의 중간 내용을 덜 주목함. |
| Multi-needle | 여러 개의 심기. 주의 분할 테스트. |
| MRCR | 다중 라운드 상호참조. 주의 포화 노출. |

## 추가 자료

- [Kamradt (2023). Needle In A Haystack](https://github.com/gkamradt/LLMTest_NeedleInAHaystack)
- [Hsieh et al. (2024). RULER](https://arxiv.org/abs/2404.06654)
- [Bai et al. (2024). LongBench v2](https://arxiv.org/abs/2412.15204)
- [Modarressi et al. (2024). NoLiMa](https://arxiv.org/abs/2404.06666)
- [Kuratov et al. (2024). BABILong](https://arxiv.org/abs/2406.10149)
- [Liu et al. (2024). Lost in the Middle](https://arxiv.org/abs/2307.03172)
