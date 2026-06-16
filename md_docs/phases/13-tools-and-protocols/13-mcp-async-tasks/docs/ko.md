# 비동기 Tasks (SEP-1686) — 장기 실행 작업을 위한 지금 호출, 나중에 가져오기

> 실제 에이전트 작업은 몇 분에서 몇 시간이 걸립니다: CI 실행, 심층 연구 합성, 배치 내보내기. 동기식 도구 호출은 연결을 끊거나, 타임아웃되거나, UI를 차단합니다. 2025-11-25에 병합된 SEP-1686은 Tasks 프리미티브를 추가합니다: 모든 요청이 태스크로 증강될 수 있으며, 결과는 나중에 가져오거나 상태 알림을 통해 스트리밍될 수 있습니다. 드리프트 위험 참고: Tasks는 2026년 상반기까지 실험적; SDK 표면이 아직 사양 주변에서 설계 중입니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, 비동기 태스크 상태 머신)
**Prerequisites:** 13단계 07과 (MCP 서버), 13단계 09과 (전송)
**Time:** 약 75분

## 학습 목표

- 도구를 동기에서 태스크 증강으로 전환해야 하는 시기(30초 이상의 서버 측 작업)를 식별할 수 있다.
- 태스크 라이프사이클을 설명할 수 있다: `working` → `input_required` → `completed` / `failed` / `cancelled`.
- 충돌이 진행 중인 작업을 잃지 않도록 태스크 상태를 유지할 수 있다.
- `tasks/status`를 폴링하고 `tasks/result`를 올바르게 가져올 수 있다.

## 문제

`generate_report` 도구는 다분 추출 파이프라인을 실행합니다. 동기식 모델에서의 옵션:

1. 3분 동안 연결 유지. 원격 전송이 끊김; 클라이언트가 타임아웃; UI가 멈춤.
2. 자리 표시자와 함께 즉시 반환; 클라이언트가 커스텀 엔드포인트를 폴링하도록 요구. MCP 통일성 깨짐.
3. 발사 후 망각; 결과 없음.

어느 것도 좋지 않습니다. SEP-1686이 네 번째를 추가: 태스크 증강. 모든 요청(일반적으로 `tools/call`)이 태스크로 태그될 수 있음. 서버가 즉시 태스크 ID를 반환. 클라이언트가 완료되면 `tasks/status`를 폴링하고 `tasks/result`를 가져옴. 서버 측 상태가 재시작 후에도 유지됨.

## 개념

### 태스크 증강

요청은 `params._meta.task.required: true`(또는 `optional: true`, 서버 결정)를 설정하여 태스크가 됨. 서버가 즉시 응답:

```json
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "_meta": {
      "task": {
        "id": "tsk_9f7b...",
        "state": "working",
        "ttl": 900000
      }
    }
  }
}
```

`ttl`은 서버가 상태를 유지하겠다는 약속; ttl 후 태스크 결과는 폐기됨.

### 도구별 옵트인

도구 주석이 태스크 지원을 선언할 수 있음:

- `taskSupport: "forbidden"` — 이 도구는 항상 동기 실행. 빠른 도구에 안전.
- `taskSupport: "optional"` — 클라이언트가 태스크 증강을 요청할 수 있음.
- `taskSupport: "required"` — 클라이언트가 태스크 증강을 사용해야 함.

`generate_report` 도구는 `required`가 될 것. `notes_search` 도구는 `forbidden`이 될 것.

### 상태

```
working  -> input_required -> working  (엘리시테이션을 통한 루프)
working  -> completed
working  -> failed
working  -> cancelled
```

상태 머신은 추가 전용: `completed`, `failed` 또는 `cancelled`가 되면 태스크는 종료.

### 메소드

- `tasks/status {taskId}` — 현재 상태 및 진행 힌트 반환.
- `tasks/result {taskId}` — 차단하거나 아직 완료되지 않았으면 404 반환.
- `tasks/cancel {taskId}` — 멱등; 종료 상태는 무시.
- `tasks/list` — 선택 사항; 활성 및 최근 완료 태스크 열거.

### 상태 변경 스트리밍

서버가 지원하는 경우 클라이언트가 상태 알림을 구독할 수 있음:

```
server -> notifications/tasks/updated {taskId, state, progress?}
```

폴링보다 스트리밍하는 클라이언트가 더 나은 UX를 얻음. 폴링은 항상 최소 표면으로 지원됨.

### 지속 상태

태스크 지원을 선언하는 서버는 상태를 유지해야 한다고 사양이 요구. 충돌이 ttl 내에서 완료된 결과를 잃지 않아야 함. 저장소는 SQLite에서 Redis, 파일시스템까지 다양. 13과 하네스는 파일시스템을 사용.

### 취소 의미론

`tasks/cancel`은 멱등. 태스크가 실행 중이면 서버가 중지 시도(실행자 협력적 취소 확인). 이미 종료 상태이면 요청은 무효.

### 충돌 복구

서버 프로세스가 재시작될 때:

1. 모든 유지된 태스크 상태 로드.
2. 프로세스가 죽은 `working` 태스크를 오류 `CRASH_RECOVERY`와 함께 `failed`로 표시.
3. ttl 동안 `completed` / `failed` / `cancelled` 유지.

