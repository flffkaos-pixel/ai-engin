# 프롬프트 인젝션 탐지기

> 프롬프트 인젝션은 악성 지침이 프롬프트에 주입되는 공격입니다. RAG 시스템(레슨 69)에서 검색된 문서에는 지침을 무시하는 주입이 포함될 수 있습니다. 이 레슨은 분류기(레슨 82)를 사용하여 주입을 감지하고, 의심스러운 프롬프트를 필터링하고, 안전한 프롬프트를 LLM으로 전달하는 프롬프트 인젝션 탐지기를 구축합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 69, 82
**Time:** ~90 minutes

## Learning Objectives

- 레슨 82의 분류 체계를 사용하여 프롬프트 인젝션을 감지하는 프롬프트 인젝션 탐지기를 구현합니다.
- 감지기를 RAG 파이프라인(레슨 69)에 연결하여 생성 전에 주입된 프롬프트를 필터링합니다.

## The Problem

RAG 시스템에서 검색된 문서에는 지침을 무시하거나 유해한 출력을 생성하는 프롬프트 인젝션이 포함될 수 있습니다. 탐지기가 생성 전에 이러한 주입을 필터링해야 합니다.

## The Concept

### Prompt injection detection

탐지기는 프롬프트를 분석하고 레슨 82의 분류 체계를 사용하여 주입을 식별합니다. 주입이 감지되면 프롬프트는 차단되거나(거부) 정리됩니다(주입 제거).

### Integration with RAG

탐지기는 RAG 파이프라인(레슨 69)에 연결됩니다. 검색된 문서에서 각 청크가 주입에 대해 스캔됩니다. 감지된 청크는 생성기로 전달되기 전에 필터링됩니다.

## Build It

`code/main.py` implements:

- `PromptInjectionDetector` - 프롬프트에서 프롬프트 인젝션을 감지합니다. 레슨 82의 분류 체계를 사용합니다.
- `RAGInjectionFilter` - RAG 파이프라인(레슨 69)에 연결됩니다: 검색된 문서를 스캔하고 인젝션 청크를 필터링합니다.

파일 하단의 데모는 RAG 파이프라인을 시뮬레이션하고, 검색된 문서에 인젝션을 주입하고, 탐지기가 이를 필터링하는지 확인합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 필터링 전후의 청크 수를 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 RAG 보안으로 확장합니다.

**Defense in depth.** 여러 방어 계층: 프롬프트 인젝션 탐지기 + LLM 출력 검증 + 인간 검토.

**Adversarial robustness.** 탐지기는 적대적 공격에 강건해야 합니다. 정기적인 업데이트가 필요합니다.

**Latency budget.** 탐지기는 생성 전에 실행되므로 프롬프트 처리에 지연 시간이 추가됩니다. 지연 시간과 보안의 균형이 필요합니다.

## Use It

프로덕션 패턴:

- **Detector as middleware.** 탐지기는 프롬프트가 LLM에 도달하기 전에 실행되는 미들웨어입니다.
- **Logging and alerting.** 감지된 인젝션은 로깅되어야 합니다. 반복되는 공격에 대한 경고가 트리거되어야 합니다.

## Ship It

`outputs/skill-prompt-injection-detector.md`는 실제 프로젝트에서 사용할 탐지기 모델, 민감도 임계값 및 RAG 필터가 연결되는 방법을 설명합니다.

## Exercises

1. 탐지기 민감도를 제어하는 `--sensitivity` CLI 플래그를 추가합니다.
2. 감지된 인젝션의 로깅 및 경고를 추가합니다.
3. 감지기를 LLM 출력 검증(생성된 출력 스캔)과 통합합니다.
4. 감지기 지연 시간을 RAG 처리량에 대해 벤치마킹합니다.
5. 감지기에 대한 적대적 훈련을 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Prompt injection | "Adversarial prompt" | 악성 지침이 포함된 프롬프트 |
| Detector | "Guardrail" | 프롬프트에서 인젝션을 감지하는 분류기 |
| RAG injection filter | "RAG security" | 검색된 문서에서 인젝션을 필터링 |
| Defense in depth | "Multiple defenses" | 여러 방어 계층 |

## Further Reading

- [Perez and Ribeiro, Exploiting Programmatic Behavior of LLMs: Systematic Propagation of Prompt Injection (arXiv 2202.12173)](https://arxiv.org/abs/2202.12173) - 프롬프트 인젝션의 원본 논문
- [Greshake et al., Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection (AISec 2023)](https://arxiv.org/abs/2302.12173) - 간접 프롬프트 인젝션(RAG)
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-llm-applications/) - LLM 보안 위험
- Phase 19 · 69 - 엔드-투-엔드 RAG 시스템(이 탐지기가 보호하는 대상)
- Phase 19 · 82 - 탈옥 분류 체계(이 탐지기의 기반)
