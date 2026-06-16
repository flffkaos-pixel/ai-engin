# Reflexion: 언어적 강화학습

> 경사 기반 RL은 실패 모드를 수정하는 데 수천 번의 시행과 GPU 클러스터가 필요하다. Reflexion (Shinn et al., NeurIPS 2023)은 자연어로 이를 수행한다: 각 실패 시도 후 에이전트가 반성을 작성하고, 일화 기억에 저장하며, 다음 시도를 해당 기억에 조건화한다. 이는 Letta의 sleep-time compute, Claude Code의 CLAUDE.md 학습, pro-workflow의 learn-rule 뒤에 있는 패턴이다.

**Type:** Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 02 (ReWOO)
**Time:** ~60분

## 학습 목표

- Reflexion의 세 가지 구성 요소(Actor, Evaluator, Self-Reflector)와 일화 기억의 역할을 명명한다.
- 이진 평가기, 반성 버퍼, 새로운 재시도를 사용하여 stdlib Reflexion 루프를 구현한다.
- 주어진 작업에 대해 스칼라, 휴리스틱, 자체 평가 피드백 소스 중에서 선택한다.
- 언어적 강화가 경사 기반 RL이 수천 번의 시행이 필요한 오류를 잡는 이유를 설명한다.

## 문제

에이전트가 작업에 실패한다. 표준 RL에서는 수천 번의 더 많은 시행을 실행하고, 경사를 계산하며, 가중치를 업데이트해야 한다. 비싸고 느리며, 대부분의 프로덕션 에이전트는 모든 실패에 대한 훈련 예산이 없다.

Reflexion (Shinn et al., arXiv:2303.11366)은 다른 질문을 한다: 에이전트가 왜 실패했는지 생각하고 그 생각을 프롬프트에 담아 다시 시도하면 어떨까? 가중치 업데이트가 없다. 경사가 없다. 시행 사이에 저장된 자연어만 있을 뿐이다.

결과: ALFWorld에서 ReAct 및 기타 미세 조정되지 않은 기준선을 능가한다. HotpotQA에서 ReAct보다 개선된다. 코드 생성(HumanEval/MBPP)에서 당시 최첨단을 기록한다. 단 한 번의 경사 step도 없이.

## 개념

### 세 가지 구성 요소

```
Actor         : generates a trajectory (ReAct-style loop)
Evaluator     : scores the trajectory — binary, heuristic, or self-eval
Self-Reflector: writes a natural-language reflection on the failure
```

하나의 데이터 구조 추가:

```
Episodic memory: list of prior reflections, prepended to the next trial's prompt
```

한 번의 시행은 Actor를 실행한다. Evaluator가 점수를 매긴다. 점수가 낮으면 Self-Reflector가 반성을 생성한다("X에 관한 질문으로 오해해서 잘못된 도구를 선택했다"). 반성은 일화 기억에 들어간다. 다음 시행은 새로 시작하지만 반성을 본다.

### 세 가지 평가기 유형

1. **스칼라** — 외부 이진 신호. ALFWorld는 성공 또는 실패. HumanEval 테스트는 통과 또는 실패. 가장 간단하고, 신호가 가장 강하다.
2. **휴리스틱** — 사전 정의된 실패 시그니처. "에이전트가 같은 행동을 두 번 연속 생성하면 정체로 표시." "궤적이 50 step을 초과하면 비효율적으로 표시."
3. **자가 평가** — LLM이 자신의 궤적을 평가. 실제 정답이 없을 때 필요. 더 약한 신호; 도구 기반 검증(레슨 05 — CRITIC)과 잘 어울린다.

2026년 기본값은 혼합: 가능하면 스칼라, 없으면 자가 평가, 안전 레일로서 휴리스틱.

### 일반화되는 이유

Reflexion은 새로운 알고리즘이라기보다 명명된 패턴에 가깝다. 거의 모든 프로덕션 "자가 치유" 에이전트는 어떤 변형을 실행한다:

- Letta의 sleep-time compute (레슨 08): 별도 에이전트가 과거 대화를 반영하고 메모리 블록에 기록.
- Claude Code의 `CLAUDE.md` / "save memory" 패턴: 학습으로 캡처된 반성, 향후 세션 앞에 추가.
- pro-workflow의 `/learn-rule` 명령: 명시적 규칙으로 캡처된 수정.
- LangGraph의 반성 노드: 출력을 평가하고 필요시 개선으로 라우팅하는 노드.

모두 같은 통찰에서 비롯된다: 자연어는 실행 간 "실패에서 배운 것"을 전달하기에 충분히 풍부한 매체다.

### 언제 효과적이고 언제 그렇지 않은가

Reflexion은 다음 경우에 효과적이다:

- 명확한 실패 신호가 있을 때 (테스트 실패, 도구 오류, 잘못된 답변).
- 작업 클래스가 재현 가능할 때 (같은 유형의 질문을 다시 할 수 있음).
- 반성이 궤적을 개선할 여지가 있을 때 (충분한 행동 예산).

Reflexion은 다음 경우에 도움이 되지 않는다:

