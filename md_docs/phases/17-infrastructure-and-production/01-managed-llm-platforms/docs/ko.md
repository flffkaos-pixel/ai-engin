# 관리형 LLM 플랫폼 — Bedrock, Vertex AI, Azure OpenAI

> 세 개의 하이퍼스케일러, 세 가지 뚜렷한 전략. AWS Bedrock은 모델 마켓플레이스입니다 — 하나의 API 뒤에 Claude, Llama, Titan, Stability, Cohere. Azure OpenAI는 독점적인 OpenAI 파트너십과 전용 용량을 위한 Provisioned Throughput Units (PTU)입니다. Vertex AI는 최상의 장기 컨텍스트와 멀티모달 스토리를 가진 Gemini-first입니다. 2026년 Artificial Analysis는 Llama 3.1 405B 등가물에서 Azure OpenAI를 ~50 ms 중앙값으로, Bedrock을 ~75 ms로 측정합니다 — PTU가 격차를 설명합니다, 왜냐하면 전용 용량이 공유 온디맨드를 능가하기 때문입니다. 결정 규칙은 "어느 것이 가장 빠른가"가 아니라 "어느 모델 카탈로그와 FinOps 표면이 내 제품과 맞느냐"입니다. 이 레슨은 분위기가 아닌权衡을 서면으로 정리하여 선택하도록 가르칩니다.

**유형:** 학습
**언어:** Python (stdlib, toy cost-and-latency 비교기)
**선수 과목:** Phase 11 (LLM Engineering), Phase 13 (Tools & Protocols)
**소요 시간:** ~60분

## 학습 목표

- 세 가지 플랫폼 전략 (마켓플레이스 대 독점 대 Gemini-first)을 이름 짓고 각각을 제품 사용 사례와 매핑합니다.
- Azure OpenAI에서 Provisioned Throughput Units (PTU)가 무엇을 사는 지 설명하고 405B 규모에서 온디맨드 Bedrock이 일반적으로 ~25 ms 더 느리게 읽는 이유를 설명합니다.
- 각 플랫폼의 FinOps 귀인 표면을 다이어그램으로 그립니다 (Bedrock Application Inference Profiles 대 Vertex team별 프로젝트 대 Azure scopes + PTU 예약).
- "이중 제공자 최소" 정책을 서면으로 작성하고 2026년 단일 공급업체 종속이 비용이 많이 드는 실수인 이유를 설명합니다.

## 문제

Claude 3.7 Sonnet을 제품에 선택했습니다. 이제 그것을 제공해야 합니다. Anthropic API를 직접 호출하거나, AWS Bedrock을 통해 호출하거나, 게이트웨이를 통과할 수 있습니다. 직접 API가 가장 간단합니다; Bedrock은 BAA, VPC 엔드포인트, IAM, CloudWatch 귀인을 추가합니다. 게이트웨이는 장애 조치, 통합 청구, 제공자 간 비율 제한을 추가합니다.

더 깊은 질문은 카탈로그입니다. 같은 제품에서 Claude와 Llama와 Gemini가 모두 필요하면, 그 곳이 Bedrock plus Vertex plus Azure OpenAI를 동시에でない 한 한 곳에서 모두 살 수 없습니다. 하이퍼스케일러는 상호 교환 가능하지 않습니다 — 각각이 모델 레이어를 누가 소유할 것인지에 대해 다른 내기를 했습니다.

이 레슨은 세 가지 내기, 지연 시간 격차, FinOps 격차, 종속 위험을 매핑합니다.

## 개념

### 세 가지 전략

**AWS Bedrock** — 마켓플레이스. Claude (Anthropic), Llama (Meta), Titan (AWS 1차), Stability (이미지), Cohere (임베딩), Mistral, plus 이미지 및 임베딩 하위 카탈로그. 하나의 API, 하나의 IAM 표면, 하나의 CloudWatch 익스포트. Bedrock의 내기는 고객이 단일 모델보다 선택권을 더 원한다는 것입니다.

**Azure OpenAI** — 독점적 파트너십. Azure 데이터 센터에서 GPT-4 / 4o / 5 / o-series, DALL·E, Whisper 및 OpenAI 모델의 fine-tuning을 얻습니다. "Azure OpenAI Service" 카탈로그에 비OpenAI 모델 없음 —它们는 Azure AI Foundry로갑니다 (별도 제품). Azure의 내기는 OpenAI가 프론티어에 남아 있고 고객이 그 특정 관계에서 기업 제어를 원한다는 것입니다.

**Vertex AI** — Gemini first, 나머지는 second. Gemini 1.5 / 2.0 / 2.5 Flash 및 Pro, plus Model Garden (서드파티). Vertex의 내기는 멀티모달 장기 컨텍스트입니다 — 1M 토큰 Gemini 컨텍스트가 차별화 요소입니다.

