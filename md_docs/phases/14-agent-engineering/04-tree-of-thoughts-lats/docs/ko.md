# Tree of Thoughts와 LATS: 의도적 검색

> 단일 chain-of-thought 궤적은 되돌아갈 여지가 없다. ToT (Yao et al., 2023)는 추론을 각 노드에 자체 평가가 있는 트리로 만든다. LATS (Zhou et al., 2024)는 Monte Carlo Tree Search 아래 ToT, ReAct, Reflexion을 통합한다. Game of 24가 4% (CoT)에서 74% (ToT)로 향상되고, LATS는 HumanEval에서 92.7% pass@1을 달성한다.

**Type:** Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 03 (Reflexion)
**Time:** ~75분

## 학습 목표

- 추론을 검색으로 프레이밍: 노드는 "생각", 엣지는 "확장", 값은 "얼마나 유망한가".
- 자체 평가 점수를 사용하여 stdlib ToT 스타일 BFS 트리 검색을 구현한다.
- Select / Expand / Simulate / Backpropagate를 사용하여 장난감 LATS MCTS 루프로 확장한다.
- 검색이 토큰 승수를 지불할 가치가 있는 경우(Game of 24, 코드 생성)와 단일 궤적으로 충분한 경우(간단한 Q&A)를 결정한다.

## 문제

Chain-of-thought는 선형 보행이다. 첫 번째 단계가 틀리면 모든 후속 단계가 잘못된 전제에서 작업한다. Game of 24(네 자리 숫자로 + − × ÷를 사용하여 24 만들기)에서 GPT-4 CoT는 4% 정확도를 기록한다. 모델이 초기에 잘못된 하위 표현식을 선택하고 회복할 수 없다.

추론에 필요한 것은 여러 후보를 제안하고, 평가하고, 유망한 것을 선택하며, 막다른 골목에서 되돌아갈 수 있는 능력이다. 그것이 검색이다. Tree of Thoughts와 LATS는 두 가지 표준 공식이다.

## 개념

### Tree of Thoughts (Yao et al., NeurIPS 2023)

각 노드는 일관된 중간 단계("생각")다. 각 노드는 K개의 자식 생각으로 확장될 수 있다. LLM은 점수 프롬프트로 각 노드를 자체 평가한다. 검색은 트리(BFS, DFS 또는 빔)를 탐색한다.

```
                     (root: "find 24 from 4 6 4 1")
                    /               |            \
           ("6 - 4 = 2")    ("4 + 1 = 5")    ("4 * 6 = 24")  <- Score: HIGH
              /   \              |                  |
          ...    ...          ...                finish
```

자체 평가가 핵심이다. 논문은 세 가지 변형을 보여준다: `sure / likely / impossible` 분류, `1..10` 숫자 점수, 후보 간 투표. 세 가지 모두 Game of 24에서 CoT를 크게 능가한다(4% -> 74%, GPT-4 기준).

### LATS (Zhou et al., ICML 2024)

LATS는 MCTS 아래 ToT, ReAct, Reflexion을 통합한다. LLM은 세 가지 역할을 수행한다:

- **정책**: 후보 다음 행동 제안(ReAct 스타일).
- **가치 함수**: 부분 궤적에 점수 부여(ToT 스타일 자체 평가).
- **자기 반영자**: 실패 시 자연어 반성 작성(Reflexion 스타일) 및 향후 롤아웃 재시드에 사용.

환경 피드백(관찰)이 가치 함수에 혼합되어 검색이 모델 의견뿐 아니라 실제 도구 결과에 의해 정보를 얻는다. 논문 당시 결과: HumanEval pass@1 92.7% (GPT-4, SOTA), WebShop 평균 75.9 (GPT-3.5, 경사 기반 미세 조정에 근접).

### MCTS, 최소한으로

반복당 네 단계:

1. **Select** — UCT(트리용 상위 신뢰 경계)를 사용하여 루트에서 리프로 이동.
2. **Expand** — 정책을 통해 K개의 자식 생성.
3. **Simulate** — 자식에서 정책을 사용하여 롤아웃, 가치 함수(또는 환경 보상)로 리프 점수 부여.
4. **Backpropagate** — 방문 횟수와 가치 추정치를 경로 위로 업데이트.

UCT 공식: `Q(s, a) + c * sqrt(ln N(s) / N(s, a))`. 첫 번째 항은 활용, 두 번째는 탐험. 작업별로 `c`를 조정하라.

### 비용 현실

검색은 토큰을 폭발시킨다. Game of 24에서 ToT는 CoT의 100-1000배 토큰을 사용한다. LATS도 비슷하다. 이는 무료가 아니다; 검색은 다음 경우에만 사용하라:

- 단일 궤적으로는 명백히 불충분한 작업 (Game of 24, 복잡한 코드).
- 벽시계 시간보다 정확성이 더 중요한 작업.
- 저렴하고 신뢰할 수 있는 가치 함수가 있는 작업 (코드용 단위 테스트, 수학용 명시적 목표).

