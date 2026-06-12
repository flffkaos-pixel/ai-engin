# FIPA-ACL와 Speech Acts의 유산

> MCP 이전, A2A 이전, FIPA-ACL가 있었습니다. 2000년에 IEEE Foundation for Intelligent Physical Agents가 20개의 수행적, 2개의 콘텐츠 언어, 계약 네트워크, 구독/알림, 요청-언제 등의 상호작용 프로토콜 세트를 갖춘 에이전트 통신 언어를 비준했습니다. 온톨로지 오버헤드가 웹에서 너무 무거웠기 때문에 산업에서 사라졌지만, LLM 멀티에이전트 시스템의 부상은 형식 의미론 없이 같은 아이디어를 조용히 재구현하고 있습니다: JSON 계약이 수행적을 대신하고, 자연어가 온톨로지를 대신합니다. 이 레슨은 FIPA-ACL를 진지하게 읽어 2026 프로토콜 결정 중 어떤 것이 재발명이고, 현재 물결이 어디서 2000년대에 이미 해결된 문제를 다시 발견할지 볼 수 있게 해줍니다.

**유형:** 학습
**언어:** Python (stdlib)
**선수 과목:** Phase 16 · 01 (Why Multi-Agent)
**소요 시간:** ~60분

## 문제

2026 에이전트 프로토콜 생태계는 붐빕니다: 툴을 위한 MCP, 에이전트를 위한 A2A, 기업 감사를 위한 ACP, 분산 신뢰를 위한 ANP, 자연어 콘텐츠를 위한 NLIP, plus CA-MCP와 두 달린 연구 제안. 각 스펙은 스스로를 기반이라고 선언합니다.

정직한 해석은 그 중 대부분이 매우 구체적인 20년 된 결정 트리를 다시 발견하고 있다는 것입니다. Austin (1962)과 Searle (1969)의 speech-act 이론은 "말은 행동이다"를 우리에게 제공했습니다. KQML (1993)이 이를 와이어 프로토콜로 만들었습니다. FIPA-ACL (2000년 비준)은 참조 표준화를 산출했습니다: 20개의 수행적, 콘텐츠 언어 SL0/SL1, 계약 네트워크와 구독-알림을 위한 상호작용 프로토콜. JADE와 JACK이 Java 참조 플랫폼이었습니다. 노력은 2010년경 온톨로지 오버헤드가 너무 무거웠고 웹이 승리하면서 사라졌습니다.

MCP의 `tools/call`, A2A의 작업 수명주기, CA-MCP의 공유 컨텍스트 저장소를 볼 때, FIPA 결정의 더 부드럽고 JSON 네이티브 재해석을 보고 있는 것입니다. 유산을 알면 두 가지 일이 알려줍니다: 어떤 새로운 "혁신"이 실제로 재발명인지, 그리고 어떤 오래된 실패 모드가 새로운 스펙에서 다시 발견될지.

## 개념

### Speech acts, 한 단락으로

Austin은 일부 문장이 세계를 설명하지 않고 변경한다는 것을 주목했습니다. "약속합니다." "요청합니다." "선언합니다." 그는 이를 수행적 발화라고 불렀습니다. Searle은 5개 범주를 형식화했습니다: 주장, 지시, 약속, 표현, 선언. KQML (Finin et al., 1993)은 소프트웨어 에이전트에 이를 운영 가능하게 만들었습니다: 메시지는 수행적 (행동) plus 콘텐츠 (행동이 관련된 것)입니다. FIPA-ACL는 KQML의 격차를 정리하고 20개의 수행적 주변으로 표준화했습니다.

### 20개의 FIPA 수행적 (부분 목록)

| 수행적 | 의도 |
|---|---|
| `inform` | "P가 사실이라고 당신에게 알려줍니다" |
| `request` | "X를 하도록 당신에게 요청합니다" |
| `query-if` | "P가 사실인가?" |
| `query-ref` | "X의 값은 무엇인가?" |
| `propose` | "X를 하자고 제안합니다" |
| `accept-proposal` | "제안을 수락합니다" |
| `reject-proposal` | "제안을 거절합니다" |
| `agree` | "X를 하기로 동의합니다" |
| `refuse` | "X를 거절합니다" |
| `confirm` | "P가 사실이라고 확인합니다" |
| `disconfirm` | "P를 부인합니다" |
| `not-understood` | "당신의 메시지가 파싱되지 않았습니다" |
| `cfp` | "X에 대한 제안 요청" |
| `subscribe` | "X가 변경될 때 알림을 받습니다" |
| `cancel` | "진행 중인 X를 취소합니다" |
| `failure` | "X를 시도했지만 실패했습니다" |