### 규모에서의 지연 시간 격차

Artificial Analysis가 지속적인 벤치마크를 실행합니다. 동등한 Llama 3.1 405B 배포 (공유 온디맨드)에서 Azure OpenAI 중앙값 첫 번째 토큰 지연 시간은 약 50 ms입니다; Bedrock은 약 75 ms입니다. 격차는 AWS 실패가 아니라 용량 모델 차이입니다. Azure는 PTU (Provisioned Throughput Units)를 판매하여 테넌트 전용 GPU 용량을 예약합니다. Bedrock의 동등물 (Provisioned Throughput)이 존재하지만 단위당 ~$21/시간에서 시작하고 대부분의 고객은 공유 온디맨드에 있습니다.

온디맨드 공유 용량은 다른 모든 고객의 트래픽과 경쟁합니다. 전용 용량은 경쟁하지 않습니다. 제품 SLA가 P99에서 TTFT < 100 ms이면 Azure에서 PTU를 사거나, Bedrock Provisioned Throughput을 사거나, 기본 분산을 受け入れ해야 합니다.

### Provisioned Throughput 경제학

Azure PTU: 예약된 추론 컴퓨트 블록. 예측 가능한 작업에서 온디맨드 대비 최대 70% 절감. 트래픽과 무관하게 시간당 고정 비용 — 유휴시에도 예약에 지불합니다. 균형점은 보통 지속적으로 40-60% 이용률 근처입니다.

Bedrock Provisioned Throughput: 모델 및 지역에 따라 $21-$50/시간. 유사한 계산 — 균형점은 피크 활용의 약 절반입니다. 월별 커밋먼트가 필요합니다.

Vertex Provisioned 용량은 Gemini SKU별로 판매됩니다; 가격은 모델 및 지역에 따라 다르며 공개적으로广告される较少합니다.

### FinOps 표면 — 실제 차별화

**Bedrock Application Inference Profiles**는 마켓플레이스에서 가장 깨끗한 귀인입니다. `team`, `product`, `feature`로 프로필에 태그를 지정합니다; 모든 모델 호출을 프로필을 통해 라우팅합니다; CloudWatch가 사후 처리 없이 프로필별로 비용을 구분합니다. 2025년 추가, 여전히 가장 세분화된 하이퍼스케일러 네이티브.

**Vertex** 귀인은 team별 프로젝트 plus 레이블到处. 각 팀을 GCP 프로젝트로 모델링하고, 모든 리소스에 레이블을 지정하고, BigQuery Billing Export + DataStudio를 사용하여 롤업합니다. 더 많은 작업이지만 BigQuery가 비용 데이터에 대한 임의의 SQL을 제공합니다.

**Azure**는 subscription/resource-group scopes plus 태그에 의존하며 PTU 예약을 일등 비용 객체로 합니다. 태그는 리소스 그룹에서 상속되지 요청에서 상속되므로 요청당 귀인에는 Application Insights 사용자 정의 메트릭 또는 헤더에 스탬프를 지정하는 게이트웨이가 필요합니다.

패턴: Bedrock 네이티브가 가장 깨끗하고, Vertex가 BigQuery를 통해 가장 유연하며, Azure는 계측하지 않는 한 가장 불투명합니다.

### 종속이 2026년 위험입니다

단일 하이퍼스케일러 커밋은 하나의 모델이 지배할 때 괜찮았습니다. 2026년 프론티어가每月 이동합니다 — 한 분기에는 Claude 3.7, 다음에는 Gemini 2.5, 그 다음 분기에는 GPT-5. 하나의 플랫폼에 잠기면 프론티어의 3분의 2에서 배제됩니다.

팀이 채택하는 패턴: 제품 중요 LLM 호출에 대해 이중 제공자 최소. 일반적인 쌍은 Bedrock plus Azure OpenAI — 하나에서 Claude, 다른 하나에서 GPT, 그들 간 장애 조치, 동일한 게이트웨이. 비용 상승은 게이트웨이가 최적路由하기 때문에 무시할 수 있습니다; 가동 중지 시간 (2025년 1월 Azure OpenAI 인시던트, AWS us-east-1 정전 같은)中 가용성 상승이 결정적입니다.

### 데이터 거주지, BAA, 규제 산업

Bedrock: 대부분의 지역에서 BAA; VPC 엔드포인트; 가드레일. 일반적인 핀테크 기본값.
Azure OpenAI: HIPAA, SOC 2, ISO 27001; EU 데이터 거주지; 기업 규제 기본값.
Vertex: HIPAA, GDPR, 지역별 데이터 거주지; Google Cloud의 규정 준수 스택.

