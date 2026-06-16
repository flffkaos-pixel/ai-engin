# Agentic RAG와 지식 그래프

> Agentic RAG는 단일 검색 쿼리를 에이전트가 여러 도구(웹 검색, 벡터 DB, 지식 그래프)를 사용하는 다단계 계획으로 대체한다. 지식 그래프는 엔터티 관계를 모델링한다. 에이전트는 그래프를 탐색하여 특정 정보를 찾는다. 최종 단계는 검색 결과를 하나의 답변으로 합성한다.

**Type:** Learn + Build (Capstone)
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 10 (Skill Libraries)
**Time:** ~90분

## 학습 목표

- Agentic RAG(다단계 검색 계획)와 기본 RAG(단일 검색 쿼리)의 차이를 설명한다.
- 지식 그래프(엔터티 + 관계)가 있고 없는 RAG의 경우를 비교한다.
- Agentic RAG 시스템의 세 가지 단계를 명명한다: 검색 계획, 도구별 검색, 결과 합성.
- 에이전트 루프(레슨 01)를 RAG 파이프라인에 연결하는 `검색_계획` → `도구_실행` → `합성` 패턴을 구현한다.

## 문제

기본 RAG는 사용자 질문을 가져와 단일 검색 쿼리로 변환하고, 벡터 DB에서 결과를 검색한다. 정보가 여러 소스에 분산되어 있을 때 실패한다. Agentic RAG는 검색을 다단계 계획으로 대체한다. "마지막 3분기 매출 성장률은?" → 계획 수립: "재무 보고서 확인" → "분기별 성장 계산" → "답변 합성."

## 개념

### RAG의 진화

1. **기본 RAG.** "매출 성장" → 단일 벡터 검색 → 가장 가까운 문서 반환.
2. **Agentic RAG.** "매출 성장" → 검색 계획 수립 → 웹 검색(최신 뉴스), 벡터 DB(분기별 보고서), 지식 그래프(회사 엔터티) → 결과 합성.

### Agentic RAG 단계

**1단계: 검색 계획**

에이전트가 사용자 질문을 평가하고 검색 전략을 수립:

- 어느 저장소에 쿼리할 것인가? (웹, 벡터 DB, 지식 그래프)
- 어떤 정보가 필요한가? (텍스트, 엔터티, 관계)
- 어떤 순서로? (병렬 또는 순차적 검색)

**2단계: 도구별 검색**

각 저장소에 계획을 실행:

- **웹 검색.** 최신 정보.
- **벡터 DB.** 의미 검색.
- **지식 그래프.** 엔터티 관계 검색. 지식 그래프가 없으면 벡터 검색만으로 충분할 수 있음.

**3단계: 합성**

에이전트가 검색 결과를 취합하여 최종 답변 생성. 충돌하는 정보를 해결.

### 지식 그래프

지식 그래프는 엔터티와 그 관계를 명시적으로 모델링. 지식 그래프가 RAG에 도움이 되는 경우:

- **엔터티 관계.** "회사 A가 회사 B를 인수" — 그래프가 관계를 저장.
- **멀티 홉 추론.** "회사 A의 모든 자회사는?" — 그래프 탐색 필요.

지식 그래프가 없는 경우: "텍스트만 있어도 괜찮다면 벡터 검색으로 충분."

### 도구

| 도구 | Agentic RAG에서의 역할 | 예시 |
|------|----------------------|---------|
| 웹 검색 | 최신 정보 | "2026년 시장 동향" |
| 벡터 DB | 의미 검색 | "RAG 패턴 문서" |
| 지식 그래프 | 엔터티 관계 검색 | "회사 A가 회사 B를 소유" |
| 코드 실행 | 검색 결과 변환 | "분기별 성장 계산" |

### 이 패턴이 잘못되는 경우

- **과잉 검색.** 정보가 하나의 벡터 DB에 있을 때 웹 검색, 그래프 검색, 벡터 검색을 모두 사용. 단일 소스로 충분.
- **합성 전에 결과 검증 부족.** 검색 결과가 신뢰할 수 없는 경우 합성 단계에서 잘못된 답변을 생성. 결과 점수를 합성에 포함.
- **그래프를 RAG에만 사용.** 지식 그래프는 쿼리 보강 이상의 가치가 있음. 추론 및 분석에도 사용.

## 직접 구현하기

`code/main.py`는 Agentic RAG 시스템을 구현:

- 검색 계획자: 질문 분석, 3개의 검색 엔진에 쿼리 계획 수립.
- 검색 엔진: 웹 검색(시뮬레이션), 벡터 DB, 지식 그래프.
- 합성 엔진: 검색 결과 취합, 충돌 해결, 최종 답변 생성.
- 지식 그래프: 엔터티(회사)와 관계(인수, 소유)가 있는 인메모리 그래프.

실행:

```
python3 code/main.py
```

출력: 검색 계획, 도구별 검색 결과, 합성된 답변.

## 활용하기

- **Agentic RAG** for questions that span multiple sources or need multi-hop reasoning.
- **Basic RAG** for simple Q&A from a single document store.
- **Knowledge graphs** for entity-rich domains (finance, law, healthcare).

## 배포하기

`outputs/skill-agentic-rag.md` scaffolds an Agentic RAG pipeline with search planner, tool-specific search, and synthesis with an optional knowledge graph.

## 연습 문제

1. 장난감 시스템에 네 번째 검색 엔진(데이터베이스) 추가. 검색 계획자가 쿼리를 어디로 라우팅하는가?
2. 합성 단계에서 충돌 해결 구현: 검색 엔진 A가 "매출 10% 증가"라고 하고 검색 엔진 B가 "매출 5% 감소"라고 하면 합성 엔진은 무엇을 하는가?
3. 검색 결과 점수 매기기 추가: 각 검색 결과에 신뢰도 점수를 할당하고 합성 단계에서 사용.
4. 지식 그래프와 벡터 검색을 비교: 동일한 질문에서 그래프가 있는 경우와 없는 경우의 결과 차이를 보여줌.
5. 검색 계획을 모듈러 프롬프트(레슨 31)로 교체: 다른 질문 유형이 다른 검색 전략을 사용하는 방법.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Agentic RAG | "다단계 검색" | 다중 도구 검색 계획 + 합성 |
| Basic RAG | "단일 검색" | 단일 벡터 검색 + 읽기 |
| Knowledge graph | "엔터티 관계" | 엔터티와 그 관계 모델링 |
| Search planner | "검색 전략" | 검색할 저장소와 순서 결정 |
| Synthesis | "결과 취합" | 충돌 해결과 함께 최종 답변 생성 |
| Multi-hop reasoning | "멀티 단계 추론" | 답변을 위해 여러 검색 단계가 필요한 질문 |

## 추가 자료

- [LangChain, Agentic RAG](https://blog.langchain.dev/agentic-rag/) — multi-step search patterns
- [Neo4j, Knowledge Graphs + LLMs](https://neo4j.com/blog/graphrag-manifesto/) — knowledge graph RAG
- [Microsoft, GraphRAG](https://www.microsoft.com/en-us/research/project/graphrag/) — global query over knowledge graphs
- [OpenAI, RAG guide](https://platform.openai.com/docs/guides/rag) — basic RAG vs agentic RAG
