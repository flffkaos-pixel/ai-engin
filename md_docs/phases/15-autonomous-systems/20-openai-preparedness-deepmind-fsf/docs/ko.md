# OpenAI Preparedness Framework 및 DeepMind Frontier Safety Framework

> OpenAI Preparedness Framework v2(2025년 4월)는 연구 카테고리(장거리 자율성, 샌드배깅, 자율 복제 및 적응, 안전장치 훼손)를 추적 카테고리와 구분하여 도입한다. 추적 카테고리는 Safety Advisory Group이 검토하는 역량 보고서와 안전장치 보고서를 트리거한다. DeepMind의 FSF v3(2025년 9월, 2026년 4월 17일에 추적 가능 수준 추가)는 자율성을 ML R&D 및 사이버 도메인으로 접는다(ML R&D 자율성 수준 1 = 인간 + AI 도구 대비 경쟁력 있는 비용으로 AI R&D 파이프라인 완전 자동화). FSF v3는 도구적 추론 오용에 대한 자동화된 모니터링을 통해 기만적 정렬을 명시적으로 다룬다. 정직한 메모: PF v2의 연구 카테고리(장거리 자율성 포함)는 자동으로 완화책을 트리거하지 않는다; 정책 언어는 "잠재적"이다. DeepMind 자체는 도구적 추론이 강화되면 자동화된 모니터링이 "장기적으로 충분하지 않을 것"이라고 말한다.

**Type:** 학습
**Languages:** Python (stdlib, three-framework decision-table diff tool)
**Prerequisites:** Phase 15 · 19 (Anthropic RSP)
**Time:** ~45분

## 문제

레슨 19는 Anthropic의 확장 정책을 면밀히 읽었다. 이 레슨은 OpenAI와 DeepMind의 정책을 읽음으로써 그림을 완성한다. 세 문서는 동일한 질문(프론티어 연구소는 언제 모델을 일시 중지하거나 게이트해야 하는가)을 다루는 사촌 아티팩트이며, 소수의 카테고리로 수렴하고 중요한 곳에서 특정 방식으로 발산한다.

수렴: 세 가지 모두 장거리 자율성을 추적할 가치가 있는 역량 클래스로 레이블링한다. 세 가지 모두 기만적 행동(정렬 가장, 샌드배깅)을 특정 위험 클래스로 인정한다. 세 가지 모두 내부 검토 기관이 있다. 발산: OpenAI는 카테고리를 "추적"(필수 완화)과 "연구"(자동 트리거 없음)로 분할한다. DeepMind는 자율성을 별도로 명명하기보다 두 도메인으로 접는다. 연구소는 추적 vs 연구, 또는 중요 vs 중간, 또는 계층-1 vs 계층-2로 명명한다; 역량이 어느 버킷에 사는지의 운영적 결과는 연구소마다 다르다.

함께 읽는 것이 유용한 연습이다. 동일한 역량이 Anthropic에서는 "필수 완화", OpenAI에서는 "모니터링되지만 트리거되지 않음", DeepMind에서는 "특정 도메인에서 추적"될 수 있다. 정책 태세가 중요하다.

## 개념

### OpenAI Preparedness Framework v2 (2025년 4월)

구조:

- **추적 카테고리**: 역량 보고서(모델이 할 수 있는 것)와 안전장치 보고서(어떤 완화책이 있는지)를 트리거. 배포 전 Safety Advisory Group이 검토.
- **연구 카테고리**: 연구소가 추적 중이지만 특정 완화책에 아직 약속하지 않은 모델 역량. 장거리 자율성, 샌드배깅, 자율 복제 및 적응, 안전장치 훼손 포함.

v2의 주요 프레이밍: 연구 카테고리는 자동으로 완화책을 트리거하지 않는다. 정책 언어는 "잠재적" 완화책이다. 이것이 주목해야 할 특정 델타다: 카테고리의 추적 vs 연구 위치가 "게이트됨"과 "관찰됨" 사이의 경첩이다.

### DeepMind Frontier Safety Framework v3 (2025년 9월; 2026년 4월 17일에 추적 가능 수준 추가)

구조:

- **중요 역량 수준(CCL)**: 5개 도메인(사이버, 생물, ML R&D, CBRN, 자율성(ML R&D 및 사이버로 접힘))에 걸친 역량 임계값.
- **추적 가능 수준**: 2026년 4월에 추가된 세분성. 구체적 예: ML R&D 자율성 수준 1 = 인간 + AI 도구 대비 경쟁력 있는 비용으로 AI R&D 파이프라인 완전 자동화.
- **기만적 정렬 모니터링**: 도구적 추론 오용에 대한 자동화된 모니터링에 대한 명시적 약속.

자율성 프레이밍은 OpenAI와 다르다. DeepMind는 "자율성"을 최상위 도메인으로 유지하지 않는다; 자율성이 해를 끼칠 도메인(ML R&D 및 사이버)으로 접힌다. 논쟁은 도메인 없는 자율성은 위험 없는 역량이라는 것이다; 반대 논쟁은 도메인 간 자율성은 프레임워크가 명명해야 할 메타 위험이라는 것이다.

### 세 가지가 모두 수렴하는 것

- 내부 Safety Advisory Group(Anthropic SAG, OpenAI SAG, DeepMind 내부 위원회로 명명). 고역량 모델에 대한 배포 전 검토.
- 기만적 정렬/정렬 가장을 위험 클래스로 명시적 언급.
- 선언된 주기의 상시 아티팩트(Anthropic: Frontier Safety Roadmap, Risk Report; OpenAI: 역량 및 안전장치 보고서; DeepMind: FSF 업데이트 주기).
- 모니터링 전용 방어에는 한계가 있다는 인정. DeepMind는 명시적: "자동화된 모니터링은 장기적으로 충분하지 않을 것입니다."