세 가지 모두 기본 체크리스트를 충족합니다. 차이점은 데이터 보존 정책, 로그 처리 방법, 남용 모니터링이 트래픽을 읽는지에 있습니다 (기본값 대부분의 옵트인; 기업용 옵트아웃 가능).

### 기억해야 할 숫자

- 동등한 Llama 3.1 405B에서 Azure OpenAI 중앙값 TTFT: ~50 ms (PTU 포함).
- 온디맨드 Bedrock 중앙값 TTFT: ~75 ms.
- Bedrock Provisioned Throughput: 단위당 $21-$50/시간.
- Azure PTU 균형점: 지속적인 이용률 ~40-60%.
- 높은 이용률에서 온디맨드 대비 PTU 절감: 최대 70%.

## 활용

`code/main.py`는 합성 작업에서 세 플랫폼을 비교합니다 — 온디맨드 대 PTU 경제학, TTFT 분산, 비용 귀인 충실도를 모델링합니다. 실행하여 PTU가 payoff하는 곳과 마켓플레이스의 모델 폭이 TTFT 격차를 능가하는 곳을 확인합니다.

## 결과물

이 레슨은 `outputs/skill-managed-platform-picker.md`를 산출합니다. 작업 프로필 (필요한 모델, TTFT SLA, 일일 볼륨, 규정 준수 요구사항)이 주어지면 기본 플랫폼, 대체책, FinOps 계측 계획을 권장합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 70B 클래스 모델에서 Azure PTU가 온디맨드를 이기는 지속적인 利用률은 어느 정도입니까? 균형점을 계산하고 광고된 40-60% 대역과 비교하세요.
2. 제품에 Claude 3.7 Sonnet과 GPT-4o가 필요합니다. 이중 제공자 배포를 디자인하세요 — 어느 것이 어느 하이퍼스케일러로 가는지, 어떤 게이트웨이가 앞에 있는지, 장애 조치 정책은 무엇인지.
3. 규제받는 의료 고객이 BAA, US-East 데이터 거주지, P99 TTFT 100ms 미만을 요구합니다. 플랫폼을 선택하고 세 가지 특정 기능으로 정당화하세요.
4.Bedrock 청구서가 트래픽 변화 없이 이번 달 4배 뛰었다는 것을 발견했습니다. Application Inference Profiles 없이는 어떻게 원인자를 찾을 것입니까? 프로필이 있으면 얼마나 걸립니까?
5. Azure OpenAI 및 Bedrock 가격 페이지를 읽으세요. 100M 토큰/월 Claude 작업량의 경우,哪一个가 더 저렴합니까 — 직접 Anthropic API, Bedrock 온디맨드, 아니면 Bedrock Provisioned Throughput?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| Bedrock | "AWS LLM 서비스" | Claude, Llama, Titan, Mistral, Cohere를 포괄하는 모델 마켓플레이스 |
| Azure OpenAI | "Azure의 ChatGPT" | 기업 제어가 있는 Azure 데이터 센터의 독점적인 OpenAI 모델 |
| Vertex AI | "Google의 LLM" | 서드파티 모델용 Model Garden과 함께 Gemini-first 플랫폼 |
| PTU | "전용 용량" | Provisioned Throughput Unit — 예약된 추론 GPU, 시간당 가격 |
| Application Inference Profile | "Bedrock 태깅" | 태그가 있는 CloudWatch 네이티브인 제품별 비용/사용량 프로필 |
| Model Garden | "Vertex 카탈로그" | Gemini와 별도인 Vertex AI의 서드파티 모델 섹션 |
| 이중 제공자 최소 | "LLM 이중화" | 모든 중요한 LLM 경로를 ≥2 하이퍼스케일러에서 실행하는 정책 |
| BAA | "HIPAA 서류" | Business Associate Agreement; PHI에 필요; 세 곳 모두 제공 |
| 남용 모니터링 | "로그 감시자" | 프롬프트/출력에 대한 제공자 측 안전 스캔; 기업용 옵트아웃 가능 |

## 추가 자료

- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) — 공식 요금 카드 및 Provisioned Throughput 가격.
- [Azure OpenAI Service Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/) — PTU 경제학 및 요금 카드.
- [Vertex AI Generative AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) — Gemini 등급 및 Model Garden 추가 비용.
- [Artificial Analysis LLM Leaderboard](https://artificialanalysis.ai/) — 제공자 간 지속적인 지연 시간 및 처리량 벤치마크.
- [The AI Journal — AWS Bedrock vs Azure OpenAI CTO Guide 2026](https://theaijournal.co/2026/03/aws-bedrock-vs-azure-openai/) — 기업 결정 프레임워크.
- [Finout — Bedrock vs Vertex vs Azure FinOps](https://www.finout.io/blog/bedrock-vs.-vertex-vs.-azure-cognitive-a-finops-comparison-for-ai-spend) — 귀인 메커니즘 나란히.