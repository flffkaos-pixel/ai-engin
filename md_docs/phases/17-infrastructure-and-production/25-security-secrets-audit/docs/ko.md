# 보안 — 시크릿, API 키 로테이션, 감사 로그, 가드레일

> 시크릿 스프롤을 중앙 집중식 볼트 (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault)를 통해eliminate합니다. 자격 증명을 구성 파일, VCS의 env 파일, 스프레드시트에 저장하지 마세요. 정적 키보다 IAM 역할을 사용합니다; CI/CD에는 OIDC. AI-게이트웨이 패턴이 2026년 솔루션입니다: 앱 → 게이트웨이 → 모델 공급업체, 게이트웨이가 런타임에 볼트에서 자격 증명을pull합니다. 볼트에서 로테이션하면 모든 앱이 몇 분 내에pick up합니다 — 재배포 없음, "새 키는 누구에게" Slack 메시지 없음. 로테이션 정책 ≤ 90일; 모든 커밋에서 TruffleHog / GitGuardian / Gitleaks로 스캔. 제로 트러스트: MFA, SSO, RBAC/ABAC, 단기 토큰, 디바이스 포스처. PII 스크럽은 전달 전에 PHI/PII를 마스킹하기 위해 엔티티 인식을 사용합니다; 일관된 토큰화 (Mesh 접근 방식)는 민감한 값을 안정적인 플레이스홀더에 매핑하여 LLM이 코드/관계 의미론을 유지합니다. 네트워크 송신: LLM 서비스를 전용 VPC/VNet 서브넷에 배치하고 `api.openai.com`, `api.anthropic.com` 등만 허용 목록에 추가합니다; 다른 모든 송신을 차단합니다. 2026년 인시던트 동인:compromised CI/CD 자격 증명을 통해 수천 개의 고객 배포에 env vars를 유출한 Vercel supply-chain 공격.

**유형:** 학습
**언어:** Python (stdlib, toy PII 스크러버 + 감사 로그 작성기)
**선수 과목:** Phase 17 · 19 (AI 게이트웨이), Phase 17 · 13 (관찰 가능성)
**소요 시간:** ~60분

## 학습 목표

- 4가지 시크릿 관리 안티패턴 (VCS의 구성 파일, 하드코딩된 env, 스프레드시트, 정적 키)을 열거하고它们的 대안을 이름 짓습니다.
- AI-게이트웨이-pulls-from-vault 패턴을 2026년 프로덕션 표준으로 설명합니다.
- 일관된 토큰화로 PII 스크러버를 구현합니다 (동일한 값 → 동일한 플레이스홀더) 의미론이 유지되도록 합니다.
- 2026년 Vercel 인시던트를 이름 짓고 CI/CD 자격 증명 위생에 대해 배운 것을 설명합니다.

## 문제

인턴이 API 키가 있는 `.env`을 커밋합니다. 빠르게 삭제합니다. 키가 이미 git 히스토리에 있습니다 — GitGuardian 스캔이それを捕らえ, 로테이션 프로세스는 "팀에 Slack, 40개 구성 파일 업데이트, 모든 서비스 재배포." 8시간 후, 서비스 절반이 live이고 절반이 배포 창을 기다리고 있습니다.

별도로, 사용자 프롬프트에 "내 SSN은 123-45-6789입니다."가 포함됩니다. 프롬프트가 OpenAI로 전송됩니다. BAA가 있지만 내부 정책은 전달 전에 PII를 마스킹하는 것입니다. 하지 않았습니다.

별도로, EKS 클러스터의 LLM 팟이 모든 인터넷 호스트에 연결할 수 있습니다. 누군가가 공격자 통제 도메인으로 DNS 조회를 통해 데이터를 유출합니다. 아무것도 그것을 차단하지 않았습니다.

LLM 서비스 보안을 위해서는 세 가지 벡터를 모두 처리해야 합니다. 볼트 지원 자격 증명. PII 스크럽bing. 네트워크 송신 필터링. 감사 로그.

## 개념

### 중앙 집중식 볼트 + IAM 역할 pull

**볼트**: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager. 단일 진실 공급자.

**IAM 역할**: 앱/게이트웨이가 정적 키가 아닌 IAM ID를 통해 인증합니다. 볼트가 토큰 수명 동안 시크릿을 반환합니다.

**AI-게이트웨이 패턴**: 게이트웨이가 요청 시간에 볼트에서 `OPENAI_API_KEY`를pull합니다. 볼트에서 로테이션; 다음 요청이 새 키를 가져옵니다. 재배포 없음.

### 로테이션 정책 ≤ 90일

모든 API 키, 볼트 루트 토큰, CI/CD 자격 증명. 가능한 자동 로테이션. 수동 로테이션은 기록되고 추적됩니다.

### 시크릿 스캐닝

- **TruffleHog** — 커밋에서 정규식 + 엔트로피.
- **GitGuardian** — 상업용, 높은 정확도.
- **Gitleaks** — OSS, CI에서 실행.

모든 커밋에서 실행합니다. 새 시크릿이 감지되면 PR을 차단합니다.

### 제로 트러스트 자세

- 모든 계정에서 MFA 필요.
- SAML/OIDC를 통한 SSO.
- 세분화된 액세스를 위한 RBAC (역할 기반) 또는 ABAC (속성 기반).
- 단기 토큰 (시간, 일 아님).
- 디바이스 포스처 — 디스크 암호화가 있는 기업 기기만.

### PII / PHI 스크럽bing

프롬프트가 인프라를 떠나기 전에:

