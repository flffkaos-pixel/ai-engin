# 브라우저 에이전트 및 장기 실행 웹 작업

> ChatGPT 에이전트(2025년 7월)는 Operator와 딥 리서치를 하나의 브라우저/터미널 에이전트로 통합하고 BrowseComp SOTA를 68.9%로 설정했다. OpenAI는 2025년 8월 31일 Operator를 종료했다 — 제품 계층에서의 통합. Anthropic의 Vercept 인수는 OSWorld에서 Claude Sonnet을 15% 미만에서 72.5%로 끌어올렸다. WebArena-Verified(ServiceNow, ICLR 2026)는 원본 WebArena의 11.3%포인트 거짓 음성률을 수정하고 258개 작업 Hard 하위 집합을 출시했다. 수치는 실제다. 공격 표면도 마찬가지다: OpenAI의 준비 책임자는 브라우저 에이전트에 대한 간접 프롬프트 인젝션이 "완전히 패치될 수 없는 버그"라고 공개적으로 밝혔다. 문서화된 2025-2026 공격: Tainted Memories(Atlas CSRF), HashJack(Cato Networks), Perplexity Comet의 원클릭 하이재킹.

**Type:** 학습
**Languages:** Python (stdlib, indirect prompt-injection attack surface model)
**Prerequisites:** Phase 15 · 10 (권한 모드), Phase 15 · 01 (장기 실행 에이전트)
**Time:** ~45분

## 문제

브라우저 에이전트는 신뢰할 수 없는 콘텐츠를 읽고 결과적인 작업을 수행하는 장기 실행 에이전트다. 에이전트가 방문하는 모든 페이지는 사용자가 작성하지 않은 입력이다. 모든 페이지의 모든 양식은 잠재적인 명령 채널이다. 2025-2026년 공격 사례는 이것이 가상이 아님을 보여준다: Tainted Memories는 공격자가 제작된 페이지를 통해 에이전트의 메모리에 악성 명령어를 바인딩할 수 있게 한다; HashJack은 에이전트가 방문하는 URL 프래그먼트에 명령어를 숨긴다; Perplexity Comet 하이재킹은 한 번의 클릭으로 발생한다.

방어 상황은 불편하다. OpenAI의 준비 책임자는 조용히 하던 말을 공개적으로 했다: 간접 프롬프트 인젝션은 "완전히 패치될 수 없는 버그"다. 이는 공격이 에이전트의 읽기-대-행동 경계에 존재하기 때문이며, 이는 아키텍처적으로 모호하다 — 모델이 읽는 모든 토큰은 원칙적으로 명령어로 읽힐 수 있다.

이 레슨은 공격 표면을 명명하고, 벤치마크 현황(BrowseComp, OSWorld, WebArena-Verified)을 명명하며, 레슨 14와 18에서 실제 방어에 대해 추론할 수 있도록 최소 간접 프롬프트 인젝션 시나리오를 모델링한다.

## 개념

### 2026년 현황, 시스템별 한 문단

**ChatGPT 에이전트(OpenAI).** 2025년 7월 출시. Operator(브라우징)와 딥 리서치(다시간 연구) 통합. 2025년 8월 31일 독립형 Operator 종료. BrowseComp에서 SOTA 68.9%; OSWorld 및 WebArena-Verified에서 강력한 수치.

**Claude Sonnet + Vercept(Anthropic).** Anthropic의 Vercept 인수는 컴퓨터 사용 기능에 초점을 맞췄다. OSWorld에서 Claude Sonnet을 <15%에서 72.5%로 이동. Claude Computer Use는 도구 API로 제공.

**Gemini 3 Pro with Browser Use(DeepMind).** Browser Use 통합이 컴퓨터 사용 제어를 제공; FSF v3(2026년 4월, 레슨 20)는 특히 ML R&D 도메인에서 자율성을 추적.

**WebArena-Verified(ServiceNow, ICLR 2026).** 잘 문서화된 문제를 수정: 원본 WebArena는 ~11.3% 거짓 음성률(실제로 해결되었지만 실패로 표시된 작업)을 가졌다. Verified 릴리스는 인간이 선별한 성공 기준으로 재채점하고 258개 작업 Hard 하위 집합을 추가한다(ICLR 2026 논문, openreview.net/forum?id=94tlGxmqkN).

### BrowseComp vs OSWorld vs WebArena

