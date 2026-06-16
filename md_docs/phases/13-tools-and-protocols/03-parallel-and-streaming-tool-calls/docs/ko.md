# 병렬 도구 호출 및 도구와 함께하는 스트리밍

> 세 번의 독립적인 날씨 조회를 직렬로 처리하면 세 번의 왕복입니다. 병렬로 실행하면 총 시간이 가장 느린 단일 호출로 줄어듭니다. 모든 최첨단 제공자는 이제 한 턴에 여러 도구 호출을 출력합니다. 그 대가는 실질적입니다; 배관은 미묘합니다. 이 레슨은 두 부분을 모두 다룹니다: 병렬 팬아웃과 스트리밍 인자 재조립, 특히 ID 상관 관계 함정에 중점을 둡니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, 스레드 풀 + 스트리밍 하네스)
**Prerequisites:** 13단계 02과 (함수 호출 심층 분석)
**Time:** 약 75분

## 학습 목표

- `parallel_tool_calls: true`가 존재하는 이유와 비활성화해야 할 때를 설명할 수 있다.
- 병렬 팬아웃 중 스트리밍된 인자 청크를 올바른 도구 호출 ID와 상관시킬 수 있다.
- 조기 파싱 없이 부분적인 `arguments` 문자열을 완전한 JSON으로 재조립할 수 있다.
- 순차 대 병렬 지연 시간을 보여주는 세 도시 날씨 벤치마크를 실행할 수 있다.

## 문제

병렬 호출 없이 "벵갈루루, 도쿄, 취리히의 날씨는?"에 답하는 에이전트는 이렇게 합니다:

```
사용자 -> LLM
LLM -> get_weather(벵갈루루) 호출
호스트 -> 실행자 실행, 결과로 응답
LLM -> get_weather(도쿄) 호출
호스트 -> 실행자 실행, 결과로 응답
LLM -> get_weather(취리히) 호출
호스트 -> 실행자 실행, 결과로 응답
LLM -> 최종 텍스트 답변
```

세 번의 LLM 왕복, 각각 실행자 지연 시간도 추가로 부담합니다. 이상적 벽시계 시간의 약 4배입니다.

병렬 호출 사용:

```
사용자 -> LLM
LLM -> get_weather(벵갈루루) 호출; get_weather(도쿄) 호출; get_weather(취리히) 호출
호스트 -> 세 실행자를 모두 동시에 실행, 세 결과로 응답
LLM -> 최종 텍스트 답변
```

한 번의 LLM 왕복. 실행자 시간은 합이 아닌 세 개 중 최대값입니다. OpenAI, Anthropic, Gemini의 프로덕션 벤치마크는 팬아웃 워크로드에서 60~70%의 벽시계 감소를 보여줍니다.

대가는 상관 관계 복잡성입니다. 세 호출이 순서 없이 완료될 때 결과는 일치하는 `tool_call_id`를 가지고 있어야 모델이 정렬할 수 있습니다. 결과가 스트리밍될 때는 실행 전에 부분 인자 조각을 완전한 JSON으로 조립해야 합니다. Gemini 3은 동일한 도구에 대한 두 병렬 호출을 구분할 수 없었던 실제 문제를 해결하기 위해 부분적으로 고유 ID를 추가했습니다.

## 개념

### 병렬 활성화

- **OpenAI.** `parallel_tool_calls: true` 기본 켜짐. `false` 설정으로 직렬 강제.
- **Anthropic.** `disable_parallel_tool_use: false`(Claude 3.5 이상 기본값)로 병렬. `true` 설정으로 직렬.
- **Gemini.** 항상 병렬 가능; `tool_config.function_calling_config.mode = "AUTO"`로 모델이 결정.

도구에 순서 종속성이 있거나(`create_file` 후 `write_file`), 한 호출의 출력이 다른 호출의 입력에 영향을 주거나, 속도 제한기가 팬아웃을 처리할 수 없을 때 병렬을 비활성화하세요.

### ID 상관 관계

모델이 출력하는 모든 호출에는 `id`가 있습니다. 호스트가 반환하는 모든 결과에는 동일한 id가 포함되어야 합니다. 이것이 없으면 결과가 모호합니다.

- **OpenAI.** 각 도구 역할 메시지의 `tool_call_id`.
- **Anthropic.** 각 `tool_result` 블록의 `tool_use_id`.
- **Gemini.** 각 `functionResponse`의 `id`(Gemini 3 이상; Gemini 2는 이름으로 매칭되어 동일 이름 병렬 호출에서 문제 발생).

### 호출 동시 실행

호스트는 각 호출의 실행자를 자체 스레드, 코루틴 또는 원격 워커에서 실행합니다. 가장 간단한 하네스는 스레드 풀을 사용합니다; 프로덕션은 asyncio와 `asyncio.gather` 또는 구조화된 동시성을 사용합니다. 완료 순서는 예측 불가능 — id가 식별자입니다.

