# 캡스톤 05 — 자율 연구 에이전트 (AI-Scientist 클래스)

> Sakana의 AI-Scientist-v2가 완전한 논문을 게시했다. Agent Laboratory가 실험을 실행했다. Allen AI가 traces를 공유했다. 2026년 형태는 실험 트리에 대한 계획-실행-검증 트리 검색, 예산화된 비용, 샌드박스된 코드 실행, 비전 피드백 LaTeX 작성기, 자동화된 NeurIPS 스타일 검토자 앙상블이다. 캡스톤은 $30 이내에 종단 간 논문을 작성하고 Sakana가 문서화한 샌드박스 탈출 레드 팀을 생존하는 것이다.

**유형:** 캡스톤
**언어:** Python (에이전트 + 샌드박스), LaTeX (출력)
**선수 과목:** Phase 2 (ML), Phase 3 (딥러닝), Phase 7 (트랜스포머), Phase 10 ( scratch에서 LLM), Phase 14 (에이전트), Phase 15 (자율), Phase 16 (다중 에이전트), Phase 18 (안전)
**활용 phases:** P0 · P2 · P3 · P7 · P10 · P14 · P15 · P16 · P18
**소요 시간:** 40시간

## 문제

자율 연구 에이전트는 2026년에 한계를 넘었다. Sakana AI의 AI-Scientist-v2는 워크숍 동료 검토를クリア한 생성된 논문과 함께 Nature에 게시되었다. ShinkaEvolve(ICLR 2026)는 진화 가설로 확장을 이어갔다. AMD의 Agent Laboratory는 재현 가능한 traces를 shipped했다. 에이전트는 마법이 아니다 — 그들은 비용 상한, 시드 바운드 샌드박스, 자동화된 검토가 있는 실험 후보 트리에서 실행되는 계획-실행-검증 루프이다. crafts는 루프, 예산, 안전 스토리에 있다.

 Narrow 도메인(예: 100M 파라미터 트랜스포머의 attention-sparsity ablation)에서 시드 아이디어에 대해 하나를 구현함으로써 루프를 배운다. 가치는 첫 실행에서 새로운 것을 발견하는 데 있지 않다. 가치는 인프라에 있다: 트리 검색, 실험 샌드박스, 작성기-검토자 루프, 레드 팀 보고서. Sakana 팀은 샌드박스 탈출 실패를 문서화했다; 당신의 에이전트는 동일한 레드 팀을 통과해야 한다.

## 개념

에이전트는 최선 우선 트리 검색이다. 노드는 실험 사양이다: (가설, 구성, 코드, 예상 결과). 확장 단계는 작은 편집(옵티마이저 교체, 배치 크기 이동, 구성 요소 ablation)으로 하위를 제안한다. 각 하위는 하드 리소스 상한이 있는 새 샌드박스에서 실행된다. 결과는 (novelty × quality × 남은 예산)로 노드를 순위 매기는 채점 함수로フィードバック된다. 예산이 소진될 때까지 트리가 성장하고, 그 다음 최고 분기가 작성된다.

작성기는 멀티모달이다. LaTeX 초안을 생성하고, 컴파일하고, 그림을 렌더링하고, 렌더링된 PDF를 Claude Opus 4.7의 비전 모드로フィードバック하여 레이아웃, 그림 가독성, 주张-証拠 정렬에 대한 비판을 받는다. 5명의 LLM 심사위원의 검토자 앙상블이 NeurIPS 스타일 점수(novelty, rigor, clarity, reproducibility, impact)를发放한다; 평균이 임계값 미만이면 논문이 비평과 함께 작성기에 반환된다.

안전은 구조적으로 필요하다. 모든 실험은 네트워크 출구 없음, 경계 wall-clock, 고정된 리소스 제한이 있는 E2B 또는 Daytona 샌드박스에서 실행된다. 에이전트의 코드 생성 단계는 샌드박스를 탈출하는 syscall을 차단하는 정책 레이어를 통과한다. 레드 팀 보고서는 Sakana가 문서화한 공격 표면(fork bombs, 파일시스템 탈출, LLM이 작성한 네트워크 호출)을 재현한다.

## 아키텍처

