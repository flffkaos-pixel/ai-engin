# 캡스톤 04 — 멀티모달 문서 QA (비전 우선 PDF, 테이블, 차트)

> 2026년 문서 QA 프론티어는 OCR-then-text에서 비전 우선 후기 상호작용으로 이동했다. ColPali, ColQwen2.5, ColQwen3-omni는 각 PDF 페이지를 이미지로 처리하고, 다중 벡터 후기 상호작용으로 임베딩하며, 쿼리가 패치에 직접 attend하게 한다. 금융 10-K, 과학 논문, 필기 노트에서 이 패턴은 OCR-then-text를 큰 격차로 능가한다. 파이프라인을 10k 페이지에서 종단 간 구축하고 OCR-then-text 기준과 나란히 비교한다.

**유형:** 캡스톤
**언어:** Python (파이프라인), TypeScript (뷰어 UI)
**선수 과목:** Phase 4 (컴퓨터 비전), Phase 5 (NLP), Phase 7 (트랜스포머), Phase 11 (LLM 엔지니어링), Phase 12 (멀티모달), Phase 17 (인프라)
**활용 phases:** P4 · P5 · P7 · P11 · P12 · P17
**소요 시간:** 30시간

## 문제

기업들은 OCR 파이프라인이 망가뜨리는 PDF 위에 앉아 있다: 회전된 테이블이 있는 스캔 10-K, 방정식이 가득한 과학 논문, 이미지로만 의미가 있는 차트, 필기 주석. 이를 텍스트 우선으로 취급하면 신호의 절반을 잃는다. 2026년 답변은 원본 페이지 이미지에 대한 후기 상호작용 다중 벡터 검색이다. ColPali(Illuin Tech)가 이를 도입했고; ColQwen2.5-v0.2와 ColQwen3-omni가 정확도를 높였다. ViDoRe v3에서 비전 우선 검색은 OCR-then-text보다 의미 있는 격차로 높은 점수를 받는다 — 그리고 차트, 테이블, 필기에서 격차가 벌어진다.

트레이드오프는 저장 공간과 지연 시간이다. ColQwen 임베딩은 페이지당 ~2048 패치 벡터이며, 단일 1024차원 벡터가 아니다. 원본 저장 공간이 급등한다. DocPruner(2026)가 측정 가능한 정확도 손실 없이 50% 프루닝을 가져온다. 10k 페이지를 인덱싱하고, ViDoRe v3 nDCG@5를 측정하며, 2초 이내에 답변을 제공할 것이며, OCR-then-text 기준과 직접 비교할 것이다.

## 개념

후기 상호작용은 모든 쿼리 토큰이 모든 패치 토큰에 대해 점수를 매기고, 쿼리 토큰당 최대 점수가 합산됨을 의미한다. 단일 풀링된 벡터 없이 세밀한 매칭을 얻는다. 다중 벡터 인덱스(Vespa, Qdrant multi-vector, AstraDB)가 패치별 임베딩을 저장하고 검색 시 MaxSim을 실행한다.

응답자는 쿼리 plus top-k 검색된 페이지를 이미지로 취하는 비전-언어 모델이며, 증거 영역(바운딩 박스 또는 페이지 참조)과 함께 답변을 작성한다. Qwen3-VL-30B, Gemini 2.5 Pro, InternVL3이 2026년 프론티어 선택이다. 방정식 및 과학 표기법의 경우 OCR 폴백(Nougat, dots.ocr)이 선택적 텍스트 채널로 연결된다.

평가는 이차원 행렬이다. 하나의 축: 콘텐츠 유형(일반 텍스트 단락, 밀집 테이블, 막대/선 차트, 필기 노트, 방정식). 다른 축: 검색 접근 방식(비전 우선 후기 상호작용 vs OCR-then-text vs 하이브리드). 각 셀에 nDCG@5와 답변 정확도가 붙는다. 보고서가 결과물이다.

## 아키텍처