| 벤치마크 | 측정 내용 | 지평 |
|---|---|---|
| BrowseComp | 시간 압박 하에 공개 웹에서 특정 사실 찾기 | 분 |
| OSWorld | 전체 데스크톱(마우스, 키보드, 셸) 작동하는 에이전트 | 수십 분 |
| WebArena-Verified | 시뮬레이션 사이트에서 트랜잭션 웹 작업 | 분 |
| Hard 하위 집합 | 다중 페이지 상태 전환이 있는 WebArena-Verified 작업 | 수십 분 |

다른 축이다. 높은 BrowseComp 점수는 에이전트가 사실을 찾는다는 의미이지, 항공권을 예약할 수 있다는 의미는 아니다. OSWorld 점수는 "데스크톱에서 작동하는가"에 더 가깝다. WebArena-Verified는 "흐름을 완료할 수 있는가"에 더 가깝다. 모든 프로덕션 결정은 작업 분포와 일치하는 벤치마크가 필요하다.

### 공격 표면, 명명

1. **간접 프롬프트 인젝션.** 신뢰할 수 없는 페이지 콘텐츠에 명령어가 포함되어 있다. 에이전트가 읽는다. 에이전트가 실행한다. 공개 예시: 2024 Kai Greshake et al., 2025 Tainted Memories 논문, 2026 HashJack(Cato Networks).
2. **URL 프래그먼트/쿼리 인젝션.** 크롤링된 URL의 `#fragment` 또는 쿼리 문자열에 명령어가 포함되어 있다. 시각적으로 렌더링되지 않음; 여전히 에이전트의 컨텍스트 내에 있음.
3. **메모리 바인딩 공격.** 페이지가 에이전트에게 지속적 메모리(레슨 12는 지속 상태를 다룸)를 작성하도록 지시. 다음 세션에서 메모리가 가시적 트리거 없이 페이로드를 발사.
4. **인증된 세션에 대한 CSRF 형태 공격.** Tainted Memories 클래스: 에이전트가 어딘가에 로그인되어 있음; 공격자의 페이지가 사용자의 쿠키로 에이전트가 실행하는 상태 변경 요청을 발행.
5. **원클릭 하이재킹.** 시각적으로 무해한 버튼이 에이전트가 따르는 페이로드를 탑재. Comet 클래스.
6. **에이전트 호스트 표면의 CSP 구멍.** 렌더링 및 도구 계층 자체가 공격 벡터가 될 수 있음; 브라우저-인-브라우저-에이전트 스택은 넓음.

### "완전히 패치 불가능"한 이유

공격은 에이전트의 역량과 동형이다. 에이전트는 작업을 수행하기 위해 신뢰할 수 없는 콘텐츠를 읽어야 한다. 에이전트가 읽는 모든 콘텐츠에는 명령어가 포함될 수 있다. 에이전트가 따르는 모든 명령어는 사용자의 실제 요청과 일치하지 않을 수 있다. 방어(신뢰 경계, 분류기, 도구 허용 목록, 결과적 작업에 대한 HITL)는 공격의 비용을 높이고 폭발 반경을 줄인다. 클래스를 닫지 않는다.

이는 Lob의 정리(레슨 8)와 동일한 추론 패턴이다: 에이전트는 다음 토큰이 안전하다는 것을 증명할 수 없다; 안전하지 않은 토큰이 더 탐지 가능하도록 시스템을 설정할 수 있을 뿐이다.

### 실제로 출시되는 방어 태세

- **읽기/쓰기 경계.** 읽기는 절대 결과적이지 않다. 쓰기(양식 제출, 콘텐츠 게시, 부작용이 있는 도구 호출)는 시작 콘텐츠가 신뢰 경계 외부에서 온 경우 새로운 인간 승인이 필요하다.
- **작업별 도구 허용 목록.** 에이전트는 탐색할 수 있다; 해당 도구가 작업에 명시적으로 활성화되지 않는 한 송금을 시작할 수 없다. 레슨 13은 예산을 다룬다.
- **세션 격리.** 브라우저 에이전트 세션은 범위가 제한된 자격 증명만으로 실행된다. 프로덕션 인증 없음, 개인 이메일 없음. 모든 HTTP 요청의 로그가 감사용으로 유지된다.
- **콘텐츠 위생 처리.** 가져온 HTML은 모델 컨텍스트에 연결되기 전에 알려진 나쁜 패턴이 제거된다. (쉬운 공격을 줄임; 정교한 페이로드는 막지 못함.)
- **결과적 작업에 대한 HITL.** 제안-후-커밋 패턴(레슨 15).
- **메모리상 카나리 토큰.** 메모리 항목이 발사되면 사용자가 이를 본다(레슨 14).

