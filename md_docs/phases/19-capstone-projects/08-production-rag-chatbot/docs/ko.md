# 캡스톤 08 — 규제된 도메인용 운영 RAG 챗봇

> Harvey, Glean, Mendable, LlamaCloud는 모두 2026년에 동일한 운영 형태를 실행한다. docling 또는 Unstructured 및 ColPali로 시각적 요소 ingestion. 하이브리드 검색. bge-reranker-v2-gemma로 리랭크. 프롬프트 캐싱(60-80% 히트율)으로 Claude Sonnet 4.7로 합성. Llama Guard 4 및 NeMo Guardrails로 가드. Langfuse 및 Phoenix로 감시. 200개 질문 황금 세트에서 RAGAS로 평가. 규제된 도메인(법률, 임상, 보험)에서 하나를 구축하면, 캡스톤은 황금 세트, 레드 팀, 드리프트 대시보드를 통과하는 것이다.

**유형:** 캡스톤
**언어:** Python (파이프라인 + API), TypeScript (채팅 UI)
**선수 과목:** Phase 5 (NLP), Phase 7 (트랜스포머), Phase 11 (LLM 엔지니어링), Phase 12 (멀티모달), Phase 17 (인프라), Phase 18 (안전)
**활용 phases:** P5 · P7 · P11 · P12 · P17 · P18
**소요 시간:** 30시간

## 문제

규제된 도메인 RAG(법률 계약, 임상 시험 프로토콜, 보험 정책)는 ROI가 명확하고 위험이 구체적이기 때문에 2026년에 가장 많이 shipped되는 운영 형태이다. Harvey(Allen & Overy)가 법적용으로 구축했다. Mendable은 개발자-docs 버전을 shipped한다. Glean은 기업 검색을 커버한다. 패턴은: 충실한 ingestion, 리랭크로 하이브리드 검색, 인용 강제 및 프롬프트 캐싱으로 합성, 다중 안전 레이어로 가드, 지속적인 드리프트 모니터링이다.

어려운 부분은 모델이 아니다. 관할권 인식 컴플라이언스(HIPAA, GDPR, SOC2), 인용 수준 감사 가능성, 비용 관리(프롬프트 캐싱은 히트율이 높을 때 60-90% 할인을 제공), RAGAS 통한 환각 감지, 소스 문서가 업데이트되었지만 인덱스가追赶하지 못할 때 드리프트 감지이다. 이 캡스톤은 200개 질문 황금 세트와 레드 팀 모음과 함께 모든 것을 shipped할 것을 要求한다.

## 개념

파이프라인에는 두 가지 면이 있다. **Ingestion**: docling 또는 Unstructured가 구조화된 문서를解析하고; ColPali가 시각적으로 풍부한 문서를 처리; 청크에 요약, 태그, 역할 기반 접근 레이블이 첨부된다. 벡터는 pgvector + pgvectorscale(50M 벡터 미만) 또는 Qdrant Cloud로 이동; sparse BM25가 함께 실행된다. **대화**: LangGraph가 메모리 및 다중 턴을 처리; 각 쿼리가 하이브리드 검색을 실행하고, bge-reranker-v2-gemma-2b로 리랭크하며, (프롬프트 캐시된) Claude Sonnet 4.7로 합성하고, Llama Guard 4 및 NeMo Guardrails를 통과하며, 인용이 첨부된 응답을 emit한다.

평가 스택에는 네 가지 레이어가 있다. **황금 세트**(인용과 함께 레이블이 지정된 200개의 Q/A)는 정확도를 위해. **레드 팀**(	jailbreaks, PII 추출 시도, 도메인 외 질문)은 안전을 위해. **RAGAS**는 매 턴마다 충실도/답변 관련성/컨텍스트 정밀도를 위해. **드리프트 대시보드**(Arize Phoenix)는 매주 검색 품질 및 환각 점수를監視한다.

프롬프트 캐싱은 비용 레버이다. Claude 4.5+ 및 GPT-5+는 시스템 프롬프트 + 검색된 컨텍스트 캐싱을 지원한다. 60-80% 히트율에서 쿼리당 비용이 3-5배 감소한다. 파이프라인은 높은 캐시 히트율을 달성하기 위해 안정적인 접두사(시스템 프롬프트 + 리랭크된 컨텍스트 먼저)를 위해 설계되어야 한다.

## 아키텍처

