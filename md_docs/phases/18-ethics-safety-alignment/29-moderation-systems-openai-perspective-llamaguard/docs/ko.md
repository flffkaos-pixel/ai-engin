# 모더레이션 시스템 — OpenAI, Perspective, Llama Guard

> 프로덕션 모더레이션 시스템은 레슨 12-16에서 정의된 안전 정책을 운영화한다. OpenAI Moderation API: `omni-moderation-latest` (2024)는 GPT-4o 기반으로 텍스트 + 이미지를 한 번의 호출로 분류; 다국어 테스트 세트에서 이전 버전보다 42% 우수; 응답 스키마는 13개 카테고리 불리언을 반환 — harassment, harassment/threatening, hate, hate/threatening, illicit, illicit/violent, self-harm, self-harm/intent, self-harm/instructions, sexual, sexual/minors, violence, violence/graphic; 대부분의 개발자에게 무료. 계층화된 패턴: 입력 모더레이션(생성 전), 출력 모더레이션(생성 후), 맞춤 모더레이션(도메인 규칙). 비동기 병렬 호출이 지연 시간을 숨김; 플래그 발생 시 자리표시자 응답. Llama Guard 3/4 (레슨 16): 14개 MLCommons 위험, 코드 인터프리터 남용, 8개 언어(v3), 다중 이미지(v4). Perspective API (Google Jigsaw): LLM-as-moderator 물결 이전의 독성 점수; 주로 단일 차원 독성과 심각 독성/모욕/욕설 변형; 콘텐츠 모더레이션 연구의 기준. 폐기 예정: Azure Content Moderator 2024년 2월 폐기 예고, 2027년 2월 완전 폐기, Azure AI Content Safety로 대체.

**Type:** Build
**Languages:** Python (stdlib, 삼중 계층 모더레이션 하네스)
**Prerequisites:** Phase 18 · 16 (Llama Guard / Garak / PyRIT)
**Time:** ~60분

## 학습 목표

- OpenAI Moderation API의 카테고리 분류 체계와 그것이 Llama Guard 3의 MLCommons 세트와 어떻게 다른지 설명한다.
- 세 가지 모더레이션 계층 패턴(입력, 출력, 맞춤)을 설명하고 각각의 하나의 실패 모드를 제시한다.
- Perspective API의 LLM 이전 시대 기준선으로서의 위치와 연구에서 계속 사용되는 이유를 설명한다.
- Azure 폐기 타임라인을 설명한다.

## 문제

레슨 12-16은 공격과 방어 도구를 설명한다. 레슨 29는 사용자가 제품과 접촉하는 표면에서 방어를 운영화하는 배포된 모더레이션 시스템을 다룬다. 삼중 계층 패턴은 2026년의 기본 구성이다.

## 개념

### OpenAI Moderation API

`omni-moderation-latest` (2024). GPT-4o 기반. 텍스트 + 이미지를 한 번의 호출로 분류. 대부분의 개발자에게 무료.

카테고리 (응답 스키마의 13개 불리언):
- harassment, harassment/threatening
- hate, hate/threatening
- self-harm, self-harm/intent, self-harm/instructions
- sexual, sexual/minors
- violence, violence/graphic
- illicit, illicit/violent

멀티모달 지원은 `violence`, `self-harm`, `sexual`에 적용되지만 `sexual/minors`에는 적용되지 않음; 나머지는 텍스트 전용.

`code/main.py`의 코드 하네스에서는 `/threatening`, `/intent`, `/instructions`, `/graphic` 하위 카테고리를 교육적 단순화를 위해 상위 부모로 축소한다. 프로덕션 코드는 전체 13개 카테고리 스키마를 사용해야 한다.

이전 세대 모더레이션 엔드포인트보다 다국어 테스트 세트에서 42% 우수. 카테고리별 점수; 애플리케이션이 임계값을 설정.

### Llama Guard 3/4

레슨 16에서 다룸. 14개 MLCommons 위험 카테고리(OpenAI의 13개 응답 스키마 불리언과 다르게 구성). 8개 언어 지원(v3). Llama Guard 4 (2025년 4월)는 네이티브 멀티모달, 12B.

OpenAI와 Llama Guard 분류 체계는 겹치지만 차이가 있다. OpenAI는 "illicit"을 광범위한 카테고리로 가짐; Llama Guard는 "violent crimes"와 "non-violent crimes"를 별도로 가짐. 배포는 정책-분류 체계 적합성에 기반하여 선택.

### Perspective API (Google Jigsaw)

LLM-as-moderator 물결 이전(2020년 이전)의 독성 점수 시스템. 카테고리: TOXICITY, SEVERE_TOXICITY, INSULT, PROFANITY, THREAT, IDENTITY_ATTACK. 단일 차원 주요 점수(TOXICITY)와 하위 차원 변형.

API가 안정적이고 문서화되어 있으며 수년간의 교정 데이터가 있기 때문에 콘텐츠 모더레이션 연구 기준선으로 널리 사용됨. 현대 LLM 인접 사용 사례의 경우 Llama Guard 또는 OpenAI Moderation이 일반적으로 더 적합.

### 삼중 계층 패턴