1. 엔티티 인식 (spaCy NER, Presidio, 상업용).
2. 일치하는 엔티티 마스킹: `"내 SSN은 123-45-6789입니다"` → `"내 SSN은 [SSN_TOKEN_A3F]입니다"`.
3. 일관된 토큰화 (Mesh 접근 방식): 동일한 값이 동일한 플레이스홀더에 매핑되어 LLM이 관계를 유지합니다.
4. LLM 응답을 위한 선택적 역방향 매핑.

정적 정규식 필터가 기본 패턴을 catch합니다; NER이 더 많이 catch합니다. 둘 다 사용하세요.

### 입력 + 출력 가드레일

입력: 알려진 jailbreak, 금지된 주제 차단; 사용자당 비율 제한.

출력: 유출된 시크릿 (API 키 패턴, 거부 컨텍스트의 이메일 패턴)에 대한 정규식 스크럽, 정책 위반에 대한 분류기.

### 네트워크 송신 허용 목록

LLM 서비스를 전용 서브넷에 배치:
- 허용 목록: `api.openai.com`, `api.anthropic.com`, 벡터 DB 엔드포인트, 볼트 엔드포인트.
- 다른 모든 것: 드롭.
- 허용 목록 전용 해결사를 통한 DNS (DNS 터널링 유출 피하기).

### 감사 로그

모든 LLM 호출의 불변 로그:
- 타임스탬프.
- 사용자 / 테넌트.
- 프롬프트 해시 (개인 정보 보호를 위해 원시 프롬프트 아님).
- 모델 + 버전.
- 토큰 수.
- 비용.
- 응답 해시.
- 가드레일 trips.

규제 요구 사항에 따라 유지 (SOC 2 1년, HIPAA 6년).

### 2026년 Vercel 인시던트

공급망 공격: compromised CI/CD 자격 증명이 수천 개의 고객 배포에 env vars를 유출했습니다. 교훈: CI/CD 자격 증명은 프로덕션과 동일합니다. 볼트에 저장합니다. 좁게 범위를 지정합니다. 공격적으로 로테이션합니다.

### 기억해야 할 숫자

- 로테이션 정책: ≤ 90일.
- 모든 커밋에서 스캔: TruffleHog / GitGuardian / Gitleaks.
- Vercel 2026: CI/CD creds compromised → 수천 개의 고객 env vars 유출.
- 감사 로그 유지: SOC 2 = 1년, HIPAA = 6년.

## 활용

`code/main.py`는 일관된 토큰화와 추가 전용 감사 로그가 있는toy PII 스크러버를 구현합니다.

## 결과물

이 레슨은 `outputs/skill-llm-security-plan.md`를 산출합니다. 규제 범위 및 현재 상태 given으로 볼트 마이그레이션, 스크러버, 송신, 감사 로그를 계획합니다.

## 연습문제

1. `code/main.py`를 실행하세요. 동일한 SSN을 참조하는 두 개의 프롬프트를 보내세요. 둘 다 동일한 플레이스홀더를 받는지 확인하세요.
2. OpenAI + Anthropic + Weaviate를 호출하는 vLLM-on-EKS 배포의 네트워크 송신 정책을 설계하세요.
3. git 히스토리에서 키를 발견합니다 (2년 전). 올바른 대응은 무엇입니까 — 키 로테이션, 히스토리 스크럽, 또는 둘 다?正当화하세요.
4. 감사 로그가 매일 10GB 증가합니다. 유지 계층 (핫 30일, 웜 12개월, 콜드 6년)을 설계하세요.
5. 역 토큰화 (LLM 응답에 실제 값을 다시 대입)가 복잡성 대비 가치가 있는지 주장하세요. 플레이스홀더를 표시하는 것과 비교하여.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| 볼트 | "시크릿 저장소" | 중앙 집중식 자격 증명 관리 서비스 |
| IAM 역할 | "ID 기반 인증" | 앱이 가정하는 역할; 단기 creds 반환 |
| CI/CD용 OIDC | "클라우드 발급 토큰" | CI에 정적 키 없음 — OIDC 통한 ID |
| TruffleHog / GitGuardian / Gitleaks | "시크릿 스캐너" | 커밋 시 시크릿 감지 |
| RBAC / ABAC | "액세스 제어" | 역할 기반 vs 속성 기반 |
| PII 스크럽bing | "데이터 마스킹" | 민감한 엔티티 제거 또는 토큰화 |
| 일관된 토큰화 | "안정적 플레이스홀더" | 동일한 값 → 매번 동일한 토큰 |
| Mesh 접근 방식 | "Mesh 토큰화" | 의미론 보존 토큰화 패턴 |
| 송신 허용 목록 | "아웃바운드 허용 목록" | 도달 가능한 도메인만 허용 |
| 감사 로그 | "불변 이력" | 규정 준수를 위한 추가 전용 레코드 |

## 추가 자료

- [Doppler — 고급 LLM 보안](https://www.doppler.com/blog/advanced-llm-security)
- [Portkey — 시크릿 참조로 LLM API 키 관리](https://portkey.ai/blog/secret-references-ai-api-key-management/)
- [Datadog — LLM 가드레일 모범 사례](https://www.datadoghq.com/blog/llm-guardrails-best-practices/)
- [JumpServer — 2026년 시크릿 관리 모범 사례](https://www.jumpserver.com/blog/secret-management-best-practices-2026)
- [Microsoft Presidio](https://github.com/microsoft/presidio) — PII 감지 및 익명화.
- [HashiCorp Vault 문서](https://developer.hashicorp.com/vault/docs)