# 캡스톤 06 — Kubernetes용 DevOps 문제 해결 에이전트

> AWS의 DevOps Agent가 GA가 되었고, Resolve AI가 K8s 플레이북을 게시했으며, NeuBird가 시맨틱 모니터를 데모했고, Metoro가 AI SRE를 서비스별 SLO에 연결했다. 운영 형태는 확정되었다: 알림 웹훅이 발생하고, 에이전트가 원격 측정를 읽고, K8s 객체 그래프를 걸으며, 근본 원인 가설을 순위 매기고, 승인 버튼이 있는 Slack 브리프를 게시한다. 기본적으로 읽기 전용. 모든 재밍은 인간에 의해 게이트됨. 이 캡스톤은 20개의 합성 인시던트에서 평가되고 3개의 공유 케이스에서 AWS의 에이전트와 비교되는 에이전트이다.

**유형:** 캡스톤
**언어:** Python (에이전트), TypeScript (Slack 통합)
**선수 과목:** Phase 11 (LLM 엔지니어링), Phase 13 (도구 및 MCP), Phase 14 (에이전트), Phase 15 (자율), Phase 17 (인프라), Phase 18 (안전)
**활용 phases:** P11 · P13 · P14 · P15 · P17 · P18
**소요 시간:** 30시간

## 문제

2025-2026년 SRE 내러티브는 "AI 에이전트가 인시던트를 트라이징하고, 인간이 재밍을 승인한다"가 되었다. AWS DevOps Agent, Resolve AI, NeuBird, Metoro, PagerDuty AIOps 모두 운영에서 이 형태를 shipped한다. 에이전트는 Prometheus 메트릭, Loki 로그, Tempo 추적, kube-state-metrics, K8s 객체의 지식 그래프를 읽는다. 5분 이내에 원격 측정 인용과 함께 순위 된 근본 원인 가설을 생성한다. Slack을 통한 명시적인 인간 승인이 없는 한 파괴적인 명령을 실행하지 않는다.

大部分의 어려운 작업은 범위 지정 및 안전이며 추론이 아니다. 에이전트에는 기본적으로 읽기 전용 RBAC 표면, 강화된 MCP 도구 서버, 고려된 모든 명령의 감사 로그가 필요하다. 에이전트는 자신의 깊이 밖일 때 승격해야 한다. 그리고 OOM 킬 캐스케이드가 $5k 에이전트 청구서를 생성하지 않을 만큼 충분히 저렴하게 실행해야 한다.

## 개념

에이전트는 지식 그래프에서 작동한다. 노드는 K8s 객체(Pods, Deployments, Services, Nodes, HPAs, PVCs)와 원격 측정 소스(Prometheus 시리즈, Loki 스트림, Tempo 추적)이다. 에지는 소유권(Pod -> ReplicaSet -> Deployment), 스케줄링(Pod -> Node), 관찰(Pod -> Prometheus 시리즈)을 인코딩한다. 그래프는 kube-state-metrics 동기화로 최신 상태를 유지하며 모든 알림에서 다시 샘플링된다.

알림이 발생하면 에이전트가 영향을 받는 객체에서 근본 원인을 분석한다. 에지를 걸으며 관련 원격 측정 슬라이스(최근 15분)를 가져오고 가설을 초안한다. 가설은 증거에 의해 순위 매겨진다: 얼마나 많은 원격 측정 인용이 그것을 지원하는지, 얼마나 최근인지, 얼마나 구체적인지. 상위 3개 가설이 그래프 경로 시각화 및 재밍 작업에 대한 승인 버튼과 함께 Slack으로 전송된다.

재밍은 게이트된다. 허용되는 기본 동작은 읽기 전용이다. 파괴적인 작업(축소, 롤백, Pod 삭제)은 Slack 승인이 필요하다; ArgoCD 롤백 후크는 에이전트가 절대 보유하지 않는 auth 토큰이 필요하다. 감사 로그는 에이전트가 *고려한* 모든 명령을 기록한다 — 실행된 것만이 아니라 — 그래서 검토 프로세스가 거의 놓친 것을 포착한다.

## 아키텍처