전체 목록은 `fipa00037.pdf` (FIPA ACL Message Structure)에 있습니다. 요점은 외우는 것이 아니라 - 요점은 이 20개의 수행적 각각이 LLM 프로토콜이 결국 다시 추가하는 기본 요소에 해당한다는 것입니다.

### 표준 FIPA-ACL 메시지

```
(inform
  :sender       agent1@platform
  :receiver     agent2@platform
  :content      "((price IBM 83))"
  :language     SL0
  :ontology     finance
  :protocol     fipa-request
  :conversation-id   conv-42
  :reply-with   msg-17
)
```

7개 필드가 프로토콜 엔벨로프를 전달합니다; 하나의 필드 (`content`)가 페이로드를 전달합니다. 나머지 필드는 JSON 프로토콜에 재시도, 스레딩, 온톨로지를 붙일 때마다 매번 재발명하는 것과 정확히 같습니다.

### 두 개의 레거시 플랫폼

**JADE** (Java Agent DEvelopment framework, 1999–2020s)는 가장 많이 사용된 FIPA 준수 런타임이었습니다. 에이전트가 기본 클래스를 확장하고, ACL 메시지를 교환하고, 컨테이너 내에서 실행되고, "비헤이비어"를 사용하여 조정했습니다. 상호작용-프로토콜 라이브러리에는 계약 네트워크, 구독-알림, 요청-언제, 제안-수락이 포함되었습니다.

**JACK** (Agent Oriented Software, 상업용)은 FIPA 메시지 위에 BDI (Belief-Desire-Intention) 추론을 강조했습니다. 더 형식적이고 덜 채택되었습니다.

둘 다 웹 스택이 멀티에이전트 사용 사례를 집어삼켰습니다. MCP와 A2A가 2026의 런타임 "컨테이너"입니다.

### FIPA가 사라진 이유

- **온톨로지 오버헤드.** FIPA는 `content`를 파싱하기 위해 공유 온톨로지를 필요로 했습니다. 온톨로지에 동의하는 것은 수년간의 표준화 과정입니다. 웹은 단순히 HTTP + JSON을 사용했습니다.
- **사용되지 않은 형식 의미론.** SL (Semantic Language)은 엄밀한 진리 조건을 제공했지만, 대부분의 프로덕션 시스템은 형식주의를 무시하고 자유형식 콘텐츠를 사용했습니다.
- **도구 잠금.** JADE는 Java 전용이었습니다; JACK은 상업용이었습니다. 다국어 팀이 둘 다 우회했습니다.
- **인터넷이 스택에서 승리했습니다.** REST, then JSON-RPC, then gRPC가 ACL의 전송을 대체했습니다.

### LLM 부흥은 FIPA-lite입니다

FIPA `request`를 MCP `tools/call`과 비교합니다:

```
(request                                {
  :sender  agent1                         "jsonrpc": "2.0",
  :receiver tool-server                   "method":  "tools/call",
  :content "(lookup stock IBM)"            "params":  {"name":"lookup_stock",
  :ontology finance                                     "arguments":{"symbol":"IBM"}},
  :conversation-id c42                    "id": 42
)                                        }
```

동일한 엔벨로프, 다른 구문. 둘 다: 누가, 누구에게, 의도, 페이로드, 상관관계 ID를 전달합니다. 하나가 다른 것보다 혁신적인 것이 아닙니다 - 동일한 설계에 대한 다른 트레이드오프입니다.

2025년 Liu et al. 조사 ("A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, ANP", arXiv:2505.02279)가 이 계보학을 명시적으로 만들었습니다: MCP는 툴 사용 speech acts에 해당하고, A2A는 에이전트-피어 speech acts에 해당하고, ACP는 감사-추적 speech acts에 해당하고, ANP는 분산 ID 확장에 해당합니다. 새로운 스펙은 JSON 구문과 느슨한 의미론을 가진 ACL 후손입니다.

### 트레이드오프, 명확하게陈述

**FIPA가 제공한 것과 현대 스펙이 드롭한 것:**

- 형식 의미론 — `inform`이 송신자가 콘텐츠를 믿는다는 것을 증명할 수 있습니다.
- 수행적의 표준 카탈로그 — `cancel`이 있어야 하는지에 대해 재논의할 필요가 없습니다.
- 수십 년의 상호작용-프로토콜 패턴 — 알려진 정확성 속성을 가진 계약 네트워크, 구독-알림, 제안-수락.

**현대 스펙이 제공한 것과 FIPA가 제공하지 않은 것:**

