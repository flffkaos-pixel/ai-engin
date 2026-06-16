# 비전-언어 평가

> 비전-언어 모델의 평가는 텍스트 전용 평가(레슨 49) 이상으로 확장됩니다. 비전-언어 모델은 이미지 캡셔닝, 시각적 질문 응답(VQA) 및 이미지-텍스트 검색을 포함한 작업에서 평가됩니다. 각 작업은 다른 메트릭을 사용합니다. 이 레슨은 이미지 캡셔닝(ROUGE-L, CIDEr), VQA(정확히 일치) 및 이미지-텍스트 검색(재현율@K)을 위한 작업 정의와 평가기를 구축합니다.

**Type:** Build
**Languages:** Python
**Prerequisites:** Phase 19 lessons 58-62
**Time:** ~90 minutes

## Learning Objectives

- 이미지 캡셔닝, VQA 및 이미지-텍스트 검색을 위한 작업 정의를 구현합니다.
- 각 작업에 대한 평가기(ROUGE-L, CIDEr, 정확히 일치, 재현율@K)를 구현합니다.
- 평가 하네스(레슨 49)에 연결하여 비전-언어 평가를 실행합니다.

## The Problem

비전-언어 모델은 다양한 양식과 메트릭에 걸쳐 평가됩니다. 이미지 캡셔닝은 텍스트 생성을 평가합니다. VQA는 사실 이해를 평가합니다. 이미지-텍스트 검색은 임베딩 정렬을 평가합니다. 각 메트릭에는 자체 계산이 필요합니다. 비전-언어 평가 하네스가 없으면 이러한 평가를 처음부터 구축해야 합니다.

## The Concept

```mermaid
flowchart TD
  Model[Vision-language model] --> Tasks[Task definitions]
  Tasks --> Captioning[Image captioning]
  Tasks --> VQA[Visual QA]
  Tasks --> Retrieval[Image-text retrieval]
  Captioning --> ROUGE[ROUGE-L]
  Captioning --> CIDEr[CIDEr]
  VQA --> EM[Exact match]
  Retrieval --> Recall[Recall@K]
```

### Image captioning

이미지 캡셔닝은 이미지가 주어졌을 때 텍스트 캡션을 생성합니다. 평가기는 참조 캡션과 생성된 캡션을 비교합니다.

- **ROUGE-L** - 캡션의 가장 긴 공통 부분 수열의 F1 점수.
- **CIDEr** - TF-IDF 가중 n-gram 유사도. 이미지 캡셔닝에 특화됨.

### Visual QA (VQA)

VQA는 이미지와 질문이 주어졌을 때 답변을 생성합니다. 평가기는 생성된 답변을 참조 답변과 비교합니다.

- **Exact match** - 생성된 답변이 참조 답변과 정확히 일치하는지 확인합니다.

### Image-text retrieval

이미지-텍스트 검색은 텍스트 쿼리에 대한 가장 관련성 높은 이미지를 검색합니다. 평가기는 검색된 결과의 순위를 평가합니다.

- **Recall@K** - 상위 K개 검색 결과 내에서 올바른 이미지의 비율.

## Build It

`code/main.py` implements:

- `ImageCaptioningTask` - 이미지 캡셔닝을 위한 평가기, ROUGE-L 및 CIDEr 계산 포함.
- `VQATask` - VQA를 위한 평가기, 정확히 일치 계산 포함.
- `ImageTextRetrievalTask` - 이미지-텍스트 검색을 위한 평가기, 재현율@K 계산 포함.
- `VLEvalHarness` - 레슨 49의 평가 하네스에 연결하여 비전-언어 평가를 실행합니다.

파일 하단의 데모는 비전-언어 모델과 데이터셋을 시뮬레이션하고, 세 가지 작업을 실행하고, 메트릭을 출력합니다.

Run it:

```bash
python3 code/main.py
```

스크립트는 0으로 종료되고 이미지 캡셔닝, VQA 및 이미지-텍스트 검색 작업에 대한 메트릭을 출력합니다.

