# 모델 평가

> 모델은 그것을 측정하는 방식만큼만 좋습니다.

**유형:** 구현
**언어:** Python
**선수 과목:** Phase 1 (확률 및 분포, 통계), Phase 2 Lessons 1-8
**소요 시간:** ~90분

## 학습 목표

- K-겹 및 계층화 K-겹 교차 검증을 처음부터 구현하고 불균형 데이터에 계층화가 중요한 이유를 설명한다
- 정밀도, 재현율, F1, AUC-ROC, 회귀 지표(MSE, RMSE, MAE, R-제곱)를 처음부터 계산한다
- 학습 곡선을 해석하여 모델이 높은 편향 또는 높은 분산으로 고통받는지 진단한다
- 데이터 누수, 잘못된 지표 선택, 테스트 세트 오염 등 일반적인 평가 실수를 식별한다

## 문제

모델을 훈련시켰습니다. 데이터에서 95% 정확도를 얻습니다. 좋습니까?

아마도. 아닐 수도 있습니다. 데이터의 95%가 한 클래스에 속하면 항상 해당 클래스를 예측하는 모델이 95% 정확도를 얻지만 완전히 쓸모없습니다. 훈련한 동일한 데이터에서 평가하면 95% 숫자가 의미 없습니다 — 모델이 그냥 답을 기억했기 때문입니다. 데이터에 시간 구성 요소가 있고 분할 전에 무작위로 섞었으면, 모델이 과거를 예측하기 위해 미래 데이터를 사용할 수 있습니다.

모델 평가는 대부분의 ML 프로젝트가 잘못되는 곳입니다. 잘못된 지표는 나쁜 모델을 좋아 보이게 합니다. 잘못된 분할은 모델이 부정행위할 수 있게 합니다. 잘못된 비교는 더 나쁜 모델을 선택하게 합니다. 평가를 올바르게 하는 것은 선택사항이 아닙니다. production에서 작동하는 모델과 실제 데이터를 보는 순간 실패하는 모델의 차이입니다.

## 개념

### 훈련, 검증, 테스트

```mermaid
flowchart LR
    A[전체 데이터셋] --> B[훈련 세트 60-70%]
    A --> C[검증 세트 15-20%]
    A --> D[테스트 세트 15-20%]
    B --> E[모델 훈련]
    E --> C
    C --> F[하이퍼파라미터 튜닝]
    F --> E
    F --> G[최종 모델]
    G --> D
    D --> H[성능 보고]
```

세 가지 분할, 세 가지 목적:

- **훈련 세트**: 모델이 이 데이터에서 학습합니다. 훈련 중 이 예제들을 봅니다.
- **검증 세트**: 하이퍼파라미터 튜닝과 모델 선택에 사용됩니다. 모델은 이 데이터에서 훈련하지 않지만, 결정에 영향을 받습니다.
- **테스트 세트**: 매우 끝에서 한 번만Touch됩니다. 최종 성능을 보고합니다. 테스트 성능을 보고 다시 모델을 변경하면 더 이상 테스트 세트가 아닙니다. 두 번째 검증 세트가 됩니다.

테스트 세트는 보고된 성능이 실제 보지 못한 데이터에서 모델이 어떻게 할지 반영한다는保证입니다.

### K-겹 교차 검증

작은 데이터셋에서 단일 훈련/검증 분할은 데이터를 낭비하고 잡음이 있는 추정치를 제공합니다. K-겹 교차 검증은 모든 데이터를 훈련과 검증 모두에 사용합니다:

