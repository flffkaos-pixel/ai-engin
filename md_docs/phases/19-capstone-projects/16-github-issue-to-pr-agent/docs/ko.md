# 캡스톤 16 — GitHub 이슈→PR 자율 에이전트

> AWS Remote SWE Agents, Cursor Background Agents, OpenAI Codex 클라우드, Google Jules 모두 동일한 2026년 제품 형태를 제공합니다: 이슈에 레이블을 붙이면 PR이 나옵니다. 클라우드 샌드박스에서 에이전트를 실행하고, 테스트 통과를 확인하며, 근거와 함께 리뷰 준비가 된 PR을 게시합니다. 어려운 부분은 저장소의 빌드 환경을 자동으로 재현하고, 자격 증명 누출을 방지하며, 저장소별 예산을 적용하고, 에이전트가 강제 푸시할 수 없도록 하는 것입니다. 이 캡스톤은 자체 호스팅 버전을 구축하고 비용과 통과율에서 호스팅된 대안과 비교합니다.

**Type:** Capstone
**Languages:** Python (에이전트), TypeScript (GitHub App), YAML (Actions)
**Prerequisites:** Phase 11 (LLM 엔지니어링), Phase 13 (도구), Phase 14 (에이전트), Phase 15 (자율), Phase 17 (인프라)
**Phases exercised:** P11 · P13 · P14 · P15 · P17
**Time:** 30시간

## 문제

비동기 클라우드 코딩 에이전트는 대화형 코딩 에이전트(캡스톤 01)와는 별도의 제품 카테고리입니다. UX는 GitHub 레이블입니다. 이슈에 `@agent fix this` 레이블을 붙이면, 워커가 클라우드 샌드박스에서 실행되고, 저장소를 클론하며, 테스트를 실행하고, 파일을 편집하고, 검증하며, 에이전트의 근거를 본문에 담아 PR을 엽니다. 대화형 루프나 터미널이 없습니다. AWS Remote SWE Agents, Cursor Background Agents, OpenAI Codex 클라우드, Google Jules, Factory Droids 모두 이 방향으로 수렴합니다.

엔지니어링 과제는 구체적입니다: 환경 재현(에이전트가 캐시된 개발 이미지 없이 처음부터 저장소를 빌드해야 함), 불안정한 테스트(재실행 또는 격리 필요), 자격 증명 범위 지정(최소 세분화 권한의 GitHub App), 저장소별 일일 예산 적용, 강제 푸시 금지 정책. 이 캡스톤은 호스팅된 대안과 비교하여 통과율, 비용, 안전성을 측정합니다.

## 개념

트리거는 GitHub 웹훅(이슈 레이블 또는 PR 코멘트)입니다. 디스패처가 ECS Fargate 또는 Lambda로 작업을 큐에 넣습니다. 워커는 저장소를 Daytona 또는 E2B 샌드박스로 가져오고 저장소(언어, 프레임워크)에서 추론된 일반 Dockerfile을 사용합니다. 에이전트는 Claude Opus 4.7 또는 GPT-5.4-Codex에 대해 mini-swe-agent 또는 SWE-agent v2 루프를 실행합니다. 코드를 읽고, 수정안을 제안하고, 패치를 적용하고, 테스트를 실행하는 과정을 반복합니다.

검증은 게이트 단계입니다. PR이 열리기 전에 샌드박스 내에서 전체 CI가 통과해야 합니다. 커버리지 델타가 계산되고, 임계값을 초과하여 음수이면 PR이 열리지만 `needs-review` 레이블이 붙습니다. 에이전트는 PR 설명과 리뷰어가 후속 작업을 위해 핑할 수 있는 `@agent` 스레드에 근거를 게시합니다.

안전성은 두 가지 GitHub 표면을 통해 범위가 지정됩니다: App은 `workflows: read`와 좁은 저장소 콘텐츠/PR 범위의 단기 설치 토큰을 제공합니다. 브랜치 보호(앱 권한이 아님)는 "main에 직접 쓰기 금지"와 "강제 푸시 금지"를 적용합니다 — 앱은 우회 목록에 추가되지 않습니다. `.github/workflows`에 대한 경로 범위 읽기 전용 액세스는 실제 GitHub App 프리미티브가 아니므로, 파일 편집에 대한 에이전트의 허용 목록은 워커 수준에서 이를 적용해야 합니다. 저장소별 일일 예산 상한선은 디스패처에서 적용됩니다(예: 저장소당 하루 최대 5개 PR, PR당 $20).

