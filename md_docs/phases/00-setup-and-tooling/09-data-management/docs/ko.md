# 데이터 관리

> 데이터는 연료입니다. 관리 방법이 속도를 결정합니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 0, Lesson 01
**시간:** ~45분

## 학습 목표

- Hugging Face `datasets` 라이브러리를 사용하여 데이터셋 로드, 스트리밍, 캐싱하기
- CSV, JSON, Parquet, Arrow 형식 간 변환 및 트레이드오프 설명하기
- 고정된 랜덤 시드로 재현 가능한 train/validation/test 분할 만들기
- `.gitignore`, Git LFS, DVC를 사용하여 대용량 모델 및 데이터셋 파일 관리하기

## 문제

모든 AI 프로젝트는 데이터로 시작합니다. 데이터셋을 찾고, 다운로드하고, 형식 간 변환하고, 훈련과 평가를 위해 분할하고, 실험이 재현 가능하도록 버전 관리해야 합니다. 매번 수동으로 하면 느리고 오류가 발생하기 쉽습니다. 반복 가능한 워크플로우가 필요합니다.

## 개념

```mermaid
graph TD
    A["Hugging Face Hub"] --> B["datasets 라이브러리"]
    B --> C["로드 / 스트리밍"]
    C --> D["로컬 캐시<br/>~/.cache/huggingface/"]
    B --> E["형식 변환<br/>CSV, JSON, Parquet, Arrow"]
    E --> F["데이터 분할<br/>train / val / test"]
    F --> G["훈련 파이프라인"]
```

Hugging Face `datasets` 라이브러리는 AI 작업을 위한 데이터 로드의 표준 방식입니다. 다운로드, 캐싱, 형식 변환, 스트리밍을 기본으로 처리합니다.

## 빌드하기

### 1단계: datasets 라이브러리 설치

```bash
pip install datasets huggingface_hub
```

### 2단계: 데이터셋 로드

```python
from datasets import load_dataset

dataset = load_dataset("imdb")
print(dataset)
print(dataset["train"][0])
```

IMDB 영화 리뷰 데이터셋을 다운로드합니다. 첫 다운로드 후 `~/.cache/huggingface/datasets/`의 캐시에서 로드됩니다.

### 3단계: 대용량 데이터셋 스트리밍

일부 데이터셋은 디스크에 담기 너무 큽니다. 스트리밍은 전체를 다운로드하지 않고 행 단위로 로드합니다.

```python
dataset = load_dataset("wikimedia/wikipedia", "20220301.en", split="train", streaming=True)

for i, example in enumerate(dataset):
    print(example["title"])
    if i >= 4:
        break
```

스트리밍은 `IterableDataset`을 제공합니다. 도착하는 대로 행을 처리합니다. 데이터셋 크기에 관계없이 메모리 사용량이 일정합니다.

### 4단계: 데이터셋 형식

`datasets` 라이브러리는 내부적으로 Apache Arrow를 사용합니다. 파이프라인에 필요한 다른 형식으로 변환할 수 있습니다.

```python
dataset = load_dataset("imdb", split="train")

dataset.to_csv("imdb_train.csv")
dataset.to_json("imdb_train.json")
dataset.to_parquet("imdb_train.parquet")
```

형식 비교:

| 형식 | 크기 | 읽기 속도 | 최적 용도 |
|------|------|----------|----------|
| CSV | 큼 | 느림 | 사람이 읽기, 스프레드시트 |
| JSON | 큼 | 느림 | API, 중첩 데이터 |
| Parquet | 작음 | 빠름 | 분석, 컬럼 기반 쿼리 |
| Arrow | 작음 | 가장 빠름 | 인메모리 처리 (`datasets` 내부 사용) |

AI 작업에서는 Parquet이 최고의 저장 형식입니다. Arrow는 메모리에서 작업할 때 사용합니다. CSV와 JSON은 교환용입니다.

### 5단계: 데이터 분할

모든 ML 프로젝트에는 세 가지 분할이 필요합니다:

- **Train**: 모델이 학습하는 데이터 (일반적으로 80%)
- **Validation**: 훈련 중 진행 상황 확인 (일반적으로 10%)
- **Test**: 훈련 완료 후 최종 평가 (일반적으로 10%)

일부 데이터셋은 미리 분할되어 있습니다. 그렇지 않은 경우 직접 분할하세요:

```python
dataset = load_dataset("imdb", split="train")

split = dataset.train_test_split(test_size=0.2, seed=42)
train_val = split["train"].train_test_split(test_size=0.125, seed=42)

train_ds = train_val["train"]
val_ds = train_val["test"]
test_ds = split["test"]

print(f"Train: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")
```

재현성을 위해 항상 시드를 설정하세요. 동일한 시드는 매번 동일한 분할을 생성합니다.

### 6단계: 모델 다운로드 및 캐싱

모델은 대용량 파일입니다. `huggingface_hub` 라이브러리가 다운로드와 캐싱을 처리합니다.