```mermaid
flowchart TB
    subgraph Fold1["Fold 1"]
        direction LR
        V1["검증"] --- T1a["훈련"] --- T1b["훈련"] --- T1c["훈련"] --- T1d["훈련"]
    end
    subgraph Fold2["Fold 2"]
        direction LR
        T2a["훈련"] --- V2["검증"] --- T2b["훈련"] --- T2c["훈련"] --- T2d["훈련"]
    end
    subgraph Fold3["Fold 3"]
        direction LR
        T3a["훈련"] --- T3b["훈련"] --- V3["검증"] --- T3c["훈련"] --- T3d["훈련"]
    end
    subgraph Fold4["Fold 4"]
        direction LR
        T4a["훈련"] --- T4b["훈련"] --- T4c["훈련"] --- V4["검증"] --- T4d["훈련"]
    end
    subgraph Fold5["Fold 5"]
        direction LR
        T5a["훈련"] --- T5b["훈련"] --- T5c["훈련"] --- T5d["훈련"] --- V5["검증"]
    end
    Fold1 --> R["평균 점수"]
    Fold2 --> R
    Fold3 --> R
    Fold4 --> R
    Fold5 --> R
```

1. 데이터를 K개의 동일한 크기 fold로 분할합니다
2. 각 fold에 대해 K-1 fold에서 훈련하고 나머지 fold에서 검증합니다
3. K개의 검증 점수를 평균합니다

K=5 또는 K=10이 표준 선택입니다. 모든 데이터 포인트가 정확히 한 번씩 검증에 사용됩니다. 평균 점수가 단일 분할보다 안정적인 추정치입니다.

**계층화 K-겹**: 각 fold에서 클래스 분포를 유지합니다. 데이터셋이 클래스 A 70%와 클래스 B 30%이면, 각 fold가 대략 동일한 비율을 가집니다. 이는 클래스 불균형 데이터셋에서 중요합니다 — 무작위 분할이 모든 소수 类 샘플을 하나의 fold에 넣을 수 있습니다.

### 분류 지표

**혼동 행렬**: 기초. 이진 분류의 경우:

|  | 예측 긍정 | 예측 부정 |
|--|---|---|
| 실제 긍정 | 진짜 긍정 (TP) | 거짓 부정 (FN) |
| 실제 부정 | 거짓 긍정 (FP) | 진짜 부정 (TN) |

이 행렬에서 다른 모든 지표가 도출됩니다:

- **정확도** = (TP + TN) / (TP + TN + FP + FN). 정답의 비율. 클래스가 불균형할 때 오해의 소지가 있습니다.
- **정밀도** = TP / (TP + FP). 예측한 긍정 중 실제로 긍정인 것의 비율. 거짓 긍정 비용이 클 때 사용 (예: 스팸 필터가 실제 이메일을 스팸으로 표시).
- **재현율**(민감도) = TP / (TP + FN). 실제 긍정 중 포착한 것의 비율. 거짓 부정 비용이 클 때 사용 (예: 암 screening 종양을 놓침).
- **F1 점수** = 2 * 정밀도 * 재현율 / (정밀도 + 재현율). 정밀도와 재현율의 조화 평균. 둘 사이의 균형을 맞춥니다.
- **AUC-ROC**: ROC 곡선 아래 면적. 다양한 분류 임계값에서 진짜 긍정률 대 거짓 긍정률을 플롯합니다. AUC = 0.5는 무작위 추측, AUC = 1.0은 완벽한 분리입니다. 임계값에 independent: 모델이 긍정을 부정 위에 얼마나 잘 순위 매기는지 측정합니다.

### 회귀 지표

- **MSE**(평균 제곱 오차) = mean((y_true - y_pred)^2). 큰 오차를 이차적으로 페널티 부여. 이상치에 민감합니다.
- **RMSE**(평균 제곱근 오차) = sqrt(MSE). 대상 변수와 같은 단위. MSE보다 해석하기 쉽습니다.
- **MAE**(평균 절대 오차) = mean(|y_true - y_pred|). 모든 오차를 선형으로 처리. MSE보다 이상치에 더 강건합니다.
- **R-제곱** = 1 - SS_res / SS_tot, 여기서 SS_res = sum((y_true - y_pred)^2)이고 SS_tot = sum((y_true - y_mean)^2). 모델이 설명하는 분산의 비율. R^2 = 1.0은 완벽합니다. R^2 = 0.0은 모델이 항상 평균을 예측하는 것보다 나은 것이 없음을 의미합니다. 모델이 평균보다 나쁘면 R^2가 음수가 될 수 있습니다.

