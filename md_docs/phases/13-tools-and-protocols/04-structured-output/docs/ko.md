# 구조화된 출력 — JSON Schema, Pydantic, Zod, 제약 조건 디코딩

> "모델에게 JSON을 반환하라고 정중히 요청"하는 것은 최첨단 모델에서도 5~15% 실패합니다. 구조화된 출력은 제약 조건 디코딩으로 이 격차를 줄입니다: 모델은 스키마를 위반하는 토큰을 출력하는 것이 문자 그대로 차단됩니다. OpenAI의 strict 모드, Anthropic의 스키마 타입 tool use, Gemini의 `responseSchema`, Pydantic AI의 `output_type`, Zod의 `.parse`는 동일한 아이디어의 다섯 가지 표면 형태입니다. 이 레슨은 학습자가 모든 프로덕션 추출 파이프라인에 사용할 스키마 검증기와 엄격 모드 계약을 구축합니다.

**Type:** 빌드
**Languages:** Python (표준 라이브러리, JSON Schema 2020-12 하위 집합)
**Prerequisites:** 13단계 02과 (함수 호출 심층 분석)
**Time:** 약 75분

## 학습 목표

- 적절한 제약 조건(enum, min/max, required, pattern)을 사용하여 추출 대상에 대한 JSON Schema 2020-12를 작성할 수 있다.
- 엄격 모드와 제약 조건 디코딩이 "생성 후 검증"과 다른 보장을 제공하는 이유를 설명할 수 있다.
- 세 가지 실패 모드(파싱 오류, 스키마 위반, 모델 거절)를 구분할 수 있다.
- 타입화된 수리와 타입화된 거절 처리를 갖춘 추출 파이프라인을 구축할 수 있다.

## 문제

구매 주문 이메일을 읽는 에이전트는 자유 텍스트를 `{customer, line_items, total_usd}`로 변환해야 합니다. 세 가지 접근 방식.

**접근 방식 1: JSON 프롬프트.** "JSON으로 응답하세요. 필드는 customer, line_items, total_usd입니다." 최첨단 모델에서 85~95% 작동합니다. 여섯 가지 방식으로 실패: 중괄호 누락, 후행 쉼표, 잘못된 타입, 환각 필드, 토큰 제한에서 잘림, "다음은 JSON입니다:" 같은 산문 누출.

**접근 방식 2: 생성 후 검증.** 자유롭게 생성, 파싱, 스키마에 대해 검증, 실패 시 재시도. 신뢰할 수 있지만 비용이 많이 듭니다 — 재시도마다 비용을 지불하며, 잘림 버그는 발생당 한 턴을 추가로 소모합니다.

**접근 방식 3: 제약 조건 디코딩.** 제공자가 디코딩 시간에 스키마를 강제합니다. 유효하지 않은 토큰은 샘플링 분포에서 마스킹됩니다. 출력은 파싱이 보장되고 검증이 보장됩니다. 실패는 하나의 모드로 축소됩니다: 거절(모델이 입력이 스키마에 맞지 않는다고 판단).

2026년의 모든 최첨단 제공자는 접근 방식 3의 어떤 형태를 제공합니다.

- **OpenAI.** `response_format: {type: "json_schema", strict: true}`에 모델이 거절할 경우 응답에 `refusal` 추가.
- **Anthropic.** `tool_use` 입력에 대한 스키마 강제; `stop_reason: "refusal"`은 없지만, 도구 호출 없이 `end_turn`이 신호.
- **Gemini.** 요청 수준의 `responseSchema`; 2026년 Gemini는 선택된 타입에 대해 토큰 수준 문법 제약 조건을 제공.
- **Pydantic AI.** `output_type=InvoiceModel`이 `InvoiceModel`로 타입 지정된 구조화된 `RunResult` 출력.
- **Zod (TypeScript).** Zod 스키마에 대해 제공자 출력을 검증하는 런타임 파서; OpenAI의 `beta.chat.completions.parse`와 함께 사용.

공통점: 스키마를 한 번 선언하고 종단간 강제합니다.

## 개념

### JSON Schema 2020-12 — 공용어

모든 제공자는 JSON Schema 2020-12를 수용합니다. 가장 많이 사용하는 구성:

- `type`: `object`, `array`, `string`, `number`, `integer`, `boolean`, `null` 중 하나.
- `properties`: 필드 이름에서 하위 스키마로의 매핑.
- `required`: 반드시 나타나야 하는 필드 이름 목록.
- `enum`: 허용된 값의 폐쇄 집합.
- `minimum` / `maximum` (숫자), `minLength` / `maxLength` / `pattern` (문자열).
- `items`: 모든 배열 요소에 적용되는 하위 스키마.
- `additionalProperties`: `false`는 추가 필드를 금지(모드에 따라 기본값 다름).