```
PagerDuty / Alertmanager webhook
           |
           v
     FastAPI receiver
           |
           v
   LangGraph root-cause agent
           |
           +---- read-only MCP tools ----+
           |                             |
           v                             v
   K8s knowledge graph              telemetry slices
     (Neo4j / kuzu)              Prometheus, Loki, Tempo
   ownership + scheduling          last 15m, scoped
           |
           v
   hypothesis ranking (evidence weight)
           |
           v
   Slack brief + approval buttons
           |
           v (approved)
   ArgoCD rollback hook / PagerDuty escalate
           |
           v
   audit log: considered vs executed, every command
```

## 기술 스택

- 관찰 가능성 소스: Prometheus, Loki, Tempo, kube-state-metrics
- 지식 그래프: K8s 객체 + 원격 측정 에지의 Neo4j (관리) 또는 kuzu (임베디드)
- 에이전트: 도구별 허용 목록이 있는 LangGraph, 기본적으로 읽기 전용
- 도구 전송: FastMCP over StreamableHTTP; 승인 게이트 뒤의 파괴적 도구를 위한 별도 서버
- 모델: 근본 원인 추론을 위한 Claude Sonnet 4.7, 로그 요약을 위한 Gemini 2.5 Flash
- 재밍: ArgoCD 롤백 웹훅, PagerDuty 확대, Slack 승인 카드
- 감사: 추가 전용 구조화 로그(고려됨, 실행됨, 승인됨, 결과), 매일 S3로 shipping
- 배포: 자신의 좁은 RBAC 역할로 K8s 배포; 별도 네임스페이스

## 실습

1. **그래프 수집.** 30초마다 kube-state-metrics를 Neo4j/kuzu로 동기화. 노드: Pod, Deployment, Node, Service, PVC, HPA. 에지: OWNED_BY, SCHEDULED_ON, EXPOSES, MOUNTS, SCALES. 원격 측정 오버레이 에지: OBSERVED_BY(Pod이 Prometheus 시리즈에 의해 관찰됨).

2. **알림 수신기.** PagerDuty 또는 Alertmanager 웹훅을accept하는 FastAPI 엔드포인트. 영향을 받는 객체와 SLO 위반을 추출.

3. **읽기 전용 도구 표면.** kubectl, Prometheus 쿼리, Loki logql, Tempo traceql을 FastMCP를 통해 래핑. 모든 도구에 좁은 RBAC 동사("get", "list", "describe")가 있다. 기본 서버에 "delete", "exec", "scale"이 없다.

4. **근본 원인 에이전트.** 세 개의 노드가 있는 LangGraph: `sample`은 최근 15분 원격 측정 슬라이스를 가져오고, `walk`는 이웃 객체를 위해 그래프를 쿼리하며, `hypothesize`는 원격 측정 인용과 함께 순위 된 근본 원인 후보를 초안.

5. **Evidence 채점.** 각 가설의 점수 = 최근성 × 특이성 × 그래프 경로 길이 역수 × 인용 수. 상위 3개 반환.

6. **Slack 브리프.** 가설, 그래프 경로 시각화(서버측에서 렌더링된 하위 그래프 이미지), 최대 하나의 재밍 작업에 대한 승인 버튼이 있는 첨부 파일을 게시.

7. **재밍 게이트.** 파괴적 도구(축소, 롤백, 삭제)는 승인 토큰 뒤의 두 번째 MCP 서버에 있다. 에이전트는 Slack 카드가 인간에 의해 승인된 후에에만 호출할 수 있다.

8. **감사 로그.** 추가 전용 JSONL: 모든 후보 명령에 대해 실행되었는지, 누가 승인했는지 기록. 매일 S3로 shipping.

9. **합성 인시던트 모음.** 20개 시나리오 구축: OOMKill 캐스케이드, DNS 플랩, HPA 쓰래시, PVC 채움, 시끄러운 이웃, 결함이 있는 사이드카, 잘못된 ConfigMap rollout, 인증서 ротация, 이미지 풀 백오프 등. 근본 원인 정확도 및 가설까지 시간으로 에이전트를 채점.

## 활용

```
webhook: alert.pagerduty.com -> checkout-api SLO breach, error rate 14%
[graph]   affected: Deployment checkout-api (3 Pods, Node ip-10-2-3-4)
[walk]    neighbors: ReplicaSet checkout-api-abc, Service checkout-api,
           recent rollout 14m ago
[sample]  prometheus error_rate 14%, up-trend; loki 500s on /api/v2/pay
[hypo]    #1 bad rollout: latest image checkout-api:v2.41 fails /healthz
           citations: deploy.yaml (rev 42), prometheus errorRate, loki 500 stack
[slack]   [ROLL BACK to v2.40]  [ESCALATE]  [IGNORE]
           (approval required; agent does not roll back unilaterally)
```

