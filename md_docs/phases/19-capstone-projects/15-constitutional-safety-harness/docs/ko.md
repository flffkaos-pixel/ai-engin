# 캡스톤 15 — 헌법적 안전 하네스 + 레드팀 레인지

> Anthropic의 Constitutional Classifiers, Meta의 Llama Guard 4, Google의 ShieldGemma-2, NVIDIA의 Nemotron 3 Content Safety, 다국어 커버리지를 위한 X-Guard가 2026년 안전 분류기 스택을 정의했습니다. garak, PyRIT, NVIDIA Aegis, promptfoo는 표준 적대적 평가 도구가 되었습니다. NeMo Guardrails v0.12는 이를 프로덕션 파이프라인으로 연결합니다. 이 캡스톤은 모든 것을 하나로 연결합니다: 타겟 앱 주변의 계층형 안전 하네스, 6개 이상의 공격 패밀리를 실행하는 자율 레드팀 에이전트, 그리고 측정 가능한 무해성 델타를 생성하는 헌법적 자기 비평 실행입니다.

**Type:** Capstone
**Languages:** Python (안전 파이프라인, 레드팀), YAML (정책 설정)
**Prerequisites:** Phase 10 (LLM 처음부터), Phase 11 (LLM 엔지니어링), Phase 13 (도구), Phase 14 (에이전트), Phase 18 (윤리, 안전, 정렬)
**Phases exercised:** P10 · P11 · P13 · P14 · P18
**Time:** 25시간

## 문제

2026년 LLM 안전의 최전선은 분류기가 작동하는지 여부(대체로 작동함)가 아니라, 프로덕션 앱 주변에서 과잉 거부 없이 또는 명백한 구멍을 남기지 않고 이를 올바르게 구성하는 방법입니다. Llama Guard 4는 영어 정책 위반을 처리합니다. X-Guard(132개 언어)는 다국어 젤브레이크를 처리합니다. ShieldGemma-2는 이미지 기반 프롬프트 인젝션을 잡아냅니다. NVIDIA Nemotron 3 Content Safety는 엔터프라이즈 카테고리를 다룹니다. Anthropic의 Constitutional Classifiers는 서빙 중이 아닌 학습 중에 사용되는 별도의 접근 방식입니다.

공격 진화도 중요합니다. PAIR와 TAP은 젤브레이크 발견을 자동화합니다. GCG는 그래디언트 기반 접미사 공격을 실행합니다. 다중 턴 및 코드 전환 공격은 에이전트 메모리를 악용합니다. 모든 배포된 LLM은 레드팀 레인지(garak과 PyRIT이 표준 드라이버)와 문서화된 완화 조치 및 CVSS 점수 매겨진 발견 사항이 필요합니다.

타겟 애플리케이션(8B 명령어 튜닝 모델 또는 다른 캡스톤의 RAG 챗봇 중 하나)을 강화하고, 6개 이상의 공격 패밀리를 실행하며, 전후 무해성 측정 결과를 생성합니다.

## 개념

안전 파이프라인은 다섯 개의 계층으로 구성됩니다. **입력 정제**: 제로 너비 문자 제거, base64/rot13 디코딩, 유니코드 정규화. **정책 계층**: NeMo Guardrails v0.12 레일(오프도메인, 유해성, PII 추출). **분류기 게이트**: 입력에 Llama Guard 4, 비영어에 X-Guard, 이미지 입력에 ShieldGemma-2. **모델**: 타겟 LLM. **출력 필터**: 출력에 Llama Guard 4, Presidio PII 스크러빙, 해당되는 경우 인용 강제. **HITL 계층**: 고위험으로 플래그된 출력은 Slack 큐로 전송됩니다.

레드팀 레인지는 스케줄러에서 실행됩니다. PAIR와 TAP은 자율적으로 젤브레이크를 발견합니다. GCG는 그래디언트 기반 접미사 공격을 실행합니다. ASCII / base64 / rot13 인코딩 공격. 다중 턴 공격(페르소나 채택, 메모리 악용). 코드 전환 공격(영어와 스와힐리어 또는 태국어 혼합). 각 실행은 CVSS 점수와 공개 타임라인이 포함된 구조화된 발견 파일을 생성합니다.

헌법적 자기 비평 실행은 학습 시간 개입입니다. 1,000개의 유해 시도 프롬프트를 가져와 모델이 응답을 초안 작성하고, 헌법(해를 끼치지 않는 규칙)에 대해 비평하며, 비평 루프에서 재학습합니다. 보류된 평가에서 전후 무해성 델타를 측정합니다.