```python
from huggingface_hub import hf_hub_download, snapshot_download

model_path = hf_hub_download(
    repo_id="sentence-transformers/all-MiniLM-L6-v2",
    filename="config.json"
)
print(f"캐시 위치: {model_path}")

model_dir = snapshot_download("sentence-transformers/all-MiniLM-L6-v2")
print(f"전체 모델 위치: {model_dir}")
```

모델은 `~/.cache/huggingface/hub/`에 캐시됩니다. 한 번 다운로드하면 이후 실행 시 즉시 로드됩니다.

### 7단계: 대용량 파일 처리

모델 가중치와 대용량 데이터셋은 git에 넣지 마세요. 세 가지 옵션:

**옵션 A: .gitignore (가장 간단)**

```
*.bin
*.safetensors
*.pt
*.onnx
data/*.parquet
data/*.csv
models/
```

**옵션 B: Git LFS (git에서 대용량 파일 추적)**

```bash
git lfs install
git lfs track "*.bin"
git lfs track "*.safetensors"
git add .gitattributes
```

Git LFS는 저장소에 포인터를 저장하고 실제 파일은 별도 서버에 저장합니다. GitHub은 1GB 무료 제공.

**옵션 C: DVC (데이터 버전 관리)**

```bash
pip install dvc
dvc init
dvc add data/training_set.parquet
git add data/training_set.parquet.dvc data/.gitignore
git commit -m "DVC로 훈련 데이터 추적"
```

DVC는 데이터를 가리키는 작은 `.dvc` 파일을 만듭니다. 데이터 자체는 S3, GCS, 또는 다른 원격 저장소 백엔드에 저장됩니다.

| 접근법 | 복잡도 | 최적 용도 |
|--------|-------|----------|
| .gitignore | 낮음 | 개인 프로젝트, 다시 가져올 수 있는 다운로드 데이터 |
| Git LFS | 중간 | git을 통해 모델 가중치를 공유하는 팀 |
| DVC | 높음 | 재현 가능한 실험, 대용량 데이터셋, 팀 |

이 과정에서는 `.gitignore`로 충분합니다. 머신 간 정확한 실험을 재현해야 할 때 DVC를 사용하세요.

## 이 과정에서 사용되는 데이터셋

| 데이터셋 | 레슨 | 크기 | 학습 내용 |
|---------|------|------|----------|
| IMDB | 토큰화, 분류 | 84 MB | 텍스트 분류 기초 |
| WikiText | 언어 모델링 | 181 MB | 다음 토큰 예측 |
| SQuAD | QA 시스템 | 35 MB | 질문 응답, 스팬 |
| Common Crawl (서브셋) | 임베딩 | 다양 | 대규모 텍스트 처리 |
| MNIST | 비전 기초 | 21 MB | 이미지 분류 기초 |
| COCO (서브셋) | 멀티모달 | 다양 | 이미지-텍스트 쌍 |

지금 모두 다운로드할 필요는 없습니다. 각 레슨에서 필요한 것을 지정합니다.

## 활용하기

유틸리티 스크립트를 실행하여 모든 것이 작동하는지 확인:

```bash
python code/data_utils.py
```

작은 데이터셋을 다운로드하고, 변환하고, 분할하고, 요약을 출력합니다.

## 배포하기

이 레슨이 생성하는 것:
- `code/data_utils.py` - 재사용 가능한 데이터 로드 및 캐싱 유틸리티
- `outputs/prompt-data-helper.md` - 작업에 적합한 데이터셋 찾기 프롬프트

## 연습 문제

1. `mrpc` 구성으로 `glue` 데이터셋을 로드하고 처음 5개 예제 검사하기
2. `c4` 데이터셋을 스트리밍하고 10초 동안 몇 개의 예제를 처리할 수 있는지 세기
3. 데이터셋을 Parquet으로 변환하고 CSV와 파일 크기 비교하기
4. 고정된 시드로 70/15/15 train/val/test 분할을 만들고 크기 확인하기

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|----------|
| 데이터셋 분할 | "훈련 데이터" | ML 수명 주기의 여러 단계에서 사용되는 명명된 서브셋 (train/val/test) |
| 스트리밍 | "지연 로드" | 전체 데이터셋을 다운로드하지 않고 원격 소스에서 행 단위로 데이터 처리 |
| Parquet | "압축된 CSV" | 분석 쿼리와 저장 효율성에 최적화된 컬럼 기반 파일 형식 |
| Arrow | "빠른 데이터프레임" | 제로 카피 읽기를 위해 datasets 라이브러리에서 내부적으로 사용하는 인메모리 컬럼 형식 |
| Git LFS | "대용량 파일용 Git" | 버전 관리에 포인터를 유지하면서 git 저장소 외부에 대용량 파일을 저장하는 확장 |
| DVC | "데이터용 Git" | 클라우드 저장소와 통합되는 데이터셋 및 모델용 버전 관리 시스템 |
| 캐시 | "이미 다운로드됨" | 이전에 가져온 데이터의 로컬 복사본, 기본적으로 ~/.cache/huggingface/에 저장됨 |