```
PDFs -> page renderer (PyMuPDF, 180 DPI)
           |
           v
  ColQwen2.5-v0.2 embed (multi-vector per page, ~2048 patches)
           |
           +------> DocPruner 50% compression
           |
           v
   multi-vector index (Vespa or Qdrant multi-vector)
           |
 query ----+----> retrieve top-k pages (MaxSim)
           |
           v
  VLM answerer: Qwen3-VL-30B | Gemini 2.5 Pro | InternVL3
    inputs: query + top-k page images + optional OCR text
           |
           v
  answer with cited page numbers + evidence regions
           |
           v
  Streamlit / Next.js viewer: highlighted boxes on source page
```

## 기술 스택

- 페이지 렌더링: PyMuPDF (fitz) 180 DPI, portrait-normalized
- 후기 상호작용 모델: ColQwen2.5-v0.2 또는 ColQwen3-omni (Hugging Face의 vidore 팀)
- 인덱스: 다중 벡터 필드가 있는 Vespa, 또는 Qdrant multi-vector, 또는 MaxSim이 있는 AstraDB
- 프루닝: DocPruner 2026 정책 (고분산 패치 유지, < 0.5% 정확도 손실로 50% 압축)
- OCR 폴백 (방정식/밀집 테이블): dots.ocr 또는 Nougat
- VLM 응답자: Qwen3-VL-30B 셀프 호스트 또는 Gemini 2.5 Pro 호스티드; InternVL3을 폴백으로
- 평가: ViDoRe v3 벤치마크, 다중 페이지 추론을 위한 M3DocVQA
- 뷰어 UI: 증거 영역에 대한 canvas 오버레이가 있는 Next.js 15

## 실습

1. **수집.** 10-K, 과학 논문, 스캔 문서를 포함한 10k PDF 페이지 코퍼스를 inúmer다. 각 페이지를 1536x2048 PNG로 렌더링한다. `{doc_id, page_num, image_path}`를 유지한다.

2. **임베딩.** 각 페이지 이미지에서 ColQwen2.5-v0.2를 실행한다. 출력 형태 ~2048 패치 임베딩, 차원 128. DocPruner를 적용하여 최고 신호의 절반을 유지한다. Vespa 다중 벡터 필드 또는 Qdrant multi-vector에 기록한다.

3. **쿼리.** 각 수신 쿼리에 대해 쿼리 타워로 임베딩(토큰 수준 임베딩). 인덱스에 대해 MaxSim 실행: 모든 쿼리 토큰에 대해 페이지 패치 임베딩에 대한 최대 내적을 취하고, 합산한다. top-k 페이지를 반환한다.

4. **종합.** 쿼리와 top-5 페이지 이미지로 Qwen3-VL-30B를 호출한다. 프롬프트: "제공된 페이지만 사용하여 답변. 각 주장을 (doc_id, page)로 인용하고 영역 이름을 지정(figure, table, paragraph)."

5. **증거 영역.** 인용된 영역을 추출하기 위해 답변을 후처리한다. VLM이 바운딩 박스를发出하면(Qwen3-VL이 함), 뷰어에서 오버레이로 렌더링한다.

6. **OCR 폴백.** 방정식이 밀집된 페이지(이미지 분산에 대한 휴리스틱으로 식별)에 대해 Nougat 또는 dots.ocr을 실행하고 이미지와 함께 추가 채널로 OCR 텍스트를 전달한다.

7. **평가.** ViDoRe v3(검색 nDCG@5)와 M3DocVQA(다중 페이지 QA 정확도)를 실행한다. 동일한 코퍼스에서 동일한 합성기로 OCR-then-text 파이프라인도 실행한다. 콘텐츠 유형 × 접근 방식 행렬을 생성한다.

8. **UI.** 먼저 Streamlit 프로토타입; 증거 영역 오버레이가 있는 페이지별 Next.js 15 운영 뷰어.

## 활용

```
$ doc-qa ask "what was the 2024 operating margin change for segment EMEA?"
[retrieve]   top-5 pages in 320ms (ColQwen2.5, MaxSim, Vespa)
[synth]      qwen3-vl-30b, 1.4s, cited (form-10k-2024, p. 88) + (..., p. 92)
answer:
  EMEA operating margin moved from 18.2% to 16.8%, a 140bp decline.
  cited: 10-K-2024.pdf p.88 (Table 4, Segment Operating Margin)
         10-K-2024.pdf p.92 (MD&A, Operating Performance)
[viewer]     open with highlighted bounding boxes overlaid on p.88 Table 4
```