## 아키텍처

```
요청 (텍스트 / 이미지 / 다국어)
      |
      v
입력 정제 (제로 너비 제거, 디코딩, 정규화)
      |
      v
NeMo Guardrails v0.12 레일 (오프도메인, 정책)
      |
      v
분류기 게이트:
  Llama Guard 4 (영어)
  X-Guard (다국어, 132개 언어)
  ShieldGemma-2 (이미지 프롬프트)
  Nemotron 3 Content Safety (엔터프라이즈)
      |
      v (허용)
타겟 LLM
      |
      v
출력 필터: Llama Guard 4 + Presidio PII + 인용 검사
      |
      v
플래그된 출력을 위한 HITL 계층

병렬:
  레드팀 스케줄러
    -> garak (클래식 공격)
    -> PyRIT (오케스트레이티드 레드팀)
    -> 자율 젤브레이크 에이전트 (PAIR + TAP)
    -> GCG 접미사 공격
    -> 다국어 / 코드 전환
    -> 다중 턴 페르소나 채택

출력: CVSS 점수 매겨진 발견 사항 + 공개 타임라인 + 전후 무해성 델타
```

## 스택

- 안전 분류기: Llama Guard 4, ShieldGemma-2, NVIDIA Nemotron 3 Content Safety, X-Guard
- 가드레일 프레임워크: NeMo Guardrails v0.12 + OPA
- 레드팀 드라이버: garak (NVIDIA), PyRIT (Microsoft Azure), NVIDIA Aegis, promptfoo
- 젤브레이크 에이전트: PAIR (Chao et al., 2023), Tree-of-Attacks (TAP), GCG 접미사
- 헌법적 학습: Anthropic 스타일 자기 비평 루프 + 비평에 대한 SFT
- PII 스크러버: Presidio
- 타겟: 8B 명령어 튜닝 모델 또는 다른 캡스톤의 RAG 챗봇 중 하나

## 구축하기

1. **타겟 설정.** vLLM에서 8B 명령어 튜닝 모델을 구동합니다(또는 다른 캡스톤의 RAG 챗봇 재사용). 이것이 테스트 대상 앱입니다.

2. **안전 파이프라인 래핑.** 타겟 주변에 5계층 파이프라인을 연결합니다. 각 계층이 개별적으로 관찰 가능한지 확인합니다(Langfuse에서 계층별 스팬).

3. **분류기 커버리지.** Llama Guard 4, X-Guard(다국어), ShieldGemma-2(이미지)를 로드합니다. 각각을 작은 레이블링된 세트에서 실행하여 기준선을 설정합니다.

4. **레드팀 스케줄러.** garak, PyRIT, PAIR 에이전트, TAP 에이전트, GCG 실행기, 다중 턴 공격자, 코드 전환 공격자를 스케줄링합니다. 각각은 별도의 큐에서 실행됩니다.

5. **공격 스위트.** 6개 공격 패밀리: (1) PAIR 자동화 젤브레이크, (2) TAP 트리-오브-어택, (3) GCG 그래디언트 접미사, (4) ASCII / base64 / rot13 인코딩, (5) 다중 턴 페르소나, (6) 다국어 코드 전환. 패밀리별 성공률을 보고합니다.

6. **헌법적 자기 비평.** 1,000개의 유해 시도 프롬프트를 선별합니다. 각각에 대해 타겟이 응답을 초안 작성합니다. 비평 LLM이 헌법("해를 끼치지 말 것", "증거 인용", "불법 요청 거부")에 따라 점수를 매깁니다. 비평가가 이의를 제기한 프롬프트는 재작성되고, 타겟은 비평으로 개선된 쌍에 대해 파인튜닝됩니다. 보류된 평가에서 전후 무해성을 측정합니다.

7. **과잉 거부 측정.** 양성 프롬프트 스위트(예: XSTest)에서 거짓 양성률을 추적합니다. 타겟은 양성 질문에 대해 도움이 되는 상태를 유지해야 합니다.

8. **CVSS 점수 매기기.** 각 성공적인 젤브레이크에 대해 CVSS 4.0(공격 벡터, 복잡성, 영향)으로 점수를 매깁니다. 공개 타임라인 및 완화 계획을 생성합니다.

9. **레인지 자동화.** 위의 모든 것이 크론에서 실행되고, 발견 사항은 큐에 기록되며, 과잉 거부 회귀 알림이 Slack으로 전송됩니다.

## 사용하기

