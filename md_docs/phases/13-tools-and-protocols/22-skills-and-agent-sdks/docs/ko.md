# 스킬과 에이전트 SDK — Anthropic Skills, AGENTS.md, OpenAI Apps SDK

> MCP는 "어떤 도구가 존재하는지" 말합니다. 스킬은 "작업을 수행하는 방법"을 말합니다. 2026년 스택은 둘 다 계층화합니다. Anthropic의 Agent Skills(개방형 표준, 2025년 12월)는 점진적 공개와 함께 SKILL.md로 제공됩니다. OpenAI의 Apps SDK는 MCP에 위젯 메타데이터를 더한 것입니다. AGENTS.md(현재 60,000개 이상의 저장소에 있음)는 프로젝트 수준 에이전트 컨텍스트로 저장소 루트에 있습니다. 이 레슨은 각각이 무엇을 다루는지 명명하고 에이전트 간에 이동하는 최소 SKILL.md + AGENTS.md 번들을 구축합니다.

**Type:** 학습
**Languages:** Python (표준 라이브러리, SKILL.md 파서 및 로더)
**Prerequisites:** 13단계 07과 (MCP 서버)
**Time:** 약 45분

## 학습 목표

- 세 가지 계층(AGENTS.md (프로젝트 컨텍스트), SKILL.md (재사용 가능 노하우), MCP (도구))을 구분할 수 있다.
- YAML 프론트매터와 점진적 공개로 SKILL.md를 작성할 수 있다.
- 파일시스템 방식으로 스킬을 에이전트 런타임에 로드할 수 있다.
- MCP 서버 및 AGENTS.md와 스킬을 구성하여 하나의 패키지가 Claude Code, Cursor 및 Codex에서 작동하도록 할 수 있다.

## 문제

엔지니어가 릴리스 노트 작성 워크플로를 다단계 프롬프트로 추출: "최근 병합된 PR을 읽으세요. 영역별로 그룹화하세요. 각각을 요약하세요. 팀 스타일에 따라 체인지로그 항목을 작성하세요. Slack 초안에 게시하세요." 팀을 위해 Notion 문서에 넣음.

이제 이 워크플로를 Claude Code, Cursor 및 Codex CLI에서 사용하려고 함. 각 에이전트는 명령어를 로드하는 다른 방식이 있음: Claude Code 슬래시 명령어, Cursor 규칙, Codex `.codex.md`. 엔지니어가 워크플로를 세 번 복사하고 세 가지를 유지보수.

AGENTS.md와 SKILL.md가 함께 이를 수정:

- **AGENTS.md**는 저장소 루트에 있음. 모든 호환 에이전트가 세션 시작 시 읽음. "이 프로젝트는 어떻게 작동하나요? 규칙은 무엇인가요? 어떤 명령어가 테스트를 실행하나요?"
- **SKILL.md**는 휴대용 번들: YAML 프론트매터(이름, 설명) + 마크다운 본문 + 선택적 리소스. 스킬을 지원하는 에이전트가 요청 시 이름으로 로드.
- **MCP** (13단계 06-14과)는 스킬이 호출해야 하는 도구를 처리.

세 가지 계층, 하나의 휴대용 아티팩트.

## 개념

### AGENTS.md (agents.md)

2025년 말 출시, 2026년 4월까지 60,000개 이상의 저장소에서 채택. 저장소 루트의 하나의 파일. 형식:

```markdown
# 프로젝트: my-service

## 규칙
- 엄격 모드의 TypeScript.
- Python 쪽 모델에는 Pydantic 사용.
- 테스트는 `pnpm test`로 실행.

## 빌드 및 실행
- `pnpm dev` 로컬 개발 서버.
- `pnpm build` 프로덕션 번들.
```

에이전트가 세션 시작 시 이를 읽고 해당 프로젝트에 대한 동작을 보정. 2026년의 모든 코딩 에이전트가 AGENTS.md 지원: Claude Code, Cursor, Codex, Copilot Workspace, opencode, Windsurf, Zed.

### SKILL.md 형식

Anthropic의 Agent Skills(2025년 12월 개방형 표준으로 출시):