```
seed idea + domain
      |
      v
  literature search (Semantic Scholar + OpenAlex + FAISS cache)
      |
      v
  LangGraph plan-execute-verify tree
      |
      v
  +--- expand node ----+      per-node sandbox
  |                    |      (E2B / Daytona)
  v                    v      resource caps
  child_1           child_k   no network egress
  |                    |      deterministic seeds
  v                    v
  run experiment       run experiment
  |                    |
  v                    v
  score nodes by (novelty, quality, budget)
      |
      v
  best branch -> LaTeX writer
      |
      v
  compile + vision critique (Opus 4.7 vision)
      |
      v
  reviewer ensemble (5 LLM judges, NeurIPS rubric)
      |
      v
  paper.pdf + review.md + trace.json
```

## 기술 스택

- 오케스트레이션: 체크포인팅과 인간 승인 게이트가 있는 LangGraph
- 트리 검색: Sakana v2의 AB-MCTS 스타일 실험 노드 대한 커스텀 최선 우선
- 샌드박스: 실험당 E2B, Docker-in-Docker 폴백; cgroups를 통한 리소스 캡
- 문헌: Semantic Scholar Graph API + OpenAlex + 초록의 로컬 FAISS 캐시
- 작성기: LaTeX 템플릿 + 그림 비판 및 레이아웃을 위한 Claude Opus 4.7 (비전 모드)
- 검토자: 5명의 심사위원 앙상블(Opus 4.7, GPT-5.4, Gemini 3 Pro, DeepSeek R1, Qwen3-Max), 가중치 집계
- 실험 프레임워크: 물리적 실험을 위한 PyTorch 2.5, 로깅을 위한 W&B
- 관찰가능성: 에이전트 traces를 위한 Langfuse, 논문당 $30 하드 예산

## 실습

1. **시드 및 도메인 범위 지정.** 시드 아이디어를 가져온다(예: "하위 1B 트랜스포머의 attention map에서 sparsity 패턴 조사"). 검색 공간 정의: 모델, 데이터셋, 컴퓨트 예산.

2. **문헌 패스.** Semantic Scholar + OpenAlex에서 50개의 가장 많이 인용된 관련 논문을 쿼리; 초록을 로컬로 캐시; 1페이지 도메인 다이제스트 생성.

3. **트리 발판.** 시드 가설로 루트를 초기화. 작은 편집 제안(하위당 하나의 구성 변경)이 있는 `expand(node) -> children`을 구현. 가중치 novelty × quality × budget 항으로 `score(node)`를 구현.

4. **샌드박스 래핑.** 모든 실험이 `docker run --network=none --memory=8g --cpus=2 --pids-limit=256 --read-only` (또는 동등한 E2B 정책)로 실행된다. 시드가 샌드박스에 기록된다; 출력은 읽기 전용으로 다시 마운트된다.

5. **계획-실행-검증 루프.** `plan`이 하위를 제안한다. `execute`가 샌드박스를 실행하고 로그와 메트릭을 캡처한다. `verify`가 메트릭에 대한 단위 검사를 실행한다(손실이 감소했는가? ablation이 효과를 분리했는가?). 실패한 노드는 트리에 실패 이유가 저장된다.

6. **작성기.** 예산 후 최고 분기를 선택. matplotlib로 그림을 렌더링. 분기 추적이 컨텍스트에 있는 Claude Opus 4.7으로 LaTeX 초안을 생성. 컴파일. 컴파일된 PDF를 Opus 4.7 비전으로feedback하여 비판을 받는다. 반복.

7. **검토자 앙상블.** 5명의 심판이 NeurIPS 스타일 루브릭으로 초안에 대해 (novelty, rigor, clarity, reproducibility, impact) 점수를 매긴다. 평균 < 4.0/5이면 비평과 함께 작성기에 반환. 3번의 재작성 후 하드 스톱.

8. **레드 팀.** 샌드박스를 겨냥하는 적대적 작업 세트를 구축하거나 통합: fork bombs, 네트워크 유출 시도, 파일시스템 탈출, LLM이 작성한 셸 메타문자. 모두 차단됨을 확인. 발견 사항을 문서화.

9. **재현성.** 모든 논문은 트리 검색 추적 JSON, 시드, W&B 실행 링크, 샌드박스 구성, 종단 간 재현하는 README와 함께 제공된다.

## 활용

