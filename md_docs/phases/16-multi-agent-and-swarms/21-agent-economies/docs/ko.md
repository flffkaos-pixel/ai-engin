# 에이전트 경제, 토큰 인센티브, 평판

> 장기 자율 에이전트 (METR의 1시간에서 8시간 작업 곡선)는 경제적 주체권이 필요합니다. 등장하는 **5계층 스택**은: **DePIN** (물리적 컴퓨팅) → **Identity** (W3C DIDs + 평판 자본) → **Cognition** (RAG + MCP) → **Settlement** (계정 추상화) → **Governance** (Agentic DAOs). 프로덕션 에이전트 인센티브 네트워크에는 **Bittensor** (TAO 서브넷이 작업 특정 모델 reward), **Fetch.ai / ASI Alliance** (ASI-1 Mini LLM + FET 토큰), **Gonka** (생산적 AI 작업에 컴퓨트를 재분배하는 transformer 기반 PoW)가 포함됩니다. 학술 연구: AAMAS 2025의 분산형 LaMAS는 기여 에이전트에게 공정하게reward하는 **Shapley-value credit attribution**을 사용합니다; Google Research "Mechanism design for large language models"는 단조 집계를 사용하는 second-price 지불의 **토큰 경매**를 제안합니다. 이 레슨은 최소 에이전트 마켓플레이스를 빌드하고, 멀티 에이전트 파이프라인에 Shapley-value credit attribution을 적용하며, second-price 토큰 경매를 실행하여 게임 이론 기계가 구체적으로 적용됩니다.

**유형:** 학습
**언어:** Python (stdlib)
**선수 과목:** Phase 16 · 16 (Negotiation and Bargaining), Phase 16 · 09 (Parallel Swarm Networks)
**소요 시간:** ~75분

## 문제

멀티 에이전트 시스템은 에이전트가 공동으로 가치를 창출하지만 개별적으로reward되어야 할 때 복잡해집니다. 고전적 메커니즘 — 등분할, 마지막 기여자 전부 가져가기 — 은 공정하지 않거나 게임 가능합니다. Shapley 값을 통한 연합 기반 reward는 구성적으로 공정하지만 계산 비용이 큽니다. 2025-2026년 문헌은 유용한 근사치를 추진합니다: Shapley 샘플링, 단조 집계 경매, 확인된 기여에서 누적되는 온체인 평판.

신용 귀인eyond, 이 분야는 실제 경제적 에이전트로 전환했습니다: Bittensor TAO는 서브넷 특정 모델을 미세 조정하기 위해 컴퓨팅을 채굴하고reward하고, Fetch.ai/ASI는 FET 토큰으로 ASI-1 Mini LLM 사용을reward하고, Gonka는 생산적 AI 작업으로 transformer 工作 증명을 재배치합니다. 자율적으로 거래하는 에이전트가 오늘날 존재합니다; 문제는 인센티브를 어떻게 조정하는지입니다.

이 레슨은 에이전트 경제를 특정 문제 系列 — 신용 귀인, 메커니즘 디자인, 평판 — 으로 취급하고 아이디어가 오래 지속되도록 최소 수학으로 각각을 빌드합니다.

## 개념

### 5계층 에이전트-경제 스택

1. **DePIN (물리적 컴퓨팅).** GPU, 스토리지, 대역폭을 임대하는 분산 인프라. Bittensor 서브넷, Render Network, Akash. 에이전트 특정 아님; 에이전트가 사용합니다.
2. **Identity.** W3C 분산 식별자 (DIDs)는 각 에이전트에 플랫폼과 무관한 지속적 ID를 부여합니다. 평판이 DID에 누적됩니다. 에이전트 네트워크 프로토콜 (ANP)은 발견 레이어로 DID를 사용합니다.
3. **Cognition.** 에이전트의 추론 루프: LLM + RAG + MCP. 이것이 다른 phases가 빌드하는 것입니다.
4. **Settlement.** 계정 추상화 (ERC-4337)는 에이전트가 ETH를 보유하지 않고도 자체 잔액에서 가스를 지불할 수 있게 합니다. 에이전트는 서비스, 서로, 또는 컴퓨팅에 지불할 수 있습니다.
5. **Governance.** Agentic DAOs: 인간 *과* 에이전트가 프로토콜 변경에 투표하는治理 구조로, 투표 권력이 평판에 연결됩니다.

