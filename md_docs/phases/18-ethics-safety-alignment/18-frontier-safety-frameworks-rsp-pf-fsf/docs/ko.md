# 프론티어 안전 프레임워크 — RSP, PF, FSF

> 세 가지 주요 실험실 프레임워크가 2026년 프론티어 역량 거버넌스를 정의한다. Anthropic Responsible Scaling Policy v3.0(2026년 2월)은 생물안전 수준을 모델로 한 계층화된 AI Safety Levels(ASL-1부터 ASL-5+)를 도입하며, CBRN 관련 모델에 대해 2025년 5월에 ASL-3이 활성화되었다. OpenAI Prepared Framework v2(2025년 4월)는 추적된 역량에 대한 5개 기준을 정의하고 Capabilities Reports와 Safeguards Reports를 분리한다. DeepMind Frontier Safety Framework v3.0(2025년 9월)은 유해한 조작에 대한 새로운 Harmful Manipulation CCL을 포함한 Critical Capability Levels를 도입한다. 세 가지 모두 이제 동료 실험실이 comparable한 안전 장치 없이 출시하면 지연할 수 있는 경쟁사 조정 조항을 포함한다. 실험실 간 정렬은 구조적이지만 Terminological: "Capability Thresholds", "High Capability thresholds", "Critical Capability Levels"는 유사한 구조를denote한다.

**유형:** 학습
**언어:** 없음
**선수 과목:** Phase 18 · 17 (WMDP), Phase 18 · 07-09 (기만 실패)
**소요 시간:** 약 75분

## 학습 목표

- Anthropic의 ASL 계층 구조와 활성화된 ASL-3을 설명한다.
- OpenAI Prepared Framework v2의 추적된 역량에 대한 5개 기준을 이름 짓는다.
- DeepMind의 Critical Capability Level 구조와 유해한 조작 CCL을 설명한다.
- 경쟁사 조정 조항과 경쟁 역학에 중요한 이유를 설명한다.
- 안전 사례와 세 기둥 구조(모니터링, 이해 불가능성, 무능력)를 정의한다.

## 문제

7-17과는 기만이 가능하고, 이중 용도 역량이 존재하며, 평가에 한계가 있음을確立한다. 프론티어 역량 모델을 가진 실험실은 다음을 요구하는 내부 거버넌스 구조가 필요하다:
- 새 안전 장치가 필요한 때의しきい값을 정의한다.
- 스케일링 전 필요한 평가를 정의한다.
- 안전 사례가 어떤样子보이는지 설명한다.
- 경쟁사가 안전 장치 없이 출시하면 어떻게 할지를处理한다.

세 가지 2025-2026 프레임워크가 현재 최고의 기술 상태이다 — 불완전하고 진화 중이며, 거버넌스 질문이 있는지 여부가 아니라 그들이 Adequate한지이다.

## 개념

### Anthropic Responsible Scaling Policy v3.0 (2026년 2월)

ASL 구조:
- ASL-1: 프론티어 모델이 아니다(프론티어 미만 기준에 포함).
- ASL-2: 현재 프론티어 기준; 일반적인 안전 장치와 함께 배치.
- ASL-3: 카타스트로픽 오남용의 실질적으로 더 높은 위험; CBRN 관련 역량. 2025년 5월에 활성화.
- ASL-4: AI R&D-2 역량 문턱 통과; 입문 수준 AI 연구를 자동화할 수 있는 모델.
- ASL-5+: 고급 AI R&D; 모델이 효과적 스케일링을 급격히加速할 수 있다.

v3.0의 새로운 기능:
- Frontier Safety Roadmaps(편집된 형태로 공개).
- Risk Reports(분기별, 일부는 외부 검토).
- AI R&D가 AI R&D-2와 AI R&D-4로 세분화.
- AI R&D-4가 통과하면, 모델이 부정렬된 목표를 추구할 수 있는 misalignment 위험을 식별하는 affirmative 안전 사례가 필요하다.

### OpenAI Prepared Framework v2 (2025년 4월 15일)

추적된 역량에 대한 5개 기준:
- **그럴듯함.** 합리적인 위협 모델이 존재한다.
- **측정 가능.** 경험적 평가가 가능하다.
- **심각함.** 해害가 크다.
- **순 neto.** 기존 위험을 확대한 것이 아니다.
- **즉각적이거나 돌이킬 수 없음.** 해害가 빠르게 발생하거나 되돌릴 수 없다.

5개 모두를 충족하는 역량이 추적된다. 다른 것은 아니다.

다른 PF v2 구조:
- Capabilities Reports(모델이 할 수 있는 것)와 Safeguards Reports(어떤 통제があるか)를 분리.
- Safety Advisory Group 검토.
- 경영진이 승인;理事会の 안전 및 보안委員회가 감독.
- "조정 조항": 다른 실험실이 comparable한 안전 장치 없이 출시하면 요구를 줄일 수 있다.

### DeepMind Frontier Safety Framework v3.0 (2025년 9월)

도메인별 Critical Capability Levels(CCL):
- 생물무기 향상
- 사이버 향상
- ML R&D 가속
- 유해한 조작(v3.0의 새로운 기능): 고위험 맥락에서 신념/행동을 실질적으로변경할 수 있는 모델.