## 사용하기

`code/main.py`는 세 개의 합성 페이지에 대한 작은 브라우저 에이전트 실행을 모델링한다. 한 페이지는 양성, 하나는 가시 텍스트에 직접 프롬프트 인젝션 블롭이 있고, 하나는 URL-프래그먼트 인젝션(보이지 않지만 에이전트의 컨텍스트 내)이 있다. 스크립트는 (a) 순진한 에이전트가 할 일, (b) 읽기/쓰기 경계가 잡는 것, (c) 위생 처리기가 잡는 것, (d) 둘 다 잡지 못하는 것을 보여준다.

## 출시하기

`outputs/skill-browser-agent-trust-boundary.md`는 제안된 브라우저 에이전트 배포의 범위를 지정한다: 닿는 신뢰 영역, 쓰기 권한이 있는 것, 첫 실행 전에 갖추어야 할 방어.

## 연습문제

1. `code/main.py`를 실행하라. 위생 처리기가 잡지만 읽기/쓰기 경계가 잡지 못하는 공격과 읽기/쓰기 경계만 잡는 공격을 식별하라.

2. HashJack 스타일 URL-프래그먼트 인젝션의 한 클래스를 감지하도록 위생 처리기를 확장하라. 합법적인 프래그먼트가 있는 양성 URL에 대한 거짓 양성률을 측정하라.

3. 아는 실제 브라우저 에이전트 워크플로우(예: "항공권 예약")를 하나 골라라. 모든 읽기와 모든 쓰기를 나열하라. 어떤 쓰기에 HITL이 필요한지와 그 이유를 표시하라.

4. WebArena-Verified ICLR 2026 논문을 읽어라. 원본 WebArena의 채점이 신뢰할 수 없었던 작업 범주 하나를 식별하고 Verified 하위 집합이 이를 어떻게 해결하는지 설명하라.

5. 브라우저 에이전트 설정을 위한 메모리 카나리를 설계하라. 무엇을, 어디에 저장하고, 무엇이 경보를 트리거하는가?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|---|---|---|
| 간접 프롬프트 인젝션 (Indirect prompt injection) | "나쁜 페이지 텍스트" | 에이전트가 읽는 페이지의 신뢰할 수 없는 콘텐츠에 에이전트가 실행하는 명령어 포함 |
| Tainted Memories | "메모리 공격" | 에이전트가 공격자 제공 명령어를 지속적 메모리에 작성; 다음 세션에서 트리거 |
| HashJack | "URL 프래그먼트 공격" | URL 프래그먼트/쿼리 문자열에 숨겨진 페이로드가 에이전트의 컨텍스트에 있지만 시각적으로 렌더링되지 않음 |
| 원클릭 하이재킹 (One-click hijack) | "나쁜 버튼" | 가시적 어포던스가 에이전트가 실행하는 후속 페이로드를 탐 |
| BrowseComp | "웹 검색 벤치마크" | 공개 웹에서 특정 사실 찾기; 분 단위 지평 |
| OSWorld | "데스크톱 벤치마크" | 전체 OS 제어; 다단계 GUI 작업 |
| WebArena-Verified | "수정된 웹 작업 벤치마크" | ServiceNow의 재채점된 WebArena with Hard 하위 집합 |
| 읽기/쓰기 경계 (Read/write boundary) | "부작용 게이트" | 읽기는 절대 결과적이지 않음; 콘텐츠가 신뢰 외부인 경우 쓰기는 새로운 승인 필요 |

## 추가 읽을거리

- [OpenAI — Introducing ChatGPT agent](https://openai.com/index/introducing-chatgpt-agent/) — Operator와 딥 리서치의 통합; BrowseComp SOTA.
- [OpenAI — Computer-Using Agent](https://openai.com/index/computer-using-agent/) — Operator 계통 및 ChatGPT 에이전트가 된 아키텍처.
- [Zhou et al. — WebArena](https://webarena.dev/) — 원본 벤치마크.
- [WebArena-Verified (OpenReview)](https://openreview.net/forum?id=94tlGxmqkN) — ICLR 2026 수정 하위 집합 논문.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — 컴퓨터 사용 에이전트에 대한 공격 표면 논의 포함.
