# 스킬 라이브러리와 평생 학습 (Voyager)

> Voyager (Wang et al., TMLR 2024)는 실행 가능한 코드를 스킬로 취급한다. 스킬은 명명되고, 검색 가능하며, 구성 가능하고, 환경 피드백에 의해 개선된다. 이것이 Claude Agent SDK 스킬, skillkit 및 2026년 스킬 라이브러리 패턴의 참조 아키텍처다.

**Type:** Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 07 (MemGPT), Phase 14 · 08 (Letta Blocks)
**Time:** ~75분

## 학습 목표

- Voyager의 세 가지 구성 요소(자동 커리큘럼, 스킬 라이브러리, 반복적 프롬프팅)와 각각의 역할을 명명한다.
- Voyager가 행동 공간을 기본 명령어가 아닌 코드로 만드는 이유를 설명한다.
- 등록, 검색, 구성, 실패 기반 개선이 있는 stdlib 스킬 라이브러리를 구현한다.
- Voyager의 패턴을 2026년 Claude Agent SDK 스킬 및 skillkit 생태계에 매핑한다.

## 문제

모든 세션에서 모든 기능을 처음부터 다시 구축하는 에이전트는 세 가지 잘못된 일을 한다:

1. **토큰 낭비.** 모든 작업이 동일한 추론을 다시 유발한다.
2. **진행 손실.** 세션 A에서 학습한 수정이 세션 B로 전송되지 않는다.
3. **장기 구성 실패.** 복잡한 작업은 기능 계층이 필요하다; 원샷 프롬프트로는 표현할 수 없다.

Voyager의 답변: 각 재사용 가능한 기능을 라이브러리에 저장된 명명된 코드 청크로 취급하고, 유사도로 검색 가능하며, 다른 스킬과 구성 가능하고, 실행 피드백으로 개선한다.

## 개념

### 세 가지 구성 요소

Voyager (arXiv:2305.16291)는 에이전트를 다음과 같이 구조화한다:

1. **자동 커리큘럼.** 호기심 기반 제안기가 에이전트의 현재 스킬 세트와 환경 상태에 따라 다음 작업을 선택. 탐험은 상향식.
2. **스킬 라이브러리.** 각 스킬은 실행 가능한 코드. 새 스킬은 작업이 성공할 때 추가. 스킬은 쿼리-설명 유사도로 검색.
3. **반복적 프롬프팅 메커니즘.** 실패 시 에이전트는 실행 오류, 환경 피드백 및 자체 검증 출력을 받고 스킬을 개선.

Minecraft 평가 (Wang et al., 2024): 기준선 대비 3.3배 더 많은 고유 아이템, 8.5배 빠른 돌 도구, 6.4배 빠른 철 도구, 2.3배 더 긴 지도 탐험. 수치는 Minecraft 특화적이지만 패턴은 전송 가능하다.

### 행동 공간 = 코드

대부분의 에이전트는 기본 명령어를 출력한다. Voyager는 JavaScript 함수를 출력한다. 스킬은:

```
async function craftIronPickaxe(bot) {
  await mineIron(bot, 3);
  await mineStick(bot, 2);
  await placeCraftingTable(bot);
  await craft(bot, 'iron_pickaxe');
}
```

하위 스킬로 구성. 설명과 임베딩 키로 저장. 프롬프트가 아닌 프로그램으로 검색.

이것이 2026년 Claude Agent SDK 스킬이다: 에이전트가 요청 시 로드하는 명명되고 검색 가능한 코드 + 지시사항 청크.

### 스킬 검색

새 작업 "다이아몬드 곡괭이 만들기." 에이전트:

1. 작업 설명을 임베딩.
2. 스킬 라이브러리에서 top-k 유사 스킬 쿼리.
3. `craftIronPickaxe`, `mineDiamond`, `placeCraftingTable` 등 검색.
4. 검색된 기본 요소 + 새 로직으로 새 스킬 구성.

이것이 MCP 리소스 (Phase 13)와 Agent SDK 스킬이 구현하는 패턴이다: 지식/코드 표면에 대한 검색, 현재 작업으로 범위 지정.

### 반복적 개선

Voyager의 피드백 루프:

1. 에이전트가 스킬 작성.
2. 스킬이 환경에 대해 실행.
3. 세 가지 신호 중 하나 반환: `success`, `error` (스택 트레이스 포함), `self-verification failure`.
4. 에이전트가 신호를 컨텍스트로 사용하여 스킬 재작성.
5. 성공 또는 최대 라운드까지 반복.

이는 환경 기반 검증이 있는 코드 생성에 적용된 Self-Refine (레슨 05)이다. CRITIC (레슨 05)은 외부 도구를 검증기로 사용하는 동일한 패턴이다.

### 커리큘럼과 탐험

Voyager의 커리큘럼 모듈은 에이전트가 가진 것과 아직 하지 않은 것에 기반하여 "호수 근처에 쉼터 짓기" 같은 작업을 제안. 제안기는 환경 상태 + 스킬 인벤토리를 사용하여 현재 능력 바로 위의 작업을 선택 — 탐험의 최적 지점.