v2.0(2025년 2월)은 Deceptive Alignment 섹션과 ML R&D CCL에 대한 더 높은 보안 수준을 추가했다.

### 실험실 간 정렬

- Anthropic "Capability Thresholds."
- DeepMind "Critical Capability Levels."
- OpenAI "High Capability thresholds."

업계 표준 용어가 없다. 구조적으로 정렬됨: 세 가지 수준의 프론티어 역량과 게시된 평가 기준. 세 가지 모두 2025년 이후 경쟁사 조정 조항을 포함한다.

### 안전 사례

안전 사례는 배치이容認可能하게 안전하다는 것에 대한 최악의 가정에 따른 written论点이다. 표준 구조는 세 기둥을 대상으로 한다:

- **모니터링.** 나쁜 동작이 발생하면 감지할 수 있는가?
- **이해 불가능성.** 모델이 피해를 caused할 일관된 계획을실행할 능력이 부족한가?
- **무능력.** 모델이 문제의 해害를caused할 능력이 부족한가?

다른 안전 사례가 다른 기둥을 대상으로 한다. ASL-3 CBRN 사례의 경우, 이해 불가능성(언러닝을 통해)이 주요 대상이다. 기만적 정렬의 경우, 모니터링과 이해 불가능성이 대상이다. 사이버 향상의 경우, 세 가지 모두 relevant하다.

### 경쟁 역학 문제

경쟁사 조정 조항은controversial하다. 비평가들은 모든 세 실험실이 경쟁자가defect하면 요구를 줄이면 균형이defection 쪽으로 이동한다고 주장한다. 방어자들은 대안(일방적 안전 장치)이 덜 안전에 Conscious한 실험실이defect하면 더 나쁜 결과를 생성한다고 주장한다.

UK AISI, US CAISI, EU AI Office(24과)는 외부 거버넌스 counterparts이다. 실험실 프레임워크는 자발적이다; 규제 프레임워크는 emergence하고 있다.

## 활용

이 수업에는 코드가 없다. 세 가지 기본 출처를 읽는다: RSP v3.0, PF v2, FSF v3.0. 각 실험실의 계층 구조를 서로에게 매핑하고 다른 실험실이 정의하지 않는 하나しきい값을 식별한다.

## 결과물

이 수업은 `outputs/skill-framework-diff.md`를 생성한다. 안전 프레임워크 또는 출시 노트가 주어지면, 프레임워크의しきい값 정의, 필요한 평가, 안전 사례 구조를 RSP v3.0, PF v2, FSF v3.0과 비교하고 실험실 간 격차를 플래그한다.

## 연습 문제

1. RSP v3.0, PF v2, FSF v3.0을 읽는다. 각 실험실의 CBRN 문턱, AI R&D 문턱, 배포 전 필요한 평가를 表にまとめよ.

2. 경쟁사 조정 조항은 세 프레임워크(2025년 이후)에 포함된다. 것에 대한 한 단락을argument한다; 에 대한 한 단락을argument한다. 각 위치가依赖하는 가정을 식별한다.

3. Anthropic의 AI R&D-4 문턱을 통과하는 모델에 대한 안전 사례를 설계한다. 세 기둥(모니터링, 이해 불가능성, 무능력) 각각에 필요한 증거를 이름 짓는다.

4. DeepMind의 FSF v3.0은 유해한 조작 CCL을 도입한다. 모델이 이 문턱을 통과했음을 나타낼 세 가지 경험적 측정을 제안한다.

5. METR의 "프론티어 AI 안전 정책의 공통 요소"(2025)를 읽는다. 세 가지 가장 강한 실험실 간 수렴과 두 가지 가장 큰 차이를 이름 짓는다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| RSP | "Anthropic의 프레임워크" | Responsible Scaling Policy; ASL 계층; v3.0 2026년 2월 |
| PF | "OpenAI의 프레임워크" | Prepared Framework; 5개 기준; v2 2025년 4월 |
| FSF | "DeepMind의 프레임워크" | Frontier Safety Framework; CCL; v3.0 2025년 9월 |
| ASL-3 | "생물안전 수준 3 아날로그" | CBRN 관련 역량에 대한 Anthropic 계층; 2025년 5월에 활성화 |
| CCL | "중요 역량 수준" | DeepMind의 도메인별しきい값 구성 |
| 안전 사례 | "형식적论点" | 최악의 U에서 배치이容認可能하게 안전하다는 것에 대한 written论点 |
| 조정 조항 | "경쟁자 defection 허용" | 경쟁사가 comparable한 안전 장치 없이 출시하면 요구를 줄이는 프레임워크 조항 |

## 추가 자료

- [Anthropic — Responsible Scaling Policy v3.0 (2026년 2월)](https://www.anthropic.com/responsible-scaling-policy) — ASL 계층, 로드맵, AI R&D 세분화
- [OpenAI — Updating the Prepared Framework (2025년 4월 15일)](https://openai.com/index/updating-our-preparedness-framework/) — 5개 기준, 조정 조항
- [DeepMind — Strengthening our Frontier Safety Framework (2025년 9월)](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — CCL v3.0, 유해한 조작
- [METR — Common Elements of Frontier AI Safety Policies (2025)](https://metr.org/blog/2025-03-26-common-elements-of-frontier-ai-safety-policies/) — 실험실 간 비교