모든 프로덕션 시스템이 5가지를 모두 사용하는 것은 아닙니다. Bittensor는 1, 2, 부분적으로 3, 부분적으로 4, 5는 사용하지 않습니다. OpenAI 에이전트는 3만 사용합니다. 스택은 요구 사항이 아닌 참조 맵입니다.

### Bittensor, Fetch.ai, Gonka — 무엇이 실행되는지

**Bittensor (TAO).** 서브넷은 전문화된 작업입니다 (언어 모델링, 이미지 생성, 예측). 채굴자가 모델 출력을 제출합니다. 검증자가 순위를 매기고 지분 가중식 scoring이 TAO rewards를 분배합니다. 각 서브넷에는 자체 평가가 있습니다. 경제적 교훈: 사용된 컴퓨팅이 아닌 작업 특정 출력 품질에 지불합니다.

**Fetch.ai / ASI Alliance.** ASI-1 Mini LLM이 Fetch.ai 네트워크에서 실행됩니다; 사용자가 FET 토큰으로 추론에 지불합니다. 에이전트-as-동료 내러티브가 여기서 더 강합니다: Fetch의 에이전트가 작업에 대해 다른 에이전트를 호출하고 FET로 지불할 수 있습니다.

**Gonka.** Transformer 工作 증명: "작업"은 transformer의 forward passes입니다. 채굴자는 올바른 출력을 가진 (학습 데이터에서) 추론 작업을 실행하여earn합니다. 자원-생산적 PoW instead of hash-based PoW.

세 가지 모두 2026년 4월 현재 프로덕션 등급입니다. 수익 분배가 다릅니다. Bittensor는 서브넷 검증자에 상대적인 품질을reward합니다; Fetch는 지불 사용자가 측정한 유틸리티를reward합니다; Gonka는 검증 가능한 추론 작업을reward합니다.

### Shapley-value credit attribution

세 에이전트가 작업에 협력합니다. 출력이 0.8을 받습니다. 누가 무엇을 기여했습니까?

Shapley 값: 네 가지 공리 (효율성, 대칭성, 선형성, null)를 만족하는 고유한 credit 할당. 에이전트 `i`의 경우:

```
shapley(i) = (1/N!) * 모든 순서 O에 대한 합계 (v(S_i_O ∪ {i}) - v(S_i_O))
```

여기서 `S_i_O`는 순서 O에서 `i` 이전의 에이전트 집합입니다. 실제로: 모든 순열을 열거하고, 각 순열에서 각 에이전트의 한계 기여를 기록하고, 평균을 냅니다.

N=3 에이전트의 경우 6개의 순열이 있습니다. N=10의 경우 360만 — 그래서 실제로 순서를 샘플링而非 열거합니다.

### 집계용 second-price 경매

Google Research ("Mechanism design for large language models")는 LLM 출력 집계를 위한 second-price 토큰 경매를 제안합니다. 설정: N 에이전트가 각각 완료 제안을 합니다; 각 에이전트는 선택되는 것에 대한 개인 가치를 가집니다. 경매자가 가장 높은 가치 제안을 선택하고 *두 번째로 높은* 가치에 지불합니다. 단조 집계 (가치가 제안이 선택되었는지 여부에依赖하며 어떻게投标되었는지에 não依赖)에서 이것은 진실합니다 — 에이전트가 진정한 가치를投标합니다.

LLM 시스템에 중요한 이유: 여러 에이전트에 다양한 가격으로 완료 작업을外包할 수 있습니다; 경매가 최상을 선택 + 공정하게 지불하고, 에이전트는 잘못 보고할 인센티브가 없습니다.

### 평판 자본

 DID에 바인딩된 평판 점수가 확인된 기여에서 누적됩니다. 간단한 업데이트 규칙:

