# 캐피톤 02 — 코드베이스 RAG (크로스repo 의미 검색)

> 2026년 모든 진지한 엔지니어링 조직은 의미,不仅仅是 문자열을 이해하는 내부 코드 검색을 실행한다. Sourcegraph Amp, Cursor의 코드베이스 답변, Augment의 엔터프라이즈 그래프, Aider의 repomap, Pinterest의 내부 MCP — 동일한 형태. 여러 repo 수집, tree-sitter로 파싱, 함수 및 클래스 수준 청크 임베딩, 하이브리드 검색, 리랭크, 인용과 함께 답변. 이 캐피톤은 10개 repo에 걸쳐 2M 줄의 코드를 처리하고 모든 git push에서 증분 재색인을 생존하는 하나를 구축하도록 요청한다.

**유형:** 캐피톤
**언어:** Python (수집), TypeScript (API + UI)
**선수 과목:** Phase 5 (NLP 기초), Phase 7 (트랜스포머), Phase 11 (LLM 엔지니어링), Phase 13 (도구), Phase 17 (인프라)
**연습 phases:** P5 · P7 · P11 · P13 · P17
**시간:** 30시간

## 문제

2026년까지 모든 프론티어 코딩 에이전트는 코드베이스 검색 레이어와 함께 출시된다. 컨텍스트 창만으로는 크로스repo 질문을 해결하지 않기 때문이다. Claude의 1M 토큰 컨텍스트는 도움이 된다; 순위 검색의 필요성을 eliminate하지 않는다. 원시 청크에 대한 순진한 코사인 검색은 생성된 코드, 모노레포 중복, 거의 import되지 않는 기호의 긴 꼬리에서 결과를 poison시킨다. 프로덕션 답변은 AST 인식 청크에 대한 하이브리드(밀도 + BM25) 검색과 리랭커, 기호 참조 그래프로 백업이다.

학습 곡선이 있는 실제 fleet를 인덱싱하여 MRR@10, 인용 충실도, 증분 신선도를 측정함으로써 이것을 배운다. 실패 모드는 인프라적이다: 100k 파일 모노레포, 절반의 파일을 다시touch하는 push, 4개 repo를 가로질러 올바르게 답변해야 하는 쿼리.

## 개념

AST 인식 수집 파이프라인은 각 파일을 tree-sitter로 파싱하고, 함수 및 클래스 노드를 추출하고, 고정 토큰 창이 아닌 노드 경계에서 청크한다. 각 청크는 세 가지 표현을 얻는다: 밀도 임베딩(Voyage-code-3 또는 nomic-embed-code), 희소 BM25 용어, 짧은 자연어 요약. 요약은 세 번째 검색 가능한 양식성을 추가한다 — 사용자가 "X가 어떻게 권한 부여되는지" 물으면 요약은 코드가 `check_permission`만 있는 경우에도 "authz"를 언급한다.

검색은 하이브리드이다. 쿼리는 밀도 검색과 BM25 검색을 모두 실행하고, 상위 k를 병합하고, union을 교차 인코더 리랭커(Cohere rerank-3 또는 bge-reranker-v2-gemma-2b)에 전달한다. 리랭크된 목록은 각 클레임을 파일 및 라인 범위로 인용하도록 지시하여 긴 컨텍스트 합성기(프롬프트 캐싱이 있는 Claude Sonnet 4.7, 또는 자체 호스팅 Llama 3.3 70B)로 이동한다. 인용 없는 답변은 post-filter에 의해 거부된다.

증분 신선도는 인프라 문제이다. Git push는 diff를 트리거한다: 어떤 파일이 변경되었는지, 어떤 기호가 변경되었는지. 영향을 받는 청크만 다시 임베딩한다. 영향을 받는 크로스 파일 기호 가장자리(가져오기, 메서드 호출)가 다시 계산된다. 인덱스는 각 커밋에서 2M 줄을 다시 처리하지 않고 일관된 상태를 유지한다.

## 아키텍처

```
git push --> webhook --> ingest worker (LlamaIndex Workflow)
                           |
                           v
             tree-sitter parse + AST chunk
                           |
            +--------------+----------------+
            v              v                v
          dense        BM25 index       summary (LLM)
        (Voyage / bge)  (Tantivy)        (Haiku 4.5)
            |              |                |
            +------> Qdrant / pgvector <----+
                            |
                            v
                      symbol graph (Neo4j / kuzu)
                            |
  query --> LangGraph agent (retrieve -> rerank -> synth)
                            |
                            v
                 Claude Sonnet 4.7 1M context
                            |
                            v
                 answer + file:line citations
```

