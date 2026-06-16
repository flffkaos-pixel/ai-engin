# 챗봇 — 규칙 기반에서 신경망으로, 그리고 LLM 에이전트로

> ELIZA는 패턴 매칭으로 응답했다. DialogFlow는 의도를 매핑했다. GPT는 가중치에서 답변했다. Claude는 도구를 실행하고 검증한다. 각 시대는 이전 시대의 최악의 실패를 해결했다.

**Type:** Learn
**Languages:** Python
**Prerequisites:** Phase 5 · 13 (Question Answering), Phase 5 · 14 (Information Retrieval)
**Time:** ~75분

## 문제

사용자가 "항공편을 변경하고 싶어요"라고 말한다. 시스템은 사용자가 원하는 것, 누락된 정보, 그것을 얻는 방법, 그리고 작업을 완료하는 방법을 파악해야 한다. 그런 다음 사용자가 "잠깐, 대신 취소하면 어떻게 되죠?"라고 말하면 시스템은 컨텍스트를 기억하고 작업을 전환하며 상태를 유지해야 한다.

## 개념

**규칙 기반 (ELIZA, AIML, DialogFlow).** 수동 작성 패턴. 의도 분류기가 사전 정의된 흐름으로 라우팅.

**검색 기반.** FAQ 스타일. 발화-응답 쌍을 인코딩하고 검색.

**신경망 (seq2seq).** 대화 로그로 학습된 인코더-디코더. 처음부터 응답 생성.

**LLM 에이전트.** 계획, 도구 호출, 결과 검증 루프로 감싸진 언어 모델.

## 직접 구현하기

## 사용하기

| 사용 사례 | 아키텍처 |
|-----------|---------|
| 예약, 결제, 인증 | 규칙 기반 상태 머신 + 슬롯 채우기 |
| 고객 지원 FAQ | 큐레이션된 답변 검색 |
| 개방형 도움말 채팅 | LLM 에이전트 + RAG + 도구 호출 |
| 내부 도구 / IDE 어시스턴트 | LLM 에이전트 + 도구 호출 |

## 최종 결과물

`outputs/skill-chatbot-architect.md`로 저장:

```markdown
---
name: chatbot-architect
description: 주어진 사용 사례에 대한 챗봇 스택을 설계한다.
version: 1.0.0
phase: 5
lesson: 17
tags: [nlp, agents, chatbot]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| Intent | 사용자가 원하는 것. 핸들러로 라우팅되는 범주 레이블. |
| Slot | 봇이 필요한 파라미터. |
| RAG | 검색 증강 생성. 관련 문서 검색 후 LLM 응답 근거. |
| Tool call | LLM이 이름+인수로 구조화된 호출을 방출. |
| Agent loop | 작업 완료까지 LLM 호출과 도구 호출을 교차 실행. |
| Prompt injection | 시스템 프롬프트를 무시하려는 악의적 입력. |

## 추가 자료

- [Weizenbaum (1966). ELIZA](https://web.stanford.edu/class/cs124/p36-weizenabaum.pdf)
- [Thoppilan et al. (2022). LaMDA](https://arxiv.org/abs/2201.08239)
- [Yao et al. (2022). ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic's guide on building effective agents](https://www.anthropic.com/research/building-effective-agents)
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