- 에이전트가 첫 시도에 이미 성공할 때.
- 실패가 외부적일 때 (네트워크 다운, 도구 고장) — "네트워크가 다운됐다"는 반성은 향후 실행에 도움이 되지 않는다.
- 반성이 미신으로 변할 때 — 일회성 불안정 실행에 대한 이야기를 저장.

2026년 함정: 메모리 부패. 반성이 축적된다; 일부는 구식이거나 잘못되었다; 일화 버퍼가 커짐에 따라 재실행이 느려진다. 완화: 주기적 압축(레슨 06), 반성에 TTL, 또는 별도 sleep-time 정리 에이전트(Letta).

## 직접 구현하기

`code/main.py`는 장난감 퍼즐에 Reflexion을 구현한다: 합계가 목표가 되는 3개 요소 리스트 생성. Actor는 후보 리스트를 출력하고, Evaluator는 합계를 확인하며, Self-Reflector는 무엇이 잘못되었는지 한 줄을 작성한다. 반성은 다음 시행을 위해 일화 기억에 저장된다.

구성 요소:

- `Actor` — 반성을 볼 때 개선되는 스크립트 기반 정책.
- `Evaluator.binary()` — 목표 합계에 대한 통과/실패.
- `SelfReflector` — 실패의 한 줄 진단 생성.
- `EpisodicMemory` — TTL 의미가 있는 제한된 리스트.

실행:

```
python3 code/main.py
```

트레이스는 세 번의 시행을 보여준다. 시행 1은 실패, 반성이 저장됨, 시행 2는 반성을 보고 개선되지만 여전히 실패, 시행 3은 성공. 기준선 실행(반성 없음)과 비교 — 시행 1의 답변에 계속 머무른다.

## 활용하기

LangGraph는 반성을 노드 패턴으로 제공한다. Claude Code의 `/memory` 명령과 pro-workflow의 `/learn-rule`은 일화 버퍼를 마크다운 파일로 외부화한다. Letta의 sleep-time compute는 기본 에이전트가 지연 시간에 묶여 있는 동안 Self-Reflector를 다운타임에 실행한다. OpenAI Agents SDK는 Reflexion을 직접 제공하지 않는다; 점수로 궤적을 거부하는 커스텀 Guardrail과 실행 간에 유지되는 `Session` 메모리로 구축한다.

## 배포하기

`outputs/skill-reflexion-buffer.md`는 반성 캡처, TTL, 중복 제거가 있는 일화 버퍼를 생성하고 유지 관리한다. 작업 클래스와 실패가 주어지면 다음 시행에 실제로 도움이 되는 반성을 출력한다(일반적인 "더 조심해"가 아님).

## 연습 문제

1. 이진 평가기에서 거리 측정(목표와의 차이)을 반환하는 스칼라 평가기로 전환하라. 더 빨리 수렴하는가?
2. 반성에 10번 시행의 TTL을 추가하라. 그 시점 이후에 오래된 반성은 도움이 되는가, 해가 되는가?
3. 휴리스틱 평가기를 구현하라: 같은 행동이 반복되면 시행을 정체로 표시. Self-Reflector와 어떻게 상호작용하는가?
4. 반성을 무시하는 적대적 Actor로 Reflexion을 실행하라. Actor가 반성을 알아차리도록 강제하는 최소한의 반성 프롬프트 엔지니어링은 무엇인가?
5. Reflexion 논문의 AlfWorld에 관한 섹션 4를 읽어라. 130% 성공률 개선을 개념적으로 재현하라: 기본 ReAct와의 주요 차이는 무엇인가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Reflexion | "자기 수정" | Shinn et al. 2023 — Actor, Evaluator, Self-Reflector + 일화 기억 |
| Verbal reinforcement | "경사 없는 학습" | 다음 시행 프롬프트 앞에 추가되는 자연어 반성 |
| Episodic memory | "작업별 반성" | 하나의 작업 클래스에 대한 이전 반성의 제한된 버퍼 |
| Scalar evaluator | "이진 성공 신호" | 실제 정답으로부터의 통과/실패 또는 숫자 점수 |
| Heuristic evaluator | "패턴 기반 감지기" | 사전 정의된 실패 시그니처 (예: 정체 루프, 너무 많은 step) |
| Self-evaluator | "LLM-as-judge on own trace" | 실제 정답이 없을 때 더 약한 신호 대체 — 도구 기반 검증과 함께 사용 |
| Memory rot | "오래된 반성" | 쓸모없는 항목으로 채워지는 일화 버퍼; 압축/TTL로 수정 |
| Sleep-time reflection | "비동기 자기 반성" | 기본 에이전트가 빠르게 유지되도록 핫 경로 밖에서 Self-Reflector 실행 |

## 추가 자료

- [Shinn et al., Reflexion: Language Agents with Verbal Reinforcement Learning (arXiv:2303.11366)](https://arxiv.org/abs/2303.11366) — 표준 논문
- [Letta, Sleep-time Compute](https://www.letta.com/blog/sleep-time-compute) — 프로덕션에서의 비동기 반성
- [Anthropic, Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — 컨텍스트의 일부로 일화 버퍼 관리
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — 반성 노드 패턴