## 결과물

`outputs/skill-devops-agent.md`가 결과물이다. K8s 클러스터와 알림 소스가 주어지면 에이전트가 순위 된 근본 원인 가설과 Slack 게이트 재밍 흐름을 생성한다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 시나리오 모음에서 RCA 정확도 | 20개의 합성 인시던트에서 ≥80% 정확한 근본 원인 |
| 20 | 안전성 | 감사 로그에서 Slack 승인 없이 파괴적 행동 방어가 절대 firing하지 않음 |
| 20 | 가설까지 시간 | 알림에서 Slack 브리프까지 p50 5분 미만 |
| 20 | 설명 가능성 | 모든 가설에 그래프 경로 및 원격 측정 인용이 있음 |
| 15 | 통합 완전성 | PagerDuty, Slack, ArgoCD, Prometheus 종단 간 작동 |
| **100** | | |

## 연습 문제

1. AWS의 DevOps Agent가 데모한 동일한 3개 인시던트에서 에이전트를 실행한다. 나란히 게시한다. 에이전트가 diverg하는 곳을 보고한다.

2. 에이전트가 *고려한* 명령 중 승인 없이 파괴적였을 명령을 플래그하는 "거의 놓침" 감사를 추가한다. 일주일 동안 거의 놓임 비율을 측정한다.

3. 근본 원인 모델을 Claude Sonnet 4.7에서 셀프 호스트된 Llama 3.3 70B로 교체한다. RCA 정확도 delta 및 인시던트당 비용을 측정한다.

4. 인과 필터 구축: 상관된 원격 측정 스파이크와 진정한 근본 원인을 구별한다. 20개 시나리오 레이블에서 작은 분류자를 훈련시킨다.

5. 롤백 드라이 런 추가: 동일한 매니페스트로 스테이징 클러스터에 대해 ArgoCD 롤백. Slack 승인 버튼 전에 라이브 클러스터에서 롤백 계획을 확인한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| K8s 지식 그래프 | "Cluster graph" | 노드 = K8s 객체 + 원격 측정 시리즈; 에지 = 소유권, 스케줄링, 관찰 |
| 기본적으로 읽기 전용 | "Scoped RBAC" | 에이전트의 서비스 계정에는 get/list/describe 동사만 있음; 파괴적 동사는 승인의 뒤에 있는 별도 서버에 있음 |
| 감사 로그 | "Considered vs executed" | 모든 후보 명령, 실행 여부, 승인자)의 추가 전용 기록 |
| 가설 순위 | "Evidence score" | 최근성 × 특이성 × 그래프 경로 길이 역수 × 인용 수 |
| Slack 승인 카드 | "HITL gate" | 재밍 버튼이 있는 대화형 Slack 메시지; 인간이 클릭할 때까지 에이전트가 진행할 수 없음 |
| 원격 측정 인용 | "Evidence pointer" | 주장을 지원하는 Prometheus 쿼리, Loki 선택기 또는 Tempo 추적 URL |
| MTTR | "Time to resolution" | 알림 발생에서 SLO 복구까지의 wall-clock |

## 추가 자료

- [AWS DevOps Agent GA](https://aws.amazon.com/blogs/aws/aws-devops-agent-helps-you-accelerate-incident-response-and-improve-system-reliability-preview/) — 2026년 기준
- [Resolve AI K8s troubleshooting](https://resolve.ai/blog/kubernetes-troubleshooting-in-resolve-ai) — 경쟁사 기준
- [NeuBird semantic monitoring](https://www.neubird.ai) — 시맨틱-그래프 접근
- [Metoro AI SRE](https://metoro.io) — SLO 우선 운영 프레임밍
- [kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) — 클러스터 상태 소스
- [LangGraph](https://langchain-ai.github.io/langgraph/) — 기준 에이전트 오케스트레이터
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP 서버 프레임워크
- [ArgoCD rollback](https://argo-cd.readthedocs.io/en/stable/user-guide/commands/argocd_app_rollback/) — 게이트된 재밍 대상