### 학습 곡선

훈련 점수와 검증 점수를 훈련 세트 크기의 함수로 플롯합니다:

- **높은 편향**(과소적합): 두 곡선이 모두 낮은 점수로 수렴합니다. 더 많은 데이터가 도움이 되지 않습니다. 더 복잡한 모델이 필요합니다.
- **높은 분산**(과적합): 훈련 점수는 높지만 검증 점수가 훨씬 낮습니다. 그들 사이의 갭이 큽니다. 더 많은 데이터가 도움이 됩니다.

### 검증 곡선

훈련 점수와 검증 점수를 하이퍼파라미터의 함수로 플롯합니다:

- 낮은 복잡도: 두 점수 모두 낮습니다 (과소적합)
- 적절한 복잡도: 두 점수 모두 높고 서로 가깝습니다
- 높은 복잡도: 훈련 점수는 높지만 검증 점수가 떨어집니다 (과적합)

최적 하이퍼파라미터 값은 검증 점수가 피크인 곳입니다.

### 일반적인 평가 실수

**데이터 누수**: 테스트 세트의 정보가 훈련으로 누출됩니다. 예: 분할 전에 전체 데이터셋에서 스케일러 피팅, 시계열 예측에서 미래 데이터 포함, 대상에서 파생된 특성 사용. 항상 분할 먼저, 그 다음 전처리하세요.

**클래스 불균형**: 거래의 99%는 합법적이고 1%는 사기입니다. 항상 "합법"을 예측하는 모델이 99% 정확도를 얻습니다. 대신 정밀도, 재현율, F1 또는 AUC-ROC를 사용하세요.

**잘못된 지표**: 의학적 진단에서 재현율을 최적화해야 할 때 정확도를 최적화하거나, 무거운 이상치가 있는 데이터에서 RMSE를 최적화합니다 (대신 MAE 사용).

**계층화 분할 사용 안 함**: 불균형 데이터에서는 무작위 분할이 검증 fold에 매우 적은 소수 类 샘플을 넣을 수 있어 불안정한 추정을 제공합니다.

**너무 자주 테스트**: 테스트 성능을 보고 조정할 때마다 테스트 세트에 과적합됩니다. 테스트 세트는 단일 사용입니다.

## 실습

### 1단계: 훈련/검증/테스트 분할

```python
import random
import math


def train_val_test_split(X, y, train_ratio=0.6, val_ratio=0.2, seed=42):
    random.seed(seed)
    n = len(X)
    indices = list(range(n))
    random.shuffle(indices)

    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]

    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_val = [X[i] for i in val_idx]
    y_val = [y[i] for i in val_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]

    return X_train, y_train, X_val, y_val, X_test, y_test
```

### 2단계: K-겹 및 계층화 K-겹 교차 검증

```python
def kfold_split(n, k=5, seed=42):
    random.seed(seed)
    indices = list(range(n))
    random.shuffle(indices)

    fold_size = n // k
    folds = []

    for i in range(k):
        start = i * fold_size
        end = start + fold_size if i < k - 1 else n
        val_idx = indices[start:end]
        train_idx = indices[:start] + indices[end:]
        folds.append((train_idx, val_idx))

    return folds


def stratified_kfold_split(y, k=5, seed=42):
    random.seed(seed)

    class_indices = {}
    for i, label in enumerate(y):
        class_indices.setdefault(label, []).append(i)

    for label in class_indices:
        random.shuffle(class_indices[label])

    folds = [{"train": [], "val": []} for _ in range(k)]

    for label, indices in class_indices.items():
        fold_size = len(indices) // k
        for i in range(k):
            start = i * fold_size
            end = start + fold_size if i < k - 1 else len(indices)
            val_part = indices[start:end]
            train_part = indices[:start] + indices[end:]
            folds[i]["val"].extend(val_part)
            folds[i]["train"].extend(train_part)

    return [(f["train"], f["val"]) for f in folds]


def cross_validate(X, y, model_fn, k=5, metric_fn=None, stratified=False):
    n = len(X)

    if stratified:
        folds = stratified_kfold_split(y, k)
    else:
        folds = kfold_split(n, k)

    scores = []
    for train_idx, val_idx in folds:
        X_train = [X[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        X_val = [X[i] for i in val_idx]
        y_val = [y[i] for i in val_idx]

        model = model_fn()
        model.fit(X_train, y_train)
        predictions = [model.predict(x) for x in X_val]

        if metric_fn:
            score = metric_fn(y_val, predictions)
        else:
            score = sum(1 for yt, yp in zip(y_val, predictions) if yt == yp) / len(y_val)
        scores.append(score)

    return scores
```