## 아키텍처

```
GitHub 이슈에 `@agent fix` 레이블 또는 PR 코멘트
            |
            v
    GitHub App 웹훅 -> AWS Lambda 디스패처
            |
            v
    ECS Fargate 태스크 (또는 GitHub Actions 셀프 호스티드 러너)
       - 저장소 풀
       - Dockerfile 추론 (언어, 패키지 매니저)
       - Daytona / E2B 샌드박스 (타겟 런타임)
       - 클론 -> git worktree -> 에이전트 브랜치
            |
            v
    mini-swe-agent / SWE-agent v2 루프
       Claude Opus 4.7 또는 GPT-5.4-Codex
       도구: ripgrep, tree-sitter, 읽기/편집, run_tests, git
            |
            v
    샌드박스 내 CI 통과 확인 + 커버리지 델타 검사
            |
            v (검증됨)
    git push + GitHub App을 통해 PR 열기
       PR 본문 = 근거 + diff 요약 + 추적 URL
       레이블: needs-review
            |
            v
    운영자가 리뷰; 후속 작업을 위해 @-멘션 에이전트 가능
```

## 스택

- 트리거: 세분화된 토큰을 가진 GitHub App; Lambda 또는 Fly.io를 통한 웹훅 수신기
- 워커: ECS Fargate 태스크 (또는 GitHub Actions 셀프 호스티드 러너)
- 샌드박스: 태스크당 Daytona devcontainer 또는 E2B 샌드박스
- 에이전트 루프: Claude Opus 4.7 / GPT-5.4-Codex를 통한 mini-swe-agent 기준선 또는 SWE-agent v2
- 검색: tree-sitter repo-map + ripgrep
- 검증: 샌드박스 내 전체 CI + 커버리지 델타 게이트
- 관찰 가능성: PR 본문에 링크된 PR별 추적 아카이브가 있는 Langfuse
- 예산: 저장소별 일일 달러 상한, 저장소별 하루 최대 PR 수

## 구축하기

1. **GitHub App.** 세분화된 설치 토큰: issues 읽기+쓰기, pull_requests 쓰기, contents 읽기+쓰기, workflows 읽기. 브랜치 보호(이 작업을 수행할 수 있는 유일한 표면)는 "main에 직접 푸시 금지"와 "강제 푸시 금지"를 적용합니다; 앱은 우회 목록에 없습니다. 워커는 제안된 diff에 대한 허용 목록 검사로 `.github/workflows` 아래에 쓰기를 금지합니다(GitHub App 권한이 경로 범위가 아니기 때문).

2. **웹훅 수신기.** Lambda 함수가 이슈 레이블 / PR 코멘트 웹훅을 수락합니다. `@agent fix this` 레이블로 필터링합니다. SQS에 큐에 넣습니다.

3. **디스패처.** SQS에서 작업을 가져옵니다. 저장소별 일일 예산을 적용합니다. 저장소 URL, 이슈 본문, 새로운 Daytona 샌드박스와 함께 ECS Fargate 태스크를 시작합니다.

4. **환경 추론.** 언어(Python, Node, Go, Rust)와 패키지 매니저(uv, pnpm, go mod, cargo)를 감지합니다. Dockerfile이 없으면 즉시 생성합니다.

5. **에이전트 루프.** mini-swe-agent 또는 SWE-agent v2와 Claude Opus 4.7. 도구: ripgrep, tree-sitter repo-map, read_file, edit_file, run_tests, git. 하드 제한: $20 비용, 30분 벽시계, 30 에이전트 턴.

6. **검증.** 루프가 종료된 후 샌드박스 내에서 전체 테스트 스위트를 실행합니다. jacoco / coverage.py를 통해 커버리지 델타를 계산합니다. CI가 빨간색이면 중단, PR을 열지 않습니다. 커버리지가 2% 이상 떨어지면 `needs-review` 레이블로 PR을 엽니다.

7. **PR 게시.** 에이전트 브랜치를 푸시합니다. GitHub API를 통해 PR을 엽니다: 제목, 근거, diff 요약, 추적 URL, 비용, 턴 수.

8. **자격 증명 위생.** 워커는 단기 GitHub App 설치 토큰으로 실행됩니다. 로그는 보관 전에 비밀 정보가 제거됩니다.

