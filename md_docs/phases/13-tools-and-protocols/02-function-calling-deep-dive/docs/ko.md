# 함수 호출 심층 분석 — OpenAI, Anthropic, Gemini

> 세 최첨단 제공자는 2024년에 동일한 도구 호출 루프에 수렴한 후 나머지 모든 것에서 분기했습니다. OpenAI는 `tools`와 `tool_calls`를 사용합니다. Anthropic은 `tool_use`와 `tool_result` 블록을 사용합니다. Gemini는 `functionDeclarations`와 고유 ID 상관 관계를 사용합니다. 이 레슨은 세 가지를 나란히 비교하여 한 제공자에서 출시된 코드를 포팅할 때 깨지지 않도록 합니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, 스키마 변환기)
**Prerequisites:** 13단계 01과 (도구 인터페이스)
**Time:** 약 75분

## 학습 목표

- OpenAI, Anthropic, Gemini 함수 호출 페이로드(선언, 호출, 결과)의 세 가지 형태 차이를 설명할 수 있다.
- 하나의 도구 선언을 세 가지 제공자 형식으로 변환하고 엄격 모드 제약이 어디에서 달라질지 예측할 수 있다.
- 각 제공자에서 `tool_choice`를 사용하여 도구 호출을 강제, 금지 또는 자동 선택할 수 있다.
- 제공자별 하드 제한(도구 수, 스키마 깊이, 인자 길이)과 제한 위반 시 각각이 출력하는 오류 시그니처를 알 수 있다.

## 문제

함수 호출 요청의 형태는 제공자마다 다릅니다. 2026년 프로덕션 스택의 세 가지 구체적인 예:

**OpenAI Chat Completions / Responses API.** `tools: [{type: "function", function: {name, description, parameters, strict}}]`를 전달합니다. 모델의 응답에는 `choices[0].message.tool_calls: [{id, type: "function", function: {name, arguments}}]`가 포함되며, 여기서 `arguments`는 파싱해야 하는 JSON 문자열입니다. 엄격 모드(`strict: true`)는 제약 조건 디코딩을 통해 스키마 준수를 강제합니다.

**Anthropic Messages API.** `tools: [{name, description, input_schema}]`를 전달합니다. 응답은 `content: [{type: "text"}, {type: "tool_use", id, name, input}]`로 반환됩니다. `input`은 이미 파싱된 객체(문자열이 아님)입니다. `{type: "tool_result", tool_use_id, content}` 블록을 포함하는 새 `user` 메시지로 응답합니다.

**Google Gemini API.** `tools: [{functionDeclarations: [{name, description, parameters}]}]`를 전달합니다(`functionDeclarations` 아래에 중첩). 응답은 `candidates[0].content.parts: [{functionCall: {name, args, id}}]`로 도착하며, Gemini 3 이상에서 `id`는 병렬 호출 상관 관계를 위한 고유 값입니다. `{functionResponse: {name, id, response}}`로 응답합니다.

동일한 루프. 다른 필드 이름, 다른 중첩, 다른 문자열-대-객체 규칙, 다른 상관 관계 메커니즘. OpenAI에서 날씨 에이전트를 작성한 팀은 Anthropic으로 포팅하는 데 2일, Gemini로 포팅하는 데 또 하루를 단순한 배관 작업에 소비합니다.

이 레슨은 세 가지 형식을 하나의 표준 도구 선언으로 통합하고 에지에서 라우팅하는 변환기를 구축합니다. 13단계 17과는 동일한 패턴을 LLM 게이트웨이로 일반화합니다.

## 개념

### 공통 구조

모든 제공자는 다섯 가지가 필요합니다:

1. **도구 목록.** 도구별 이름, 설명, 입력 스키마.
2. **도구 선택.** 특정 도구 강제, 도구 금지, 또는 모델이 결정하도록 함.
3. **호출 출력.** 도구 이름과 인자를 지정하는 구조화된 출력.
4. **호출 ID.** 응답을 올바른 호출과 연관(병렬 처리에 중요).
5. **결과 주입.** 결과를 호출에 연결하는 메시지 또는 블록.

### 필드별 형태 차이

| 측면 | OpenAI | Anthropic | Gemini |
|------|--------|-----------|--------|
| 선언 봉투 | `{type: "function", function: {...}}` | `{name, description, input_schema}` | `{functionDeclarations: [{...}]}` |
| 스키마 필드 | `parameters` | `input_schema` | `parameters` |
| 응답 컨테이너 | 어시스턴트 메시지의 `tool_calls[]` | `tool_use` 타입의 `content[]` | `functionCall` 타입의 `parts[]` |
| 인자 타입 | 문자열화된 JSON | 파싱된 객체 | 파싱된 객체 |
| ID 형식 | `call_...` (OpenAI 생성) | `toolu_...` (Anthropic) | UUID (Gemini 3 이상) |
| 결과 블록 | 역할 `tool`, `tool_call_id` | `tool_result`, `tool_use_id`가 있는 `user` | 일치하는 `id`가 있는 `functionResponse` |
| 도구 강제 | `tool_choice: {type: "function", function: {name}}` | `tool_choice: {type: "tool", name}` | `tool_config: {function_calling_config: {mode: "ANY"}}` |
| 도구 금지 | `tool_choice: "none"` | `tool_choice: {type: "none"}` | `mode: "NONE"` |
| 엄격 스키마 | `strict: true` | 스키마-그자체-스키마(항상 적용) | 요청 수준의 `responseSchema` |

