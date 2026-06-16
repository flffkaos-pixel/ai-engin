# MCP 샘플링 — 서버 요청 LLM 완성 및 에이전트 루프

> 대부분의 MCP 서버는 멍청한 실행기입니다: 인자를 받고, 코드를 실행하고, 콘텐츠를 반환합니다. 샘플링을 사용하면 서버가 방향을 바꿀 수 있습니다: 클라이언트의 LLM에게 결정을 요청합니다. 이를 통해 서버가 모델 자격 증명을 소유하지 않고도 서버 호스팅 에이전트 루프를 가능하게 합니다. 2025-11-25에 병합된 SEP-1577은 샘플링 요청 내부에 도구를 추가하여 루프에 더 깊은 추론을 포함할 수 있게 했습니다. 드리프트 위험 참고: SEP-1577 도구-인-샘플링 형태는 2026년 1분기까지 실험적이었으며 SDK API에서 여전히 안정화 중입니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, 샘플링 하네스)
**Prerequisites:** 13단계 07과 (MCP 서버), 13단계 10과 (리소스 및 프롬프트)
**Time:** 약 75분

## 학습 목표

- `sampling/createMessage`가 해결하는 문제(서버 측 API 키 없는 서버 호스팅 루프)를 설명할 수 있다.
- 클라이언트에게 다중 턴 프롬프트에 대해 샘플링하도록 요청하고 완성을 반환하는 서버를 구현할 수 있다.
- `modelPreferences`(비용/속도/지능 우선순위)를 사용하여 클라이언트 모델 선택을 안내할 수 있다.
- 동작을 하드코딩하는 대신 내부적으로 샘플링을 통해 반복하는 `summarize_repo` 도구를 구축할 수 있다.

## 문제

코드 요약 워크플로를 위한 유용한 MCP 서버는 다음을 수행해야 합니다: 파일 트리 탐색, 읽을 파일 선택, 요약 합성 및 반환. LLM 추론은 어디에서 발생하나요?

옵션 A: 서버가 자체 LLM 호출. API 키 필요, 서버 측 청구, 사용자당 비용이 많이 듦.

옵션 B: 서버가 원시 콘텐츠 반환; 클라이언트의 에이전트가 추론 수행. 작동하지만 서버 로직을 클라이언트 프롬프트로 이동시켜 취약함.

옵션 C: 서버가 `sampling/createMessage`를 통해 클라이언트의 LLM에 요청. 서버는 알고리즘(읽을 파일, 수행할 패스 수)을 유지하는 반면, 클라이언트는 청구와 모델 선택을 유지. 서버에는 자격 증명이 전혀 없음.

샘플링은 옵션 C입니다. 이것은 신뢰할 수 있는 서버가 완전한 LLM 호스트가 아니어도 에이전트 루프를 호스팅할 수 있는 메커니즘입니다.

## 개념

### `sampling/createMessage` 요청