한 가지 흔한 버그: 완료 순서 대신 호출 목록 순서로 결과를 응답하는 것. 모델은 `tool_call_id`만 신경 쓰기 때문에 보통은 작동하지만, 결과가 누락되거나 중복되면 순서 없는 제출이 디버깅을 더 어렵게 만듭니다. 명시적 ID와 함께 완료 순서로 응답하는 것이 좋습니다.

### 스트리밍 도구 호출

모델이 스트리밍할 때 `arguments`는 조각으로 도착합니다. 세 병렬 호출에 대한 세 개의 개별 청크 스트림이 와이어에서 인터리브됩니다. ID당 하나의 누산기가 필요합니다.

제공자별 형태:

- **OpenAI.** 각 청크는 `choices[0].delta.tool_calls[i].function.arguments`(부분 문자열)입니다. 청크는 `index`(호출 목록 내 위치)를 전달합니다. 인덱스별로 누적하고, 처음 나타날 때 `id`를 읽고, `finish_reason = "tool_calls"`일 때 JSON을 파싱합니다.
- **Anthropic.** 스트림 이벤트는 `message_start`, 그 다음 타입 `tool_use`(id, name, 빈 input 포함)의 `content_block_start`, `content_block_delta` 이벤트가 `input_json_delta` 청크 전달, `content_block_stop`이 각 블록을 닫습니다.
- **Gemini.** `streamFunctionCallArguments`(Gemini 3 이상)는 `functionCallId`가 있는 청크를 출력하여 호출이 깔끔하게 인터리브됩니다. Gemini 3 이전에는 한 번에 하나의 완전한 호출을 반환했습니다.

### 부분 JSON과 조기 파싱 함정

`arguments`는 완료될 때까지 파싱할 수 없습니다. `{"city": "Ben`과 같은 부분 JSON은 유효하지 않으며 오류가 발생합니다. 올바른 게이트는 제공자의 호출 종료 신호입니다: OpenAI의 `finish_reason = "tool_calls"`, Anthropic의 `content_block_stop`, 또는 Gemini의 스트림 종료 이벤트. 그때만 `json.loads`를 시도하세요. 더 강력한 접근 방식은 구조가 완성될 때 이벤트를 생성하는 증분 JSON 파서를 사용하는 것입니다; OpenAI의 스트리밍 가이드는 실시간 "생각 중" 표시기를 보여주는 UX를 위해 이것을 권장합니다. 중괄호 개수 세기는 완전성 테스트로 신뢰할 수 없으며(따옴표 문자열이나 이스케이프된 콘텐츠 내부의 중괄호는 거짓 양성을 유발), 비공식 디버그 휴리스틱으로만 사용해야 합니다.

### 순서 없는 완료

```
호출_A: 빠른 API, 먼저 반환
호출_B: 느린 API, 두 번째 반환
호출_C: 중간 API, 세 번째 반환
```

호스트 응답은 여전히 id를 인용해야 합니다:

```
[{role: "tool", tool_call_id: "call_A", content: ...},
 {role: "tool", tool_call_id: "call_B", content: ...},
 {role: "tool", tool_call_id: "call_C", content: ...}]
```

응답의 순서는 OpenAI나 Anthropic의 정확성에 영향을 미치지 않습니다. Gemini는 id가 일치하기만 하면 모든 순서를 허용합니다.

### 벤치마크: 순차 대 병렬

`code/main.py`의 하네스는 400, 600, 800ms 지연 시간으로 세 개의 실행자를 시뮬레이션합니다. 순차는 총 1800ms로 실행됩니다. 병렬은 max(400, 600, 800) = 800ms로 실행됩니다. 차이는 비례가 아닌 상수이므로 도구 수가 증가할수록 절감 효과가 커집니다.

실제 주의사항: 병렬 호출은 다운스트림 API에 부담을 줍니다. 속도 제한이 있는 서비스에 10-way 팬아웃은 실패합니다. 13단계 17과는 게이트웨이 수준의 역압력을 다룹니다; 재시도 의미론은 향후 단계에서 계획됩니다.

### 스트리밍 팬아웃 벽시계

모델 자체가 스트리밍하는 경우, 모든 호출이 완료될 때까지 기다리지 않고 한 호출의 인자가 완료되는 즉시 실행을 시작할 수 있습니다. 이것은 OpenAI가 문서화하지만 모든 SDK가 노출하는 것은 아닌 최적화입니다. 이 레슨의 하네스는 이렇게 합니다: 시뮬레이션된 스트림이 완전한 인자 객체를 생성하는 즉시 호스트가 해당 호출을 시작합니다.

## 사용하기

`code/main.py`는 두 부분으로 나뉩니다. 첫 번째는 `concurrent.futures.ThreadPoolExecutor`를 사용하여 세 개의 시뮬레이션된 날씨 호출을 순차 및 병렬로 실행하고 벽시계 시간을 출력합니다. 두 번째 부분은 가짜 스트리밍 응답(하나의 스트림에 인터리브된 세 병렬 호출에 대한 `arguments` 청크)을 재생하고 `StreamAccumulator`로 ID별로 재조립합니다. LLM 없음, 네트워크 없음, 재조립 로직만 있습니다.

