# 불균형 데이터 처리

> 데이터의 99%가 "정상"일 때, 정확도는 거짓말입니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 2, Lessons 01-09
**시간:** ~90분

## 학습 목표

- SMOTE를 처음부터 구현, 합성 오버샘플링이 무작위 복제와 다른 점 설명
- 정확도 대신 F1, AUPRC, 매튜 상관 계수로 불균형 분류기 평가
- 클래스 가중치, 임계값 튜닝, 리샘플링 전략 비교, 주어진 불균형 비율에 적합한 접근법 선택
- SMOTE, 클래스 가중치, 임계값 최적화를 결합한 완전한 불균형 데이터 파이프라인 구축

## 개념

### 문제

사기 탐지 → 99.9%가 정상 → "항상 정상 예측" = 99.9% 정확도, 완전히 쓸모없음.

### 해결 전략

**데이터 수준**:
- **과소표집**: 다수 클래스 무작위 제거 → 정보 손실 위험
- **과대표집**: 소수 클래스 복제 → 과적합 위험
- **SMOTE**: 소수 클래스 점 사이 보간으로 합성 샘플 생성. k-최근접 이웃 소수 클래스 샘플 선택, 점 사이 랜덤 지점 생성.

**알고리즘 수준**:
- **클래스 가중치**: 소수 클래스 오분류에 더 높은 페널티. `class_weight = n_total / (n_classes * n_samples_per_class)`
- **임계값 이동**: 기본 0.5 대신 최적 F1/AUPRC 임계값 사용

### 올바른 지표

| 지표 | 불균형에 적합? | 이유 |
|------|-------------|------|
| 정확도 | ❌ | "항상 다수 클래스"도 높음 |
| F1 | ✅ | 정밀도-재현율 균형 |
| AUPRC | ✅ | 불균형에 특화 — 정밀도-재현율 곡선 |
| MCC | ✅ | -1~1, 모든 혼동 행렬 셀 고려 |

## 빌드하기 (SMOTE)

```python
def smote(X_minority, k=5, n_synthetic=100):
    synthetic = []
    for _ in range(n_synthetic):
        idx = np.random.randint(len(X_minority))
        nn = np.argsort(np.sum((X_minority - X_minority[idx])**2, axis=1))[1:k+1]
        nn_idx = np.random.choice(nn)
        diff = X_minority[nn_idx] - X_minority[idx]
        synthetic.append(X_minority[idx] + np.random.random() * diff)
    return np.array(synthetic)
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| SMOTE | 소수 클래스 점 사이 보간 → 합성 샘플 |
| 클래스 가중치 | 소수 클래스 오분류 페널티 증가 |
| AUPRC | 불균형 데이터용 AUC — 정밀도-재현율 |
| 임계값 이동 | 기본 0.5 대신 최적화된 결정 경계 |