```
documents (contracts, protocols, policies)
      |
      v
docling / Unstructured parse + ColPali for visuals
      |
      v
chunks + summaries + role-labels + jurisdiction tags
      |
      v
pgvector + pgvectorscale  +  BM25 (Tantivy)
      |
query + role + jurisdiction
      |
      v
LangGraph conversational agent
   +--- retrieve (hybrid)
   +--- filter by role + jurisdiction
   +--- rerank (bge-reranker-v2-gemma-2b or Voyage rerank-2)
   +--- synthesize (Claude Sonnet 4.7, prompt cached)
   +--- guard (Llama Guard 4 + NeMo Guardrails + Presidio output PII scrub)
   +--- cite + return
      |
      v
eval:
  RAGAS faithfulness / answer_relevance / context_precision (online)
  Langfuse annotation queue (sampled)
  Arize Phoenix drift (weekly)
  red team suite (pre-release)
```

## 기술 스택

- Ingestion: 구조화된 문서를 위한 Unstructured.io 또는 docling; 시각적으로 풍부한 PDF를 위한 ColPali
- Vector DB: 50M 벡터 미만은 pgvector + pgvectorscale; 그 외는 Qdrant Cloud
- Sparse: 필드 가중치가 있는 Tantivy BM25
- 오케스트레이션: Ingestion용 LlamaIndex Workflows + 대화를 위한 LangGraph
- 리랭커: 셀프 호스트된 bge-reranker-v2-gemma-2b 또는 호스티드 Voyage rerank-2
- LLM: 프롬프트 캐싱이 있는 Claude Sonnet 4.7; 폴백으로 셀프 호스트된 Llama 3.3 70B
- Eval: 온라인 RAGAS 0.2, 환각 및 jailbreak 모음을 위한 DeepEval
- 관찰가능성: 주석 대기열이 있는 셀프 호스트 Langfuse; 드리프트용 Arize Phoenix
- 가드레일: 입력/출력 분류기인 Llama Guard 4, NeMo Guardrails v0.12 정책, Presidio PII 스크럽
- 컴플라이언스: 청크에 역할 기반 접근 레이블; GDPR/HIPAA용 관할권 태그

## 실습

1. **Ingestion.** Unstructured 또는 docling으로 코퍼스(진지한 구축을 위해 1000-10000개 문서)를解析한다. 스캔/시각적Heavy 페이지의 경우 ColPali로 라우팅한다. 요약, 역할-레이블, 관할권 태그가 포함된 청크를 생성한다.

2. **인덱스.** Dense 임베딩(Voyage-3 또는 Nomic-embed-v2)을 pgvector + pgvectorscale에 저장. Tantivy를 통한 BM25 사이드 인덱스. 역할 및 관할권 필터를 페이로드로.

3. **하이브리드 검색.** 역할+관할권으로 먼저 필터링; 그런 다음 병렬 dense + BM25; 상반 순위 융합으로 병합; top-20을 리랭커에; top-5를 합성기에.

4. **프롬프트 캐싱으로 합성.** 시스템 프롬프트 + 정적 정책이 캐시 헤더에; 리랭크된 컨텍스트를 캐시 확장으로; 사용자 질문은 캐시되지 않은 접미사로. 정상 상태에서 60-80% 캐시 히트율 목표.

5. **가드레일.** 입력에서 Llama Guard 4; NeMo Guardrails rails가 도메인 외 질문 또는 정책 금지 주제를 차단; Presidio가 출력에서 우발적 PII를 스크럽; 인용 강제 포스트-필터.

6. **황금 세트.** 도메인 전문가가 (답변, 인용)와 함께 레이블을 지정한 200개의 Q/A 쌍. 정확한 인용 일치, 답변 정확도, 충실도(RAGAS)에서 에이전트를 채점.

7. **레드 팀.** 50개의 적대적 프롬프트: jailbreaks (PAIR, TAP), PII 침투 시도, 도메인 외, 교차 관할권 유출. pass/fail 및 심각도로 채점.

8. **드리프트 대시보드.** Arize Phoenix가 매주 검색 품질(nDCG, 인용 충실도)을 추적. 5% 하락 시 경고.

9. **비용 보고서.** Langfuse: 프롬프트 캐싱 히트율, 쿼리당 토큰, 단계별 $/쿼리 분류.

## 활용