OpenAI 엄격 모드는 세 가지 요구사항을 추가: 모든 속성이 `required`에 나열되어야 함, 모든 곳에서 `additionalProperties: false`, 확인되지 않은 `$ref` 없음. 이를 위반하면 API가 요청 시간에 400을 반환합니다.

### Pydantic, Python 바인딩

Pydantic v2는 `model_json_schema()`를 통해 데이터클래스 형태의 모델에서 JSON Schema를 생성합니다. Pydantic AI는 이를 래핑하여 다음과 같이 작성할 수 있게 합니다:

```python
class Invoice(BaseModel):
    customer: str
    line_items: list[LineItem]
    total_usd: Decimal
```

에이전트 프레임워크가 스키마를 에지에서 OpenAI strict 모드, Anthropic `input_schema`, 또는 Gemini `responseSchema`로 변환합니다. 모델의 출력은 타입화된 `Invoice` 인스턴스로 반환됩니다. 검증 오류는 타입화된 오류 경로와 함께 `ValidationError`를 발생시킵니다.

### Zod, TypeScript 바인딩

Zod(`z.object({customer: z.string(), ...})`)는 TS에 해당합니다. OpenAI의 Node SDK는 API의 JSON Schema 페이로드로 변환하는 `zodResponseFormat(Invoice)`를 노출합니다.

### 거절

엄격 모드는 모델이 응답하도록 강제할 수 없습니다. 입력이 스키마에 맞지 않으면("이메일이 시가 아니라 시였다"), 모델은 이유를 포함한 `refusal` 필드를 출력합니다. 코드는 이를 실패가 아닌 일급 결과로 처리해야 합니다. 거절은 또한 안전 신호로 유용합니다: 보호된 콘텐츠 이메일에서 신용 카드 번호를 추출하라는 요청을 받은 모델은 안전 이유가 첨부된 거절을 반환합니다.

### 공개 제약 조건 디코딩

오픈 가중치 구현은 세 가지 기술을 사용합니다.

1. **문법 기반 디코딩** (`outlines`, `guidance`, `lm-format-enforcer`): 스키마에서 결정적 유한 오토마톤 구축; 매 단계마다 FSM을 위반하는 토큰의 로짓을 마스킹.
2. **로짓 마스킹 + JSON 파서**: 모델과 동기화하여 스트리밍 JSON 파서 실행; 매 단계마다 유효-다음-토큰 집합 계산.
3. **검증기가 있는 투기적 디코딩**: 저렴한 초안 모델이 토큰 제안, 검증기가 스키마 강제.

상용 제공자는 이 중 하나를 내부에서 선택합니다. 2026년 최신 기술은 짧은 구조화된 출력의 경우 일반 생성보다 빠르고, 긴 출력의 경우 대략 동일한 속도입니다.

### 세 가지 실패 모드

1. **파싱 오류.** 출력이 유효한 JSON이 아님. 엄격 모드에서는 발생 불가. 비엄격 제공자에서는 여전히 발생 가능.
2. **스키마 위반.** 출력이 파싱되지만 스키마를 위반. 엄격 모드에서는 발생 불가. 외부에서는 흔함.
3. **거절.** 모델이 거절. 타입화된 결과로 처리해야 함.

### 재시도 전략

엄격 모드 외부(Anthropic tool use, 비엄격 OpenAI, 구형 Gemini)에 있을 때 복구 패턴은:

```
생성 -> 파싱 -> 검증 -> 실패 시 오류 주입 및 재시도, 최대 3회
```

한 번의 재시도면 보통 충분합니다. 세 번의 재시도는 약한 모델의 변동을 잡아냅니다. 세 번을 넘으면 잘못된 스키마의 신호입니다: 모델이 일부 입력에 대해 만족할 수 없으며, 프롬프트나 스키마를 수정해야 합니다.

### 소형 모델 지원

제약 조건 디코딩은 소형 모델에서 작동합니다. 문법 강제가 있는 3B 파라미터 오픈 모델은 원시 프롬프팅의 70B 파라미터 모델보다 구조화된 작업에서 더 뛰어납니다. 이것이 프로덕션에서 구조화된 출력이 중요한 주된 이유입니다: 신뢰성을 모델 크기와 분리합니다.

## 사용하기

`code/main.py`는 표준 라이브러리(타입, required, enum, min/max, pattern, items, additionalProperties)로 작성된 최소 JSON Schema 2020-12 검증기를 제공합니다. `Invoice` 스키마를 래핑하고 가짜 LLM 출력을 검증기를 통해 실행하여 파싱 오류, 스키마 위반, 거절 경로를 보여줍니다. 프로덕션에서 가짜 출력을 실제 제공자의 응답으로 교체하세요.