```
rep(i, t+1) = alpha * rep(i, t) + (1 - alpha) * contribution_quality(i, t)
```

`alpha`가 1에 가까운 감쇠 인자. 평판:

- 라우팅 결정에 대해 읽기 저렴합니다 ("어려운 작업을 고평판 에이전트에 보내세요").
- 위조하기昂贵합니다 (시간에 따라 누적되고 DID에 바인딩됩니다).
- 삭감될 수 있습니다: 검증에 실패한 기여가 차감됩니다.

### AAMAS 2025 분산형 LaMAS

LaMAS 제안 (AAMAS 2025)은 다음을 결합합니다: DID identity, Shapley-value credit attribution, 간단한 경매 메커니즘. 주요 주장: 신용 귀인 단계를 분산화하면 시스템이 감사 가능하고 단일 지점 조작에 면역이 됩니다.

### 경제가 무너지는 곳

- **가격 오라클 조작.** credit 함수가 게임될 수 있으면 에이전트가 그것을 게임할 것입니다. 모든 메커니즘이 적대적 테스트가 필요합니다.
- **시빌 공격.** 한 운영자가 자신의 기여를 부풀리기 위해 N개의 가짜 에이전트를 시작합니다. DID가 이를 늦추지만 멈추지는 않습니다; 평판 위조 비용이 완화책입니다.
- **검증 비용.** 신용 귀인은 검증자만큼만 공정합니다. 검증이 저렴하면 (작은 LLM) 게임될 수 있습니다; 비용이 많이 들면 (인간 패널) 시스템이 확장되지 않습니다.
- **규제 권고.** 에이전트 경제는 금융 규제와 교차합니다. Bittensor, Fetch, Gonka는 2026년 현재 일부 관할권에서 법적 회灰色 영역에서 운영됩니다.

### 에이전트 경제가 의미 있는 경우

- **이종 운영자가 있는 개방형 네트워크.** 단일 팀이 모든 에이전트를 제어하지 않습니다.
- **검증 가능한 출력.** 검증 없이는 신용 귀인이 추측입니다.
- **장기 작업 흐름.** 일회성 작업은 평판 누적의 이점이 없습니다.
- **토큰 지불이 관할권에서 법적으롤 가능합니다.**

폐쇄형 기업 시스템에서는 경제가 더 간단한 할당 (관리자가 작업을 할당하고, 지표가 내부적)으로 대체됩니다. 경제 문헌은 주로 개방형 네트워크에 적용됩니다.

## 빌드

`code/main.py`가 구현합니다:

- `shapley(value_fn, agents)` — 작은 N에 대한 열거로 정확한 Shapley 계산.
- `second_price_auction(bids)` — 진실한 메커니즘; 승자가 두 번째로 높은 가격을 지불합니다.
- `Reputation` — 지수 감쇠 및 삭감이 있는 DID 바인딩 평판.
- 데모 1: 세 에이전트가 협력하고 정확한 Shapley가 credit을 귀인합니다.
- 데모 2: 다섯 에이전트가 작업 슬롯에投标; second-price 경매가 승자 + 지불을 선택합니다.
- 데모 3: 이종 rep의 에이전트에게 100 라운드 작업 할당; rep 가중 라우팅이 무작위보다 나습니다.

실행:

```
python3 code/main.py
```

예상 출력: 각 에이전트에 대한 Shapley 값; 진실한投标 균형을 보여주는 경매 결과; 따뜻한 후 무작위보다 ~10-20% 품질 이득을 보여주는 rep 가중 라우팅.

## 활용

`outputs/skill-economy-designer.md` 최소 에이전트 경제를 디자인합니다: identity 레이어 선택, 신용 귀인 메커니즘, 지불 메커니즘, 평판 규칙.

## 결과물

2026년 에이전트 경제 운영:

