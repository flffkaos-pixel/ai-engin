# AI 환경비اث — 에너지, 물, 탄소

> 2024-2026년 AI 환경비اث 연구는 세 가지 차원으로 발전했다. 에너지: Patterson et al. 2024는 2023년 새로 설치된 데이터센터 전력이 2022년 대비 33% 증가했음을 보여준다; IEA's Datacenter Decarbonization Roadmap (2025)은 2030년까지 데이터센터 탄소 강도 목표를 설정한다. 물: Li et al. 2024(Nature)은 2022년 글로벌 AI 관련 담수 소비가 6-10 billion cubic meters임을 추정한다 — 네덜란드 연간 담수 소비와大致 동일. 폐열: IEA 2025는 AI workload가 데이터센터 폐열 온도를 높여 재활용 가능성을限制한다고 경고한다. 완화: Google의環境報告서(2024)는 2025년까지 탄소 무포인트 달성 목표; Microsoft's Carbon-aware computing initiative는 대기 시간 허용 가능한 작업의 시간을 shifted한다.

**유형:** 학습
**선수 과목:** Phase 18 · 18 (안전 프레임워크)
**소요 시간:** 약 55분

## 학습 목표

- AI 관련 에너지 소비의 규모와 2023년 데이터센터 전력 증가 추세를 설명한다.
- AI 관련 담수 소비 규모를 설명하고 물 관리 맥락에서 그것을 논의한다.
- 데이터센터 폐열 재활용의挑战과 현재 접근 방식을 설명한다.
- 탄소 무포인트, 탄소 인식 컴퓨팅, 대기 시간 허용 작업 이동을 비교한다.

## 문제

AI 모델 훈련과 추론은 상당한 에너지를 소비한다. 데이터센터는 전력과 담수를 모두 소비한다. 환경 지속 가능성에 대한 AI의 영향을 이해하는 것은 조직 수준의 배포 결정과 인프라 설계에 필수적이다.

## 개념

### 에너지 소비

Patterson et al. 2024:
- 2023년 새로 설치된 데이터센터 전력이 2022년 대비 33% 증가.
- 증가의 대부분이 AI 추론 workloads.
- GPU 클러스터의 전력 밀도가 전통적 CPU 서버보다 5-10x 높음.

IEA Datacenter Decarbonization Roadmap (2025):
- 2030년까지 데이터센터 탄소 강도 목표: kWh당 50g CO2.
- 현재 평균: 약 200g CO2/kWh.
- 달성을 위해서는 재생 에너지 procurement, 고효율 냉각, 폐열 재활용이 모두 필요.

### 담수 소비

Li et al. 2024 (Nature):
- 2022년 글로벌 AI 관련 담수 소비: 6-10 billion cubic meters.
- 네덜란드 연간 담수 소비와大致 동일.
- 추론이 훈련보다 더 많은 물을 소비할 수 있음 — 추론은 반복적이며 물리적 하드웨어에서 발생.
- 지역적 불균형: 물 부족 지역에 위치한 데이터센터가 더 큰 영향을 미침.

물 관리 맥락: 담수 소비는蒸发 손실로 water stress를 악화시킨다. 데이터센터가 물 부족 지역에서 운영되면 이는 지역 공동체와 경쟁하는 결과를生成한다.

### 폐열 문제

IEA 2025 경고:
- AI workload는 고밀도 GPU集群에서 실행되어 더 높은 온도의废열을生成.
- 높은 온도의废열은 재활용하기更难 — 더 낮은 품질의 열이다.
- 데이터센터 폐열의 80%는 현재 활용되지 않음.
- 재활용 가능한废열의 온도 임계값: 약 60°C 이상.

현재废열 재활용:
-district heating (코펜하겐, डच 데이터센터에서 사용).
- 온실 농업.
- 산업적 Proses 열.

### 완화 전략

- **탄소 무포인트 (Carbon neutrality).** 발생시킨 탄소 총량을 상쇄. Google의 2025년 목표 — 그러나 상쇄는 실제 감소가 아니다.
- **탄소 인식 컴퓨팅 (Carbon-aware computing).** Microsoft initiative — 대기 시간 허용 가능한 작업을 재생 에너지 가용성이 높은 시기로 이동. 실제로 탄소 배출을 줄인다.
- **고효율 하드웨어.** NVIDIA H100 대 A100 — Performance per watt 향상. 그러나 절대 소비는 여전히 증가.
- **액침 냉각.** Google's Delaware 데이터센터 — 물 대신 유전 사용. 물 소비는 감소하지만 에너지 효율이 높지 않을 수 있다.

## 활용

이 수업에는 코드가 없다. Google의 환경 보고서(2024)와 Microsoft의 탄소 인식 컴퓨팅 문서를 읽는다. 각사의 접근 방식의 강점과 한계를 비교한다.

## 결과물

이 수업은 `outputs/skill-environmental-audit.md`를 생성한다. 데이터센터 운영 또는 AI 서비스 배포 계획이 주어지면 탄소 발자국, 담수 소비,废열 재활용 가능성을 평가하고 완화 전략을 제안한다.

## 연습 문제

1. Patterson et al. 2024와 IEA 2025 데이터센터 보고서를 읽는다. 2030년까지 데이터센터 탄소 강도 목표를 달성하기 위해 필요한 세 가지 주요 변화를 식별한다.

2. Li et al. 2024의 담수 소비 추정을 분석한다. 이 추정치의 주요 불확실성 출처를 식별하고 신뢰 구간을 추정한다.

3. IEA의废열 재활용 온도 임계값(60°C)을 달성하기 위한 세 가지 접근 방식을 제안한다. 각각의 비용과 이점을 분석한다.

4. Google의 탄소 무포인트 대 Microsoft의 탄소 인식 컴퓨팅을 비교한다. 어떤 접근 방식이 더 효과적인 탄소 감소를 달성할 것인지argument한다.

5. 데이터센터 위치 선택이 물 부족 지역에 미치는 영향을 분석한다. 물 관리 맥락에서 데이터센터 위치 결정의 윤리적 함의를discuss한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 탄소 무포인트 | "carbon neutral" | 발생시킨 탄소를 상쇄하여 net zero 달성 |
| 탄소 인식 컴퓨팅 | "시간 이동 workload" | 재생 에너지 가용성에 따라 작업 시간을 조정 |
| 담수 소비 | "freshwater usage" | 담수(염분이 없는 물)의 소비 |
|废열 | "data center heat" | 데이터센터에서 발생하는 열 — 재활용 가능 |
| district heating | "지역 난방" | 데이터센터废열을 지역 난방 시스템에 공급 |
| 탄소 강도 | "g CO2/kWh" | 단위 전력당 탄소 배출량 |
| 액침 냉각 | "immersion cooling" | 유전체 액체에 서버를 담그어 냉각 — 물 사용 감소 |

## 추가 자료

- [Patterson et al. — 2023 Datacenter report (UC Berkeley 2024)](https://eta.internelectric.com/2024-patterson-dc-energy/) — 전력 증가 데이터
- [IEA — Datacenter Decarbonization Roadmap (2025)](https://www.iea.org/reports/datacenter-decarbonization) — 2030 목표
- [Li et al. — Water consumption by AI (Nature 2024)](https://www.nature.com/articles/s41591-024-0302-y) — 담수 소비 추정
- [Google Environmental Report (2024)](https:// sustainability.google/ operating- sustainably/) — 탄소 무포인트 진행