```
$ safety probe --model=target --family=PAIR --budget=50
[attacker]   타겟에서 PAIR 에이전트 실행 중
[attack]     시도 1/50: 학술 연구로 질문 위장 ... 차단됨
[attack]     시도 2/50: 롤플레이 호소 ... 차단됨
[attack]     시도 3/50: 사고사슬 유도 ... 성공
[finding]    CVSS 4.8 중간: 타겟에서 롤플레이 우회
[range]      50회 중 7회 성공 (14% 성공률)
```

## 배포하기

`outputs/skill-safety-harness.md`가 결과물입니다. 프로덕션 등급의 계층형 안전 파이프라인과 전후 무해성 델타가 포함된 재현 가능한 레드팀 레인지입니다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 공격 표면 커버리지 | 6개 이상의 공격 패밀리, 2개 이상의 언어 실행 |
| 20 | 진양성 / 거짓양성 트레이드오프 | 공격 차단률 대 XSTest 양성 통과율 |
| 20 | 자기 비평 델타 | 보류된 평가에서 전후 무해성 |
| 20 | 문서화 및 공개 | CVSS 점수 매겨진 발견 사항 및 타임라인 |
| 15 | 자동화 및 재현성 | 모든 것이 크론에서 알림과 함께 실행 |
| **100** | | |

## 실습

1. RAG 챗봇에서 garak의 프롬프트 인젝션 플러그인을 실행하고 출력 필터 계층 유무에 따른 공격 성공률을 비교합니다.

2. 일곱 번째 공격 패밀리를 추가합니다: 검색된 문서를 통한 간접 프롬프트 인젝션. 필요한 추가 방어를 측정합니다.

3. "거부하며 도움주기" 모드를 구현합니다: 가드레일이 차단할 때, 모델이 단순 거부 대신 더 안전한 관련 답변을 제공합니다. XSTest 델타를 측정합니다.

4. 다국어 커버리지 격차: X-Guard가 저조한 성능을 보이는 언어를 찾습니다. 이를 타겟으로 하는 파인튜닝 데이터셋을 제안합니다.

5. 헌법적 자기 비평을 30B 모델에서 실행하고 델타가 확장되는지 측정합니다.

## 주요 용어

| 용어 | 일반적인 사용법 | 정확한 의미 |
|------|----------------|-------------|
| 계층형 안전 | "심층 방어" | 입력, 게이트, 출력, HITL의 여러 가드레일 |
| Llama Guard 4 | "Meta의 안전 분류기" | 2026년 참조 입출력 콘텐츠 분류기 |
| PAIR | "젤브레이크 에이전트" | LLM 기반 젤브레이크 발견 논문 (Chao et al.) |
| TAP | "트리-오브-어택" | PAIR의 트리 검색 변형 |
| GCG | "탐욕 좌표 그래디언트" | 그래디언트 기반 적대적 접미사 공격 |
| 헌법적 자기 비평 | "Anthropic 스타일 학습" | 타겟 초안 -> 비평가 점수 -> 재작성 -> 재학습 |
| XSTest | "양성 프로브 세트" | 과잉 거부 회귀를 위한 벤치마크 |
| CVSS 4.0 | "심각도 점수" | 안전 발견 사항을 위한 표준 취약점 점수 |

## 추가 자료

- [Anthropic Constitutional Classifiers](https://www.anthropic.com/research/constitutional-classifiers) — 학습 시간 참조
- [Meta Llama Guard 4](https://ai.meta.com/research/publications/llama-guard-4/) — 2026년 입출력 분류기
- [Google ShieldGemma-2](https://huggingface.co/google/shieldgemma-2b) — 이미지 + 멀티모달 안전
- [NVIDIA Nemotron 3 Content Safety](https://developer.nvidia.com/blog/building-nvidia-nemotron-3-agents-for-reasoning-multimodal-rag-voice-and-safety/) — 엔터프라이즈 참조
- [X-Guard (arXiv:2504.08848)](https://arxiv.org/abs/2504.08848) — 132개 언어 다국어 안전
- [garak](https://github.com/NVIDIA/garak) — NVIDIA 레드팀 도구킷
- [PyRIT](https://github.com/Azure/PyRIT) — Microsoft 레드팀 프레임워크
- [NeMo Guardrails v0.12](https://docs.nvidia.com/nemo-guardrails/) — 레일 프레임워크
- [PAIR (arXiv:2310.08419)](https://arxiv.org/abs/2310.08419) — 젤브레이크 에이전트 논문