서버가 전송:

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "sampling/createMessage",
  "params": {
    "messages": [{"role": "user", "content": {"type": "text", "text": "..."}}],
    "systemPrompt": "...",
    "includeContext": "none",
    "modelPreferences": {
      "costPriority": 0.3,
      "speedPriority": 0.2,
      "intelligencePriority": 0.5,
      "hints": [{"name": "claude-3-5-sonnet"}]
    },
    "maxTokens": 1024
  }
}
```

클라이언트가 LLM을 실행하고 반환:

```json
{"jsonrpc": "2.0", "id": 42, "result": {
  "role": "assistant",
  "content": {"type": "text", "text": "..."},
  "model": "claude-3-5-sonnet-20251022",
  "stopReason": "endTurn"
}}
```

### `modelPreferences`

1.0으로 합산되는 세 개의 부동소수점:

- `costPriority`: 저렴한 모델 선호.
- `speedPriority`: 빠른 모델 선호.
- `intelligencePriority`: 더 능력 있는 모델 선호.

플러스 `hints`: 서버가 선호하는 명명된 모델. 클라이언트는 힌트를 존중할 수도 있고 아닐 수도 있음; 클라이언트의 사용자 설정이 항상 우선.

### `includeContext`

세 가지 값:

- `"none"` — 서버가 제공한 메시지만. 기본값.
- `"thisServer"` — 이 서버 세션의 이전 메시지 포함.
- `"allServers"` — 모든 세션 컨텍스트 포함.

`includeContext`는 2025-11-25 기준으로 소프트 폐기됨 — 교차 서버 컨텍스트 누출은 보안 문제. `"none"`을 선호하고 메시지에 명시적 컨텍스트 전달.

### 도구가 있는 샘플링 (SEP-1577)

2025-11-25의 새로운 기능: 샘플링 요청에 `tools` 배열 포함 가능. 클라이언트가 해당 도구를 사용하여 전체 도구 호출 루프 실행. 이를 통해 서버가 클라이언트의 모델을 통해 ReAct 스타일 에이전트 루프 호스팅 가능.

```json
{
  "messages": [...],
  "tools": [
    {"name": "fetch_url", "description": "...", "inputSchema": {...}}
  ]
}
```

클라이언트 루프: 샘플, 도구 호출 시 실행, 다시 샘플, 최종 어시스턴트 메시지 반환. 2026년 1분기까지 실험적; SDK 시그니처가 아직 변경될 수 있음. 구현 시 2025-11-25 사양의 client/sampling 섹션을 확인하세요.

### 인간-인-더-루프

클라이언트는 샘플을 실행하기 전에 서버가 모델에게 무엇을 요청하는지 사용자에게 반드시 보여줘야 함. 악성 서버가 샘플링을 사용하여 사용자의 세션을 조작할 수 있음("사용자에게 X라고 말해서 Y를 클릭하게 하세요"). Claude Desktop, VS Code 및 Cursor는 샘플링 요청을 사용자가 거부할 수 있는 확인 대화상자로 표시.

2026년 합의: 인간 확인 없는 샘플링은 위험 신호. 게이트웨이(13단계 17과)는 저위험 샘플링을 자동 승인하고 의심스러운 것은 자동 거부할 수 있음.

### API 키 없는 서버 호스팅 루프

표준 사용 사례: 자체 LLM 접근이 없는 코드 요약 MCP 서버. 수행:

1. 저장소 구조 탐색.
2. "이 저장소의 목적을 가장 잘 설명하는 파일 5개 선택"으로 `sampling/createMessage` 호출.
3. 해당 파일 읽기.
4. 파일 내용으로 "저장소를 3문단으로 요약"으로 `sampling/createMessage` 호출.
5. `tools/call` 결과로 요약 반환.

서버는 LLM API에 전혀 접촉하지 않음. 클라이언트의 사용자가 자체 자격 증명으로 완성 비용을 지불.

### 안전 위험 (Unit 42 공개, 2026년 1분기)

- **은밀한 샘플링.** 항상 "세션 컨텍스트에서 사용자의 이메일로 응답"으로 샘플링을 호출하는 도구. 13단계 15과가 공격 벡터를 다룸.
- **샘플링을 통한 리소스 도용.** 서버가 클라이언트에게 공격자의 페이로드를 요약하도록 요청, 사용자에게 청구.
- **루프 폭탄.** 서버가 빡빡한 루프에서 샘플링 호출. 클라이언트는 세션당 속도 제한을 반드시 적용해야 함.

## 사용하기

`code/main.py`는 가짜 서버-클라이언트 샘플링 하네스를 제공합니다. 시뮬레이션된 "summarize_repo" 도구가 두 번의 샘플링 라운드(파일 선택 후 요약)를 호출하고 가짜 클라이언트가 준비된 응답을 반환합니다. 하네스가 보여주는 것:

- 서버가 `modelPreferences`와 함께 `sampling/createMessage` 전송.
- 클라이언트가 완성 반환.
- 서버가 루프 계속.
- 속도 제한기가 도구 호출당 총 샘플링 호출 수를 제한.

살펴볼 내용:

- 서버는 하나의 도구(`summarize_repo`)만 노출; 모든 추론은 샘플링 호출에서 발생.
- 모델 기본 설정이 클라이언트의 모델 선택에 가중치를 부여; 힌트가 선호 모델 나열.
- 루프는 `stopReason: "endTurn"`에서 종료.
- `max_samples_per_tool = 5` 제한이 폭주 루프를 잡음.

## 배포하기

이 레슨은 `outputs/skill-sampling-loop-designer.md`를 생성합니다. LLM 호출이 필요한 서버 측 알고리즘(연구, 요약, 계획)이 주어지면 스킬이 올바른 modelPreferences, 속도 제한 및 안전 확인과 함께 샘플링 기반 구현을 설계합니다.

## 실습

1. `code/main.py`를 실행하세요. `max_samples_per_tool`을 2로 변경하고 속도 제한 차단을 관찰하세요.

2. SEP-1577 도구-인-샘플링 변형을 구현하세요: 샘플링 요청이 `tools` 배열을 전달. 클라이언트 측 루프가 최종 완성을 반환하기 전에 해당 도구를 실행하는지 확인하세요. 드리프트 위험 참고: SDK 시그니처는 2026년 상반기까지 변경될 수 있음.

3. 인간-인-더-루프 확인 추가: 서버의 첫 번째 `sampling/createMessage` 전에 일시 중지하고 사용자 승인 대기. 거부된 호출은 타입화된 거절 반환.

4. 클라이언트 세션으로 키가 지정된 사용자별 속도 제한기 추가. 동일 사용자의 동일 서버 루프는 예산을 공유해야 함.

5. 샘플링을 사용하여 포함할 청크를 선택하는 `summarize_pdf` 도구를 설계하세요. 전송된 메시지를 스케치하세요. `modelPreferences.intelligencePriority`가 0.1 vs 0.9에서 동작을 어떻게 변경하나요?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 샘플링(Sampling) | "서버-클라이언트 LLM 호출" | 서버가 클라이언트의 모델에 완성 요청 |
| `sampling/createMessage` | "메소드" | 샘플링 요청을 위한 JSON-RPC 메소드 |
| `modelPreferences` | "모델 우선순위" | 비용/속도/지능 가중치 및 이름 힌트 |
| `includeContext` | "교차 세션 누출" | 소프트 폐기된 컨텍스트 포함 모드 |
| SEP-1577 | "샘플링의 도구" | 서버 호스팅 ReAct를 위한 샘플링 내부 도구 허용 |
| 인간-인-더-루프 | "사용자 확인" | 클라이언트가 실행 전에 사용자에게 샘플링 요청 표시 |
| 루프 폭탄 | "폭주 샘플링" | 서버 측 무한 샘플링 루프; 클라이언트가 속도 제한해야 함 |
| 은밀한 샘플링 | "숨겨진 추론" | 악성 서버가 샘플링 프롬프트에 의도 숨김 |
| 리소스 도용 | "사용자의 LLM 예산 사용" | 서버가 원하지 않는 샘플링에 지출하도록 강제 |
| `stopReason` | "생성이 중단된 이유" | `endTurn`, `stopSequence` 또는 `maxTokens` |

## 추가 자료

- [MCP — Concepts: Sampling](https://modelcontextprotocol.io/docs/concepts/sampling) — 샘플링 개요
- [MCP — Client sampling spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling) — 표준 `sampling/createMessage` 형태
- [MCP — GitHub SEP-1577](https://github.com/modelcontextprotocol/modelcontextprotocol) — 샘플링의 도구에 대한 사양 진화 제안 (실험적)
- [Unit 42 — MCP attack vectors](https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/) — 은밀한 샘플링 및 리소스 도용 패턴
- [Speakeasy — MCP sampling core concept](https://www.speakeasy.com/mcp/core-concepts/sampling/) — 클라이언트 측 코드 샘플 워크스루