### 3단계: 혼동 행렬 및 분류 지표

```python
def confusion_matrix(y_true, y_pred):
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)
    return tp, tn, fp, fn


def accuracy(y_true, y_pred):
    tp, tn, fp, fn = confusion_matrix(y_true, y_pred)
    total = tp + tn + fp + fn
    return (tp + tn) / total if total > 0 else 0.0


def precision(y_true, y_pred):
    tp, tn, fp, fn = confusion_matrix(y_true, y_pred)
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def recall(y_true, y_pred):
    tp, tn, fp, fn = confusion_matrix(y_true, y_pred)
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def f1_score(y_true, y_pred):
    p = precision(y_true, y_pred)
    r = recall(y_true, y_pred)
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def roc_curve(y_true, y_scores):
    thresholds = sorted(set(y_scores), reverse=True)
    tpr_list = []
    fpr_list = []

    total_positives = sum(y_true)
    total_negatives = len(y_true) - total_positives

    for threshold in thresholds:
        y_pred = [1 if s >= threshold else 0 for s in y_scores]
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)

        tpr = tp / total_positives if total_positives > 0 else 0.0
        fpr = fp / total_negatives if total_negatives > 0 else 0.0

        tpr_list.append(tpr)
        fpr_list.append(fpr)

    return fpr_list, tpr_list, thresholds


def auc_roc(y_true, y_scores):
    fpr_list, tpr_list, _ = roc_curve(y_true, y_scores)

    pairs = sorted(zip(fpr_list, tpr_list))
    fpr_sorted = [p[0] for p in pairs]
    tpr_sorted = [p[1] for p in pairs]

    area = 0.0
    for i in range(1, len(fpr_sorted)):
        width = fpr_sorted[i] - fpr_sorted[i - 1]
        height = (tpr_sorted[i] + tpr_sorted[i - 1]) / 2
        area += width * height

    return area
```

### 4단계: 회귀 지표

```python
def mse(y_true, y_pred):
    n = len(y_true)
    return sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)) / n


def rmse(y_true, y_pred):
    return math.sqrt(mse(y_true, y_pred))


def mae(y_true, y_pred):
    n = len(y_true)
    return sum(abs(yt - yp) for yt, yp in zip(y_true, y_pred)) / n


def r_squared(y_true, y_pred):
    mean_y = sum(y_true) / len(y_true)
    ss_res = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))
    ss_tot = sum((yt - mean_y) ** 2 for yt in y_true)
    if ss_tot == 0:
        return 0.0
    return 1.0 - ss_res / ss_tot
```

### 5단계: 학습 곡선

