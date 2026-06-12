# 프롬프트 캐싱 및 컨텍스트 캐싱

> 시스템 프롬프트가 4,000 토큰입니다. RAG 컨텍스트가 20,000 토큰입니다. 모든 요청과 함께 보냅니다. 매번 둘 다 비용을 지불합니다. 프롬프트 캐싱을 사용하면 제공자가 해당 prefix를 따뜻하게 유지하고 재사용 시 정상 비용의 10%로 청구할 수 있습니다. 올바르게 사용하면推理 비용을 50-90% 절감하고 첫 토큰 지연 시간을 40-85% 절감할 수 있습니다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 11 · 01 (Prompt Engineering), Phase 11 · 05 (Context Engineering), Phase 11 · 11 (Caching and Cost)
**소요 시간:** ~60분

## 문제

코딩 agent가 대화의 모든 턴에서 동일한 15,000 토큰 시스템 프롬프트를 Claude에게 보냅니다. $3/M 입력 토큰에서 스무 턴은 사용자의 실제 메시지 이전에만 $0.90의 입력 비용입니다. 하루 10,000개의 대화에 곱하면 변경되지 않는 텍스트에 대해 $9,000/일이 됩니다.

품질을 떨어뜨리지 않고 프롬프트를 줄일 수 없습니다. 매번 보내야 합니다 -- 모델이 모든 턴에서 필요로 합니다. 유일한 방법은 제공자가 이미 본 prefix에 대해全额を 지불하는 것을 중단하는 것입니다.

그 방법이 프롬프트 캐싱입니다. Anthropic은 2024년 8월에 shipping했고(2025년에 1시간 확장 TTL variant 포함), OpenAI는 같은 해 나중에 자동화를했고, Google은 Gemini 1.5와 함께 명시적 컨텍스트 캐싱을 shipping했으며, 이제 세 곳 모두 프론티어 모델에서 기본 기능으로 제공하고 있습니다.

## 개념

![프롬프트 캐싱: 한 번 작성, 저렴하게 읽기](../assets/prompt-caching.svg)

**메커니즘.** 요청의 prefix가 최근 요청의 prefix와 일치하면 제공자가 이전 실행에서 KV-cache를 제공하는 대신 토큰을 다시 인코딩합니다. 처음에는 작은 쓰기 프리미엄을 지불하고 그 이후에는 큰 읽기 할인을 받습니다.

**2026년 세 제공자 flavor.**

| 제공자 | API 스타일 | 적중 할인 | 쓰기 프리미엄 | 기본 TTL | 캐시 가능 최소 |
|---------|-----------|--------------|---------------|-------------|---------------|
| Anthropic | 명시적 `cache_control` 마커 | 입력의 90% 할인 | 25% 할증금 | 5분 (1시간으로 확장 가능) | 1,024 토큰 (Sonnet/Opus), 2,048 (Haiku) |
| OpenAI | 자동 prefix 감지 | 입력의 50% 할인 | 없음 | 최대 1시간 (최선 노력) | 1,024 토큰 |
| Google (Gemini) | 명시적 `CachedContent` API | 스토리지 청구; 읽기는 일반의 ~25% | 토큰·시간당 스토리지 요금 | 사용자 설정 (기본 1시간) | 4,096 토큰 (Flash), 32,768 (Pro) |

**불변성.** 세 곳 모두 prefix만 캐시합니다. 요청 간 토큰이 다르면 다른 토큰 이후 모든 것이 미스입니다. *안정적인* 부분을 위에, *가변적인* 부분을 아래에 놓으세요.

### 캐시 친화적 레이아웃

```
[시스템 프롬프트]          <-- 이것을 캐시
[도구 정의]               <-- 이것을 캐시
[Few-shot 예제]           <-- 이것을 캐시
[검색된 문서]             <-- 재사용되면 캐시, 그렇지 않으면 안 함
[대화 기록]               <-- 마지막 턴까지 캐시
[현재 사용자 메시지]       <-- 절대 캐시 안 함 (매번 다름)
```

순서를 위반하면 -- 사용자 메시지를 시스템 프롬프트 위에 놓고, few-shots 사이에 동적 검색을 interleaving -- 캐시가 절대 적중하지 않습니다.