```
$ chat --role=analyst --jurisdiction=GDPR
> what is the data-retention obligation for EU user profiles under our contract?
[retrieve]  hybrid top-20 filtered to GDPR + analyst-role
[rerank]    top-5 kept
[synth]     claude-sonnet-4.7, cache hit 74%, 0.8s
answer:
  The contract (Section 12.4, Master Services Agreement dated 2024-03-11)
  obligates EU user profile deletion within 30 days of termination per GDPR
  Article 17. The DPA amendment (DPA-v2.1, Section 5) extends this to 14 days
  for "restricted" category data.
  citations: [MSA-2024-03-11 s12.4, DPA-v2.1 s5]
```

## 결과물

`outputs/skill-production-rag.md`가 결과물을 설명한다. 컴플라이언스 레이블이 첨부되고, 루브릭을 통과하며, 라이브 드리프트 모니터링으로 관찰되는 규제 도메인 챗봇.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | RAGAS 충실도 + 답변 관련성 | 황금 세트(200 Q/A)에서 온라인 점수 |
| 20 | 인용 정확도 | 검증 가능한 소스 앵커가 있는 답변 비율 |
| 20 | 가드레일 적용 범위 | Llama Guard 4 통과율 + jailbreak 모음 결과 |
| 20 | 비용/지연 엔지니어링 | 프롬프트 캐시 히트율, p95 지연, $/쿼리 |
| 15 | 드리프트 모니터링 대시보드 | 매주 검색 품질 추세가 있는 Phoenix 라이브 대시보드 |
| **100** | | |

## 연습 문제

1. 다른 관할권(예: GDPR alongside HIPAA)을 가진 두 번째 코퍼스 슬라이스를 구축한다. 20개 질문 교차 관할권 프로브에서 역할+관할권 필터링이 교차 유출을 방지하는 것을演示한다.

2. 일주일의 운영 트래픽에서 프롬프트 캐시 히트율을 측정한다. 캐시 접두사를 깨는 쿼리를 식별한다. 재구성한다.

3. 10k 토큰 요약 버퍼로 다중 턴 메모리를 추가한다. 대화가 길어질수록 충실도가 떨어지는지 측정한다.

4. Claude Sonnet 4.7을 셀프 호스트된 Llama 3.3 70B로 교체한다. $/쿼리 및 충실도 delta를 측정한다.

5. "불확실" 모드를 추가한다: 상위 리랭크 점수가 임계값 미만이면 에이전트가 "확신 있는 인용이 없습니다"라고 답 대신 말한다. 거짓 확신 감소를 측정한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 프롬프트 캐싱 | "Cached system + context" | Claude/OpenAI 기능: 캐시된 접두사 토큰이 히트 시 60-90% 할인 |
| RAGAS | "RAG evaluator" | 충실도, 답변 관련성, 컨텍스트 정밀도의 자동 점수 매기기 |
| 황금 세트 | "Labeled eval" | 인용과 함께 전문가가 레이블을 지정한 200+ Q/A; ground truth |
| 관할권 태그 | "Compliance label" | GDPR/HIPAA/SOC2 범위가 청크에 첨부; 검색 필터로 적용됨 |
| 인용 충실도 | "Grounded answer rate" | 검색 가능한 소스 스팬에 의해 백업된 주장의 비율 |
| 드리프트 | "Retrieval quality decay" | nDCG 또는 인용 점수의 주간 변경; 5% 경고 임계값 |
| 레드 팀 | "Adversarial eval" | 사전 배포 jailbreak, PII 추출, 도메인 외 프로브 |

## 추가 자료

- [Harvey AI](https://www.harvey.ai) — 기준 법률 운영 스택
- [Glean enterprise search](https://www.glean.com) — 기업 규모 기준 RAG
- [Mendable documentation](https://mendable.ai) — 개발자-docs RAG 기준
- [LlamaCloud Parse + Index](https://docs.llamaindex.ai/en/stable/examples/llama_cloud/llama_parse/) — 관리 ingestion
- [Anthropic prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — 비용 레버 기준
- [RAGAS 0.2 documentation](https://docs.ragas.io/) — 표준 RAG 평가 프레임워크
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) — 기준 드리프트 관찰 가능성
- [Llama Guard 4](https://ai.meta.com/research/publications/llama-guard-4/) — 2026년 안전 분류기
- [NeMo Guardrails v0.12](https://docs.nvidia.com/nemo-guardrails/) — 정책 레일 프레임워크