- 모든 현대 도구와 호환되는 JSON 네이티브 페이로드.
-手書き 온톨로지 없이 LLMs가 해석할 수 있는 자연어 콘텐츠.
- 웹 스택 전송 (HTTP, SSE, WebSocket).
- 자체 기술 문서 (MCP `listTools`, A2A Agent Card)를 통한 기능 검색.

구현을 더 쉽게하기 위한 느슨한 의도 의미론. 이것이 정확한 거래입니다.

### 이전할 가치가 있는 상호작용 프로토콜

FIPA는 ~15개의 상호작용 프로토콜을 제공했습니다. 3개는 LLM 멀티에이전트 시스템으로 이전할 가치가 있습니다:

1. **계약 네트워크 프로토콜 (CNP).** 관리자가 `cfp` (제안 요청)를 발행합니다; 입찰자가 `propose`로 응답합니다; 관리자가 수락/거절합니다. 이것은 표준 작업 시장 패턴입니다 (Phase 16 · 16 Negotiation).
2. **구독/알림.** 구독자가 `subscribe`를 보냅니다; 게시자가 주제가 변경될 때마다 `inform`을 보냅니다. 이것은 2026의 모든 이벤트 버스입니다.
3. **요청-언제.** "조건 Y가 유지될 때 X를 수행합니다." 전제 조건이 있는 지연 작업. 2026 analogy는 지속적 워크플로 엔진의 지연된 작업입니다 (Phase 16 · 22 Production Scaling).

각각은 최신 메시지 큐, HTTP + 폴링, 또는 SSE 스트리밍에 깔끔하게 매핑됩니다.

### 온톨로지를 드롭할 때 무엇이 망가집니다

공유 온톨로지 없이는 에이전트가 자연어 콘텐츠에서 의미를 추론합니다. 문서화된 2026 실패 모드는 **의미론적 드리프트**입니다: 두 에이전트가 같은 단어 (`"customer"`)를 미묘하게 다른 개념에 사용하고, 수신자 에이전트가 잘못된 해석에 따라 행동하며, 스키마 검증기가 그것을 포착하지 않습니다. FIPA의 온톨로지 요구사항은 파싱 시간에 메시지를 거부했을 것입니다.

완전한 온톨로지로 가지 않고 완화하는 방법:

- `content` 필드에 대한 JSON Schema — 와이어에서 구조적 오류를 거부합니다.
- 형식화된 아티팩트 (A2A) — 잘못된 양식식을 거부합니다.
- 엔벨로프의 명시적 수행적 — 콘텐츠가 자연어여도 의도를 명확하게 합니다.

### 2026 스펙, speech act 유산에 매핑

| 현대 스펙 | FIPA analogy | 유지하는 것 | 드롭하는 것 |
|---|---|---|---|
| MCP `tools/call` | `request` | 명시적 의도, 상관관계 ID | 형식 의미론, 온톨로지 |
| MCP `resources/read` | `query-ref` | 명시적 의도, 상관관계 ID | 형식 의미론 |
| A2A 작업 수명주기 | 계약 네트워크 + 요청-언제 | 비동기 수명주기, 상태 전환 | 형식적 완전성 보장 |
| A2A 스트리밍 이벤트 | 구독/알림 | 비동기 푸시 | 형식화된 조건부 구독 |
| CA-MCP 공유 컨텍스트 | 블랙보드 (Hayes-Roth 1985) | 다중 작성자 공유 메모리 | 논리적 일관성 모델 |
| NLIP | 자연어 콘텐츠 | LLM 네이티브 | 스키마 |

표를 위에서 아래로 읽으면 패턴이 있습니다: 구조적 기본 요소를 유지하고, 형식주의를 드롭하고, LLMs가 모호함을 덮습니다.

## 실습

`code/main.py`는 순수 stdlib FIPA-ACL 번역기를 구현합니다. 표준 ACL 엔벨로프를 인코딩 및 디코딩하고 모든 MCP / A2A 메시지 형태가 동일한 7개 필드로 감소하는 것을 보여줍니다. 데모:

- 5개의 MCP 스타일 및 A2A 스타일 메시지를 FIPA-ACL로 인코딩합니다.
- FIPA-ACL를 현대 등가물로 디코딩합니다.
- `cfp`, `propose`, `accept-proposal`, `reject-proposal`을 사용하여 하나의 관리자와 세 입찰자 간의toy 계약 네트워크 협상을 실행합니다.

실행:

```
python3 code/main.py
```

출력은 각 현대 메시지를 2026 JSON 형태와 FIPA-ACL 형태 모두로 보여주는 나란한 추적이며, 그 다음 계약 네트워크 입찰의 라운드트립입니다. 동일한 프로토콜 기본 요소가 라운드트립에서 생존합니다; 구문만 다릅니다.