## 스택

- 파싱: 17개 언어 문법이 있는 tree-sitter (Python, TS, Rust, Go, Java, C++ 등)
- 밀도 임베딩: Voyage-code-3(호스팅) 또는 nomic-embed-code-v1.5(자체 호스팅), bge-code-v1 폴백
- 희소 인덱스: BM25F가 있는 Tantivy(Rust), 기호 이름 가중치 4, 본문 가중치 1
- 벡터 DB: 하이브리드 검색이 있는 Qdrant 1.12, 또는 50M 벡터 미만 팀을 위한 pgvector + pgvectorscale
- 청크 요약 모델: Claude Haiku 4.5 또는 Gemini 2.5 Flash, 프롬프트 캐싱
- 리랭커: Cohere rerank-3 또는 자체 호스팅 bge-reranker-v2-gemma-2b
- 오케스트레이션: 수집을 위한 LlamaIndex Workflows, 쿼리 에이전트를 위한 LangGraph
- 합성기: 프롬프트 캐싱이 있는 Claude Sonnet 4.7 (1M 컨텍스트)
- 기호 그래프: 가져오기 및 호출 가장자리를 위한 Neo4j(관리) 또는 kuzu(임베디드)
- 가시성: 검색 + 합성 단계당 Langfuse 스팬

## 구축

1. **수집 워커.** 모든 푸시 후크에서 git 기록을 반복한다. 변경된 파일을 수집한다. 각 파일에 대해 tree-sitter로 파싱하고, 전체 소스 스팬과 함께 함수 및 클래스 노드를 추출한다. 청크 레코드 `{repo, path, start_line, end_line, symbol, body}`를 방출한다.

2. **청크 요약.** 프롬프트 캐싱을 사용하여 시스템 프리에amble에서 Haiku 4.5 호출로 배치. 프롬프트: "공용 계약과 부작용을命名하여 이 함수를 한 문장으로 요약한다." 청크 alongside에 요약을 저장한다.

3. **임베딩 풀.** 두 개의 병렬 대기열: 밀도(Voyage-code-3 배치 128) 및 요약(동일 모델, 요약 문자열에서). 페이로드 `{repo, path, start_line, end_line, symbol, kind}`와 함께 Qdrant에 벡터를 작성한다.

4. **BM25 인덱스.** 필드 가중 Tantivy 인덱스: 기호 이름 가중치 4, 기호 본문 가중치 1, 요약 가중치 2. "X라는 이름의 함수를 찾기"와 "X를 수행하는 함수를 찾기" 쿼리를 가능하게 한다.

5. **기호 그래프.** 각 청크에 대해 가장자리 기록: 가져오기(이 파일은 repo Z의 기호 Y를 사용), 호출(이 함수는 클래스 C의 메서드 M을 호출), 상속. kuzu에 저장. 쿼리 시 repo 경계를 가로질러 검색을 확장하는 데 사용된다.

6. **쿼리 에이전트.** 세 개의 노드가 있는 LangGraph. `retrieve`는 밀도 + BM25를 병렬로 실행하고, (repo, path, symbol)로 중복 제거한다. `rerank`는 상위 50개에서 교차 인코더를 실행하고 상위 10개를 유지한다. `synth`는 리랭크된 청크를 컨텍스트로 사용하여 Claude Sonnet 4.7을 호출하고, 시스템 프롬프트를 캐시하고, 파일:줄 인용을 요구한다.

7. **인용 enforcement.** 모델 출력을 파싱한다; (repo/path:start-end) 앵커 없이 클레임은 re-ask로 플래그되거나 삭제된다. 사용자에게 인용된 답변만 반환한다.

8. **증분 재인덱스.** 각 웹훅에서 기호 수준 diff를 계산한다. 텍스트가 변경된 청크만 다시 임베딩한다. 가져오기가 변경된 청크의 기호 가장자리를 다시 계산한다. 측정: 2M-LOC fleet에서 50개 파일 푸시가 60초 미만으로 재인덱싱된다.

9. **평가.** 골 파일:줄 답변과 함께 100개의 크로스repo 질문에 레이블을 지정한다. MRR@10, nDCG@10, 인용 충실도(검증 가능한 앵커가 있는 답변 클레임 비율), p50/p99 지연 시간을 측정한다.

## 사용

