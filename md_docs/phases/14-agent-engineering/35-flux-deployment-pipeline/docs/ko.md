# Flux: 배포 파이프라인

> Flux는 Weave(레슨 34)에서 승인된 평가 상태를 가져와서 프로덕션에 배포한다. Flux 없이는 "이 프롬프트가 승인되었다"는 수동 핸드오프를 의미한다. Flux를 사용하면 실험(Weave)과 프로덕션(배포됨) 사이에 명확한 게이트가 있다.

**Type:** Learn + Build
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 34 (Weave Experiment Management), Phase 14 · 33 (Dify Application)
**Time:** ~90분

## 학습 목표

- Flux가 Weave(승인된 평가 상태)를 프로덕션(배포된 앱)에 연결하는 이유를 설명한다.
- Flux의 네 가지 구성 요소를 명명한다: Regestry, Watcher, Slots, Webhook.
- Flux가 Dify(레슨 33)와 통합되는 방식을 설명한다: Dify DSL에서 Flux를 가져오기.
- 프롬프트 변경 사항을 프로덕션 롤아웃에 연결하는 파이프라인을 구현한다.

## 문제

프롬프트가 승인되면 프로덕션에 들어가야 한다. 수동 핸드오프는 느리고 오류가 발생하기 쉽다. Flux는 "Weave에서 승인된 이 프롬프트를 이 Dify 앱의 프로덕션 워크플로우에 배포한다"는 규칙을 자동화한다.

## 개념

### Flux 개요

Flux는 Dify 에코시스템의 배포 게이트웨이다. Weave(실험 관리, 레슨 34) + Dify(앱 플랫폼, 레슨 33) 사이에 위치한다.

**데이터 흐름:**

```
Weave (experiments) → Flux (gateway) → Dify (production)
```

Weave는 평가를 실행하고 프롬프트를 승인한다. Flux는 승인된 상태를 감시하고 Dify로 내보낸다.

### 구성 요소

1. **Regestry.** 프롬프트와 구성이 승인을 기다리는 저장소. Weave의 평가 결과를 기반으로 승인 상태를 유지한다.
2. **Watcher.** Regestry에서 변경 사항을 폴링하거나 변경 사항을 Flux로 푸시하는 Webhook.
3. **Slots.** Dify 앱의 위치 표시자. 프롬프트가 주입될 수 있는 템플릿 슬롯.
4. **Webhook.** Flux가 Dify로 푸시할 때 Dify가 호출하는 엔드포인트.

### Weave에서 Dify로

1. 프롬프트 템플릿이 Weave에서 평가된다.
2. 평가 점수가 임계값을 충족하면 평가가 승인된다.
3. Watcher가 승인을 감지하고 Regestry에 저장한다.
4. Slots가 승인된 프롬프트를 Dify 앱에 주입한다.
5. Webhook가 Dify를 업데이트하고, 프로덕션 앱이 새 프롬프트로 실행된다.

### 게이팅

Flux는 게이트를 적용한다:

- **평가 점수 게이트.** "이 프롬프트는 Weave 평가 점수 > 0.9여야 한다."
- **수동 승인 게이트.** "프롬프트를 프로덕션으로 승인하려면 인간 운영자가 클릭해야 한다."
- **카나리아 게이트.** "먼저 10%의 트래픽에 배포하고, 24시간 동안 모니터링한 후, 100%로 롤아웃한다."

### 이 패턴이 잘못되는 경우

- **게이트 없음.** Flux가 설치되었지만 게이트가 구성되지 않음 — 평가가 좋지 않은 프롬프트가 프로덕션으로 직접 이동.
- **Watcher만으로 충분하다고 가정.** Watcher는 Flux를 Dify와 연결하지만 Weave에서 Flux로 연결하려면 Regestry가 필요함.
- **카나리아 없음.** 프롬프트가 모든 트래픽에 일괄 배포됨 — 갑작스러운 중단이 발생할 경우 전체 롤아웃을 차단.
- **롤백 계획 없음.** Flux는 새 프롬프트를 배포했지만, 롤백 지점이 없음 — 항상 이전 버전을 보관하고 롤백 메커니즘이 있는지 확인.

## 직접 구현하기

`code/main.py`는 Flux 스타일 배포 파이프라인을 구현:

- **Regestry:** 승인 상태가 있는 프롬프트 저장소. 승인된: 점수 > 임계값.
- **Watcher:** Regestry 변경 사항을 확인하고 Slots에 푸시.
- **Slots:** Dify 앱에 주입할 프롬프트 위치.
- **Webhook:** Slots가 업데이트될 때 호출.

데모: 프롬프트 승인 → Watcher가 감지 → Slots 업데이트 → Webhook 호출.

실행:

```
python3 code/main.py
```

출력: 승인된 프롬프트, Watcher 이벤트, Slot 업데이트, Webhook 호출을 보여주는 배포 파이프라인 트레이스.

## 활용하기

- **Flux** for automated deployment between Weave experiments and Dify production.
- **CI/CD + Dify CLI** if you want to keep the deployment pipeline in version control.
- **Dify Cloud** for hosted deployment without managing your own gateway.

## 배포하기

`outputs/skill-flux-pipeline.md` scaffolds a Flux-style deployment pipeline with Regestry, Watcher, Slots, Webhook, and gate configuration.

## 연습 문제

1. 장난감 파이프라인에 카나리아 게이트 추가: 10% → 24시간 → 100%. 단계가 단계에 어떤 영향을 미치는가?
2. 수동 승인 추가: 게이트는 인간이 Regestry에서 "승인"을 클릭할 때까지 기다린다.
3. 롤백 구현: Slot 업데이트 실패 시 Watcher가 이전 프롬프트로 되돌린다.
4. Flux를 Dify에 연결: Dify DSL에 Flux가 이해할 수 있는 Slot이 있도록 한다.
5. Flux의 Regestry에 Weave 평가 상태를 어떻게 공급하는지 문서화: 평가 출력을 Regestry 입력에 매핑.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Flux | "Dify 배포 게이트웨이" | Weave에서 Dify로 프롬프트 승인 및 배포 |
| Regestry | "프롬프트 승인 저장소" | 프롬프트와 승인 상태를 보관하는 저장소 |
| Watcher | "변경 사항 폴러" | Regestry를 감시하고 변경 사항을 Slots로 푸시 |
| Slots | "프롬프트 위치 표시자" | Dify 앱에서 프롬프트가 주입될 수 있는 위치 |
| Webhook | "Dify 업데이트" | Dify가 슬롯 업데이트를 수신하는 엔드포인트 |
| Gate | "승인 조건" | 프롬프트 승인 전 충족해야 하는 조건(점수, 수동, 카나리아) |
| Canary | "점진적 롤아웃" | 먼저 소규모 트래픽에 배포, 모니터링, 전체 롤아웃 |

## 추가 자료

- [Dify docs, Deployment](https://docs.dify.ai/deployment) — deployment guides
- [Weights & Biases, Weave + Flux](https://weave-docs.wandb.ai/) — experiment + deployment pipeline
- [CI/CD for LLM apps](https://www.latent.space/p/llmops) — broader LLM deployment patterns
