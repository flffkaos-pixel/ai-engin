# 벤치마크: SWE-bench, GAIA, AgentBench

> 세 가지 벤치마크가 2026년 에이전트 평가를 주도한다. SWE-bench는 코드 패치를 테스트한다. GAIA는 제너럴리스트 도구 사용을 테스트한다. AgentBench는 다중 환경 추론을 테스트한다. 구성, 오염 상황, 그리고 측정하지 않는 것을 알아야 한다.

**Type:** Learn
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 06 (Tool Use)
**Time:** ~60분

## 학습 목표

- SWE-bench의 테스트 하네스(FAIL_TO_PASS)를 명명하고 단위 테스트에 조건을 거는 이유를 설명한다.
- SWE-bench Verified (OpenAI, 500개 작업)가 존재하는 이유와 제거하는 것을 설명한다.
- GAIA의 설계를 설명한다: 인간에게는 간단, AI에게는 어려움; 세 가지 난이도.
- AgentBench의 8가지 환경과 오픈소스 LLM의 주요 차단 요소를 명명한다.
- SWE-bench+ 오염 발견과 그 시사점을 요약한다.

## 문제

리더보드는 어떤 모델이 하나의 벤치마크에서 이기는지 알려준다. 다음은 알려주지 않는다:

- 벤치마크가 오염되었는지 (훈련 데이터의 솔루션, 테스트 누출).
- 벤치마크가 사용자가 관심 있는 것을 측정하는지 (코드 vs 브라우징 vs 제너럴리스트).
- 평가기가 견고한지 (AST 매칭, 상태 확인, 사람 검토).

숫자를 인용하기 전에 세 가지 앵커 벤치마크와 그 실패 모드를 알아야 한다.

## 개념

### SWE-bench (Jimenez et al., ICLR 2024 oral)

- 12개의 인기 Python 리포지토리에서 가져온 2,294개의 실제 GitHub 이슈.
- 에이전트가 받는 것: 수정 전 커밋의 코드베이스 + 자연어 이슈 설명.
- 에이전트가 생성: 패치.
- 평가기: 패치 적용, 리포지토리의 테스트 스위트 실행. 패치는 FAIL_TO_PASS 테스트(이전에 실패, 지금 통과)를 뒤집어야 하며 PASS_TO_PASS 테스트를 깨뜨리지 않아야 함.

SWE-agent (Yang et al., 2024)는 출시 시 12.5%를 기록하며 에이전트-컴퓨터 인터페이스(파일 편집기 명령, 모델이 이해하는 검색 구문)를 강조.

### SWE-bench Verified

OpenAI, Aug 2024. 사람이 선별한 500개 작업 하위 집합. 모호한 이슈, 신뢰할 수 없는 테스트, 수정이 불명확한 작업을 제거. "당신의 에이전트가 실제 패치를 제공하는가?"에 대한 기본 벤치마크.

### 오염

- SWE-bench 이슈의 94% 이상이 대부분의 모델 컷오프 이전.
- **SWE-bench+** 는 성공적인 패치의 32.67%가 이슈 텍스트에서 솔루션을 누출했으며(모델이 설명에서 수정을 봄), 31.08%가 약한 테스트 커버리지로 인해 의심스러운 것으로 나타났음.
- Verified는 더 깨끗하지만 오염이 없는 것은 아님.

실용적 시사점: SWE-bench에서 50%를 기록하는 모델은 SWE-bench+에서 35%를 기록할 수 있음. SWE-bench 성능을 주장한다면 항상 둘 다 보고하라.

### GAIA (Mialon et al., Nov 2023)

- 466개 질문; 300개가 huggingface.co/gaia-benchmark의 비공개 리더보드에 유지.
- 설계 철학: "인간에게 개념적으로 간단함(92%)하지만 AI에게 어려움(플러그인이 있는 GPT-4: 15%)."
- 추론, 멀티모달, 웹, 도구 사용 테스트.
- 세 가지 난이도; 레벨 3은 모달리티 간 긴 도구 체인 필요.

GAIA는 "제너럴리스트 능력"을 측정하기 위해 실행하는 것이다. 코드 특정 벤치마크와 혼동하지 마라.

### AgentBench (Liu et al., ICLR 2024)

- 코드(Bash, DB, KG), 게임(Alfworld, LTP), 웹(WebShop, Mind2Web), 개방형 생성 등 8개 환경.
- 멀티 턴, 분할당 ~4k-13k 턴.
- 주요 발견: 장기 추론, 의사 결정 및 지시 따르기가 OSS LLM이 상용을 따라잡는 데 장벽.

