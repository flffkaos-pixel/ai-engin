# 그룹 채팅 및发言자 선택

> AutoGen의 GroupChat은 N개의 에이전트가 순환 또는 LLM 선택 speaker로 공동 대화를 만드는 프레임워크입니다. 2024년 후반 GroupChat은 "중요한 것을 말하고" 결정하도록 명시적 역할을 도입했습니다. 이는 시코판시와 불필요한 반복을 줄이지만 역할을 "말해야 할 것"으로 conflate하여 때때로 더 나쁜集体적 결정을 초래합니다. 이 레슨은 GroupChat의 mechanics, 그 진화, 그리고 2026년 프로덕션 사용의 교훈을 다룹니다.

**유형:** 학습
**언어:** Python (stdlib)
**선수 과목:** Phase 16 · 04 (Primitive Model)
**소요 시간:** ~45분

## 문제

에이전트 팀이 공동으로 무언가를 결정해야 합니다. 순차적 파이프라인은 너무rigid합니다. 수퍼바이저는 불필요한 오버헤드입니다. 가장 자연스러운 해결책: 모두 같은 방에 있고轮流发言합니다.

AutoGen의 GroupChat이 정확히 그것입니다. N개의 에이전트가 대화를 공유합니다. 각 턴에서 speaker가 선택됩니다.她们는 메시지를 추가합니다. 대화가 종료될 때까지 반복됩니다.

문제는 speaker를 선택하는 방법입니다.

## 개념

### GroupChat mechanics

AutoGen GroupChat의 핵심 구성요소:

```python
groupchat = GroupChat(
    agents=[agent1, agent2, agent3],
    messages=[],
    max_round=10,
    speaker_selection_method="auto",
)

result = groupchat.chat()
```

세 가지 speaker 선택 방법:

1. **手动** — 사용자 또는 외부 로직이 다음 speaker를 명시적으로 선택합니다.
2. **라운드 로빈** — 에이전트가 차례로发言합니다. 단순하지만 결정적이지 않고adaptive하지 않습니다.
3. **LLM 선택** — LLM이 대화를 읽고 "누가次に发言해야 합니까?"라고 묻습니다. 적응적이지만 느리고昂贵的입니다.

### 2024년 말 역할 도입

AutoGen v0.4 (2024년 후반)는 명시적 역할을 도입했습니다:

```python
groupchat = GroupChat(
    agents=[planner, coder, reviewer],
    messages=[],
    roles={
        "planner": "당신의工作是分解任务并制定计划",
        "coder": "당신의工作是编写代码",
        "reviewer": "당신의工作是审查代码质量",
    },
)
```

역할은 두 가지 문제를 해결하도록 설계되었습니다:
- **시코판시 줄이기** — 에이전트가 자신의 역할을 알고 있기 때문에 다른 사람의 의견에 덜 동의합니다.
- **불필요한 반복 줄이기** — 플래너가 이미 말했다면 다시 말할 필요가 없습니다.

### 역할의 실패: 역할confirmation

역할의意想不到한 결과: 에이전트가 역할을 "말해야 할 것"으로 conflate하기 시작합니다. 플래너가 코딩 질문에 대해 강력한 의견을 가질지라도, "나는 플래너다, 코딩은 내 일이 아니다"라고感じ합니다. 결과적으로集体的 결정이 각 역할의狭い 시야에 의해 제약됩니다.

Cemri et al. (MAST)는 이것을 "역할固化"라고 부릅니다 — 에이전트가 역할을 넘어 생각하는 것을 중단합니다.

### 대안: 능력 기반 선택

역할 대신 능력으로发言자를 선택합니다:

```python
def select_speaker(messages, agents):
    last_task = messages[-1]["content"]
    
    if "write code" in last_task or "implement" in last_task:
        return find_agent("coder")
    elif "review" in last_task or "check" in last_task:
        return find_agent("reviewer")
    else:
        return find_agent("planner")
```

이것은说话자를 선택하기 전에 대화를 분석합니다. 역할보다 더 유연하지만 구현하기 더 복잡합니다.

### GroupChat 대 LangGraph

| 측면 | GroupChat | LangGraph |
|------|----------|-----------|
| 구조 | 에이전트 풀 +speaker 선택 | 명시적 그래프 |
| 결정론 |speaker 선택의 불확실성 | 그래프 에지가 명시적 |
| 디버깅 | 대화가 혼합되어 어려움 | 각 노드가 분리됨 |
| 확장성 | N 에이전트에 적합 | 파이프라인에 더 적합 |
| 유연성 |speaker 선택을 사용자 정의 가능 | 노드/에지 추가로 유연 |

GroupChat은 "에이전트를 모으고 대화를 시작하세요"에 좋습니다. LangGraph는 "정확한 워크플로우가 있고 그 것을 시행하세요"에 좋습니다.

### 실패 모드

- **시cofancy cascade** — 모든 에이전트가 가장自信のあるspeaker를 따라갑니다.
- **역할固化** — 에이전트가 역할을 넘어 추론하는 것을 중단합니다.
- **반복** —speaker 선택이 대화를 읽지 않아 이전speaker가 다시发言합니다.
- **무한 루프** — 종료 조건이 없으면 대화가 영원히 계속됩니다.

## 실습

`code/main.py`는 GroupChat의 세 가지speaker 선택 방법을 시뮬레이션합니다:

- 라운드 로빈: 단순하지만 대화가 주제에서 벗어날 때適応하지 않습니다
- LLM 선택: 적응적이지만 비용이 많이 듭니다
- 능력 기반: 가장 유연하지만 구현이 복잡합니다

데모는 세 방법 모두에서 동일한 대화를 실행하고speaker 시퀀스를 비교합니다.

실행:

```
python3 code/main.py
```

## 활용

GroupChat이 적절한 경우:
- 브레인스토밍 및 아이디어 생성
- 다양한 관점의 검토가 필요한 설계 결정
- 에이전트 역할이模糊하거나 자주 변경되는 탐색적 작업

GroupChat이 잘못된 경우:
- 엄격한 순서가 필요한 워크플로우 (LangGraph 사용)
- 결정론적 감사/재현이 필요한 작업
- 2명 이하의 에이전트 (오버헤드가 가치가 없음)

## 핵심 용어

| 용어 |人们在说什么 | 实际含义 |
|------|----------------|------------------------|
| GroupChat | "에이전트 대화" | N개의 에이전트가 공유 대화에 참여하고speaker가 순환합니다. |
| speaker 선택 | "누가次に 말합니까" | 다음发言자를 결정하는 메커니즘. 방법: 수동, 라운드 로빈, LLM. |
| 역할固化 | "역할이 갑옷이 됩니다" | 에이전트가 역할을越えて思考する 것을 중단하여集体적 결정이 역할의狭い 시야에 의해制約されます. |
| 능력 기반 선택 | "태스크에 따라 다릅니다" |speaker를 선택하기 전에 대화를 분석하여 가장 적합한 에이전트를 선택합니다. |
| 시cofancy cascade | "가장自信のある 사람.follow" | 모든 에이전트가 가장自信のあるspeaker를 따르는集体적 실패. |

## 추가 자료

- [AutoGen GroupChat 문서](https://microsoft.github.io/autogen/stable/) — GroupChat의 공식 문서
- [AutoGen v0.4 릴리스 노트](https://github.com/microsoft/autogen/releases) — 역할 도입에 대한 세부 정보
- [Cemri et al. — 왜 멀티에이전트 LLM 시스템이 실패하는가?](https://arxiv.org/abs/2503.13657) — 역할固化을 문서화하는 MAST