```python
def learning_curve(X, y, model_fn, metric_fn, train_sizes=None, val_ratio=0.2, seed=42):
    random.seed(seed)
    n = len(X)
    indices = list(range(n))
    random.shuffle(indices)

    val_size = int(n * val_ratio)
    val_idx = indices[:val_size]
    pool_idx = indices[val_size:]

    X_val = [X[i] for i in val_idx]
    y_val = [y[i] for i in val_idx]

    if train_sizes is None:
        train_sizes = [int(len(pool_idx) * r) for r in [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]]

    train_scores = []
    val_scores = []

    for size in train_sizes:
        subset = pool_idx[:size]
        X_train = [X[i] for i in subset]
        y_train = [y[i] for i in subset]

        model = model_fn()
        model.fit(X_train, y_train)

        train_pred = [model.predict(x) for x in X_train]
        val_pred = [model.predict(x) for x in X_val]

        train_scores.append(metric_fn(y_train, train_pred))
        val_scores.append(metric_fn(y_val, val_pred))

    return train_sizes, train_scores, val_scores
```

### 6단계: 테스트를 위한 간단한 분류기 + 전체 데모

```python
class SimpleLogistic:
    def __init__(self, lr=0.1, epochs=100):
        self.lr = lr
        self.epochs = epochs
        self.weights = None
        self.bias = 0.0

    def sigmoid(self, z):
        z = max(-500, min(500, z))
        return 1.0 / (1.0 + math.exp(-z))

    def fit(self, X, y):
        n_features = len(X[0])
        self.weights = [0.0] * n_features
        self.bias = 0.0

        for _ in range(self.epochs):
            for xi, yi in zip(X, y):
                z = sum(w * x for w, x in zip(self.weights, xi)) + self.bias
                pred = self.sigmoid(z)
                error = yi - pred
                for j in range(n_features):
                    self.weights[j] += self.lr * error * xi[j]
                self.bias += self.lr * error

    def predict_proba(self, x):
        z = sum(w * xi for w, xi in zip(self.weights, x)) + self.bias
        return self.sigmoid(z)

    def predict(self, x):
        return 1 if self.predict_proba(x) >= 0.5 else 0


class SimpleLinearRegression:
    def __init__(self, lr=0.001, epochs=200):
        self.lr = lr
        self.epochs = epochs
        self.weights = None
        self.bias = 0.0

    def fit(self, X, y):
        n_features = len(X[0])
        self.weights = [0.0] * n_features
        self.bias = 0.0
        n = len(X)

        for _ in range(self.epochs):
            for xi, yi in zip(X, y):
                pred = sum(w * x for w, x in zip(self.weights, xi)) + self.bias
                error = yi - pred
                for j in range(n_features):
                    self.weights[j] += self.lr * error * xi[j] / n
                self.bias += self.lr * error / n

    def predict(self, x):
        return sum(w * xi for w, xi in zip(self.weights, x)) + self.bias


def standardize(values):
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    std = math.sqrt(var) if var > 0 else 1.0
    return [(v - mean) / std for v in values], mean, std


def make_classification_data(n=300, seed=42):
    random.seed(seed)
    X = []
    y = []
    for _ in range(n):
        x1 = random.gauss(0, 1)
        x2 = random.gauss(0, 1)
        label = 1 if (x1 + x2 + random.gauss(0, 0.5)) > 0 else 0
        X.append([x1, x2])
        y.append(label)
    return X, y


def make_regression_data(n=200, seed=42):
    random.seed(seed)
    X = []
    y = []
    for _ in range(n):
        x1 = random.uniform(0, 10)
        x2 = random.uniform(0, 5)
        target = 3 * x1 + 2 * x2 + random.gauss(0, 2)
        X.append([x1, x2])
        y.append(target)
    return X, y


def make_imbalanced_data(n=300, minority_ratio=0.05, seed=42):
    random.seed(seed)
    X = []
    y = []
    for _ in range(n):
        if random.random() < minority_ratio:
            x1 = random.gauss(3, 0.5)
            x2 = random.gauss(3, 0.5)
            label = 1
        else:
            x1 = random.gauss(0, 1)
            x2 = random.gauss(0, 1)
            label = 0
        X.append([x1, x2])
        y.append(label)
    return X, y


if __name__ == "__main__":
    X_clf, y_clf = make_classification_data(300)

    print("=== 훈련/검증/테스트 분할 ===")
    X_train, y_train, X_val, y_val, X_test, y_test = train_val_test_split(X_clf, y_clf)
    print(f"  훈련: {len(X_train)}, 검증: {len(X_val)}, 테스트: {len(X_test)}")
    print(f"  훈련 클래스 분포: {sum(y_train)}/{len(y_train)} 긍정")
    print(f"  검증 클래스 분포: {sum(y_val)}/{len(y_val)} 긍정")

    model = SimpleLogistic(lr=0.1, epochs=200)
    model.fit(X_train, y_train)

    print("\n=== 분류 지표 ===")
    y_pred = [model.predict(x) for x in X_test]
    tp, tn, fp, fn = confusion_matrix(y_test, y_pred)
    print(f"  혼동 행렬: TP={tp}, TN={tn}, FP={fp}, FN={fn}")
    print(f"  정확도:  {accuracy(y_test, y_pred):.4f}")
    print(f"  정밀도: {precision(y_test, y_pred):.4f}")
    print(f"  재현율:    {recall(y_test, y_pred):.4f}")
    print(f"  F1 점수:  {f1_score(y_test, y_pred):.4f}")

    y_scores = [model.predict_proba(x) for x in X_test]
    auc = auc_roc(y_test, y_scores)
    print(f"  AUC-ROC:   {auc:.4f}")

    print("\n=== K-겹 교차 검증 (K=5) ===")
    cv_scores = cross_validate(
        X_clf, y_clf,
        model_fn=lambda: SimpleLogistic(lr=0.1, epochs=200),
        k=5,
        metric_fn=accuracy,
    )
    mean_cv = sum(cv_scores) / len(cv_scores)
    std_cv = math.sqrt(sum((s - mean_cv) ** 2 for s in cv_scores) / len(cv_scores))
    print(f"  Fold 점수: {[round(s, 4) for s in cv_scores]}")
    print(f"  평균: {mean_cv:.4f} (+/- {std_cv:.4f})")

    print("\n=== 계층화 K-겹 교차 검증 (K=5) ===")
    strat_scores = cross_validate(
        X_clf, y_clf,
        model_fn=lambda: SimpleLogistic(lr=0.1, epochs=200),
        k=5,
        metric_fn=accuracy,
        stratified=True,
    )
    strat_mean = sum(strat_scores) / len(strat_scores)
    strat_std = math.sqrt(sum((s - strat_mean) ** 2 for s in strat_scores) / len(strat_scores))
    print(f"  Fold 점수: {[round(s, 4) for s in strat_scores]}")
    print(f"  평균: {strat_mean:.4f} (+/- {strat_std:.4f})")

    print("\n=== 불균형 데이터: 정확도가 거짓말하는 이유 ===")
    X_imb, y_imb = make_imbalanced_data(300, minority_ratio=0.05)
    positives = sum(y_imb)
    print(f"  클래스 분포: {positives} 긍정, {len(y_imb) - positives} 부정 ({positives/len(y_imb)*100:.1f}% 긍정)")

    always_negative = [0] * len(y_imb)
    print(f"  항상-부정 기준:")
    print(f"    정확도:  {accuracy(y_imb, always_negative):.4f}")
    print(f"    정밀도: {precision(y_imb, always_negative):.4f}")
    print(f"    재현율:    {recall(y_imb, always_negative):.4f}")
    print(f"    F1 점수:  {f1_score(y_imb, always_negative):.4f}")

    X_tr_i, y_tr_i, X_v_i, y_v_i, X_te_i, y_te_i = train_val_test_split(X_imb, y_imb)
    model_imb = SimpleLogistic(lr=0.5, epochs=500)
    model_imb.fit(X_tr_i, y_tr_i)
    y_pred_imb = [model_imb.predict(x) for x in X_te_i]
    print(f"\n  불균형 데이터에서 훈련된 모델:")
    print(f"    정확도:  {accuracy(y_te_i, y_pred_imb):.4f}")
    print(f"    정밀도: {precision(y_te_i, y_pred_imb):.4f}")
    print(f"    재현율:    {recall(y_te_i, y_pred_imb):.4f}")
    print(f"    F1 점수:  {f1_score(y_te_i, y_pred_imb):.4f}")

    print("\n=== 회귀 지표 ===")
    X_reg, y_reg = make_regression_data(200)

    col0 = [x[0] for x in X_reg]
    col1 = [x[1] for x in X_reg]
    col0_s, m0, s0 = standardize(col0)
    col1_s, m1, s1 = standardize(col1)
    X_reg_scaled = [[col0_s[i], col1_s[i]] for i in range(len(X_reg))]

    X_tr_r, y_tr_r, X_v_r, y_v_r, X_te_r, y_te_r = train_val_test_split(X_reg_scaled, y_reg)
    reg_model = SimpleLinearRegression(lr=0.01, epochs=500)
    reg_model.fit(X_tr_r, y_tr_r)
    y_pred_r = [reg_model.predict(x) for x in X_te_r]

    print(f"  MSE:       {mse(y_te_r, y_pred_r):.4f}")
    print(f"  RMSE:      {rmse(y_te_r, y_pred_r):.4f}")
    print(f"  MAE:       {mae(y_te_r, y_pred_r):.4f}")
    print(f"  R-제곱: {r_squared(y_te_r, y_pred_r):.4f}")

    mean_baseline = [sum(y_tr_r) / len(y_tr_r)] * len(y_te_r)
    print(f"\n  평균 기준:")
    print(f"    MSE:       {mse(y_te_r, mean_baseline):.4f}")
    print(f"    R-제곱: {r_squared(y_te_r, mean_baseline):.4f}")

    print("\n=== 학습 곡선 ===")
    sizes, train_sc, val_sc = learning_curve(
        X_clf, y_clf,
        model_fn=lambda: SimpleLogistic(lr=0.1, epochs=200),
        metric_fn=accuracy,
    )
    print(f"  {'크기':>6} {'훈련':>8} {'검증':>8}")
    for s, tr, va in zip(sizes, train_sc, val_sc):
        print(f"  {s:>6} {tr:>8.4f} {va:>8.4f}")

    print("\n=== 통계적 모델 비교 ===")
    model_a_scores = cross_validate(
        X_clf, y_clf,
        model_fn=lambda: SimpleLogistic(lr=0.1, epochs=100),
        k=5, metric_fn=accuracy,
    )
    model_b_scores = cross_validate(
        X_clf, y_clf,
        model_fn=lambda: SimpleLogistic(lr=0.1, epochs=500),
        k=5, metric_fn=accuracy,
    )
    diffs = [a - b for a, b in zip(model_a_scores, model_b_scores)]
    mean_diff = sum(diffs) / len(diffs)
    std_diff = math.sqrt(sum((d - mean_diff) ** 2 for d in diffs) / len(diffs))
    t_stat = mean_diff / (std_diff / math.sqrt(len(diffs))) if std_diff > 0 else 0.0
    print(f"  모델 A (100 에포크) 평균: {sum(model_a_scores)/len(model_a_scores):.4f}")
    print(f"  모델 B (500 에포크) 평균: {sum(model_b_scores)/len(model_b_scores):.4f}")
    print(f"  평균 차이: {mean_diff:.4f}")
    print(f"  짝을 이룬 t-통계량: {t_stat:.4f}")
    print(f"  (df=4에서 p<0.05에 대해 |t| > 2.78)")
```