### 실제로 부딪힐 제한

- **OpenAI.** 요청당 128개 도구. 스키마 깊이 5. 인자 문자열 <= 8192 바이트. 엄격 모드는 `$ref`, 중복이 있는 `oneOf`/`anyOf`/`allOf` 불가, 모든 속성이 `required`에 나열되어야 함.
- **Anthropic.** 요청당 64개 도구. 스키마 깊이는 사실상 무제한이지만 실용적 한도 10. 엄격 모드 플래그 없음; 스키마는 계약이며 모델은 따르는 경향이 있음.
- **Gemini.** 요청당 64개 함수. 스키마 타입은 OpenAPI 3.0 하위 집합(JSON Schema 2020-12와 약간의 차이). Gemini 3부터 병렬 호출 고유 ID.

### `tool_choice` 동작

모두가 지원하는 세 가지 모드, 이름만 다름:

- **자동.** 모델이 도구 또는 텍스트 선택. 기본값.
- **필수 / Any.** 모델이 최소 하나의 도구를 호출해야 함.
- **없음.** 모델이 도구를 호출하지 않아야 함.

각 제공자에 고유한 모드 하나:

- **OpenAI.** 이름으로 특정 도구 강제.
- **Anthropic.** 이름으로 특정 도구 강제; `disable_parallel_tool_use` 플래그가 단일 대 다중을 구분.
- **Gemini.** `mode: "VALIDATED"`는 모델 의도와 관계없이 모든 응답을 스키마 검증기를 통과시킴.

### 병렬 호출

OpenAI의 `parallel_tool_calls: true`(기본값)는 하나의 어시스턴트 메시지에서 여러 호출을 출력합니다. 모두 실행하고 `tool_call_id`당 하나의 항목이 있는 배치된 도구 역할 메시지로 응답합니다. Anthropic은 역사적으로 단일 호출을 했음; `disable_parallel_tool_use: false`(Claude 3.5부터 기본값)가 다중을 활성화합니다. Gemini 2는 병렬 호출을 허용했지만 안정적인 ID를 제공하지 않았음; Gemini 3은 UUID를 추가하여 순서 없는 응답이 깔끔하게 상관되도록 합니다.

### 스트리밍

세 가지 모두 스트리밍 도구 호출을 지원합니다. 와이어 형식이 다릅니다:

- **OpenAI.** `tool_calls[i].function.arguments`의 델타 청크가 증분적으로 도착합니다. `finish_reason: "tool_calls"`까지 누적합니다.
- **Anthropic.** 블록-시작 / 블록-델타 / 블록-중지 이벤트. `input_json_delta` 청크가 부분 인자를 전달합니다.
- **Gemini.** `streamFunctionCallArguments`(Gemini 3 신규)는 `functionCallId`가 있는 청크를 출력하여 여러 병렬 호출이 인터리브될 수 있게 합니다.

13단계 03과는 병렬 + 스트리밍 재조립을 깊이 다룹니다. 이 레슨은 선언 및 단일 호출 형태에 초점을 맞춥니다.

### 오류 및 수리

잘못된 인자 오류도 다르게 보입니다.

- **OpenAI (비엄격).** 모델이 `arguments: "{bad json}"` 반환, JSON 파싱 실패, 오류 메시지를 주입하고 재호출.
- **OpenAI (엄격).** 디코딩 중 검증 발생; 잘못된 JSON은 불가능하지만 `refusal`이 나타날 수 있음.
- **Anthropic.** `input`에 예상치 못한 필드가 포함될 수 있음; 스키마는 참고 사항. 서버 측에서 검증.
- **Gemini.** OpenAPI 3.0 특이점: 객체 필드의 `enum`이 조용히 무시됨; 직접 검증.

### 변환기 패턴

코드의 표준 도구 선언은 다음과 같습니다(형태는 선택):

```python
Tool(
    name="get_weather",
    description="Use when ...",
    input_schema={"type": "object", "properties": {...}, "required": [...]},
    strict=True,
)
```

세 개의 작은 함수가 이를 세 가지 제공자 형태로 변환합니다. `code/main.py`의 하네스가 정확히 이 작업을 수행한 후 가짜 도구 호출을 각 제공자의 응답 형태를 통해 왕복합니다. 네트워크 불필요 — 이 레슨은 HTTP가 아닌 형태를 가르칩니다.

프로덕션 팀은 이 변환기를 `AbstractToolset`(Pydantic AI), `UniversalToolNode`(LangGraph), 또는 `BaseTool`(LlamaIndex)로 래핑합니다. 13단계 17과는 세 제공자 중 하나 앞에 OpenAI 형태의 API를 노출하는 게이트웨이를 제공합니다.