### 측정하지 않는 것

- 실제 운영 비용 (토큰, 벽시계).
- 적대적 조건에서의 안전 행동.
- 도메인에서의 성능 (자체 평가 사용, 레슨 30).
- 꼬리 실패 (벤치마크는 평균; 프로덕션 운영자는 최악의 1%를 중요시).

### 벤치마킹이 잘못되는 경우

- **단일 숫자 집착.** SWE-bench 50%는 P50/P75/P95 비용 + 단계 분포보다 덜 알려줌.
- **오염된 주장.** SWE-bench를 Verified나 SWE-bench+ 언급 없이 보고하는 것은 오해의 소지가 있음.
- **벤치마크-as-개발-목표.** 벤치마크 최적화는 프로덕션 유용성과 괴리.

## 직접 구현하기

`code/main.py`는 장난감 SWE-bench 유사 하네스를 구현한다:

- 합성 버그 수정 작업 (3개 작업).
- 패치를 제안하는 스크립트 기반 "에이전트".
- FAIL_TO_PASS (버그 수정됨) 및 PASS_TO_PASS (아무것도 깨지지 않음)를 확인하는 테스트 러너.
- 질문 분해 깊이에 기반한 GAIA 스타일 난이도 분류기.

실행:

```
python3 code/main.py
```

출력은 작업당 + 난이도별 해결률을 보여주고 평가기 규칙을 구체적으로 만든다.

## 활용하기

- **SWE-bench Verified** for code agents. Always report Verified scores.
- **GAIA** for generalist agents. Use the private leaderboard split.
- **AgentBench** for multi-environment comparison.
- **Custom evals** (레슨 30) for your product's actual shape.

## 배포하기

`outputs/skill-benchmark-harness.md`는 FAIL_TO_PASS / PASS_TO_PASS 게이팅으로 모든 코드베이스-작업 쌍에 대한 SWE-bench 스타일 하네스를 구축한다.

## 연습 문제

1. 장난감 하네스를 실제 리포지토리(자신의 것 중 하나 선택)에서 실행하도록 포팅. 알려진 버그에 대해 3개의 FAIL_TO_PASS 테스트 작성.
2. 단계 수 메트릭 추가. 3개 작업에서 해결당 몇 개의 에이전트 단계?
3. SWE-bench+ 논문 읽기. 솔루션 누출 검사 구현 (이슈 텍스트를 diff와 패턴 매칭).
4. 공개 분할에서 GAIA 질문 다운로드. GPT-4급 에이전트가 무엇을 할지 추적. 어떤 도구가 필요한가?
5. AgentBench의 환경별 분석 읽기. 어떤 환경이 제품 표면을 반영하는가? "SOTA"가 거기서 어떻게 보이는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| SWE-bench | "코드 에이전트 벤치마크" | 2,294개 GitHub 이슈; 패치는 FAIL_TO_PASS 테스트를 뒤집어야 함 |
| SWE-bench Verified | "클린 SWE-bench" | 500개 사람 선별 작업, OpenAI |
| FAIL_TO_PASS | "수정 게이트" | 이전에 실패했으며 패치 후 통과해야 하는 테스트 |
| PASS_TO_PASS | "회귀 방지 게이트" | 이전에 통과했으며 여전히 통과해야 하는 테스트 |
| GAIA | "제너럴리스트 벤치마크" | 466개 인간-쉬움 / AI-어려움 멀티 도구 질문 |
| AgentBench | "다중 환경 벤치마크" | 8개 환경; 장기 멀티 턴 |
| Contamination | "훈련 세트 누출" | 모델 훈련에 존재하는 벤치마크 작업 |
| SWE-bench+ | "오염 감사" | 성공적인 SWE-bench 패치에서 32.67% 솔루션 누출 발견 |

## 추가 자료

- [Jimenez et al., SWE-bench (arXiv:2310.06770)](https://arxiv.org/abs/2310.06770) — the original benchmark
- [OpenAI, SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) — the curated subset
- [Mialon et al., GAIA (arXiv:2311.12983)](https://arxiv.org/abs/2311.12983) — generalist benchmark
- [Liu et al., AgentBench (arXiv:2308.03688)](https://arxiv.org/abs/2308.03688) — multi-environment suite