살펴볼 내용:

- 검증기는 경로와 메시지가 있는 타입화된 `[ValidationError]` 목록을 반환합니다. 이것이 재시도 프롬프트에 표시하려는 형태입니다.
- 거절 분기는 재시도하지 않습니다. 기록하고 타입화된 거절을 반환합니다. 14단계 09과는 거절을 안전 신호로 사용합니다.
- `additionalProperties: false` 검사는 적대적 테스트 입력에서 발동하여 엄격 모드가 환각 필드의 문을 닫는 이유를 보여줍니다.

## 배포하기

이 레슨은 `outputs/skill-structured-output-designer.md`를 생성합니다. 자유 텍스트 추출 대상(인보이스, 지원 티켓, 이력서 등)이 주어지면 스킬이 엄격 모드 호환 JSON Schema 2020-12와 이를 미러링하는 Pydantic 모델을 생성하며, 타입화된 거절 및 재시도 처리가 스텁되어 있습니다.

## 실습

1. `code/main.py`를 실행하세요. `total_usd`가 음수인 네 번째 테스트 케이스를 추가하세요. 검증기가 `minimum` 제약 조건 경로로 이를 거부하는지 확인하세요.

2. 검증기를 확장하여 식별자가 있는 `oneOf`를 지원하세요. 일반적인 사례: `line_item`이 `kind`로 태그된 제품 또는 서비스. 엄격 모드에는 미묘한 규칙이 있습니다; OpenAI의 구조화된 출력 가이드를 확인하세요.

3. 동일한 Invoice 스키마를 Pydantic BaseModel로 작성하고 `model_json_schema()` 출력을 수제 스키마와 비교하세요. Pydantic이 기본적으로 설정하지만 수제 버전이 생략하는 한 필드를 식별하세요.

4. 거절 비율을 측정하세요. 추출할 수 없는 10개의 입력(노래 가사, 수학 증명, 빈 이메일)을 구성하고 엄격 모드로 실제 제공자를 통해 실행하세요. 거절 대 환각 출력을 계산하세요. 이것이 거절 인식 재시도의 기준 진실입니다.

5. OpenAI의 구조화된 출력 가이드를 처음부터 끝까지 읽으세요. 일반 JSON Schema가 허용하지만 엄격 모드에서 명시적으로 금지하는 하나의 구문을 식별하세요. 그런 다음 금지된 구문을 필수적이지 않게 사용하는 스키마를 설계하고 엄격 호환으로 리팩터링하세요.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| JSON Schema 2020-12 | "스키마 사양" | 모든 최신 제공자가 사용하는 IETF 초안 스키마 방언 |
| 엄격 모드(Strict mode) | "보장된 스키마" | 제약 조건 디코딩을 통해 스키마를 강제하는 OpenAI 플래그 |
| 제약 조건 디코딩(Constrained decoding) | "로짓 마스킹" | 유효하지 않은 다음 토큰을 마스킹하는 디코딩 시간 강제 |
| 거절(Refusal) | "모델이 거절" | 입력이 스키마에 맞지 않을 때의 타입화된 결과 |
| 파싱 오류(Parse error) | "잘못된 JSON" | 출력이 JSON으로 파싱되지 않음; 엄격 모드에서는 불가능 |
| 스키마 위반(Schema violation) | "잘못된 형태" | 파싱되었지만 타입/required/enum/범위 위반 |
| `additionalProperties: false` | "추가 항목 금지" | 알 수 없는 필드 금지; OpenAI 엄격 모드에서 필수 |
| Pydantic BaseModel | "타입화된 출력" | JSON Schema를 출력하고 검증하는 Python 클래스 |
| Zod 스키마 | "TypeScript 출력 타입" | 제공자 출력 검증을 위한 TS 런타임 스키마 |
| 문법 강제(Grammar enforcement) | "오픈 가중치 제약 디코딩" | FSM 기반 로짓 마스킹 (outlines/guidance 등) |

## 추가 자료

- [OpenAI — Structured outputs](https://platform.openai.com/docs/guides/structured-outputs) — 엄격 모드, 거절 및 스키마 요구사항
- [OpenAI — Introducing structured outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) — 2024년 8월 출시 포스트, 디코딩 보장 설명
- [Pydantic AI — Output](https://ai.pydantic.dev/output/) — 각 제공자로 직렬화하는 타입화된 output_type 바인딩
- [JSON Schema — 2020-12 release notes](https://json-schema.org/draft/2020-12/release-notes) — 표준 사양
- [Microsoft — Structured outputs in Azure OpenAI](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs) — 엔터프라이즈 배포 참고 사항 및 엄격 모드 주의사항