```markdown
---
name: release-notes-writer
description: 이 프로젝트 스타일에 따라 최근 병합된 PR에 대한 체인지로그 항목을 작성합니다.
---

# 릴리스 노트 작성기

호출되면 다음 단계를 실행하세요:

1. 마지막 태그 이후 병합된 PR을 나열하세요. `gh pr list --base main --state merged` 사용.
2. 레이블별로 그룹화: feature, fix, chore, docs.
3. 각 그룹의 각 PR에 대해 한 줄 작성: `- <제목> (#<번호>)`.
4. 릴리스 노트 초안을 작성하고 CHANGELOG.md에 스테이징하세요.

사용자가 "출시"라고 말하면 `git tag vX.Y.Z` 및 `gh release create`를 실행하세요.

## 참고

- PR이 없는 커밋은 절대 포함하지 마세요.
- 공개 체인지로그에서 "chore" 항목은 건너뛰세요.
```

프론트매터는 스킬의 정체성을 선언. 본문은 스킬이 로드될 때 모델에 표시되는 프롬프트.

### 점진적 공개

스킬은 에이전트가 필요할 때만 가져오는 하위 리소스를 참조 가능. 예:

```
skills/
  release-notes-writer/
    SKILL.md
    style-guide.md
    template.md
    scripts/
      generate.sh
```

SKILL.md는 "스타일 규칙은 style-guide.md를 참조하세요"라고 말함. 에이전트는 스킬이 활성적으로 실행 중일 때만 style-guide.md를 가져옴. 이렇게 하면 모델이 필요하지 않을 수 있는 세부 정보로 프롬프트를 부풀리는 것을 피함.

### 파일시스템 검색

에이전트 런타임이 알려진 디렉토리에서 SKILL.md 파일 스캔:

- `~/.anthropic/skills/*/SKILL.md`
- 프로젝트 `./skills/*/SKILL.md`
- `~/.claude/skills/*/SKILL.md`

로딩은 폴더 이름 및 프론트매터 `name`으로 수행. Claude Code, Anthropic Claude Agent SDK 및 SkillKit(교차 에이전트) 모두 이 패턴을 따름.

### Anthropic Claude Agent SDK

`@anthropic-ai/claude-agent-sdk` (TypeScript) 및 `claude-agent-sdk` (Python)는 세션 시작 시 스킬을 로드하고, 런타임 내에서 호출 가능한 "에이전트"로 노출. 사용자가 호출할 때 에이전트 루프가 스킬로 디스패치.

### OpenAI Apps SDK

2025년 10월 출시; MCP 위에 직접 구축. OpenAI의 이전 Connectors 및 Custom GPT Actions를 단일 개발자 표면 아래 통합. Apps SDK 앱은:

- MCP 서버 (도구, 리소스, 프롬프트).
- ChatGPT UI용 위젯 메타데이터 추가.
- 대화형 표면을 위한 선택적 MCP Apps `ui://` 리소스.

동일한 프로토콜, 더 풍부한 UX.

### SkillKit을 통한 교차 에이전트 이식성

SkillKit 및 유사한 교차 에이전트 배포 계층은 단일 SKILL.md를 32개 이상의 AI 에이전트(Claude Code, Cursor, Codex, Gemini CLI, OpenCode 등) 각각의 네이티브 형식으로 변환. 하나의 진실 공급원; 많은 소비자.

### 세 가지 계층 스택

| 계층 | 파일 | 로드 시점 | 목적 |
|-------|------|-------------|---------|
| AGENTS.md | 저장소 루트 | 세션 시작 | 프로젝트 수준 규칙 |
| SKILL.md | skills 디렉토리 | 스킬 호출 시 | 재사용 가능 워크플로 |
| MCP 서버 | 외부 프로세스 | 도구 필요 시 | 호출 가능한 액션 |

세 가지 모두 구성: 에이전트가 세션 시작 시 AGENTS.md 읽기, 사용자가 스킬 호출, 스킬의 명령어에 MCP 도구 호출 포함, 에이전트가 MCP 클라이언트를 통해 디스패치.

## 사용하기

`code/main.py`는 stdlib SKILL.md 파서와 로더를 제공. `./skills/` 아래 스킬 검색, YAML 프론트매터 + 마크다운 본문 파싱, 스킬 이름을 키로 하는 딕셔너리 생성. 그런 다음 이름으로 `release-notes-writer`를 호출하는 에이전트 루프 시뮬레이션.

살펴볼 내용:

- 최소 stdlib 파서로 파싱된 YAML 프론트매터( `pyyaml` 의존성 없음).
- 스킬 본문이 그대로 저장됨; 에이전트가 호출 시 시스템 프롬프트 앞에 추가.
- 요청 시 참조된 파일을 가져오는 `read_subresource` 함수로 점진적 공개 데모.

## 배포하기

이 레슨은 `outputs/skill-agent-bundle.md`를 생성합니다. 워크플로가 주어지면 스킬이 결합된 SKILL.md + AGENTS.md + MCP-서버-청사진 번들을 생성하며, 에이전트 간 이식 가능.

## 실습

1. `code/main.py`를 실행하세요. `skills/` 아래에 두 번째 스킬을 추가하고 로더가 이를 감지하는지 확인하세요.

2. 이 코스 저장소를 위한 AGENTS.md를 작성하세요. 테스트 명령어, 스타일 규칙 및 13단계 개념 모델을 포함하세요.

3. 팀의 내부 문서에서 다단계 워크플로를 SKILL.md로 포팅하세요. Claude Code에서 로드되는지 확인하세요.

4. 스킬을 Cursor 및 Codex의 네이티브 규칙 형식으로 수동 변환하세요. 형식 간 차이를 세세요 — 이것이 SkillKit이 자동화하는 변환 표면입니다.

5. Anthropic Agent Skills 블로그 포스트를 읽으세요. Claude Agent SDK에서 이 레슨의 로더가 다루지 않는 기능을 식별하세요. (힌트: 에이전트 하위 호출.)

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| SKILL.md | "스킬 파일" | YAML 프론트매터 + 마크다운 본문, 에이전트 런타임에 의해 로드됨 |
| AGENTS.md | "저장소 루트 에이전트 컨텍스트" | 세션 시작 시 읽히는 프로젝트 수준 규칙 파일 |
| 점진적 공개(Progressive disclosure) | "지연 로드 하위 리소스" | 필요할 때만 가져오는 파일을 참조하는 스킬 본문 |
| 프론트매터(Frontmatter) | "상단 YAML 블록" | `---` 구분 기호 안의 메타데이터(이름, 설명) |
| Claude Agent SDK | "Anthropic의 스킬 런타임" | `@anthropic-ai/claude-agent-sdk`, 스킬 로드 및 라우팅 |
| OpenAI Apps SDK | "MCP + 위젯 메타" | MCP 및 ChatGPT UI 훅 위에 구축된 OpenAI의 개발 표면 |
| 스킬 검색(Skill discovery) | "파일시스템 스캔" | SKILL.md에 대해 알려진 디렉토리 탐색, 이름으로 키 지정 |
| 교차 에이전트 이식성(Cross-agent portability) | "하나의 스킬 많은 에이전트" | SkillKit 스타일 도구를 통해 하나의 SKILL.md를 32개 이상의 에이전트로 변환 |
| Agent Skill | "휴대용 노하우" | MCP의 도구 개념 밖의 재사용 가능한 작업 템플릿 |
| Apps SDK | "MCP + ChatGPT UI" | MCP에 통합된 Connectors 및 Custom GPTs |

## 추가 자료

- [Anthropic — Agent Skills announcement](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — 2025년 12월 출시
- [Anthropic — Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — SKILL.md 형식 참조
- [OpenAI — Apps SDK](https://developers.openai.com/apps-sdk) — ChatGPT용 MCP 기반 개발자 플랫폼
- [agents.md](https://agents.md/) — AGENTS.md 형식 및 채택 목록
- [Anthropic — anthropics/skills GitHub](https://github.com/anthropics/skills) — 공식 스킬 예제
