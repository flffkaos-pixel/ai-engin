# A2A — 에이전트-에이전트 프로토콜

> MCP는 에이전트-도구입니다. A2A(Agent2Agent)는 에이전트-에이전트 — 다른 프레임워크로 구축된 불투명한 에이전트가 협업할 수 있게 하는 개방형 프로토콜입니다. 2025년 4월 Google이 발표하고, 2025년 6월 Linux Foundation에 기증되었으며, 2026년 4월 AWS, Cisco, Microsoft, Salesforce, SAP, ServiceNow를 포함한 150개 이상의 지지자와 함께 v1.0에 도달했습니다. IBM의 ACP를 흡수하고 AP2 결제 확장을 추가했습니다. 이 레슨은 Agent Card, Task 라이프사이클 및 두 가지 전송 바인딩을 살펴봅니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, Agent Card + Task 하네스)
**Prerequisites:** 13단계 06과 (MCP 기초), 13단계 08과 (MCP 클라이언트)
**Time:** 약 75분

## 학습 목표

- 에이전트-도구(MCP)와 에이전트-에이전트(A2A) 사용 사례를 구분할 수 있다.
- `/.well-known/agent.json`에 스킬 및 엔드포인트 메타데이터와 함께 Agent Card를 게시할 수 있다.
- Task 라이프사이클(submitted → working → input-required → completed / failed / canceled / rejected)을 설명할 수 있다.
- Parts(텍스트, 파일, 데이터)와 Artifacts를 출력으로 사용하는 Messages를 사용할 수 있다.

## 문제

고객 서비스 에이전트가 보고서 작성을 전문 작가 에이전트에 위임해야 합니다. A2A 이전의 옵션:

- 커스텀 REST API. 작동하지만 모든 페어링이 일회성.
- 공유 코드베이스. 두 에이전트가 동일한 프레임워크를 실행해야 함.
- MCP. 맞지 않음: MCP는 도구 호출용이지, 각 에이전트의 불투명한 내부 추론을 보존하면서 두 에이전트가 협업하는 것이 아님.

A2A가 격차를 메웁니다. 상호작용을 한 에이전트가 다른 에이전트에 Task를 전송하는 것으로 모델링하며, 라이프사이클, 메시지 및 아티팩트가 있습니다. 호출된 에이전트의 내부 상태는 불투명하게 유지 — 호출자는 작업 상태 전환과 최종 출력만 봅니다.

A2A는 "프레임워크 간 에이전트가 서로 대화할 수 있게 하는" 프로토콜입니다. MCP를 대체하지 않습니다; 둘은 상호 보완적입니다.

## 개념

### Agent Card

모든 A2A 호환 에이전트는 `/.well-known/agent.json`에 카드를 게시:

```json
{
  "schemaVersion": "1.0",
  "name": "research-agent",
  "description": "학술 논문을 요약하고 인용을 초안 작성합니다.",
  "url": "https://research.example.com/a2a",
  "version": "1.2.0",
  "skills": [
    {
      "id": "summarize_paper",
      "name": "논문 요약",
      "description": "논문 PDF를 읽고 3문단 요약을 생성합니다.",
      "inputModes": ["text", "file"],
      "outputModes": ["text", "artifact"]
    }
  ],
  "capabilities": {"streaming": true, "pushNotifications": true}
}
```

검색은 URL 기반: 카드를 가져오고, A2A 엔드포인트의 URL을 배우고, 스킬을 열거.

### 서명된 Agent Cards (AP2)

AP2 확장(2025년 9월)은 Agent Cards에 암호학적 서명을 추가. 게시자가 JWT로 자체 카드 서명; 소비자가 확인. 사칭 방지.

### Task 라이프사이클

```
submitted -> working -> completed | failed | canceled | rejected
             -> input_required -> working (메시지를 통한 루프)
```

클라이언트가 `tasks/send`로 시작. 호출된 에이전트가 상태를 전환; 클라이언트가 SSE 또는 폴링을 통해 상태 업데이트 구독.

### Messages와 Parts

메시지는 하나 이상의 Parts를 전달:

- `text` — 일반 콘텐츠.
- `file` — mimeType이 있는 base64 blob.
- `data` — 타입화된 JSON 페이로드(호출된 에이전트용 구조화된 입력).

예:

```json
{
  "role": "user",
  "parts": [
    {"type": "text", "text": "이 논문을 요약해줘."},
    {"type": "file", "file": {"name": "paper.pdf", "mimeType": "application/pdf", "bytes": "..."}},
    {"type": "data", "data": {"targetLength": "3 paragraphs"}}
  ]
}
```

### Artifacts

출력은 Artifacts이며, 원시 문자열이 아님. Artifact는 명명된, 타입화된 출력:

```json
{
  "name": "summary",
  "parts": [{"type": "text", "text": "..."}],
  "mimeType": "text/markdown"
}
```

Artifacts는 청크로 스트리밍 가능. 호출자가 누적.

### 두 가지 전송 바인딩

1. **HTTP를 통한 JSON-RPC.** `/a2a` 엔드포인트, POST는 요청용, 선택적 SSE는 스트리밍용. 기본 바인딩.
2. **gRPC.** gRPC가 네이티브인 엔터프라이즈 환경용.

두 바인딩 모두 동일한 논리적 메시지 형태를 전달.

### 불투명성 보존

핵심 설계 원칙: 호출된 에이전트의 내부 상태는 불투명. 호출자는 작업 상태와 아티팩트를 봄. 호출된 에이전트의 사고 사슬, 도구 호출, 하위 에이전트 위임 — 모두 보이지 않음. 이것은 도구 호출이 투명한 MCP와 다름.