### 손익 계산

Anthropic의 25% 쓰기 프리미엄은 캐시된 블록이 순 netsave를 위해 최소 두 번 읽혀야 함을 의미합니다. 1 쓰기 + 1 읽기는 요청당 평균 0.675x 비용(32% 절감)입니다. 1 쓰기 + 10 읽기는 평균 0.205x(80% 절감)입니다. 경험法则: TTL 내에서 3번 이상 재사용할 것으로 예상되는 것은 모두 캐시합니다.

## 실습

### 단계 1: Anthropic 명시적 마커가 있는 프롬프트 캐싱

```python
import anthropic

client = anthropic.Anthropic()

SYSTEM = [
    {
        "type": "text",
        "text": "You are a senior Python reviewer. Follow the rubric exactly.\n\n" + RUBRIC_15K_TOKENS,
        "cache_control": {"type": "ephemeral"},
    }
]

def review(code: str):
    return client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": code}],
    )
```

`cache_control` 마커는 Anthropic에게 블록을 5분 동안 저장하도록 지시합니다. 해당 창 내 재사용은 적중됩니다; 만료 후 재사용은 다시 씁니다.

**응답 사용량 필드:**

```python
response = review(code_a)
response.usage
# InputTokensUsage(
#     input_tokens=120,
#     cache_creation_input_tokens=15023,   # 1.25x로支払い
#     cache_read_input_tokens=0,
#     output_tokens=340,
# )

response_b = review(code_b)
response_b.usage
# cache_creation_input_tokens=0
# cache_read_input_tokens=15023           # 0.1x로支払い
```

CI에서 두 필드를 모두 확인 -- `cache_read_input_tokens`가 요청 전반에 걸쳐 0으로 유지되면 캐시 키가 드리프트하고 있는 것입니다.

### 단계 2: 1시간 확장 TTL

장기 실행 배치 작업의 경우 5분 기본값이 작업 간에 만료됩니다. `ttl` 설정:

```python
{"type": "text", "text": RUBRIC, "cache_control": {"type": "ephemeral", "ttl": "1h"}}
```

1시간 TTL은 쓰기 프리미엄의 2배(기본 대비 50% 할증이 아닌 25% 할인)를 cost하지만 prefix를 5번 이상 재사용하는 모든 배치에서 빠르게 상쇄됩니다.

### 단계 3: OpenAI 자동 캐싱

OpenAI는 구성할 것이 없습니다. 1,024 토큰 이상의 이전 요청과 일치하는 모든 prefix가 자동으로 50% 할인을 받습니다.

```python
from openai import OpenAI
client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},   # 길고 안정적
        {"role": "user", "content": user_msg},
    ],
)
resp.usage.prompt_tokens_details.cached_tokens  # 할인된 부분
```

동일한 캐시 친화적 레이아웃 규칙이 적용됩니다. OpenAI의 캐시를 죽이지만 Anthropic의 캐시를 죽이지 않는 두 가지: `user` 필드 변경(캐시 키 구성 요소로 사용)과 도구 재정렬.

### 단계 4: Gemini 명시적 컨텍스트 캐싱

Gemini는 생성하고 이름 짓는 첫 번째 클래스로 캐시를 취급합니다:

```python
from google import genai
from google.genai import types

client = genai.Client()

cache = client.caches.create(
    model="gemini-3-pro",
    config=types.CreateCachedContentConfig(
        display_name="rubric-v3",
        system_instruction=RUBRIC,
        contents=[FEW_SHOT_EXAMPLES],
        ttl="3600s",
    ),
)

resp = client.models.generate_content(
    model="gemini-3-pro",
    contents=["Review this code:\n" + code],
    config=types.GenerateContentConfig(cached_content=cache.name),
)
```

Gemini는 캐시가 존재하는 동안 토큰·시간당 스토리지를 청구하고 일반 입력 레이트의 ~25%에서 읽습니다. 이것은 며칠에 걸쳐 큰 프롬프트를 많은 세션에서 재사용할 때 올바른 형태입니다.

### 단계 5: 프로덕션에서 적중률 측정