살펴볼 내용:

- 순차 타이머는 1.8초입니다. 병렬 타이머는 동일한 가짜 지연 시간에서 0.8초입니다.
- 누산기는 ID별로 버퍼링하고 각 호출의 JSON이 완료될 때만 파싱하여 순서 없이 도착하는 청크를 처리합니다.
- 실행자는 모든 스트림이 끝날 때까지 기다리지 않고 ID의 인자가 완료되는 즉시 시작됩니다.

## 배포하기

이 레슨은 `outputs/skill-parallel-call-safety-check.md`를 생성합니다. 도구 레지스트리가 주어지면 스킬이 병렬화해도 안전한 도구, 순서 종속성이 있는 도구, 다운스트림 속도 제한을 압도할 도구를 감사하여 도구당 `parallel_safe` 플래그가 있는 수정된 레지스트리를 반환합니다.

## 실습

1. `code/main.py`를 실행하고 시뮬레이션된 지연 시간을 변경하세요. 병렬 대 순차 비율이 대략 `max/sum`인지 확인하세요(실제 실행은 스레드 스케줄링, 직렬화, 하네스 오버헤드로 인해 이상에서 약간 벗어납니다). 어떤 지연 시간 분포에서 병렬이 더 이상 의미가 없어지나요?

2. 누산기를 확장하여 "호출이 스트림 도중 취소됨" 사례를 처리하도록 버퍼를 버리고 `cancelled` 이벤트를 출력하세요. 어떤 제공자가 이 사례를 명시적으로 문서화하나요? Anthropic의 `content_block_stop` 의미론과 OpenAI의 `finish_reason: "length"` 동작을 확인하세요.

3. 스레드 풀을 `asyncio.gather`로 교체하세요. 둘 다 벤치마크하세요. 컨텍스트 전환 비용이 낮기 때문에 async에서 약간의 개선이 있어야 하지만, 실행자가 실제 I/O를 수행하는 경우에만 해당합니다.

4. 병렬화하면 안 되는 두 도구(예: `create_file` 후 `write_file`)를 선택하세요. 레지스트리에 `ordering_dependency` 그래프를 추가하고 해당 그래프에서 병렬 팬아웃을 게이트하세요. 이것은 미래의 에이전트 엔지니어링 단계에서 공식화될 종속성 인식 스케줄링의 최소 장치입니다.

5. OpenAI의 병렬 함수 호출 섹션과 Anthropic의 `disable_parallel_tool_use` 문서를 읽으세요. Anthropic이 병렬화 비활성화를 권장하는 실제 도구 유형을 식별하세요. (힌트: 동일 리소스에 대한 결과적 변경.)

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 병렬 도구 호출(Parallel tool calls) | "한 턴에 팬아웃" | 모델이 하나의 어시스턴트 메시지에서 여러 도구 호출 출력 |
| `parallel_tool_calls` | "OpenAI의 플래그" | 다중 호출 출력 활성화 또는 비활성화 |
| `disable_parallel_tool_use` | "Anthropic의 역플래그" | 옵트아웃 플래그; 기본값은 병렬 활성화 |
| 도구 호출 ID(Tool call id) | "상관 관계 핸들" | 결과 메시지가 반영해야 하는 호출별 식별자 |
| 누산기(Accumulator) | "스트림 버퍼" | 부분 `arguments` 청크를 위한 ID별 문자열 버퍼 |
| 순서 없는 완료(Out-of-order completion) | "가장 빠른 것 먼저" | 병렬 호출이 예측 불가능한 순서로 완료; id가 접착제 |
| 종속성 그래프(Dependency graph) | "순서 제약" | 출력이 다른 도구의 입력이 되는 도구; 병렬화 불가 |
| 조기 파싱 함정(Parse-early trap) | "JSON.parse 폭발" | 불완전한 `arguments` 문자열 파싱 시도 |
| `streamFunctionCallArguments` | "Gemini 3 기능" | 호출당 고유 ID가 있는 스트리밍 인자 청크 |
| 완료 순서 응답(Completion-order reply) | "모두 기다리지 않음" | 도착하는 대로 id별로 키가 지정된 결과로 응답 |

## 추가 자료

- [OpenAI — Parallel function calling](https://platform.openai.com/docs/guides/function-calling#parallel-function-calling) — 기본 동작 및 옵트아웃 플래그
- [Anthropic — Tool use: implementing tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implementing-tool-use) — `disable_parallel_tool_use` 및 결과 배칭
- [Google — Gemini function calling parallel section](https://ai.google.dev/gemini-api/docs/function-calling) — Gemini 3의 ID 상관 병렬 호출
- [OpenAI — Streaming responses with tools](https://platform.openai.com/docs/api-reference/responses-streaming) — OpenAI 스트림을 위한 청크 인자 재조립
- [Anthropic — Streaming messages](https://docs.anthropic.com/en/api/messages-streaming) — `input_json_delta`가 있는 `content_block_delta`