프로덕션 에이전트의 경우 이는 "무엇이 누락되었나" 연산자로 변환: 현재 스킬 라이브러리와 도메인이 주어지면 아직 다루지 않은 스킬은 무엇인가? 팀은 일반적으로 이를 커리큘럼 검토로 수동 구현한다.

### 이 패턴이 잘못되는 경우

- **스킬 라이브러리 부패.** 같은 스킬이 약간 다른 설명으로 10번 추가. 쓰기 시 중복 제거 추가; 검색은 하나만 반환.
- **구성된 스킬 드리프트.** 부모 스킬이 개선된 자식에 의존. 스킬 버전 관리; v1에 고정된 부모가 마법처럼 v3를 가져오지 않음.
- **검색 품질.** 스킬 설명에 대한 벡터 검색은 라이브러리가 수백 개를 넘으면 저하. 태그 필터와 하드 제약("`category=tooling`인 스킬만")으로 보완.

## 직접 구현하기

`code/main.py`는 stdlib 스킬 라이브러리를 구현한다:

- `Skill` — name, description, code (문자열), version, tags, dependencies.
- `SkillLibrary` — register, search (토큰 중복), compose (의존성의 위상 정렬), refine (업데이트 시 버전 범프).
- 세 가지 기본 스킬을 등록하고, 네 번째를 구성하고, 실패를 만나고, 개선하는 스크립트 기반 에이전트.

실행:

```
python3 code/main.py
```

트레이스는 라이브러리 쓰기, 검색, 구성, 실패한 실행 및 v2 개선을 보여준다 — Voyager의 루프를 처음부터 끝까지.

## 활용하기

- **Claude Agent SDK 스킬** (Anthropic) — 2026년 참조: 각 스킬에는 설명, 코드 및 지시사항이 있으며 에이전트 세션 중 요청 시 로드됨.
- **skillkit** (npm: skillkit) — 32개 이상의 AI 코딩 에이전트를 위한 교차 에이전트 스킬 관리.
- **커스텀 스킬 라이브러리** — 도메인별 (데이터 에이전트용 SQL 스킬, 인프라 에이전트용 Terraform 스킬). Voyager 패턴은 축소 가능.
- **OpenAI Agents SDK `tools`** — 낮은 수준에서 각 도구는 경량 스킬.

## 배포하기

`outputs/skill-skill-library.md`는 모든 대상 런타임에 대해 등록, 검색, 버전 관리 및 개선이 연결된 Voyager 형태의 스킬 라이브러리를 생성한다.

## 연습 문제

1. `compose()`에 의존성 사이클 감지기를 추가하라. 스킬 A가 B에 의존하고 B가 A에 의존하면 어떻게 되는가? 오류 vs 경고?
2. 스킬별 버전 고정을 구현하라. 부모 스킬이 자식 `crafting@1`을 구성할 때 `crafting@2`로의 개선이 부모를 자동 업그레이드하지 않아야 함.
3. 토큰 중복 검색을 sentence-transformers 임베딩(또는 BM25 stdlib 구현)으로 교체. 50개 스킬 장난감 라이브러리에서 retrieval@5 측정.
4. "커리큘럼" 에이전트 추가: 현재 라이브러리와 도메인 설명이 주어지면 누락된 스킬 5개 제안. 주간 실행.
5. Anthropic의 Claude Agent SDK 스킬 문서를 읽어라. 장난감 라이브러리를 SDK의 스킬 스키마로 포팅. 발견 가능성에 대해 무엇이 바뀌는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Skill | "재사용 가능한 기능" | 설명이 있는 명명된 코드 청크, 유사도로 검색 가능 |
| Skill library | "에이전트의 방법 기억" | 검색 가능하고 구성 가능한 스킬의 지속적 저장소 |
| Curriculum | "작업 제안기" | 현재 능력 격차에 의해 구동되는 상향식 목표 생성기 |
| Composition | "스킬 DAG" | 스킬이 스킬을 호출; 실행 시 위상 정렬 |
| Iterative refinement | "자체 수정 루프" | 환경 피드백 + 오류 + 자체 검증이 다음 버전으로 접힘 |
| Action-space-as-code | "프로그래밍 방식 행동" | 시간적으로 확장된 동작을 위해 기본 명령어가 아닌 함수 출력 |
| Dedup on write | "스킬 축소" | 거의 중복된 설명이 하나의 표준 스킬로 축소 |

## 추가 자료

- [Wang et al., Voyager (arXiv:2305.16291)](https://arxiv.org/abs/2305.16291) — 원본 스킬 라이브러리 논문
- [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — 2026년 제품화로서의 스킬
- [Anthropic, Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — 실제 스킬과 하위 에이전트
- [Madaan et al., Self-Refine (arXiv:2303.17651)](https://arxiv.org/abs/2303.17651) — Voyager 아래의 개선 루프
