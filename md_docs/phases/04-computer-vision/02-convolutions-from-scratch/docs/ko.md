# 합성곱 처음부터 구현

> 합성곱은 이미지 위를 슬라이딩하는 작은 완전연결층으로, 모든 위치에서 동일한 가중치를 공유합니다.

**유형:** 빌드
**언어:** Python
**선수 과목:** Phase 3, Phase 4 Lesson 01
**시간:** ~75분

## 개념

### 합성곱 = 공유 가중치 슬라이딩 창

```
출력[i,j] = Σ_k Σ_l 입력[i+k, j+l] * 커널[k,l]
```

커널이 이미지 위를 슬라이딩하며 지역적 패턴(에지, 텍스처)을 감지.

### 파라미터 효율성

- 완전연결: H×W×C → 뉴런당 H×W×C 파라미터
- 합성곱: K×K×C → 뉴런당 K×K×C 파라미터 (공유!)
- 3×3 커널은 위치에 관계없이 동일한 검출기 사용

### 주요 용어

- **스트라이드**: 커널 이동 간격. 2 = 출력 크기 절반
- **패딩**: 경계 처리. 'same' = 출력 크기 유지
- **커널/필터**: 학습 가능한 작은 가중치 행렬
- **특성 맵**: 합성곱 출력 — 하나의 커널이 하나의 특성 맵 생성

## 빌드하기

```python
def conv2d_forward(X, kernel, stride=1, pad=0):
    N, C_in, H, W = X.shape
    C_out, _, K, _ = kernel.shape
    H_out = (H + 2*pad - K) // stride + 1
    W_out = (W + 2*pad - K) // stride + 1
    X_pad = np.pad(X, ((0,0),(0,0),(pad,pad),(pad,pad)))
    out = np.zeros((N, C_out, H_out, W_out))
    for n in range(N):
        for c_out in range(C_out):
            for i in range(H_out):
                for j in range(W_out):
                    region = X_pad[n, :, i*stride:i*stride+K, j*stride:j*stride+K]
                    out[n, c_out, i, j] = np.sum(region * kernel[c_out])
    return out
```

## 주요 용어

| 용어 | 실제 의미 |
|------|----------|
| 커널 | 작은 학습 가능 필터 — 패턴 검출기 |
| 스트라이드 | 슬라이딩 간격 — 출력 크기 제어 |
| 특성 맵 | 합성곱 출력 — 활성화 평면 |