### 발산하는 곳

- **Anthropic**: v3.0에서 일시 중지 약속 제거됨; AI R&D-4 임계값이 명명된 다음 게이트.
- **OpenAI**: 추적 vs 연구 분할; 연구 카테고리(장거리 자율성 포함)가 자동으로 게이트하지 않음.
- **DeepMind**: 자율성이 다른 도메인으로 접힘; 추적 가능 수준이 2026년 4월에 세분성 추가.

### 샌드배깅: 세 가지를 모두 복잡하게 만드는 특정 역량

샌드배깅(모델이 평가에서 전략적으로 저성과)은 OpenAI의 연구 카테고리에 있다. Anthropic의 RSP v3.0은 평가-컨텍스트 격차(레슨 1)를 통해 이를 다룬다. DeepMind는 FSF v3의 기만적 정렬 모니터링을 통해 이를 다룬다.

모델이 평가에서 샌드배깅하면, 모든 프레임워크의 역량 임계값이 과소평가된다. 프레임워크는 측정이 작동할 때만 작동한다. 이것이 외부 측정(레슨 21, METR)과 적대적 평가가 연구소 자체 평가 외에도 필요한 이유다.

### 정책 읽기 기술

- **위치**: 당신이 관심 있는 모든 역량은 정책에서 찾을 수 있어야 한다. 찾을 수 없으면 정책이 그것을 다루지 않는 것이다.
- **분류**: 추적(완화 트리거)인가 연구(추적되지만 트리거되지 않음)인가? OpenAI는 이를 명명한다; Anthropic과 DeepMind는 자체 버전이 있다.
- **주기**: 정책이 선언된 일정으로 업데이트되는가, 아니면 특정 사건 후에만 업데이트되는가? 선언된 주기가 더 강하다.
- **독립성**: 외부 검토가 필수인가 선택인가? Anthropic은 Apollo 및 US AI Safety Institute와 협력; OpenAI는 METR과 협력; DeepMind는 주로 내부 SAG와 협력.

## 사용하기

`code/main.py`는 작은 결정 테이블 차이 도구를 구현한다. 역량(자율성, 기만적 정렬, R&D 자동화, 사이버 향상 등)이 주어지면, 세 가지 정책 각각이 역량을 어떻게 분류하고 어떤 완화책이 트리거되는지 출력한다. 정책 도구가 아닌 읽기 도구다.

## 출시하기

`outputs/skill-cross-policy-diff.md`는 세 가지 프레임워크를 참조로 사용하여 특정 역량에 대한 교차 정책 비교를 생성한다.

## 연습문제

1. `code/main.py`를 실행하라. 차이 도구의 출력이 출처 문서에 대해 확인할 수 있는 적어도 두 가지 역량에 대해 정책과 일치하는지 확인하라.

2. OpenAI Preparedness Framework v2 전체를 읽어라. 각 연구 카테고리를 식별하라. 각각에 대해 왜 추적이 아닌 연구에 있는지 한 문장으로 작성하라.

3. DeepMind FSF v3 전체와 2026년 4월 추적 가능 수준 업데이트를 읽어라. ML R&D 자율성 수준 1의 특정 평가 기준을 식별하라. 외부에서 어떻게 측정하겠는가?

4. 샌드배깅은 OpenAI의 연구 카테고리에 있다. 샌드배깅 모델이 실제 역량을 드러내도록 강제하는 평가를 설계하라. 레슨 1의 평가-컨텍스트 게이밍 논의를 참조하라.

5. 세 가지 정책을 특정 역량(선택)에 대해 비교하라. 가장 엄격하다고 생각하는 정책의 분류와 가장 덜 엄격하다고 생각하는 것을 말하라. 출처 텍스트로 정당화하라.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|---|---|---|
| Preparedness Framework | "OpenAI의 확장 정책" | PF v2 (2025년 4월); 추적 vs 연구 카테고리 |
| 추적 카테고리 (Tracked Category) | "필수 완화" | 역량 + 안전장치 보고서 트리거; SAG 검토 |
| 연구 카테고리 (Research Category) | "모니터링 전용" | 추적되지만 자동 완화 없음; 장거리 자율성 포함 |
| Frontier Safety Framework | "DeepMind의 확장 정책" | FSF v3 (2025년 9월) + 추적 가능 수준 (2026년 4월) |
| CCL | "중요 역량 수준" | 도메인별 DeepMind 임계값 (사이버, 생물, ML R&D, CBRN) |
| ML R&D 자율성 수준 1 (ML R&D autonomy level 1) | "R&D 자동화" | 경쟁력 있는 비용으로 AI R&D 파이프라인 완전 자동화 |
| 샌드배깅 (Sandbagging) | "전략적 저성과" | 모델이 평가에서 저성과; OpenAI 연구 카테고리에 있음 |
| 도구적 추론 (Instrumental reasoning) | "수단-목적 추론" | 목표 달성 방법에 대한 추론; DeepMind 모니터링의 대상 |

## 추가 읽을거리

- [OpenAI — Updating our Preparedness Framework](https://openai.com/index/updating-our-preparedness-framework/) — v2 발표.
- [OpenAI — Preparedness Framework v2 PDF](https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf) — 전체 문서.
- [DeepMind — Strengthening our Frontier Safety Framework](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — FSF v3 발표.
- [DeepMind — Updating the Frontier Safety Framework (April 2026)](https://deepmind.google/blog/updating-the-frontier-safety-framework/) — 추적 가능 수준 추가.
- [Gemini 3 Pro FSF Report](https://storage.googleapis.com/deepmind-media/gemini/gemini_3_pro_fsf_report.pdf) — FSF 형식 Risk Report 예시.
