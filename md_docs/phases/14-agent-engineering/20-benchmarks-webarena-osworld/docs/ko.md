# 벤치마크: WebArena와 OSWorld

> WebArena는 네 개의 자체 호스팅 앱에서 웹 에이전트 능력을 테스트한다. OSWorld는 Ubuntu, Windows, macOS에서 데스크톱 에이전트 능력을 테스트한다. 출시 시(2023-2024) 둘 다 최고급 에이전트와 인간 사이에 큰 격차를 보여주었다. 격차는 좁혀지고 있지만 실패 모드는 변하지 않았다.

**Type:** Learn
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 19 (SWE-bench, GAIA)
**Time:** ~60분

## 학습 목표

- WebArena의 네 가지 자체 호스팅 앱과 실행 기반 평가가 중요한 이유를 설명한다.
- OSWorld가 접근성 API 대신 실제 OS 스크린샷을 사용하는 이유를 설명한다.
- 두 가지 주요 OSWorld 실패 모드(GUI 그라운딩 및 운영 지식)를 명명한다.
- OSWorld-G와 OSWorld-Human이 기본 벤치마크 위에 추가하는 것을 요약한다.

## 문제

제너럴리스트 에이전트는 도구를 호출할 수 있다. 20번의 클릭으로 브라우저를 구동하여 쇼핑 체크아웃을 완료할 수 있는가? 키보드와 마우스만으로 Linux 박스를 구성할 수 있는가? 이것이 WebArena와 OSWorld가 답하는 질문이다.

## 개념

### WebArena (Zhou et al., ICLR 2024)

- 네 개의 자체 호스팅 웹 앱(쇼핑 사이트, 포럼, GitLab 유사 개발 도구, 비즈니스 CMS)에서 812개의 장기 작업.
- 지도, 계산기, 스크래치패드 같은 유틸리티 추가.
- 평가는 gym API를 통한 실행 기반 — 주문이 완료되었는가, 이슈가 종료되었는가, CMS 페이지가 업데이트되었는가?
- 출시 시: 최고 GPT-4 에이전트 14.41% 성공 vs 인간 78.24%.

자체 호스팅 프레이밍이 중요 — 대상 앱이 고정되고 재현 가능하기 때문에 벤치마크가 불안정하지 않음.

### 확장

- **VisualWebArena** — 시각적으로 근거한 작업, 성공이 이미지 해석에 달려 있음(스크린샷을 일급 관찰로).
- **TheAgentCompany** (Dec 2024) — 터미널 + 코딩 추가; 실제 원격 작업 환경과 더 유사.

### OSWorld (Xie et al., NeurIPS 2024)

- Ubuntu, Windows, macOS에서 369개의 실제 컴퓨터 작업.
- 실제 애플리케이션의 자유 형식 키보드 및 마우스 제어.
- 1920×1080 스크린샷을 관찰로 사용.
- 출시 시: 최고 모델 12.24% vs 인간 72.36%.

### 주요 실패 모드

1. **GUI 그라운딩.** 픽셀 → 요소 매핑. 모델이 1920×1080에서 UI 요소를 안정적으로 찾는 데 어려움.
2. **운영 지식.** 어떤 메뉴에 설정이 있는지, 어떤 키보드 단축키, 어떤 환경 설정 창. 인간이 수년에 걸쳐 구축하는 지식 꼬리.

### 후속 연구

- **OSWorld-G** — 564개 샘플 그라운딩 스위트 + Jedi 훈련 세트. 계획에서 그라운딩을 분해하여 별도로 측정 가능.
- **OSWorld-Human** — 수동으로 선별된 골드 행동 궤적. 최고 에이전트가 필요한 것보다 1.4-2.7배 더 많은 단계를 사용한다는 것을 보여줌 (궤적 효율성 격차).

### 이것이 중요한 이유

Claude computer use, OpenAI CUA, Gemini 2.5 Computer Use (레슨 21) 모두 WebArena와 OSWorld에 의해 형성된 워크로드로 훈련. 벤치마크는 목표이고, 프로덕션 모델은 출시된 답변이다.