근거: A2A는 경쟁사가 내부를 공개하지 않고 협업할 수 있게 함. A2A는 호출자가 해당 에이전트가 서비스를 구현하는 방법을 배우지 않고 "이 고객 서비스 에이전트를 호출"할 수 있음.

### 타임라인

- **2025-04-09.** Google이 A2A 발표.
- **2025-06-23.** Linux Foundation에 기증.
- **2025-08.** IBM의 ACP 흡수.
- **2025-09.** AP2 확장(Agent Payments) 출시.
- **2026-04.** 150개 이상의 지원 조직과 함께 v1.0 출시.

### MCP와의 관계

| 차원 | MCP | A2A |
|-----------|-----|-----|
| 사용 사례 | 에이전트-도구 | 에이전트-에이전트 |
| 불투명성 | 투명한 도구 호출 | 불투명한 내부 추론 |
| 일반적 호출자 | 에이전트 런타임 | 다른 에이전트 |
| 상태 | 도구 호출 결과 | 라이프사이클이 있는 Task |
| 권한 부여 | OAuth 2.1 (13단계 16과) | JWT 서명 Agent Cards (AP2) |
| 전송 | Stdio / Streamable HTTP | HTTP / gRPC를 통한 JSON-RPC |

특정 도구를 호출하려면 MCP 사용. 전체 작업을 다른 에이전트에 위임하려면 A2A 사용. 많은 프로덕션 시스템이 둘 다 사용: 에이전트는 도구 계층에 MCP를, 협업 계층에 A2A를 사용.

## 사용하기

`code/main.py`는 최소 A2A 하네스 구현: 연구 에이전트가 카드 게시, 작가 에이전트가 PDF와 텍스트 명령을 포함한 parts와 함께 `tasks/send`를 수신, working → input_required → working → completed로 전이, 텍스트 아티팩트 반환. 모두 표준 라이브러리; 메시지 형태에 집중하기 위해 인메모리 전송 사용.

살펴볼 내용:

- Agent Card JSON 형태.
- Task id 할당 및 상태 전이.
- 혼합 타입 parts가 있는 Messages.
- 작업 중간의 Input-required 분기.
- 완료 시 Artifact 반환.

## 배포하기

이 레슨은 `outputs/skill-a2a-agent-spec.md`를 생성합니다. 다른 에이전트가 호출할 수 있어야 하는 새 에이전트가 주어지면 스킬이 Agent Card JSON, 스킬 스키마 및 엔드포인트 청사진을 생성합니다.

## 실습

1. `code/main.py`를 실행하세요. 호출된 에이전트가 명확화를 요청하는 input-required 일시 중지를 포함한 전체 Task 라이프사이클을 추적하세요.

2. 서명된 Agent Card를 추가하세요. 카드의 표준 JSON에 대해 HMAC으로 서명. 검증기를 작성하고 변이된 카드에서 실패하는지 확인하세요.

3. 작업 스트리밍 구현: 작가 에이전트가 SSE를 통해 세 개의 증분 아티팩트 청크를 출력하고 호출자가 누적.

4. MCP 서버를 래핑하는 A2A 에이전트를 설계하세요. 각 MCP 도구를 A2A 스킬에 매핑. 트레이드오프를 기록 — 어떤 불투명성이 손실되나요?

5. A2A v1.0 발표를 읽고 2026년 4월 기준 어떤 프레임워크도 아직 구현하지 않은 기능을 식별하세요. (힌트: 다중 홉 작업 위임 관련.)

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| A2A | "Agent-to-Agent 프로토콜" | 불투명한 에이전트 협업을 위한 개방형 프로토콜 |
| Agent Card | "`.well-known/agent.json`" | 에이전트의 스킬과 엔드포인트를 설명하는 게시된 메타데이터 |
| 스킬(Skill) | "호출 가능한 단위" | 에이전트가 지원하는 명명된 작업(MCP 도구에 해당) |
| Task | "위임 단위" | 라이프사이클과 최종 아티팩트가 있는 작업 항목 |
| 메시지(Message) | "Task 입력" | Parts(텍스트, 파일, 데이터) 전달 |
| Part | "타입화된 청크" | 메시지의 `text` / `file` / `data` 요소 |
| Artifact | "Task 출력" | 완료 시 반환되는 명명된, 타입화된 출력 |
| AP2 | "Agent Payments Protocol" | 신뢰 및 결제를 위한 서명된 Agent Cards 확장 |
| 불투명성(Opacity) | "블랙박스 협업" | 호출된 에이전트의 내부가 호출자에게 숨겨짐 |
| Input-required | "Task 일시 중지" | 에이전트가 더 많은 정보가 필요할 때의 라이프사이클 상태 |

## 추가 자료

- [a2a-protocol.org](https://a2a-protocol.org/latest/) — 표준 A2A 사양
- [a2aproject/A2A — GitHub](https://github.com/a2aproject/A2A) — 참조 구현 및 SDK
- [Linux Foundation — A2A launch press release](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents) — 2025년 6월 거버넌스 이전
- [Google Cloud — A2A protocol upgrade](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade) — 로드맵 및 파트너 모멘텀
- [Google Dev — A2A 1.0 milestone](https://discuss.google.dev/t/the-a2a-1-0-milestone-ensuring-and-testing-backward-compatibility/352258) — v1.0 릴리스 노트 및 이전 버전 호환 지침