- **평판으로 시작하고, 토큰으로 시작하지 마세요.** 평판은 구현하기 저렴하고 단독으로 가치가 있습니다; 토큰은 법적·경제적 복잡성을 추가합니다.
- **reward하기 전에 검증하세요.** 독립적 검증 단계 없이 credit을 분배하지 마세요. 자기 보고 품질은 시빌 게임을accumulate합니다.
- **Shapley-exact而非 Shapley-sample.** 100-1000 순서를 샘플링하세요; 정확한 열거가 확장되지 않습니다.
- **감쇠 인자를 제한하고 평판 바닥을 설정하세요.** 무제한 감쇠는 합법적 기여자를 지웁니다; 너무 느린 감쇠는 오래된 고평판 에이전트를reward합니다.
- **적대적으로 메커니즘을 감사하세요.** 네트워크를 열기 전에 red-team 시나리오를 실행하세요. 모든 메커니즘에는 게임 이론이 있습니다; 구멍을 찾는 것이 아니라 공격자를 찾고 싶습니다.

## 연습문제

1. `code/main.py`를 실행하세요. Shapley 값의 합이 총价值和 (효율성 공리)를-confirm하세요. 가치 함수를 변경하세요; Shapley 할당이 예상 방향으로 변경됨니까?
2. Shapley *샘플링*을 구현하세요 (K 순서에 대한 Monte Carlo). K가近似 정확도에 어떻게 영향을 미칩니까? N=4에 대한 정확함과 비교하세요.
3. 경매 전 coalition 형성을 구현하세요: 에이전트가 팀으로 병합하고 단위로投标할 수 있습니다. 어떤 연합이 형성됨니까? 결과가 개인投标보다 Pareto 더 낫습니까?
4. Google Research 메커니즘-디자인 게시물을 읽으세요. 위반되면 진실성을 깨는 하나의 가정을 식별하세요. LLM 설정에서 그 실패 모드가 어떻게 보입니까?
5. AAMAS 2025 분산형 LaMAS 논문을 읽으세요. 합성 작업에서 10 에이전트에 대한 Shapley 단계를 구현하세요. 정확한 계산이 얼마나 걸립니까? 100 드로우로 샘플링이 얼마나 가깝습니까?

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| DePIN | "분산된 물리적 인프라" | 토큰 인센티브 컴퓨팅/스토리지/대역폭. Bittensor, Akash, Render. |
| DID | "분산 식별자" | 이식 가능한 ID를 위한 W3C 스펙. 에이전트 평판이 플랫폼이 아닌 DID에 바인딩됩니다. |
| ERC-4337 | "계정 추상화" | 에이전트 결제를 가능하게 하는 컨트랙트 계정. |
| Shapley 값 | "공정 신용 귀인" | 효율성, 대칭성, 선형성, null을 만족하는 고유한 할당. |
| Second-price 경매 | "Vickrey 경매" | 진실한 메커니즘: 승자가 두 번째로 높은投标를 지불합니다. 단조 집계 호환. |
| 평판 자본 | "누적 품질 점수" | 확인된 기여からの DID 바인딩 점수; 시간에 따라 감쇠합니다. |
| Agentic DAO | "에이전트 + 인간이 관리" | 에이전트 투표자를 일등 시민으로, 투표 권력을 평판에 연결한 DAO. |
| TAO / FET / GPU 크레딧 | "토큰 명칭" | Bittensor TAO, Fetch.ai FET, 다양한 DePIN 토큰. |

## 추가 자료

- [The Agent Economy](https://arxiv.org/abs/2602.14219) — 5계층 에이전트-경제 스택의 2026년 조사
- [Google Research — Mechanism design for large language models](https://research.google/blog/mechanism-design-for-large-language-models/) — 단조 집계가 있는 토큰 경매
- [AAMAS 2025 — decentralized LaMAS](https://www.ifaamas.org/Proceedings/aamas2025/pdfs/p2896.pdf) — Shapley-value credit attribution
- [Bittensor TAO documentation](https://docs.bittensor.com/) — 서브넷 구조 및 reward 분배
- [Fetch.ai / ASI Alliance](https://fetch.ai/) — ASI-1 Mini LLM 및 FET 토큰
- [W3C Decentralized Identifiers (DIDs) spec](https://www.w3.org/TR/did-core/) — identity 기초