### 벤치마킹이 잘못되는 경우

- **스크린샷 전용 평가.** OSWorld는 스크린샷 기반; DOM이나 접근성 API를 사용하는 에이전트를 OSWorld에서 평가하면 그라운딩 과제를 놓침.
- **궤적 길이 무시.** 성공률만 점수 매기면 OSWorld-Human이 드러내는 1.4-2.7배 단계 비효율을 놓침.
- **오래된 자체 호스팅 앱.** WebArena의 앱은 특정 버전을 고정; 재선별 없이 업데이트하면 비교 가능성이 깨짐.

## 직접 구현하기

`code/main.py`는 장난감 웹 에이전트 하네스를 구현한다:

- 최소 "쇼핑 앱" 상태 머신: list_items, add_to_cart, checkout.
- 3개 작업에 대한 골드 궤적.
- 각 작업을 시도하는 스크립트 기반 에이전트.
- 실행 기반 평가기(상태 확인) 및 궤적 효율성 메트릭(단계 vs 골드).

실행:

```
python3 code/main.py
```

출력: OSWorld-Human의 방법론을 미러링하는 작업당 성공률 및 궤적 효율성.

## 활용하기

- **WebArena Verified** self-hosted on an internal cluster for continuous evaluation.
- **OSWorld** in a VM fleet for desktop agents.
- **Computer-use agents** (레슨 21) — Claude, OpenAI CUA, Gemini — all trained on workloads like these.
- **Your own product flows** — capture gold trajectories for your top 20 tasks; run agents against them weekly.

## 배포하기

`outputs/skill-web-desktop-harness.md` builds a web/desktop agent harness with execution-based eval and trajectory efficiency metric.

## 연습 문제

1. 두 번째 앱(포럼)으로 장난감 하네스 확장. 3개 작업과 골드 궤적 작성.
2. 작업당 궤적 효율성 보고 추가. 장난감에서 에이전트가 골드의 1배, 2배 또는 3배인가?
3. "방해 요소" 도구 구현 — 골드 궤적이 절대 사용하지 않는 것. 스크립트 기반 에이전트가 유혹받는가?
4. OSWorld-G 읽기. 자체 평가에서 그라운딩 실패와 계획 실패를 어떻게 분리할 것인가?
5. WebArena의 앱 README 읽기. 고정된 앱 버전 중 하나를 업그레이드하면 무엇이 깨지는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| WebArena | "웹 에이전트 벤치마크" | 4개 자체 호스팅 앱에서 812개 작업; gym 스타일 평가 |
| VisualWebArena | "시각적 WebArena" | 시각적으로 근거한 WebArena; 스크린샷이 관찰 |
| OSWorld | "데스크톱 에이전트 벤치마크" | 실제 Ubuntu/Windows/macOS에서 369개 작업 |
| GUI grounding | "픽셀-요소 매핑" | 1920x1080에서 UI 요소를 찾는 모델 |
| Operational knowledge | "OS 노하우" | 어떤 메뉴, 어떤 단축키, 어떤 환경 설정 창 |
| OSWorld-G | "그라운딩 스위트" | 564개 그라운딩 전용 샘플 + 훈련 세트 |
| OSWorld-Human | "골드 궤적" | 효율성 측정을 위한 수동 전문가 행동 시퀀스 |
| Trajectory efficiency | "골드 대비 단계" | 에이전트 단계 수를 인간 최소값으로 나눔 |

## 추가 자료

- [Zhou et al., WebArena (arXiv:2307.13854)](https://arxiv.org/abs/2307.13854) — four-app web benchmark
- [Xie et al., OSWorld (arXiv:2404.07972)](https://arxiv.org/abs/2404.07972) — cross-OS desktop benchmark
- [Anthropic, Introducing computer use](https://www.anthropic.com/news/3-5-models-and-computer-use) — Claude's benchmark-shaped capability
- [OpenAI, Computer-Using Agent](https://openai.com/index/computer-using-agent/) — OSWorld and WebArena numbers