`code/main.py`의 3개 제공자 회계사를 참조하여 쓰기/읽기/미스 수를 추적하고 1K 요청당 혼합 비용을 계산합니다. 대상 적중률에서 배포 게이트 -- 대부분의 프로덕션 Anthropic 설정은 워밍업 후 >80% 읽기 분율을 보여야 합니다.

## 2026년에도 여전히 shipping되는 함정들

- **상단의 동적 타임스탬프.** 시스템 프롬프트 상단의 `"Current time: 2026-04-22 15:30:02"`. 모든 요청이 미스합니다. 캐시 중단점 아래로 타임스탬프를 이동합니다.
- **도구 재정렬.** 도구를 안정적인 순서로 직렬화 -- 배포 간 dict reshuffle이 모든 적중을 break합니다.
- **유사 중복 텍스트.** "You are helpful." 대 "You are a helpful assistant." -- 1바이트 차이가 = 전체 미스.
- **너무 작은 블록.** Anthropic은 1,024 토큰 기준(2,048 for Haiku)을 enforce합니다. 더 작은 블록은 조용히 캐시되지 않습니다.
- **-blind 비용 대시보드.** "입력 토큰"을 캐시됨 대 캐시되지 않음으로 분할합니다. 그렇지 않으면 트래픽 감소가 캐시 승리로 보입니다.

## 활용

2026년 캐싱 스택:

| 상황 | 선택 |
|-----------|------|
| 안정적인 10k+ 시스템 프롬프트가 있는 Agent, 많은 턴 | 5분 TTL의 Anthropic `cache_control` |
| 30분 이상 prefix를 재사용하는 배치 작업 | `ttl: "1h"`의 Anthropic |
| GPT-5의 서버리스 엔드포인트, 커스텀 인프라 없음 | OpenAI 자동 (prefix를 안정적이고 길게 만들기만 하면 됨) |
| 큰 코드/문서 코퍼스를 며칠간 재사용 | Gemini 명시적 `CachedContent` |
| 크로스 제공자 폴백 | 캐시 가능한 prefix 레이아웃을 제공자 간 동일하게 유지하여 모든 적중이 작동하도록 함 |

사용자 메시지 레이어에서 시맨틱 캐싱(Phase 11 · 11)과 결합: 프롬프트 캐싱은 *토큰 동일* 재사용을 처리하고, 시맨틱 캐싱은 *의미 동일* 재사용을 처리합니다.

## 배포

`outputs/skill-prompt-caching-planner.md`를 저장하세요:

```markdown
---
name: prompt-caching-planner
description: 캐시 친화적 프롬프트 레이아웃을 설계하고 올바른 제공자 캐싱 모드를 선택합니다.
version: 1.0.0
phase: 11
lesson: 15
tags: [llm-engineering, caching, cost]
---

프롬프트(시스템 + 도구 + few-shot + 검색 + 기록 + 사용자)와 사용량 프로필(시간당 요청, 필요한 TTL, 제공자)이 주어지면:

1. 레이아웃. 단일 캐시 중단점이 표시된 재정렬된 섹션; 안정적인 섹션과 가변적인 섹션을 설명합니다.
2. 제공자 모드. Anthropic cache_control, OpenAI 자동 또는 Gemini CachedContent. TTL 및 재사용 패턴에서 정당화합니다.
3. 손익분기점. TTL 내 쓰기당 예상 읽기 수; 수학을 통한 순 비용 대 비캐시.
4. 검증 계획. 두 번째 동일 요청에서 cache_read_input_tokens > 0인 CI 어설션; 캐시됨 대 캐시되지 않은 토큰별로 분할된 대시보드.
5. 실패 모드. 이 설정에서 캐시가 미스할 가장 가능성 높은 3가지 이유(동적 타임스탬프, 도구 재정렬, 유사 중복 텍스트)를 나열하고 각각을 방지하는 방법을 설명합니다.

캐시 중단점 위에 동적 필드를 배치하는 캐시 플랜을 shipping 거부. 재사용 횟수가 2x 쓰기 프리미엄을 상쇄하지 않는 한 1h TTL 활성화 거부.
```

## 연습 문제