## 활용

scikit-learn으로 평가가 워크플로우에 내장되어 있습니다:

```python
from sklearn.model_selection import cross_val_score, StratifiedKFold, learning_curve
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, mean_squared_error, r2_score,
)
from sklearn.linear_model import LogisticRegression

model = LogisticRegression()
scores = cross_val_score(model, X, y, cv=StratifiedKFold(5), scoring="f1")
```

처음부터 구현한 버전은 교차 검증을 수행하는 방법(루프와 인덱스 추적만, 마법 없음), 각 지표가 계산되는 방법(TP/FP/TN/FN 세기만), 계층화가 중요한 이유(각 fold에서 클래스 비율 유지)를 보여줍니다. 라이브러리 버전은 병렬 처리, 더 많은 점수 옵션, 파이프라인 통합을 추가합니다.

## 결과물

이 수업은 다음을 생성합니다:
- `outputs/skill-evaluation.md` - 분류 및 회귀 모델의 평가 전략을 다루는 skill

## 연습 문제

1. 정밀도-재현율 곡선을 구현하세요: 다양한 임계값에서 정밀도를 재현율에 대해 플롯합니다. PR 곡선 아래 면적(평균 정밀도)을 계산하세요. 불균형 데이터셋에서 PR 곡선을 ROC 곡선과 비교하고 각각이 언제 더 유익한지 설명하세요.

