# ML 파이프라인

> 모델은 제품이 아닙니다. 파이프라인이 제품입니다. 원시 데이터부터 배포된 예측까지 모든 것이 파이프라인이며, 모든 단계가 재현 가능해야 합니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 2, Lesson 12
**시간:** ~120분

## 학습 목표

- 결측치 대체, 스케일링, 인코딩, 모델 훈련을 단일 재현 가능 객체로 연결하는 ML 파이프라인 구축
- 데이터 누수 시나리오 식별, 파이프라인이 훈련 데이터에만 변환기를 적합시켜 누수를 방지하는 방법 설명
- 수치 특성과 범주형 특성에 다른 전처리를 적용하는 ColumnTransformer 구축
- 파이프라인 직렬화 구현, 훈련과 프로덕션에서 동일한 적합 파이프라인이 동일한 결과를 생성함을 시연

## 개념

### 파이프라인 구성 요소

```
원시 데이터 → 결측치 대체 → 스케일링 → 인코딩 → 특성 선택 → 모델
```

각 단계는 `.fit()` (훈련 시)과 `.transform()` (예측 시)이 있는 변환기.

### 데이터 누수 방지

- **누수**: 전체 데이터셋으로 전처리 파라미터 계산 (중앙값, 평균 등)
- **해결**: `.fit()`은 훈련 데이터에만 호출. 파이프라인이 이를 자동 시행.

### ColumnTransformer

수치 열과 범주형 열에 다른 전처리 적용:
- 수치: 중앙값 대체 + 표준화
- 범주형: 최빈값 대체 + 원-핫 인코딩

### 직렬화

적합된 파이프라인 저장 → 프로덕션에서 로드 → 훈련과 정확히 동일한 변환 보장.

## 빌드하기

```python
class Pipeline:
    def __init__(self, steps):
        self.steps = steps

    def fit(self, X, y=None):
        data = X
        for name, transformer in self.steps[:-1]:
            data = transformer.fit_transform(data)
        self.steps[-1][1].fit(data, y)
        return self

    def transform(self, X):
        return self._run_steps(X, range(len(self.steps) - 1))

    def predict(self, X):
        data = self.transform(X)
        return self.steps[-1][1].predict(data)

    def _run_steps(self, X, idxs):
        data = X
        for i in idxs:
            data = self.steps[i][1].transform(data)
        return data
```

## 연습 문제

1. 결측치 대체 → 표준화 → 로지스틱 회귀 파이프라인 구축
2. ColumnTransformer로 수치/범주형 혼합 특성 처리
3. 적합된 파이프라인 pickle 저장 후 로드, 동일한 출력 확인

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 파이프라인 | 변환 + 모델을 단일 객체로 연결 |
| 데이터 누수 | 미래/테스트 정보가 훈련으로 유입 |
| ColumnTransformer | 열 유형별 다른 전처리 |
| 직렬화 | 적합된 파이프라인 저장 → 프로덕션에서 재사용 |