9. **평가.** 다양한 난이도의 30개의 시드된 내부 이슈. 통과율, PR 품질(diff 크기, 스타일, 커버리지), 비용, 레이턴시를 측정합니다. 동일한 이슈에 대해 Cursor Background Agents 및 AWS Remote SWE Agents와 비교합니다.

## 사용하기

```
# github.com에서
  - 사용자가 이슈 #842에 `@agent fix this` 레이블 지정
  - 14분 후 PR #1903이 나타남
  - 본문:
    > widget.dedupe()에서 null comparator 항목으로 인한 NPE 수정
    > 회귀 테스트 widget_test.go::TestDedupeNullComparator 추가
    > 커버리지 델타: +0.12%
    > 턴: 7  비용: $1.80  추적: langfuse:...
    > 레이블: needs-review
```

## 배포하기

`outputs/skill-issue-to-pr.md`가 결과물입니다. 레이블이 지정된 이슈를 제한된 비용과 범위가 지정된 자격 증명으로 리뷰 준비가 된 PR로 전환하는 GitHub App + 비동기 클라우드 워커입니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 30개 이슈에 대한 통과율 | 엔드투엔드 성공 (CI 초록 + 커버리지 OK) |
| 20 | PR 품질 | Diff 크기, 커버리지 델타, 스타일 준수 |
| 20 | 해결된 이슈당 비용 및 레이턴시 | PR당 $ 및 벽시계 시간 |
| 20 | 안전성 | 범위가 지정된 토큰, 저장소별 예산, 강제 푸시 금지, 자격 증명 위생 |
| 15 | 운영자 UX | 근거 코멘트, 재시도 기능, @-멘션 후속 작업 |
| **100** | | |

## 실습

1. "불안정한 테스트 수정" 모드를 추가합니다: `@agent stabilize-flake TestX` 레이블이 테스트를 샌드박스 내에서 50번 실행하고 안정화하는 최소 변경을 제안합니다.

2. 세 개의 공유 이슈에서 Cursor Background Agents와 비용을 비교합니다. 어떤 도구가 어디서 우세한지 보고합니다.

3. 예산 대시보드를 구현합니다: 저장소별 일일 비용, 사용자별 비용. 이상 징후에 대한 알림.

4. "드라이 런" 모드를 구축합니다: CI를 실행하지 않고 초안 PR을 열어 리뷰어가 계획을 저렴하게 검토할 수 있도록 합니다.

5. 보존 정책을 추가합니다: 병합 없이 7일 이상 지난 PR 브랜치는 자동으로 삭제됩니다.

## 주요 용어

| 용어 | 일반적인 사용법 | 정확한 의미 |
|------|----------------|-------------|
| GitHub App | "범위가 지정된 봇 ID" | 세분화된 권한 + 단기 설치 토큰이 있는 앱 |
| 비동기 클라우드 에이전트 | "백그라운드 에이전트" | 터미널이 아닌 클라우드 샌드박스에서 실행되는 비대화형 워커 |
| 환경 추론 | "Dockerfile 합성" | 언어 + 패키지 매니저 감지, 없으면 Dockerfile 생성 |
| 검증 | "샌드박스 내 CI" | PR을 열기 전에 워커 내부에서 전체 테스트 스위트 실행 |
| 커버리지 델타 | "커버리지 보존" | 기준 브랜치에서 에이전트 브랜치로의 테스트 커버리지 % 변화 |
| 저장소별 예산 | "일일 상한" | 디스패처에서 적용되는 달러 및 PR 수 제한 |
| 근거 | "PR 본문 설명" | 무엇이 변경되었고 왜 변경되었는지에 대한 에이전트 요약 |

## 추가 자료

- [AWS Remote SWE Agents](https://github.com/aws-samples/remote-swe-agents) — 표준 비동기 클라우드 에이전트 참조
- [SWE-agent](https://github.com/SWE-agent/SWE-agent) — CLI 참조
- [Cursor Background Agents](https://docs.cursor.com/background-agent) — 상용 대안
- [OpenAI Codex (클라우드)](https://openai.com/codex) — 호스티드 경쟁사
- [Google Jules](https://jules.google) — Google의 호스티드 버전
- [Factory Droids](https://www.factory.ai) — 대체 상용 참조
- [GitHub App 문서](https://docs.github.com/en/apps) — 범위가 지정된 봇 ID
- [Daytona 클라우드 샌드박스](https://daytona.io) — 참조 샌드박스