2. 중첩 교차 검증 루프를 구축하세요: 외부 루프가 모델 성능을 평가하고, 내부 루프가 하이퍼파라미터를 튜닝합니다. 검증 데이터가 평가에 누출되지 않고 두 모델을 공정하게 비교하는 데 사용하세요.

3. 모델 비교를 위한 순열 검증을 구현하세요: 레이블을 섞고, 재훈련하고, 성능을 측정하세요. 100번 반복하여 null 분포를 구축하세요. 관찰된 모델 성능에 대한 p-값을 이 분포に対して計算하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| 과적합 | "훈련 데이터를 기억한다" | 모델이 훈련 데이터의 노이즈를 포착하여 훈련에서는 잘 하지만 보지 못한 데이터에서 poorly 수행합니다 |
| 교차 검증 | "다른 청크에서 테스트한다" | 검증에 사용되는 데이터 부분을 체계적으로 순환시키고 결과를 평균합니다 |
| 정밀도 | "예측한 긍정 중 얼마나 많은 것이 정확한가" | TP / (TP + FP): 실제로 긍정인 예측된 양성의 비율 |
| 재현율 | "얼마나 많은 실제 양성을 찾았는가" | TP / (TP + FN): 모델이 올바르게 식별한 실제 양성의 비율 |
| AUC-ROC | "모델이 클래스를 얼마나 잘 분리하는가" | 모든 임계값에서 진짜 긍정률 대 거짓 긍정률 곡선의 아래 면적, 0.5(무작위)에서 1.0(완벽)까지 |
| R-제곱 | "설명되는 분산의 양" | 1 - (잔차 제곱합 / 총 제곱합): 모델이 포착한 대상 분산의 비율 |
| 데이터 누수 | "모델이 부정행위했다" | 예측 시점에 사용 가능하지 않을 정보를 훈련에 사용하여 낙관적 평가로 이어집니다 |
| 학습 곡선 | "더 많은 데이터로 성능이 어떻게 변하는가" | 훈련 및 검증 점수를 훈련 세트 크기 대비 플롯하여 과적합 또는 과소적합을 보여줍니다 |
| 계층화 분할 | "클래스 비율을 균형 있게 유지한다" | 각 하위 집합이 전체 데이터셋과 동일한 각 클래스의 비율을 가지도록 데이터를 분할합니다 |

## 추가 자료

- [scikit-learn Model Selection Guide](https://scikit-learn.org/stable/model_selection.html) -- 교차 검증, 지표, 하이퍼파라미터 튜닝에 대한 종합 참조
- [Beyond Accuracy: Precision and Recall (Google ML Crash Course)](https://developers.google.com/machine-learning/crash-course/classification/precision-and-recall) -- 대화형 예제로 명확한 설명
- [A Survey of Cross-Validation Procedures (Arlot & Celisse, 2010)](https://projecteuclid.org/journals/statistics-surveys/volume-4/issue-none/A-survey-of-cross-validation-procedures-for-model-selection/10.1214/09-SS054.full) -- 다양한 CV 전략이 작동하는 이유와 시기에 대한 엄격한 치료