# 법적 핵심 및 규정 준수

> AI 에이전트는 모든 관할권에서 적용되며 글로벌 규정(예: EU AI Act, NIST AI RMF)을 준수해야 한다. EU AI Act는 2024-2027년에 단계적으로 시행된다. 이 레슨은 필요한 인증이 아닌 인식에 관한 것이다. AI 에이전트를 만드는 모든 사람이 전문 규정 준수 변호사가 되어야 한다는 의미는 아니다.

**Type:** Learn
**Languages:** None
**Prerequisites:** None
**Time:** ~30분

## 학습 목표

- EU AI Act(금지된 관행, 고위험 분류, GPAI 의무)의 핵심 구조를 설명한다.
- NIST AI RMF(Govern, Map, Measure, Manage)의 네 가지 기능을 명명한다.
- 안전, 관찰 가능성, 평가(Phase 14 전체)를 규정 준수 요구 사항에 연결한다.
- AI 규정 준수에 대한 전문 법률 조언을 구해야 하는 시기를 인식한다.

## 문제

AI 규정이 존재하며 확장되고 있다. 이 레슨은 변호사를 대체하는 것이 아니라, 엔지니어가 현재 법적 범위에 대해 인식하도록 하는 것이다. 전문 법률 조언을 구해야 하는 시기를 알기 위해서다. 규정을 완전히 이해하지 않고 준수한다고 가정하지 마라.

## 개념

### EU AI Act

- 계층적 위험 기반 프레임워크.
- **금지됨** (2025년 2월 2일부터 적용). 예: 사회적 점수, 실시간 원격 생체 인식.
- **고위험** (2026년 8월 2일부터 적용). 예: 고용, 중요 인프라, 법 집행. 적합성 평가 필요.
- **GPAI** (2025년 8월 2일부터 적용). 범용 AI 모델에 대한 투명성 의무.
- **제한된 위험.** 투명성(사용자에게 AI임을 알림).
- **최소 위험.** 규제 없음.

### NIST AI RMF

네 가지 기능:

1. **Govern (Govern).** 정책, 책임, 위험 허용 범위 수립.
2. **Map (Map).** 사용 사례 맥락화, 위험 식별, 영향 평가.
3. **Measure (Measure).** 신뢰성 특성 테스트(정확성, 안전성, 보안, 회복력).
4. **Manage (Manage).** 위험을 정기적으로 모니터링하고 대응.

### Phase 14와의 연관성

| Phase 14 레슨 | NIST 기능 | EU AI Act 연관성 |
|---------------|-----------|-----------------|
| 안전(레슨 27, 39) | Measure, Manage | 고위험 적합성 |
| 관찰 가능성(레슨 23-24) | Measure | GPAI 투명성 |
| 평가(레슨 30) | Measure | 고위험 성능 |
| 방어 UX(레슨 28) | Govern | 제한된 위험 투명성 |
| 해석 가능성(레슨 29) | Measure | GPAI 투명성 |

### 오해

**"AI Act는 아직 적용되지 않는다."** 금지 사항은 2025년 2월, 대부분은 2026년 8월에 적용된다.

**"나는 EU에 있지 않다."** AI Act는 EU 시장에 대한 접근을 통제한다. EU 외부 회사도 EU 사용자에게 도달하는 제품의 경우 준수해야 한다.

**"내 모델이 API를 통해 제공되므로 GPAI가 아니다."** GPAI 의무는 API 제공에도 적용된다.

**"오픈소스는 면제된다."** AI Act는 오픈소스 GPAI에 대한 제한된 면제를 포함하지만, 고위험 시스템은 여전히 포함된다.

### 이 패턴이 잘못되는 경우

- **법적 조언 없이 준수한다고 가정.** 문서를 읽고 "준수"라고 결정 — 문서는 변호사를 대체하지 않음.
- **규정 준수를 품질과 혼동.** 평가 점수가 높다고 해서 규정을 준수하는 것은 아님.
- **EU AI Act에만 집중.** 다른 관할권이 자체 법률을 개발 중. 규정 준수는 글로벌.

## 직접 구현하기

`code/main.py`는 규정 준수 체크리스트와 감사 로그를 구현:

- **규정 준수 체크리스트:** EU AI Act 위험 분류, 사용 사례가 적용되는지 확인. NIST 기능 매핑.
- **감사 로그:** 엔지니어링 결정이 수집됨 — 프롬프트 모듈화, 안전, 평가. 배포 로그에 기록.
- **아니요, 법적 조언을 대체하지 않음.** 표시됨.

실행:

```
python3 code/main.py
```

출력: 체크리스트 결과, 감사 로그 항목.

## 활용하기

- 규정 준수 변호사에게 Phase 14의 문서(안전, 평가, 관찰 가능성)를 제공하여 검토.
- 감사 로그에 엔지니어링 결정을 기록 — 미래의 규정 준수 감사 대비.
- EU AI Act, NIST RMF, 기타 관련 규정의 변경 사항을 정기적으로 검토.

## 배포하기

`outputs/skill-compliance-scaffold.md` scaffolds a compliance checklist and audit log aligned with EU AI Act and NIST AI RMF.

## 연습 문제

1. 체크리스트를 프로덕션 에이전트에 적용: 귀하의 사용 사례가 EU AI Act에서 어떤 위험 분류에 속하는가?
2. NIST AI RMF 기능에 대한 엔지니어링 결정을 감사 로그에 기록: 각 Phase 14 레슨이 어떤 기능과 일치하는가?
3. 규정 준수 요구 사항을 해당 Phase 14 방어 수단에 연결: 분류기가 EU AI Act의 "고위험"과 어떻게 연결되는가?
4. 다른 관할권 조사: 귀하의 시장과 관련된 규정은 무엇인가?
5. 규정 준수 체크리스트를 엔지니어링 파이프라인에 통합: 모든 배포 전에 확인.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| EU AI Act | "EU AI 법률" | 위험 기반 AI 규정 프레임워크 |
| NIST AI RMF | "미국 AI 위험 프레임워크" | Govern, Map, Measure, Manage |
| Prohibited | "허용되지 않음" | 금지된 AI 관행 (2025년 2월부터 적용) |
| High-risk | "적합성 필요" | 엄격한 요구 사항이 있는 고위험 시스템 (2026년 8월부터 적용) |
| GPAI | "범용 AI" | 범용 AI 모델에 대한 투명성 의무 |
| Conformity assessment | "규정 준수 감사" | 법적 요구 사항 충족 확인 |

## 추가 자료

- [EU AI Act (Regulation 2024/1689)](https://eur-lex.europa.eu/eli/reg/2024/1689) — the regulation itself
- [NIST AI RMF 1.0](https://www.nist.gov/artificial-intelligence/executive-order-safe-secure-and-trustworthy-artificial-intelligence) — four-function framework
- [EU AI Act compliance checker (EC)](https://artificialintelligenceact.eu/assessment/) — check your use case