## 결과물

`outputs/skill-doc-qa.md`가 결과물을 설명한다: ViDoRe v3에서 OCR-then-text 기준과 비교하여 특정 코퍼스에 맞게 조정된 비전 우선 멀티모달 문서 QA 시스템.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | ViDoRe v3 / M3DocVQA 정확도 | OCR-text 기준 및 게시된 리더보드 대비 벤치마크 수치 |
| 20 | 증거 영역 grounding | 답변 범위를 실제로 포함하는 인용 영역 비율 |
| 20 | 저장 및 지연 엔지니어링 | DocPruner 압축 비율, 인덱스 p95, 답변 p95 |
| 20 | 다중 페이지 추론 | 손으로 레이블이 지정된 100개 질문 세트에서 정확도 |
| 15 | 소스 검사 UX | 뷰어 명확성, 오버레이 충실도, 나란히 비교 도구 |
| **100** | | |

## 연습 문제

1. 동일한 코퍼스에서 ColQwen2.5-v0.2 대 ColQwen3-omni를 측정한다. 하나가 올바르고 다른 하나가 놓치는 페이지는? 인덱스에 "콘텐츠 클래스" 태그를 추가하여 유형별로 라우팅한다.

2. 임베딩을 공격적으로 프루닝한다(75%, 90%). 압축 절벽을 찾는다: ViDoRe nDCG@5가 OCR 기준 이하로 떨어지는 지점.

3. 하이브리드를 구축한다: OCR-then-text와 ColQwen을 병렬로 실행하고 RRF로 융합하고 교차 인코더로 리랭크한다. 하이브리드가 개별적으로보다 나은가? 어디서 가장 도움이 되는가?

4. Qwen3-VL-30B를 더 작은 VLM(Qwen2.5-VL-7B)으로 교체한다. 정확도-당비曲线를 측정한다.

5. 필기 노트 지원을 추가한다. 필기 코퍼스를 렌더링하고 ColQwen으로 임베딩하며 검색을 측정한다. 필기 OCR 파이프라인과 비교한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 후기 상호작용 | "ColPali-style retrieval" | 쿼리 토큰이 페이지 패치에 독립적으로 점수를 매김; MaxSim이 집계 |
| 다중 벡터 | "Per-patch embedding" | 각 문서에 많은 벡터가 있음, 하나의 풀링된 벡터가 아님 |
| MaxSim | "Late-interaction scoring" | 모든 쿼리 토큰에 대해 문서 벡터에 대한 최대 유사도를 취하고 합산 |
| DocPruner | "Patch compression" | 2026 프루닝 — 측정 가능한 정확도 손실 없이 50%의 패치를 유지 |
| ViDoRe v3 | "Document-retrieval benchmark" | 시각적 문서 검색 측정을 위한 2026년 표준 |
| 증거 영역 | "Cited bounding box" | 소스 페이지에서 답변 범위를 지역화하는 bbox |
| OCR 폴백 | "Equation channel" | 방정식 또는 테이블이 많은 페이지에서 비전 alongside 사용되는 텍스트 파이프라인 |

## 추가 자료

- [ColPali (Illuin Tech) repository](https://github.com/illuin-tech/colpali) — 기준 후기 상호작용 문서 검색
- [ColPali paper (arXiv:2407.01449)](https://arxiv.org/abs/2407.01449) — 기초 방법 논문
- [ColQwen family on Hugging Face](https://huggingface.co/vidore) — 운영 готов 체크포인트
- [M3DocRAG (Adobe)](https://arxiv.org/abs/2411.04952) — 다중 페이지 멀티모달 RAG 기준
- [Vespa multi-vector tutorial](https://docs.vespa.ai/en/colpali.html) — 기준 서빙 스택
- [Qdrant multi-vector support](https://qdrant.tech/documentation/concepts/vectors/#multivectors) — 대체 인덱스
- [AstraDB multi-vector](https://docs.datastax.com/en/astra-db-serverless/databases/vector-search.html) — 대체 관리 인덱스
- [Nougat OCR](https://github.com/facebookresearch/nougat) — 방정식 가능한 OCR 폴백