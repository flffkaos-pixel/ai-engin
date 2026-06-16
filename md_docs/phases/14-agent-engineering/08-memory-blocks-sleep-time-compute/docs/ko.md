# 메모리 블록과 Sleep-Time Compute (Letta)

> MemGPT는 2024년에 Letta가 되었다. 2026년 진화는 두 가지 아이디어를 추가한다: 모델이 직접 편집할 수 있는 개별 기능적 메모리 블록과 기본 에이전트가 유휴 상태일 때 비동기적으로 메모리를 통합하는 sleep-time 에이전트. 이것이 하나의 대화를 넘어 메모리를 확장하는 방법이다.

**Type:** Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 07 (MemGPT)
**Time:** ~75분

## 학습 목표

- Letta가 사용하는 세 가지 메모리 계층(core, recall, archival)과 각각의 역할을 명명한다.
- 메모리 블록 패턴을 설명한다: Human 블록, Persona 블록 및 일급 타입 객체로서의 사용자 정의 블록.
- Sleep-time compute가 무엇인지, 왜 중요 경로에서 벗어나는지, 그리고 기본 에이전트보다 더 강력한 모델을 실행할 수 있는 이유를 설명한다.
- 기본 에이전트가 응답을 제공하고 sleep-time 에이전트가 턴 사이에 블록을 통합하는 스크립트 기반 2-에이전트 루프를 구현한다.

## 문제

MemGPT (레슨 07)는 가상 메모리 제어 흐름을 해결했다. 세 가지 프로덕션 문제가 나타났다:

1. **지연 시간.** 모든 메모리 작업이 중요 경로에 있다. 에이전트가 사용자가 기다리는 동안 가지치기, 요약 또는 조정을 해야 하면 꼬리 지연 시간이 폭발한다.
2. **메모리 부패.** 쓰기가 축적된다. 모순된 사실이 남아 있다. 검색이 오래된 콘텐츠에 빠진다.
3. **구조 손실.** 평면 아카이브 저장소는 "Human 블록은 항상 프롬프트에 있고, Persona 블록은 항상 프롬프트에 있으며, Task 블록은 세션별로 교체된다"는 것을 표현할 수 없다.

Letta (letta.com)는 2026년의 재작성이다. 메모리 블록은 구조를 명시적으로 만들고, sleep-time compute는 통합을 중요 경로에서 제거한다.

## 개념

### 세 가지 계층

| 계층 | 범위 | 위치 | 작성자 |
|------|------|------|--------|
| Core | 항상 표시 | 메인 프롬프트 내부 | 에이전트 도구 호출 + sleep-time 재작성 |
| Recall | 대화 기록 | 검색 가능 | 자동 턴 로깅 |
| Archival | 임의 사실 | 벡터 + KV + 그래프 | 에이전트 도구 호출 + sleep-time 수집 |

Core는 MemGPT 코어다. Recall은 축출된 꼬리가 있는 대화 버퍼다. Archival은 외부 저장소다. 분할은 MemGPT의 2계층 과부하를 정리한다.

### 메모리 블록

블록은 코어 계층의 타입화된, 지속적이며, 편집 가능한 섹션이다. 원본 MemGPT 논문은 두 가지를 정의했다:

- **Human 블록** — 사용자에 관한 사실 (이름, 역할, 선호도, 목표).
- **Persona 블록** — 에이전트의 자아 개념 (정체성, 어조, 제약).

Letta는 임의의 사용자 정의 블록으로 일반화한다: 현재 목표를 위한 `Task` 블록, 코드베이스 사실을 위한 `Project` 블록, 하드 제약을 위한 `Safety` 블록. 각 블록에는 `id`, `label`, `value`, `limit` (문자 제한), `description` (모델이 언제 편집해야 하는지 알 수 있도록)이 있다.

블록은 도구 표면을 통해 편집 가능:

- `block_append(label, text)`
- `block_replace(label, old, new)`
- `block_read(label)`
- `block_summarize(label)` — 제한에 가까운 블록 압축.

### Sleep-time compute

2025년 Letta 추가: 중요 경로 밖에서 백그라운드에서 두 번째 에이전트 실행. Sleep-time 에이전트는 대화 트랜스크립트와 코드베이스 컨텍스트를 처리하고, 공유 블록에 `learned_context`를 기록하며, 아카이브 레코드를 통합하거나 무효화한다.

결과 속성:

- **지연 시간 비용 없음.** 기본 응답이 메모리 작업을 기다리지 않음.
- **더 강력한 모델 허용.** Sleep-time 에이전트는 지연 시간 제약이 없기 때문에 더 비싸고 느린 모델일 수 있음.
- **자연스러운 통합 기간.** 사용자가 기다리지 않을 때 중복 제거, 요약, 모순된 사실 무효화.

형태는 인간이 작업하는 방식과 일치한다: 작업을 수행하고, 잠을 자고, 장기 기억은 밤사이에 정착된다.

### Letta V1과 네이티브 추론