1. **쉬움.** 5,000 토큰 시스템 프롬프트로 Claude에 대해 10턴 대화를 가져옵니다. `cache_control` 없이 실행한 다음 사용합니다. 각각의 입력 토큰 비용을 보고합니다.
2. **중간.** 프롬프트 템플릿과 요청 로그가 주어지면 각 제공자(Anthropic 5m, Anthropic 1h, OpenAI 자동, Gemini 명시적)에 대한 예상 적중률과 달러 절감액을 계산하는 테스트 harness를 작성합니다.
3. **어려움.** 레이아웃 optimizer 구축: `stable=True/False`로 표시된 필드 목록과 프롬프트가 주어지면 정보를 잃지 않으면서 최대 캐시 친화적 위치에 단일 캐시 중단점을 놓도록 프롬프트를 다시 작성합니다. 실제 Anthropic 엔드포인트에서 검증합니다.

## 핵심 용어

| 용어 |人们在说什么 |실제로 의미하는 것 |
|------|-----------------|-----------------------|
| 프롬프트 캐싱 | "긴 프롬프트를 저렴하게" | 일치하는 prefix에 대한 provider-side KV-cache 재사용; 반복 입력 토큰의 50-90% 할인 |
| `cache_control` | "Anthropic 마커" | "여기까지的一切이 캐시 가능"을 선언하는 콘텐츠 블록 속성; `{"type": "ephemeral"}` |
| 캐시 쓰기 | "프리미엄 지불" | 캐시를 populated하는 첫 번째 요청; Anthropic에서 입력 레이트의 ~1.25x로 청구, OpenAI에서 무료 |
| 캐시 읽기 | "할인" | prefix와 일치하는 후속 요청; Anthropic에서 10%, OpenAI에서 50%, Gemini에서 ~25% |
| TTL | "생존 기간" | 캐시가 따뜻하게 유지되는 시간; Anthropic 기본 5분 (1시간으로 확장 가능), OpenAI 최대 1시간, Gemini 사용자 설정 |
| 확장 TTL | "1시간 Anthropic 캐시" | `{"type": "ephemeral", "ttl": "1h"}`; 2x 쓰기 프리미엄이지만 배치 재사용에 worth it |
| prefix 일치 | "왜 내 캐시가 미스했는지" | 캐시는 시작부터 중단점까지 모든 토큰이 바이트 동일할 때만 적중합니다 |
| 컨텍스트 캐싱 (Gemini) | "명시적のもの" | Google의 명명된 스토리지 청구 캐시 객체; 큰 코퍼스의 며칠간 재사용에 최적 |

## 추가 자료

- [Anthropic — Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) -- `cache_control`, 1h TTL, 손익분기표
- [OpenAI — Prompt caching](https://platform.openai.com/docs/guides/prompt-caching) -- 자동 prefix 매칭
- [Google — Context caching](https://ai.google.dev/gemini-api/docs/caching) -- `CachedContent` API 및 스토리지 가격 책정
- [Anthropic engineering — Prompt caching for long-context workloads](https://www.anthropic.com/news/prompt-caching) -- 지연 시간 숫자가 있는 원래 출시 게시물
- Phase 11 · 05 (Context Engineering) -- 캐시가 착지할 수 있도록 프롬프트를 슬라이스하는 위치
- Phase 11 · 11 (Caching and Cost) -- 사용자 메시지에서 시맨틱 캐시와 쌍으로 프롬프트 캐싱
- [Pope et al., "Efficiently Scaling Transformer Inference" (2022)](https://arxiv.org/abs/2211.05102) -- 프롬프트 캐싱이 사용자에게 노출하는 KV-cache 메모리 모델; 캐시된 prefix가 다시 읽을 때 재계산보다 ~10× 저렴한 이유를 설명
- [Agrawal et al., "SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills" (2023)](https://arxiv.org/abs/2308.16369) -- prefill은 프롬프트 캐싱이 shortcuts하는 phase입니다; TTFT가 캐시 적중에서 dramatically 떨어지는 이유와 TPOT가 영향을 받지 않는 이유를 설명하는 논문
- [Leviathan et al., "Fast Inference from Transformers via Speculative Decoding" (2023)](https://arxiv.org/abs/2211.17192) -- 프롬프트 캐싱은投机적 디코딩, Flash Attention 및 MQA/GQA와 함께 추론 비용 곡선을 구부리는 레버입니다; 다른 세 가지를 위해 이것을 읽으세요