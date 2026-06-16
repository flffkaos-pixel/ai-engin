# 대화 상태 추적

> "북쪽에 저렴한 레스토랑을 원해요... 사실 중간 가격으로 바꾸고... 이탈리안도 추가요." 세 턴, 세 가지 상태 업데이트. DST가 슬롯-값 딕셔너리를 동기화하여 예약이 작동하도록 한다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 5 · 17 (Chatbots), Phase 5 · 20 (Structured Outputs)
**Time:** ~75분

## 문제

작업 지향 대화 시스템에서 사용자의 목표는 슬롯-값 쌍의 집합으로 인코딩된다: `{cuisine: italian, area: north, price: moderate}`. 사용자의 각 턴은 슬롯을 추가, 변경 또는 제거할 수 있다. 시스템은 전체 대화를 읽고 현재 상태를 올바르게 출력해야 한다.

DST는 사용자가 말한 것과 백엔드가 실행하는 것 사이의 연결고리다.

## 개념

**작업 구조.** 스키마가 도메인(레스토랑, 호텔, 택시)과 슬롯(cuisine, area, price, people)을 정의한다.

**두 가지 DST 공식화.** 분류 또는 생성.

**메트릭.** JGA(Joint Goal Accuracy) — *모든* 슬롯이 올바른 턴의 비율.

## 직접 구현하기

## 사용하기

```python
from pydantic import BaseModel
from typing import Literal, Optional
import instructor

class RestaurantState(BaseModel):
    cuisine: Optional[Literal["italian", "chinese", "indian", "thai", "any"]] = None
    area: Optional[Literal["north", "south", "east", "west", "center"]] = None
    price: Optional[Literal["cheap", "moderate", "expensive"]] = None
    people: Optional[int] = None

def llm_dst(history, llm):
    prompt = f"""You track the slot values of a restaurant booking across turns.
Dialogue so far:
{render(history)}

Update the state based on the latest user turn. Output only the JSON state."""
    return llm(prompt, response_model=RestaurantState)
```

## 최종 결과물

`outputs/skill-dst-designer.md`로 저장:

```markdown
---
name: dst-designer
description: 대화 상태 추적기를 설계한다 — 스키마, 추출기, 업데이트 정책, 평가.
version: 1.0.0
phase: 5
lesson: 29
tags: [nlp, dialogue, task-oriented]
---
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| DST | 대화 상태 추적. 대화 턴 전체에 걸쳐 슬롯-값 딕셔너리 유지. |
| Slot | 사용자 의도의 단위. 백엔드에 필요한 명명된 파라미터. |
| Domain | 작업 영역. 레스토랑, 호텔, 택시 등 슬롯 집합. |
| JGA | Joint Goal Accuracy. 모든 슬롯이 올바른 턴의 비율. |
| MultiWOZ | 다중 도메인 WOZ 데이터셋. 표준 DST 평가. |
| Ontology-free DST | 고정 목록 없이 슬롯 이름과 값을 직접 생성. |
| Correction | 이전에 채워진 슬롯을 덮어쓰는 턴. |

## 추가 자료

- [Budzianowski et al. (2018). MultiWOZ](https://arxiv.org/abs/1810.00278)
- [Feng et al. (2023). LDST](https://arxiv.org/abs/2310.14970)
- [Heck et al. (2020). TripPy](https://arxiv.org/abs/2005.02877)
- [King, Flanigan (2024). Unsupervised TOD with LLMs](https://arxiv.org/abs/2404.10753)
- [MultiWOZ leaderboard](https://github.com/budzianowski/multiwoz)