## 사용하기

`code/main.py`는 하나의 표준 `Tool` 데이터 클래스와 OpenAI, Anthropic, Gemini 선언 JSON을 출력하는 세 개의 변환기를 정의합니다. 그런 다음 각 형태의 수작업 제공자 응답을 동일한 표준 호출 객체로 파싱하여 의미론이 표면 아래에서 동일함을 보여줍니다. 실행하고 세 선언을 나란히 비교하세요.

살펴볼 내용:

- 세 선언 블록은 봉투와 필드 이름만 다릅니다.
- 세 응답 블록은 호출이 있는 위치(최상위 `tool_calls`, `content[]` 블록, `parts[]` 항목)가 다릅니다.
- 하나의 `canonical_call()` 함수가 세 응답 형태 모두에서 `{id, name, args}`를 추출합니다.

## 배포하기

이 레슨은 `outputs/skill-provider-portability-audit.md`를 생성합니다. 한 제공자에 대한 함수 호출 통합이 주어지면 스킬이 이식성 감사를 생성합니다: 어떤 제공자 제한에 의존하는지, 어떤 필드의 이름을 바꿔야 하는지, 각 다른 제공자로 포팅할 때 무엇이 깨지는지.

## 실습

1. `code/main.py`를 실행하고 세 제공자 선언 JSON이 모두 동일한 기본 `Tool` 객체를 직렬화하는지 확인하세요. 표준 도구를 수정하여 enum 파라미터를 추가하고 Gemini 변환기만 OpenAPI 특이점을 처리해야 하는지 확인하세요.

2. 각 제공자에 대한 `ListToolsResponse` 파서를 추가하여 모델이 `list_tools` 또는 검색 호출 후 반환하는 도구 목록을 추출하세요. OpenAI에는 네이티브로 없습니다; 이 비대칭성을 기록하세요.

3. `tool_choice` 변환을 구현하세요: 표준 `ToolChoice(mode="force", tool_name="x")`를 세 제공자 형태로 매핑하세요. 그런 다음 `mode="any"`와 `mode="none"`을 매핑하세요. 레슨의 차이 테이블을 확인하세요.

4. 세 제공자 중 하나를 선택하고 함수 호출 가이드를 처음부터 끝까지 읽으세요. 다른 두 제공자가 지원하지 않는 스키마 사양의 필드를 찾으세요. 후보: OpenAI `strict`, Anthropic `disable_parallel_tool_use`, Gemini `function_calling_config.allowed_function_names`.

5. 테스트 벡터를 작성하세요: 선언된 스키마를 위반하는 인자가 있는 도구 호출. 각 제공자의 검증기(1과의 표준 라이브러리 검증기를 대리로 사용 가능)를 통해 실행하고 어떤 오류가 발생하는지 기록하세요. 엄격성 측면에서 프로덕션에 사용할 제공자를 문서화하세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 함수 호출(Function calling) | "도구 사용" | 구조화된 도구 호출 출력을 위한 제공자 수준 API |
| 도구 선언(Tool declaration) | "도구 사양" | 이름 + 설명 + JSON 스키마 입력 페이로드 |
| `tool_choice` | "강제/금지" | 자동 / 필수 / 없음 / 특정 이름 모드 |
| 엄격 모드(Strict mode) | "스키마 강제" | 스키마에 맞게 디코딩을 제한하는 OpenAI 플래그 |
| `tool_use` 블록 | "Anthropic의 호출 형태" | id, name, input이 있는 인라인 콘텐츠 블록 |
| `functionCall` 파트 | "Gemini의 호출 형태" | name, args, id를 포함하는 `parts[]` 항목 |
| 문자열-인자(Arguments-as-string) | "문자열화된 JSON" | OpenAI는 args를 객체가 아닌 JSON 문자열로 반환 |
| 병렬 도구 호출(Parallel tool calls) | "한 턴에 팬아웃" | 하나의 어시스턴트 메시지의 여러 도구 호출 |
| 거절(Refusal) | "모델이 거절" | 호출 대신 엄격 모드 전용 거절 블록 |
| OpenAPI 3.0 하위 집합 | "Gemini 스키마 특이점" | Gemini가 사용하는 JSON-Schema-유사 방언, 약간의 차이 있음 |

## 추가 자료

- [OpenAI — Function calling guide](https://platform.openai.com/docs/guides/function-calling) — 엄격 모드 및 병렬 호출을 포함한 표준 참조
- [Anthropic — Tool use overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) — `tool_use` 및 `tool_result` 블록 의미론
- [Google — Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling) — 병렬 호출, 고유 ID 및 OpenAPI 하위 집합
- [Vertex AI — Function calling reference](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling) — Gemini의 엔터프라이즈 표면
- [OpenAI — Structured outputs](https://platform.openai.com/docs/guides/structured-outputs) — 엄격 모드 스키마 강제 세부 사항