작업에 단일 정답과 노이즈가 많은 평가기가 있으면 검색은 종종 상황을 악화시킨다 — "좋은 점수"의 틀린 답변을 찾는다.

### 2026년 위치

대부분의 프로덕션 에이전트는 LATS를 실행하지 않는다. 그들은 도구 기반 검증(CRITIC, 레슨 05)과 함께 ReAct를 실행한다. 검색은 전문화된 영역에서 나타난다:

- 가치 함수로 테스트를 실행하는 코딩 에이전트 (HumanEval 스타일).
- 여러 쿼리 경로를 탐색하는 심층 연구 에이전트.
- LangGraph 하위 그래프 내의 계획 중심 워크플로우.

AlphaEvolve (레슨 11)는 2025년의 극단적 사례다: 코드에 대한 진화적 검색, 기계 확인 가능한 적합도, 프론티어 개선 (56년 만의 첫 4x4 행렬 곱셈 개선).

## 직접 구현하기

`code/main.py`는 다음을 구현한다:

- 스타일화된 "산술 연산 선택" 작업에 대한 작은 ToT BFS.
- 동일한 작업에 대한 장난감 LATS MCTS 루프 (Select / Expand / Simulate / Backpropagate)와 UCT 선택.
- 기호 점수와 자체 평가 점수를 구성하는 가치 함수.

실행:

```
python3 code/main.py
```

트레이스는 BFS로 노드당 세 후보를 확장하는 ToT를, MCTS를 통해 최상의 롤아웃으로 수렴하는 LATS와 비교하여 보여준다. 두 경우 모두 토큰 수가 출력된다.

## 활용하기

LangGraph는 ToT 스타일 탐색을 하위 그래프 패턴으로 제공한다; LangChain 팀의 LATS 블로그(2024년 5월)가 참조 자습서다. LlamaIndex는 `TreeOfThoughts` 에이전트를 제공한다. 대부분의 2026년 프로덕션 에이전트에서 이 패턴은 `if task_complexity > threshold: use_search()` 게이트 뒤에 있다 — 레슨 05의 evaluator-optimizer 패턴 참조.

## 배포하기

`outputs/skill-search-policy.md`는 작업 형태, 예산, 평가기 충실도에 따라 선형 ReAct, ToT, LATS 및 진화적 검색 중에서 선택한다.

## 연습 문제

1. UCT c=0.1과 c=2.0으로 장난감 LATS를 실행하라. 트레이스에서 무엇이 바뀌는가?
2. 가치 함수를 더 노이즈가 많은 평가기로 교체하라(랜덤 지터 추가). MCTS가 여전히 최상의 리프를 찾는가? 허용되는 최소 신호 대 잡음비는 얼마인가?
3. 빔 검색 ToT(각 레벨에서 top-k 유지)를 구현하고 BFS와 비교하라. 빡빡한 토큰 예산에서 어느 것이 더 나은가?
4. LATS 섹션 5.1을 읽어라. HumanEval 궤적 수를 재현하라: 보고된 pass@1을 달성하는 데 몇 번의 롤아웃이 필요한가?
5. LATS 논문의 "LATS가 덜 도움이 되는 경우"에 대한 논의를 읽어라. 작업 형태를 검색 전략에 매핑하는 한 단락의 결정 규칙을 작성하라.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Tree of Thoughts | "분기 CoT" | Yao et al. — 자체 평가가 있는 생각 노드의 트리 |
| LATS | "MCTS for LLMs" | Zhou et al. — MCTS 아래 ToT + ReAct + Reflexion 통합 |
| UCT | "상위 신뢰 경계" | 활용(Q)과 탐험(ln N / n)의 균형을 맞추는 선택 공식 |
| Value function | "이 상태가 얼마나 좋은가" | 프롬프트된 LLM 점수 또는 환경 보상; 역전파 공급 |
| Policy | "행동 제안자" | ReAct 스타일 생성기; 후보 다음 생각/행동 출력 |
| Rollout | "시뮬레이션된 궤적" | 정책을 사용해 노드에서 리프로 이동, 값으로 점수 부여 |
| Backpropagate | "조상 업데이트" | 리프의 보상을 경로 위로 푸시, 방문 횟수와 Q 업데이트 |
| Search cost | "토큰 폭발" | Game of 24에서 CoT의 100-1000배; 채택 전 예산 고려 |

## 추가 자료

- [Yao et al., Tree of Thoughts (arXiv:2305.10601)](https://arxiv.org/abs/2305.10601) — 표준 논문
- [Zhou et al., LATS (arXiv:2310.04406)](https://arxiv.org/abs/2310.04406) — Reflexion 피드백이 있는 MCTS
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — 검색용 하위 그래프 패턴
- [AlphaEvolve (arXiv:2506.13131)](https://arxiv.org/abs/2506.13131) — 프로그래밍 방식 평가기가 있는 진화적 검색