Letta V1 (`letta_v1_agent`, 2026)은 `send_message`/하트비트와 인라인 `Thought:` 토큰을 폐기하고 네이티브 추론을 채택한다. Responses API (OpenAI)와 확장 사고가 있는 Messages API (Anthropic)는 별도 채널로 추론을 출력하며, 턴 간에 전달된다(프로덕션에서는 공급자 간 암호화됨). 제어 루프는 여전히 ReAct다. 생각 트레이스는 프롬프트 형태가 아닌 구조적이다.

### 이 패턴이 잘못되는 경우

- **블록 비대.** 무한 `block_append`가 빠르게 제한에 도달. 제한을 초과하는 쓰기 전에 블록 요약기를 연결하라.
- **침묵 드리프트.** Sleep-time 에이전트가 블록을 재작성하고 기본 에이전트가 알아차리지 못함. 블록 버전 관리 및 트레이스에 차이점 표시.
- **중독된 통합.** Sleep-time 에이전트가 공격자 접근 가능 콘텐츠를 코어로 처리. 레슨 27이 sleep-time 표면에도 적용된다.

## 직접 구현하기

`code/main.py`는 다음을 구현한다:

- `Block` — id, label, value, limit, description.
- `BlockStore` — CRUD + `near_limit(label)` 헬퍼.
- 두 개의 스크립트 기반 에이전트 — `PrimaryAgent`는 턴을 제공, `SleepTimeAgent`는 턴 사이에 통합.
- 블록 쓰기가 있는 3턴 대화와 블록을 요약하고 오래된 사실을 무효화하는 sleep-time 패스를 보여주는 트레이스.

실행:

```
python3 code/main.py
```

트랜스크립트는 분할을 보여준다: 기본 턴은 빠르고 원시 쓰기를 생성하고, sleep 패스는 압축 및 정리한다.

## 활용하기

- **Letta** (letta.com) — 참조 구현. 자체 호스팅 또는 관리형 클라우드.
- **Claude Agent SDK 스킬** — 블록 형태의 지식. 스킬은 에이전트가 요청 시 로드하는 명명되고 버전 관리되며 검색 가능한 명령어 블록.
- **커스텀 빌드** — 스토리지 백엔드에 대한 제어를 원하는 팀용. 나중에 마이그레이션할 수 있도록 Letta API 계약 사용.

## 배포하기

`outputs/skill-memory-blocks.md`는 모든 런타임에 대해 안전 규칙과 인용 연결이 포함된 Letta 형태의 블록 시스템을 생성한다.

## 연습 문제

1. `near_limit`가 true를 반환할 때 블록 값을 모델 생성 요약으로 대체하는 `block_summarize` 도구를 추가하라. 요약 호출과 블록 오버플로우를 모두 최소화하는 트리거 임계값은?
2. 아카이브에 대한 sleep-time 중복 제거를 구현하라: 90% 이상의 토큰 중복이 있는 두 레코드는 하나로 축소. 중요 경로에서는 절대 안 하고 sleep 패스에서만 수행.
3. 블록 버전 관리. 모든 쓰기마다 이전 값과 차이점 기록. 운영자가 "왜 에이전트가 X를 잊었는지" 디버깅할 수 있도록 `block_history(label)` 공개.
4. Sleep-time 에이전트를 신뢰할 수 없는 작성자로 취급. Persona 또는 Safety 블록을 건드릴 때 커밋 전에 두 번째 에이전트 검토 필요.
5. 예제를 Letta API (`letta_v1_agent`) 사용으로 포팅. 블록 스키마에서 무엇이 바뀌고, 네이티브 추론이 트레이스 형태를 어떻게 변경하는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Memory block | "편집 가능한 프롬프트 섹션" | 코어 메모리의 타입화되고 지속적이며 LLM이 편집 가능한 세그먼트 |
| Human block | "사용자 메모리" | 사용자에 관한 사실, 코어에 고정 |
| Persona block | "에이전트 정체성" | 자아 개념, 어조, 제약, 코어에 고정 |
| Sleep-time compute | "비동기 메모리 작업" | 중요 경로 밖에서 통합을 수행하는 두 번째 에이전트 |
| Core / Recall / Archival | "계층" | 3계층 메모리 분할: 항상 표시 / 대화 / 외부 |
| Block limit | "제한" | 블록당 문자 제한; 요약 강제 |
| Native reasoning | "생각 채널" | 프롬프트 수준의 `Thought:`가 아닌 프로바이더 수준의 추론 출력 |
| Learned context | "수면 출력" | Sleep-time 에이전트가 공유 블록에 기록하는 사실 |

## 추가 자료

- [Letta, Memory Blocks blog](https://www.letta.com/blog/memory-blocks) — 블록 패턴
- [Letta, Sleep-time Compute blog](https://www.letta.com/blog/sleep-time-compute) — 비동기 통합
- [Letta, Rearchitecting the Agent Loop](https://www.letta.com/blog/letta-v1-agent) — 네이티브 추론 재작성
- [Packer et al., MemGPT (arXiv:2310.08560)](https://arxiv.org/abs/2310.08560) — 기원
