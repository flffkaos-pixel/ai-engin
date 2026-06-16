# Dify

> Dify는 오픈소스 LLM 앱 개발 플랫폼이다. 가져오기/내보내기 형식은 YAML/JSON이며, DSL이 있다. RAG 파이프라인, 에이전트, 워크플로우를 위한 비주얼 편집기. 코드 저장소에 체크인되는 배포 형식 — 팀이 프롬프트와 구성을 버전 제어로 유지할 수 있다.

**Type:** Learn + Build
**Languages:** Python, YAML
**Prerequisites:** Phase 14 · 07 (MCP), Phase 14 · 12 (Workflows)
**Time:** ~90분

## 학습 목표

- Dify의 세 가지 기본 요소를 명명한다: RAG 파이프라인, 에이전트, 워크플로우.
- Dify의 가져오기/내보내기 형식(YAML/JSON DSL)이 코드 저장소 체크인을 어떻게 지원하는지 설명한다.
- 에이전트 위에 방어 UX(레슨 28)를 구현하는 Dify의 게이트를 설명한다.
- Dify RAG를 MCP 서버(레슨 07) 및 OTel GenAI(레슨 23)와 연결한다.

## 문제

에이전트를 구축했지만 배포해야 한다. 운영팀은 에이전트를 관리해야 한다 — 프롬프트 변경, RAG 재인덱싱, 사용자 관리. Dify와 같은 플랫폼은 비개발자에게 사용자 인터페이스를 제공하고 구성 파일을 저장소에 체크인할 수 있도록 내보낸다. 캔버스에서 프롬프트를 끌어서 놓기 vs 코드에서 프롬프트를 수동으로 편집하기. Dify의 경쟁자(Botpress, Flowise, Langflow)가 존재하지만 여기서는 다루지 않는다.

## 개념

### Dify의 기본 요소

1. **RAG 파이프라인.** 업로드된 문서 → 청킹 → 임베딩 → 벡터 DB. 검색 전략 하이브리드: 벡터 + 키워드, 또는 LLM 리랭킹.
2. **에이전트.** 도구를 사용하는 LLM. 변수, 대화 변수, 파일 업로드로 구성 가능.
3. **워크플로우.** 노드가 있는 그래프: LLM, 코드 노드, 조건, 변환, HTTP 요청. 상태 저장 또는 비저장.

### 배포 형식

Dify DSL은 YAML/JSON이다. 앱은 단일 파일로 내보낸다.

```yaml
app:
  name: customer-support-agent
  type: agent
  description: Handles basic customer support

model:
  provider: openai
  name: gpt-4o

features:
  memory: true
  files: true

tools:
  - type: api
    name: get_order_status
    url: "https://api.example.com/orders"
```

이 파일을 저장소에 체크인한다 — 배포가 감사 가능하고 재현 가능하다.

### 게이트

Dify는 에이전트 위에 방어 UX를 구현한다:

- **콘텐츠 검토.** 에이전트 출력이 전송되기 전에 인간 검토 필요.
- **게이트.** 에이전트가 특정 작업을 완료한 후 인간 확인 필요.
- **중재.** 인젝션 콘텐츠 차단을 위해 사전 구축된 중재 API에 연결.
- **모니터링.** Langfuse 데이터 세트 및 OTel 추적에 연결.

### 통합

Dify RAG는 벡터 DB(Qdrant, Weaviate, Milvus)에 연결. MCP 서버(레슨 07)를 도구/리소스로 사용.

## 직접 구현하기

`code/main.py`는 두 가지 모드로 Dify 배포를 시뮬레이션:

1. **빌더.** 사용자가 끌어서 놓기 캔버스를 통해 에이전트를 구성 — Dify DSL JSON을 생성.
2. **런타임.** DSL을 가져오고 구성된 도구로 에이전트를 실행하는 에이전트 런타임.

데모: 3개 도구, 가드레일 게이트, Langfuse 데이터 세트 연결.

실행:

```
python3 code/main.py
```

출력: 구축된 앱, 각 단계에서 생성 또는 확인 이벤트, 배포된 앱의 흐름.

## 활용하기

- **Dify** for low-code agent deployment. RAG, agents, workflows in a visual canvas.
- **DSL export** to version-control agent configurations.
- **MCP server integration** (레슨 07) to extend agent tools.

## 배포하기

`outputs/skill-dify-deploy.md` scaffolds a Dify app configuration with RAG pipeline, agent tools, guard gates, and observability hooks.

## 연습 문제

1. Dify Cloud에 가입. 3개 도구가 있는 에이전트 구축. DSL을 YAML로 내보내기.
2. RAG 파이프라인 구축: 문서 업로드, 청킹 테스트, 검색 품질 측정.
3. Dify 앱에 게이트 추가: "민감한 작업" 전 확인 단계. 게이트가 작동할 때 Dify 로그에 무엇이 표시되는가?
4. Dify RAG를 MCP 서버에 연결: MCP 도구가 Dify의 RAG에 어떻게 통합되는가?
5. 앱을 Langfuse 데이터 세트와 연결: Dify의 OTel 연결을 에이전트 평가에 어떻게 사용하는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Dify DSL | "앱 구성" | Dify 앱 형식의 YAML/JSON |
| RAG pipeline | "검색 증강 생성" | 문서 업로드 → 청킹 → 임베딩 → 검색 |
| Agent | "도구 사용 LLM" | 도구로 구성된 에이전트 |
| Workflow | "그래프" | LLM, 조건, 변환이 있는 노드 |
| Gate | "안전 확인" | 출력 전 인간 검토 또는 확인 |
| Canvas | "비주얼 편집기" | 끌어서 놓기 앱 빌더 |

## 추가 자료

- [Dify docs](https://docs.dify.ai/) — platform overview, DSL format
- [Dify GitHub](https://github.com/langgenius/dify) — open-source LLM app platform
- [Dify + Langfuse integration](https://langfuse.com/docs/integrations/dify) — observability hook