## Production Patterns

세 가지 패턴이 이 레슨을 프로덕션 비전-언어 평가로 확장합니다.

**Evaluation on multiple datasets.** 각 작업은 여러 데이터셋(예: COCO 캡션, Flickr30k)에서 평가되어야 합니다. 모델 성능은 데이터셋 전반에 걸쳐 보고되어야 합니다. 평가 하네스는 작업당 여러 데이터셋을 지원해야 합니다.

**Normalized metrics for comparison.** CIDEr와 ROUGE-L은 데이터셋 간에 직접 비교할 수 없습니다. 평가 하네스는 모델 비교를 위해 메트릭을 정규화해야 합니다.

**Human evaluation for open-ended generation.** 이미지 캡셔닝 및 VQA에 대한 자동 메트릭은 인간 판단과 완벽하게 상관되지 않습니다. 인간 평가가 때때로 필요합니다.

## Use It

프로덕션 패턴:

- **Checkpoint evaluation during pretraining.** 사전 훈련(레슨 62) 중에 모델이 여러 체크포인트에서 평가되어야 합니다. 각 체크포인트는 하나의 평가 작업에 대해 평가됩니다.
- **Zero-shot evaluation.** 비전-언어 모델은 작업별 미세 조정 없이 평가되어야 합니다. 모델의 일반화 능력을 나타냅니다.
- **Few-shot evaluation.** 비전-언어 모델은 작업의 몇 가지 예제가 주어졌을 때 평가되어야 합니다. 모델의 맥락 내 학습 능력을 나타냅니다.

## Ship It

`outputs/skill-vl-eval.md`는 실제 프로젝트에서 사용할 데이터셋, 평가 메트릭 및 평가가 실행되는 빈도를 설명합니다. 이 레슨은 엔진을 제공합니다.

## Exercises

1. 이미지 캡셔닝을 위한 BLEU 메트릭을 추가합니다.
2. 이미지-텍스트 검색을 위한 정밀도@K 메트릭을 추가합니다.
3. VQA 평가를 위한 작업과 메트릭의 정의를 YAML 파일로 외부화합니다.
4. 각 작업의 실행 간 변동성을 측정하기 위해 여러 시드에 걸쳐 평가를 실행하는 `--num-seeds` 플래그를 추가합니다.
5. 이미지 캡셔닝 평가를 위해 인간 평가 점수 수집을 시뮬레이션합니다.

## Key Terms

| Term | What people say | What it actually means |
|------|-----------------|------------------------|
| Image captioning | "Describe the image" | 이미지가 주어졌을 때 텍스트 설명 생성 |
| VQA | "Visual question answering" | 이미지와 질문이 주어졌을 때 답변 생성 |
| Image-text retrieval | "Search images by text" | 텍스트 쿼리에 대한 가장 관련성 높은 이미지 검색 |
| CIDEr | "Caption metric" | TF-IDF 가중 n-gram 유사도 |
| ROUGE-L | "Longest common subsequence" | 가장 긴 공통 부분 수열의 F1 점수 |

## Further Reading

- [Lin, ROUGE: A Package for Automatic Evaluation of Summaries (ACL 2004)](https://aclanthology.org/W04-1013/) - ROUGE 메트릭
- [Vedantam et al., CIDEr: Consensus-based Image Description Evaluation (CVPR 2015)](https://arxiv.org/abs/1411.5726) - CIDEr 메트릭
- [Antol et al., VQA: Visual Question Answering (ICCV 2015)](https://arxiv.org/abs/1505.00468) - VQA 데이터셋 및 작업
- Phase 19 · 49 - LM 평가 하네스(비전-언어 평가가 확장하는 기반)
- Phase 19 · 62 - 비전-언어 사전 훈련(이 평가가 평가하는 모델)
- Phase 19 · 69 - 엔드-투-엔드 RAG 시스템(비전-언어 검색과 관련됨)
