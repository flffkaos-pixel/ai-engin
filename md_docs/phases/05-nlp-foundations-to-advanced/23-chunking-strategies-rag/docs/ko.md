# RAG를 위한 청킹 전략

> 청킹 설정은 임베딩 모델 선택만큼 검색 품질에 영향을 미친다. 청킹을 잘못하면 어떤 재순위화도 구할 수 없다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 14 (Information Retrieval), Phase 5 · 22 (Embedding Models)
**Time:** ~60분

## 문제

50페이지 계약서를 RAG 시스템에 넣었다. 사용자가 "해지 조항이 무엇인가요?"라고 묻는다. 검색기가 표지를 반환한다. 이유는? 모델이 512-토큰 청크로 학습되었고 해지 조항은 20페이지 뒤, 페이지 나누기에 걸쳐 있고 쿼리와 연결되는 지역 키워드가 없다.

해결책은 "더 나은 임베딩 모델을 사라"가 아니다. 해결책은 청킹이다.

## 개념

**고정 청킹.** N 문자/토큰마다 분할. 가장 단순한 기준선.

**재귀적.** LangChain의 RecursiveCharacterTextSplitter. `\n\n`, `\n`, `.`, 공백 순으로 분할.

**의미론적.** 각 문장 임베딩. 인접 문장 간 코사인 유사도 계산. 유사도가 임계값 아래로 떨어지면 분할.

**문장.** 문장 경계에서 분할.

**부모-문서.** 작은 자식 청크를 검색용으로 저장하고 큰 부모 청크를 컨텍스트용으로 저장.

**늦은 청킹.** 토큰 수준에서 전체 문서를 먼저 임베딩한 후 토큰 임베딩을 청크 임베딩으로 풀링.

## 직접 구현하기

## 사용하기

| 쿼리 유형 | 청크 크기 |
|-----------|----------|
| 사실형 ("CEO 이름이 뭐예요?") | 256-512 토큰 |
| 분석적 / 다중 홉 | 512-1024 토큰 |
| 전체 섹션 이해 | 1024-2048 토큰 |

## 최종 결과물

`outputs/skill-chunker.md`로 저장:

```markdown
---
name: chunker
description: 주어진 말뭉치와 쿼리 분포에 대한 청킹 전략을 선택한다.
version: 1.0.0
phase: 5
lesson: 23
tags: [nlp, rag, chunking]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Chunk | 문서의 조각. 임베딩, 인덱싱, 검색되는 하위 문서 단위. |
| Overlap | 인접 청크 간 공유 토큰. |
| Semantic chunking | 인접 문장 임베딩 유사도가 떨어지는 곳에서 분할. |
| Parent-document | 2단계 검색. 작은 자식 검색, 큰 부모 반환. |
| Late chunking | 임베딩 후 청킹. |
| Contextual retrieval | 인덱싱 전 각 청크에 LLM 생성 요약을 앞에 추가. |

## 추가 자료

- [LangChain Recursive Character Splitter](https://python.langchain.com/docs/how_to/recursive_text_splitter/)
- [Vectara (2024). Chunking configurations analysis](https://arxiv.org/abs/2410.13070)
- [Jina AI — Late Chunking](https://jina.ai/news/late-chunking-in-long-context-embedding-models/)
- [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