### 비동기 태스크 + 샘플링

태스크가 자체적으로 `sampling/createMessage`를 호출할 수 있음. 이것이 장기 실행 연구 태스크가 작동하는 방식: 서버의 태스크 스레드가 필요에 따라 클라이언트의 모델을 샘플링하는 동안 클라이언트의 UI는 주기적 진행 업데이트와 함께 태스크를 `working`으로 표시.

### 이것이 실험적인 이유

SEP-1686은 2025-11-25에 출시되었지만 더 넓은 로드맵은 세 가지 미해결 문제를 지적: 지속적인 구독 프리미티브, 하위 태스크(부모-자식 태스크 관계), 결과-TTL 표준화. 사양이 2026년을 통해 진화할 것으로 예상. 프로덕션 코드는 일반적인 경우에만 Tasks를 안정적으로 취급하고 하위 태스크에 대한 향후 SDK 변경에 대비해야 함.

## 사용하기

`code/main.py`는 지속 태스크 저장소(파일시스템 기반)와 백그라운드 스레드에서 실행되는 `generate_report` 도구를 구현합니다. 클라이언트가 도구를 호출하고 즉시 태스크 ID를 받고, 작업자가 진행률을 업데이트하는 동안 `tasks/status`를 폴링하고, 완료되면 `tasks/result`를 가져옵니다. 취소 작동; 충돌 복구는 작업자 스레드를 죽이고 상태를 다시 로드하여 시뮬레이션됨.

살펴볼 내용:

- `/tmp/lesson-13-tasks/<id>.json`에 유지된 태스크 상태 JSON.
- 작업자 스레드가 `progress` 필드 업데이트; 폴링이 진행되는 모습.
- 클라이언트 측 취소가 이벤트 설정; 작업자가 확인하고 조기 종료.
- "충돌" 시 상태 재로드가 진행 중인 태스크를 `CRASH_RECOVERY`와 함께 `failed`로 표시.

## 배포하기

이 레슨은 `outputs/skill-task-store-designer.md`를 생성합니다. 장기 실행 도구(연구, 빌드, 내보내기)가 주어지면 스킬이 태스크 저장소(상태 형태, ttl, 지속성)를 설계하고, 올바른 taskSupport 플래그를 선택하고, 진행 알림을 스케치합니다.

## 실습

1. `code/main.py`를 실행하세요. `generate_report` 태스크를 시작하고, 상태를 폴링한 다음 결과를 가져오세요.

2. 실행 중간에 `tasks/cancel` 호출을 추가하세요. 작업자가 이를 존중하고 상태가 `cancelled`가 되는지 확인하세요.

3. 충돌 복구 시뮬레이션: 작업자 스레드를 죽이고 로더를 재시작한 후 `CRASH_RECOVERY` 실패 모드를 관찰하세요.

4. 저장소를 SQLite로 확장하세요. 지속성 이점은 동일; 쿼리 옵션이 열림(세션 X의 모든 태스크 나열).

5. 2026년 MCP 로드맵 포스트를 읽으세요. 향후 1년 내 SDK API 설계에 가장 큰 영향을 미칠 Tasks 관련 미해결 문제를 식별하세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 태스크(Task) | "장기 실행 도구 호출" | 비동기 실행을 위해 `_meta.task`로 증강된 요청 |
| SEP-1686 | "Tasks 사양" | 2025-11-25에 Tasks를 추가한 사양 진화 제안 |
| `_meta.task` | "태스크 봉투" | id, state, ttl을 포함하는 요청별 메타데이터 |
| taskSupport | "도구 플래그" | 도구당 `forbidden` / `optional` / `required` |
| `tasks/status` | "폴링 메소드" | 현재 상태 및 선택적 진행 힌트 가져오기 |
| `tasks/result` | "결과 가져오기" | 완료된 페이로드 반환 또는 아직 완료되지 않았으면 404 |
| `tasks/cancel` | "중지" | 멱등 취소 요청 |
| ttl | "보존 예산" | 서버가 태스크 상태를 유지하기로 약속한 밀리초 |
| `notifications/tasks/updated` | "상태 푸시" | 서버 주도 상태 변경 이벤트 |
| 지속 저장소(Durable store) | "충돌 안전 상태" | 파일시스템 / SQLite / Redis 지속성 계층 |

## 추가 자료

- [MCP — GitHub SEP-1686 issue](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1686) — 발의 제안 및 전체 토론
- [WorkOS — MCP async tasks for AI agent workflows](https://workos.com/blog/mcp-async-tasks-ai-agent-workflows) — 설계 워크스루 및 근거
- [DeepWiki — MCP task system and async operations](https://deepwiki.com/modelcontextprotocol/modelcontextprotocol/2.7-task-system-and-async-operations) — 메커니즘 및 상태 머신
- [FastMCP — Tasks](https://gofastmcp.com/servers/tasks) — SDK 수준 태스크 구현 패턴
- [MCP blog — 2026 roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — 미해결 문제 및 2026 우선순위 (하위 태스크 포함)