```
$ ai-scientist run --seed "attention sparsity in sub-1B transformers" --budget 30
[lit]    50 papers, digest in 12s
[tree]   expanded 8 nodes, budget 12/30
[exec]   node #3 sparsity=top-8, loss=2.83 (best so far)
[exec]   node #6 sparsity=top-4, loss=3.12 (worse)
[exec]   ...
[tree]   chose branch rooted at node #3 (novelty 0.62, quality 0.81)
[write]  LaTeX draft v1 complete
[vision] critique: figure 2 legend too small, claim-evidence ok
[write]  draft v2 after 3 edits
[review] mean 4.2/5 (novelty 3.9, rigor 4.3, clarity 4.1, repro 4.5, impact 4.2)
[done]   paper.pdf + review.md + trace.json     $28.40 spent
```

## 결과물

`outputs/skill-ai-scientist.md`가 결과물이다. 시드 아이디어 + 도메인 + $30 예산이 주어지면 전체 파이프라인을 실행하고 검토 가능한 논문과 재현성 번들을 emit한다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 논문 품질 | 게시된 워크숍 논문에 대한 블라인드 루브릭 검토 |
| 20 | 실험 엄격성 | 기준선, 시드, ablation; 모든 주장이 결과 테이블의 셀에 의해 백업됨 |
| 20 | 비용 및 컴퓨트 훈련 | $30/논문 상한 적용, Langfuse 추적됨 |
| 20 | 안전성 | 샌드박스 레드 팀 통과; 네트워크 정책 및 킬 스위치 확인됨 |
| 15 | 재현성 | 동일한 시드로 원클릭 재실행이 논문을 재현함 |
| **100** | | |

## 연습 문제

1. 동일한 도메인에서 세 가지 다른 시드 아이디어에 대해 파이프라인을 실행한다. 트리 검색이 重複하는 부분을 비교한다. 낭비된 컴퓨트를 식별한다.

2. $5 이상으로 추정되는 노드의 실험 실행 전에 인간-@-루프 게이트를 추가한다. 총 비용이 얼마나 떨어지는지 측정한다.

3. 검토자 앤상블을 단일 심판으로 교체한다. 알려진 잘못된 논문 보류 세트에서 false-accept 비율을 측정한다.

4. 네트워크 유출 레드 팀 테스트를 도입한다: 에이전트가 외부 주소로 `curl`하려는 코드를 작성한다. `--network=none` 정책이 차단하는지 확인한다. 시도를 로그한다.

5. 플랫 랜덤 기준선(동일한 예산, 확장 전략 없음)과 트리 검색을 비교한다. novelty × quality 이점을 보고한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 트리 검색 | "AB-MCTS-style expansion" | novelty×quality×budget 점수로 실험 노드에 대한 최선 우선 탐색 |
| 샌드박스 | "Experiment isolation" | 네트워크 없음, 경계 CPU/메모리, 고정된 시드, 읽기 전용 입력이 있는 컨테이너 |
| 비전 비판 | "Render-then-read" | 논문을 PDF로 컴파일하고, PDF를 VLM에反馈하여 레이아웃 및 주张-証拠 비판을 받음 |
| 검토자 앙상블 | "Automated peer review" | NeurIPS 루브릭으로 논문을 점수 매기는 다중 LLM 심판; 파이프라인을 게이트하는 가중치 집계 |
| Novelty 점수 | "Is this new?" | 50개 논문 문헌 캐시에 대한 근접도에 따라 페널티를 부여하는 휴리스틱 |
| 비용 상한 | "$ budget" | 논문당 총 지출에 대한 하드 캡; Langfuse 카운터 + 사전 실행 추정치 |
| 레드 팀 | "Sandbox-escape audit" | 정책이 잘못되면 샌드박스를 탈출할 적대적 작업 |

## 추가 자료

- [Sakana AI-Scientist-v2 repository](https://github.com/SakanaAI/AI-Scientist-v2) — 기준 운영 연구 에이전트
- [Sakana AI-Scientist-v1 paper (arXiv:2408.06292)](https://arxiv.org/abs/2408.06292) — 원래 방법론
- [ShinkaEvolve (Sakana ICLR 2026)](https://sakana.ai) — 진화적 확장
- [Agent Laboratory (AMD)](https://github.com/SamuelSchmidgall/AgentLaboratory) — 다중 역할 연구실 프레임워크
- [LangGraph documentation](https://langchain-ai.github.io/langgraph/) — 기준 오케스트레이션 레이어
- [Semantic Scholar Graph API](https://api.semanticscholar.org/) — 문헌 검색
- [E2B sandboxes](https://e2b.dev) — 기준 실험 격리
- [NeurIPS reviewer guidelines](https://neurips.cc/Conferences/2026/Reviewer-Guidelines) — 검토자 앙상블이 인코딩하는 루브릭