1. **입력 모더레이션.** 생성 전 사용자의 프롬프트를 분류. 플래그 발생 시 거부. 지연 시간: 분류기 한 번 호출.
2. **출력 모더레이션.** 전달 전 모델의 출력을 분류. 플래그 발생 시 거부로 대체. 지연 시간: 생성 후 분류기 한 번 호출.
3. **맞춤 모더레이션.** 도메인 특화 규칙(정규식, 허용 목록, 비즈니스 정책). 입력 또는 출력에서 실행.

세 계층은 설계상 순차적이다: 입력 모더레이션은 생성 전에 완료되어야 하고, 출력 모더레이션은 생성 후에 실행된다. 병렬 처리는 계층 내에서 적용된다 — 동일한 텍스트에 대해 여러 분류기(예: OpenAI Moderation + Llama Guard + Perspective)를 동시에 실행하면 분류기별 지연 시간이 숨겨진다. 선택적 최적화로 입력 모더레이션이 완료되고 토큰-1 스트리밍이 지연되는 동안 자리표시자 응답("잠시만 기다려 주세요, 확인 중...")이 표시될 수 있다. 플래그 동작은 구성 가능: 거부, 정화, 인간 검토로 에스컬레이션.

### 실패 모드

- **입력만.** 출력 환각을 잡지 못함(레슨 12-14 인코딩 공격이 입력 분류기를 우회).
- **출력만.** 모든 입력이 모델에 도달하도록 허용; 비용 증가; 내부 추론을 공격자에게 노출.
- **맞춤만.** 카테고리 전반에 걸쳐 견고하지 않음; 정규식은 취약.

계층화가 기본. 이중 안전 장치.

### Azure 폐기

Azure Content Moderator: 2024년 2월 폐기 예고, 2027년 2월 완전 폐기. Azure AI Content Safety로 대체되며, 이는 LLM 기반이고 Azure OpenAI와 통합됨. 마이그레이션은 Azure 배포를 위한 2024-2027년 현장 수준 프로젝트.

### Phase 18에서의 위치

레슨 16은 레드팀 컨텍스트에서 모더레이션 도구를 다룬다. 레슨 29는 배포된 모더레이션을 다룬다. 레슨 30은 현재의 이중 용도 역량 증거로 마무리된다.

## 사용하기

`code/main.py`는 삼중 계층 모더레이션 하네스를 구축한다: 입력 모더레이터(키워드 + 카테고리 점수), 출력 모더레이터(출력에 동일 분류기), 맞춤 모더레이터(도메인 규칙). 입력을 실행하고 어떤 계층이 무엇을 잡는지 관찰할 수 있다.

## 결과물

이 레슨은 `outputs/skill-moderation-stack.md`를 생성한다. 배포가 주어지면 모더레이션 스택 구성을 권장한다: 입력에 어떤 분류기, 출력에 어떤 분류기, 어떤 맞춤 규칙, 에지 케이스에 대한 어떤 판단자.

## 실습

1. `code/main.py`를 실행한다. 무해, 경계선, 유해 입력을 세 계층 모두를 통해 실행한다. 각각에 대해 어떤 계층이 발동하는지 보고한다.

2. 특정 카테고리에 Perspective-API 스타일 독성 점수로 하네스를 확장한다. 임계값 동작을 카테고리 점수와 비교한다.

3. OpenAI Moderation API 문서와 Llama Guard 3 카테고리 목록을 읽는다. 각 OpenAI 카테고리를 가장 가까운 Llama Guard 카테고리에 매핑한다. 깔끔하게 매핑되지 않는 세 가지 카테고리를 식별한다.

4. 코드 어시스턴트 배포(예: GitHub Copilot)를 위한 모더레이션 스택을 설계한다. 가장 관련성 높은 카테고리와 가장 관련성 낮은 카테고리를 식별하고 맞춤 규칙을 제안한다.

5. Azure Content Moderator는 2027년 2월에 완전 폐기된다. Azure AI Content Safety로의 마이그레이션을 계획한다. 마이그레이션에서 가장 위험한 요소를 식별한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| OpenAI Moderation | "omni-moderation-latest" | GPT-4o 기반 13개 카테고리(텍스트) 분류기, 부분 멀티모달 지원 |
| Perspective API | "Google Jigsaw 독성" | LLM 이전 시대 독성 점수 기준선 |
| Llama Guard | "MLCommons 14개 카테고리" | Meta의 위험 분류기 (v3: 8B 텍스트, 8개 언어; v4: 12B 멀티모달) |
| 입력 모더레이션 | "생성 전 필터" | 모델 호출 전 사용자 프롬프트에 대한 분류기 |
| 출력 모더레이션 | "생성 후 필터" | 전달 전 모델 출력에 대한 분류기 |
| 맞춤 모더레이션 | "도메인 규칙" | 배포 특화 규칙 (정규식, 허용 목록, 정책) |
| 계층형 모더레이션 | "세 계층 모두" | 표준 프로덕션 배포 패턴 |

## 추가 자료

- [OpenAI Moderation API docs](https://platform.openai.com/docs/api-reference/moderations) — omni-moderation 엔드포인트
- [Meta PurpleLlama + Llama Guard](https://github.com/meta-llama/PurpleLlama) — Llama Guard 저장소
- [Google Jigsaw Perspective API](https://perspectiveapi.com/) — 독성 점수
- [Azure AI Content Safety](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/) — Azure 대체