## 활용

`outputs/skill-fipa-mapper.md`는 모든 에이전트-프로토콜 스펙을 읽고 FIPA-ACL 매핑을 생성하는 스킬입니다. 새로운 프로토콜을 채택하기 전에 사용하여: "이것이 실제로 새로운 것인지, 아니면 JSON 구문이 있는 `inform`인지" 답변합니다.

## 결과물

FIPA-ACL를 되가져오지 마세요. 되가져올 것은 체크리스트입니다:

- 각 메시지의 의도 기본 요소 (수행적)是什么?
- 요청-응답 및 취소를 위한 상관관계 ID가 있습니까?
- 명시적 콘텐츠 언어 (JSON-RPC, 일반 텍스트, 구조화된 형식화된 아티팩트)가 있습니까?
- 상호작용 프로토콜이 1순위인가, 아니면 계약 네트워크를 처음부터 재구현하고 있는 건가?
- 두 에이전트가 콘텐츠 의미에 동의하지 않을 때 어떻게 되는가 (의미론적 드리프트)?

새 프로토콜을 프로덕션에 배송하기 전에 이 5가지 질문을 문서화하세요.

## 연습 문제

1. `code/main.py`를 실행합니다. 라운드트립 인코딩을 관찰합니다. 어떤 FIPA 수행적이 `tools/call`, `resources/read`, A2A 작업 생성에 해당하는지 식별합니다.
2. 관리자가 입찰 중기에 작업을 철회할 수 있는 `cancel` 수행적으로 계약 네트워크 데모를 확장합니다. `cancel`이 재시도만으로 해결하지 않는 어떤 실패 사례를 해결합니까?
3. FIPA ACL Message Structure (http://www.fipa.org/specs/fipa00037/) 섹션 4.1–4.3을 읽습니다. 이 레슨에서 다루지 않은 하나의 수행적을 선택하고 그 현대 JSON-RPC analogy를 설명합니다.
4. Liu et al., arXiv:2505.02279를 읽습니다. MCP, A2A, ACP, ANP 각각에 대해 유지하고 드롭하는 FIPA 수행적 제품군을 나열합니다.
5. 자체 시스템에서 `request` 수행적의 `content` 필드에 대한 최소한의 JSON-Schema를 설계합니다. 그 스키마가 순수 자연어에서 제공하는 것과 제공하지 않는 것은 무엇이며, 비용은 무엇입니까?

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|------------------------|
| Speech act | "무언가를 하는 발화" | Austin/Searle: 행위로서의 발화. ACL의 이론적 부모. |
| FIPA | "그 오래된 XML 것" | IEEE Foundation for Intelligent Physical Agents. 2000년 ACL을 표준화했습니다. |
| ACL | "Agent Communication Language" | FIPA의 엔벨로프 형식: 수행적 + 콘텐츠 + 메타데이터. |
| 수행적 | "동사" | 메시지의 의도 클래스: `inform`, `request`, `propose`, `cfp` 등. |
| KQML | "FIPA의 선행자" | Knowledge Query and Manipulation Language (1993). 더 단순하고 좁습니다. |
| 온톨로지 | "공유 어휘" | 콘텐츠 언어가 이야기하는 개념의 형식적 정의. |
| SL0 / SL1 | "FIPA 콘텐츠 언어" | 의미론적 언어 레벨 0과 1 — 형식적 콘텐츠 언어 제품군. |
| 계약 네트워크 | "작업 시장" | 관리자가 cfp를 발행합니다; 입찰자가 제안합니다; 관리자가 수락합니다. 표준 상호작용 프로토콜. |
| 상호작용 프로토콜 | "메시지 패턴" | 알려진 정확성을 가진 수행적 시퀀스: 요청-언제, 구독-알림 등. |

## 추가 자료

- [Liu et al. — 에이전트 상호운용성 프로토콜 조사: MCP, ACP, A2A, ANP](https://arxiv.org/html/2505.02279v1) - 현대 스펙을 FIPA 유산에 연결하는 표준 2025 조사
- [FIPA ACL Message Structure Specification (fipa00037)](http://www.fipa.org/specs/fipa00037/) - 비준된 2000년 엔벨로프 형식
- [FIPA Communicative Act Library Specification (fipa00037)](http://www.fipa.org/specs/fipa00037/) - 완전한 수행적 카탈로그
- [MCP specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) - `request`/`query-ref`의 현대적 툴 사용 equivalent
- [A2A specification](https://a2a-protocol.org/latest/specification/) - 계약 네트워크와 구독-알림의 현대적 에이전트-피어 equivalent