```
$ code-rag ask "how is S3 multipart abort wired into our retry budget?"
[retrieve]  12 chunks dense + 7 chunks bm25, 16 unique after dedup
[rerank]    top-5 kept (cohere rerank-3)
[synth]     claude-sonnet-4.7, cache hit rate 68%, 2.1s
answer:
  Multipart aborts are triggered by `AbortMultipartOnFail` in
  services/uploader/retry.go:122-148, which decrements the per-bucket
  retry budget defined in config/budgets.yaml:34-51 ...
  citations: [services/uploader/retry.go:122-148, config/budgets.yaml:34-51,
              libs/s3client/multipart.ts:44-61]
```

## 발송

산출물 skill `outputs/skill-codebase-rag.md`. repo 코퍼스가 주어지면 수집 파이프라인, 하이브리드 인덱스, 쿼리 에이전트를 구축하고 모든 크로스repo 질문에 대한 인용 답변을 반환한다. 기준표:

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 검색 품질 | 100개 질문 홀드아웃 세트에서 MRR@10 및 nDCG@10 |
| 20 | 인용 충실도 | 검증 가능한 파일:줄 앵커가 있는 답변 클레임의 비율 |
| 20 | 지연 시간 및 확장 | 인덱싱된 코퍼스 크기에서 10k QPS의 p95 쿼리 지연 |
| 20 | 증분 인덱싱 정확성 | 50개 파일 커밋에서 git push에서 검색 가능까지의 시간 |
| 15 | UX 및 답변 형식 지정 | 인용 클릭 가능성, 스니펫 미리보기, 후속 작업 어포던스 |
| **100** | | |

## 연습 문제

1. Voyage-code-3를 자체 호스팅 nomic-embed-code로 교환한다. MRR@10 델타를 측정한다. 리랭킹이 활성화되면 격차가 닫히는지 보고한다.

2. 코퍼스에 20% 생성된 코드(LLM이 생성한 상용구)를 주입하고 다시 평가한다. 검색 포이즈닝을 관찰한다. 페이로드에 "generated" 플래그를 추가하고 해당 히트를 down-weight한다.

3. 코퍼스 크기에서 Qdrant 하이브리드 검색 대 pgvector + pgvectorscale을 벤치마킹한다. 배치 크기 1에서 p99를 보고한다.

4. 드리프트 검사를 샘플링 기반으로 추가: 주간, 100개 질문 평가를 다시 실행한다. MRR@10 하락 > 5%에서 경고.

5. 교차 언어 기호 해석으로 확장: gRPC를 통해 Go 서비스를 호출하는 Python 함수. 기호 그래프를 사용하여 이를 연결한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|------------------------|
| AST-aware chunking | "함수 수준 분할" | 고정 토큰 창 대신 tree-sitter 노드 경계에서 코드 절단 |
| Hybrid search | "밀도 + 희소" | BM25와 벡터 검색을 병렬로 실행하고, 상위 k를 병합하고, 리랭크 |
| Cross-encoder rerank | "두 번째 단계 순위" | 각 (쿼리, 후보) 쌍을 함께 점수로 매기는 모델; 코사인보다 더 정확 |
| Prompt caching | "캐시된 시스템 프롬프트" | 2026 Claude/OpenAI 기능으로 반복 접두사 토큰을 최대 90% 할인 |
| Symbol graph | "코드 그래프" | 파일 및 repo 전체에서 가져오기, 호출, 상속에 대한 가장자리 |
| Citation faithfulness | "근거된 답변률" | 사용자가 앵커를 클릭하고 참조된 스팬을 읽어 검증할 수 있는 클레임의 비율 |
| Incremental re-index | "푸시-투-검색 시간" | git push에서 변경된 기호가 쿼리 가능할 때까지의 벽 시계 |

## 추가 자료

- [Sourcegraph Amp](https://ampcode.com) — 프로덕션 크로스repo 코드 인텔리전스
- [Sourcegraph Cody RAG architecture](https://sourcegraph.com/blog/how-cody-understands-your-codebase) — 이 캐피톤에 대한 참조 딥다이브
- [Aider repo-map](https://aider.chat/docs/repomap.html) — tree-sitter 순위 repo 보기
- [Augment Code enterprise graph](https://www.augmentcode.com) — 상용 기호 그래프 RAG
- [Qdrant hybrid search docs](https://qdrant.tech/documentation/concepts/hybrid-queries/) — 참조 구현
- [Voyage AI code embeddings](https://docs.voyageai.com/docs/embeddings) — Voyage-code-3 세부 정보
- [Cohere rerank-3](https://docs.cohere.com/reference/rerank) — 교차 인코더 참조
- [Pinterest MCP internal search](https://medium.com/pinterest-engineering) — 내부 플랫폼 참조