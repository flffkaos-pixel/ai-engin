# 코드 실행 메트릭

> 코드 생성 LLM은 perplexity와 정확히 일치와 같은 텍스트 메트릭으로 평가될 수 없습니다. 출력이 참조와 일치하는지는 중요하지 않습니다; 중요한 것은 코드가 올바르게 실행되는지입니다. 코드 실행 메트릭은 생성된 코드를 샌드박스 환경에서 실행하고, 통과/실패 상태를 확인하고, 통과율(pass@k)을 계산합니다. 이 레슨은 생성된 코드를 실행하고, 통과/실패를 확인하고, 통과율을 계산하는 코드 실행 평가기를 구현합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 30-37
**Time:** ~60 minutes

## Learning Objectives

- 생성된 코드를 샌드박스 환경에서 안전하게 실행하고 통과/실패 상태를 확인하는 코드 실행 평가기를 구현합니다.
- 통과율(pass@k)을 계산합니다.

## The Problem

코드 생성 LLM은 코드 생성을 위해 특화된 메트릭이 필요합니다. perplexity나 정확히 일치는 생성된 코드가 올바른지 측정하지 않습니다. 코드가 올바르게 실행되는지 확인하기 위해 실행이 필요합니다.

## The Concept

```mermaid
flowchart TD
  Code[Generated code] --> Sandbox[Sandbox execution]
  Test[Test cases] --> Sandbox
  Sandbox --> PassFail[Pass/fail status]
  PassFail --> PassRate[pass@k]
```

### Pass@k

Pass@k는 생성된 k개 코드 샘플 중 테스트를 통과하는 샘플의 비율입니다. 1개 중 통과(pass@1) 또는 k개 중 통과(pass@k)로 계산됩니다.

### Sandbox execution

코드는 안전한 환경(샌드박스)에서 실행되어야 합니다. 샌드박스는 호스트 시스템에 대한 액세스를 제한하고 악성 코드가 피해를 입히는 것을 방지합니다. Python의 `subprocess` 모듈은 격리된 프로세스에서 코드를 실행하는 데 사용될 수 있습니다.

## Build It

`code/main.py` implements:

- `CodeExecutor` - 샌드박스 환경에서 생성된 코드를 실행하고 통과/실패 상태를 반환합니다.
- `PassRateCalculator` - 주어진 테스트에 대해 pass@1 및 pass@k를 계산합니다.

파일 하단의 데모는 생성된 코드를 시뮬레이션하고, 샌드박스에서 실행하고, pass@k 메트릭을 계산합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 pass@k 메트릭을 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 코드 평가로 확장합니다.

**Timeout for sandbox execution.** 생성된 코드는 무한 루프에 빠질 수 있습니다. 샌드박스 실행은 시간 제한이 있어야 합니다.

**Resource limits for sandbox.** 생성된 코드는 너무 많은 메모리나 CPU를 사용할 수 있습니다. 샌드박스는 리소스를 제한해야 합니다.

**Test case generation.** 테스트 케이스는 문제 설명에서 자동으로 생성되어야 합니다.

## Use It

프로덕션 패턴:

- **pass@k with temperature sampling.** pass@k에서 k는 생성된 샘플 수를 제어합니다. 더 높은 온도 샘플링은 더 다양한 코드를 생성합니다.

## Ship It

`outputs/skill-code-exec-metric.md`는 실제 프로젝트에서 사용할 k, 샌드박스 구성 및 테스트 케이스가 생성되는 방법을 설명합니다. 이 레슨은 엔진을 제공합니다.

## Exercises

1. 샌드박스 실행을 위한 `--timeout` 플래그를 추가합니다.
2. 샌드박스 실행을 위한 `--memory-limit` 플래그를 추가합니다.
3. pass@1, pass@5 및 pass@k를 계산하는 pass@k 평가기를 추가합니다.
4. 문제 설명에서 테스트 케이스를 생성하는 테스트 케이스 생성을 추가합니다.
5. pass@k에서 온도 샘플링을 추가합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Pass@k | "k-shot pass rate" | k개 생성된 코드 샘플 중 테스트를 통과하는 비율 |
| Sandbox execution | "Safe execution" | 제한된 리소스로 격리된 환경에서 코드 실행 |
| Test case | "Verification" | 코드의 정확성을 검증하기 위한 입력-출력 쌍 |

## Further Reading

- [Chen et al., Evaluating Large Language Models Trained on Code (arXiv 2107.03374)](https://arxiv.org/abs/2107.03374) - pass@k의 원본 논문
- [HumanEval benchmark](https://github.com/openai/human-eval) - 코드 생성을 위한 표준 벤치마크
- Phase 19 · 71 - 고전 메트릭(코드 실행 메트릭의 대안)
- Phase 19 · 75 - 엔드-투-엔드 평가 러너(코드 실행 메트릭 통합)
