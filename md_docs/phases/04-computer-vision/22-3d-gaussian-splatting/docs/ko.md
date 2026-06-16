# 3D Gaussian Splatting 처음부터 구현하기

> 장면은 수백만 개의 3D 가우시안의 구름이다. 각각은 위치, 방향, 스케일, 불투명도, 그리고 시야 방향에 따라 달라지는 색상을 가진다. 이를 래스터화하고, 래스터화를 통해 역전파하면 끝이다.

**유형:** 빌드
**언어:** Python
**사전 요구사항:** 4단계 13과(3D 비전 & NeRF), 1단계 12과(텐서 연산), 4단계 10과(확산 기초, 선택 사항)
**시간:** ~90분

## 학습 목표

- 3D Gaussian Splatting이 2026년에 NeRF를 대체하여 사실적인 3D 재구성의 프로덕션 기본값이 된 이유를 설명한다
- 여섯 가지 가우시안별 매개변수(위치, 회전 쿼터니언, 스케일, 불투명도, 구면 조화 색상, 선택적 특징)와 각각이 기여하는 float 수를 설명한다
- 알파 합성을 사용하여 2D Gaussian Splatting 래스터라이저를 처음부터 구현한 다음, 3D 경우가 동일한 루프로 투영되는 방법을 보여준다
- `nerfstudio`, `gsplat` 또는 `SuperSplat`을 사용하여 20-50장의 사진에서 장면을 재구성하고 `KHR_gaussian_splatting` glTF 확장 또는 OpenUSD 26.03 `UsdVolParticleField3DGaussianSplat` 스키마로 내보낸다

## 문제

NeRF는 장면을 MLP의 가중치로 저장한다. 렌더링된 모든 픽셀은 광선을 따라 수백 번의 MLP 쿼리이다. 훈련에는 시간이 걸리고, 렌더링에는 초가 걸리며, 가중치는 편집할 수 없다 — 장면 내부의 의자를 옮기려면 다시 훈련해야 한다.

3D Gaussian Splatting(Kerbl, Kopanas, Leimkühler, Drettakis, SIGGRAPH 2023)이 이 모든 것을 대체했다. 장면은 3D 가우시안의 명시적 집합이다. 렌더링은 100+fps의 GPU 래스터화이다. 훈련은 몇 분이 걸린다. 편집은 직접적이다: 가우시안 서브셋을 이동시키면 의자를 옮긴 것이다. 2026년까지 Khronos Group은 가우시안 스플랫을 위한 glTF 확장을 비준했고, OpenUSD 26.03은 가우시안 스플랫 스키마를 제공하며, Zillow와 Apartments.com은 이들로 부동산을 렌더링하고, 대부분의 새로운 3D 재구성 연구 논문은 핵심 3DGS 아이디어의 변형이다.

멘탈 모델은 간단하지만, 수학은 대부분의 입문서가 래스터화부터 시작하여 투영과 구면 조화를 건너뛸 정도로 많은 움직이는 부분을 가지고 있다. 이 과목은 전체를 구축한다 — 먼저 2D 버전, 그 다음 3D 확장.

## 개념

### 가우시안이 가지는 것

하나의 3D 가우시안은 공간의 매개변수적 블롭이며 다음과 같은 속성을 가진다:

```
position         mu         (3,)    세계 좌표의 중심
rotation         q          (4,)    방향을 인코딩하는 단위 쿼터니언
scale            s          (3,)    축별 로그 스케일 (렌더링 시 지수화)
opacity          alpha      (1,)    시그모이드 후 불투명도 [0, 1]
SH coefficients  c_lm       (3 * (L+1)^2,)   시점 의존 색상
```

회전 + 스케일이 3x3 공분산을 구축한다: `Sigma = R S S^T R^T`. 이것이 3D에서 가우시안의 형태이다. 구면 조화는 시점 방향에 따라 색상이 변하게 한다 — 반사 하이라이트, 미세한 광택, 시점 의존 발광 — 뷰별 텍스처를 저장하지 않고. SH 차수 3에서 색상 채널당 16개 계수, 색상만을 위해 가우시안당 48개의 float을 얻는다.

장면은 일반적으로 1-5백만 개의 가우시안을 가진다. 각각은 대략 60개의 float(3 + 4 + 3 + 1 + 48 + 기타)을 저장한다. 5백만 가우시안 장면의 경우 240MB이다 — 포인트별 텍스처가 있는 동등한 포인트 클라우드보다 훨씬 작고, 고해상도로 재렌더링된 NeRF의 MLP 가중치보다 한 자릿수 작다.

### 래스터화, 광선 행진이 아님

```mermaid
flowchart LR
    SCENE["수백만 개의 3D 가우시안<br/>(위치, 회전, 스케일,<br/>불투명도, SH 색상)"] --> PROJ["2D로 투영<br/>(카메라 외부 + 내부 파라미터)"]
    PROJ --> TILES["타일에 할당<br/>(16x16 화면 공간)"]
    TILES --> SORT["깊이 정렬<br/>타일별"]
    SORT --> ALPHA["알파 합성<br/>앞에서 뒤로"]
    ALPHA --> PIX["픽셀 색상"]

    style SCENE fill:#dbeafe,stroke:#2563eb
    style ALPHA fill:#fef3c7,stroke:#d97706
    style PIX fill:#dcfce7,stroke:#16a34a
```

다섯 단계, 모두 GPU 친화적. 픽셀당 MLP 쿼리 없음. 단일 RTX 3080 Ti는 600만 개의 스플랫을 147fps로 렌더링한다.

### 투영 단계

세계 위치 `mu`와 3D 공분산 `Sigma`를 가진 3D 가우시안은 화면 위치 `mu'`와 2D 공분산 `Sigma'`를 가진 2D 가우시안으로 투영된다:

```
mu' = project(mu)
Sigma' = J W Sigma W^T J^T          (2 x 2)

W = 뷰 변환 (카메라의 회전 + 평행 이동)
J = mu'에서 원근 투영의 야코비안
```

2D 가우시안의 발자국은 `Sigma'`의 고유벡터가 축인 타원이다. 이 타원 내부의 모든 픽셀은 `exp(-0.5 * (p - mu')^T Sigma'^-1 (p - mu'))`로 가중치가 적용된 가우시안의 기여를 받는다.

### 알파 합성 규칙

하나의 픽셀에 대해, 그것을 덮는 가우시안은 뒤에서 앞으로(또는 동등하게 반전된 공식으로 앞에서 뒤로) 정렬된다. 색상은 1980년대 이후 모든 반투명 래스터라이저와 동일한 방정식으로 합성된다:

```
C_pixel = sum_i alpha_i * T_i * c_i

T_i = prod_{j < i} (1 - alpha_j)       i까지의 투과율
alpha_i = opacity_i * exp(-0.5 * d^T Sigma'^-1 d)   지역 기여
c_i = eval_SH(SH_i, view_direction)    시점 의존 색상
```

이는 **NeRF의 체적 렌더링과 동일한 방정식**이며, 단지 광선을 따른 밀집 샘플 대신 명시적 희소 가우시안 집합에 대한 것이다. 이 동일성이 렌더링 품질이 NeRF와 일치하는 이유이다 — 둘 다 동일한 복사장 방정식을 적분하고 있기 때문이다.

### 이것이 미분 가능한 이유

모든 단계 — 투영, 타일 할당, 알파 합성, SH 평가 — 는 가우시안 매개변수에 대해 미분 가능하다. 정답 이미지가 주어지면, 렌더링된 픽셀 손실을 계산하고, 래스터라이저를 통해 역전파하며, 경사 하강법으로 모든 `(mu, q, s, alpha, c_lm)`을 업데이트한다. 약 30,000회 반복을 통해 가우시안은 올바른 위치, 스케일, 색상을 찾는다.

### 농축 및 가지치기

고정된 가우시안 집합으로는 복잡한 장면을 덮을 수 없다. 훈련에는 두 가지 적응 메커니즘이 포함된다:

- **복제** — 경사 크기가 크지만 스케일이 작을 때 현재 위치의 가우시안을 복제한다 — 재구성이 더 많은 세부 묘사를 필요로 한다.
- **분할** — 경사가 높을 때 큰 스케일의 가우시안을 두 개의 작은 것으로 분할한다 — 하나의 큰 가우시안이 영역에 맞추기에는 너무 부드럽다.
- **가지치기** — 불투명도가 임계값 아래로 떨어지는 가우시안을 제거한다 — 기여하지 않는다.

농축은 N회 반복마다 실행된다. 장면은 일반적으로 ~100k개의 초기 가우시안(SfM 포인트에서 시드됨)에서 훈련 종료 시 1-5M으로 성장한다.

### 구면 조화를 한 단락으로

시점 의존 색상은 단위 구에서의 함수 `c(direction)`이다. 구면 조화는 구의 푸리에 기저이다. 차수 `L`에서 자르면 채널당 `(L+1)^2`개의 기저 함수를 얻는다. 새 뷰에 대한 색상 평가는 학습된 SH 계수와 시야 방향에서 평가된 기저 사이의 내적이다. 차수 0 = 하나의 계수 = 일정한 색상. 차수 3 = 16개 계수 = Lambertian 음영, 반사, 약한 반사를 포착하기에 충분하다. SD Gaussian Splatting 논문은 기본적으로 차수 3을 사용한다.

### 2026년 프로덕션 스택

```
1. 캡처         스마트폰 / DJI 드론 / 핸드헬드 스캐너
2. SfM / MVS    COLMAP 또는 GLOMAP이 카메라 포즈 + 희소 포인트 도출
3. 3DGS 훈련    nerfstudio / gsplat / inria 공식 / PostShot (~10-30분 on RTX 4090)
4. 편집         SuperSplat / SplatForge (떠다니는 물체 정리, 분할)
5. 내보내기     .ply -> glTF KHR_gaussian_splatting 또는 .usd (OpenUSD 26.03)
6. 보기         Cesium / Unreal / Babylon.js / Three.js / Vision Pro
```

### 4D 및 생성 변형

- **4D Gaussian Splatting** — 가우시안이 시간의 함수; 체적 비디오에 사용됨(Superman 2026, A$AP Rocky의 "Helicopter").
- **생성적 스플랫** — 텍스트-투-스플랫 모델(World Labs의 Marble)로 전체 장면을 환각.
- **3D Gaussian Unscented Transform** — 자율주행 시뮬레이션을 위한 NVIDIA NuRec의 변형.

## 빌드 It

### 단계 1: 2D 가우시안

먼저 2D 래스터라이저를 구축한다. 3D 경우는 투영 후 이것으로 축소된다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


def eval_2d_gaussian(means, covs, points):
    """
    means:  (G, 2)      중심
    covs:   (G, 2, 2)   공분산 행렬
    points: (H, W, 2)   픽셀 좌표
    returns: (G, H, W)  모든 가우시안의 모든 픽셀에서의 밀도
    """
    G = means.size(0)
    H, W, _ = points.shape
    flat = points.view(-1, 2)
    inv = torch.linalg.inv(covs)
    diff = flat[None, :, :] - means[:, None, :]
    d = torch.einsum("gpi,gij,gpj->gp", diff, inv, diff)
    density = torch.exp(-0.5 * d)
    return density.view(G, H, W)
```

`einsum`은 모든 (가우시안, 픽셀) 쌍에 대해 이차 형식 `diff^T Sigma^-1 diff`를 수행한다.

### 단계 2: 2D 스플래팅 래스터라이저

앞에서 뒤로 알파 합성. 2D에서 깊이는 무의미하므로, 순서를 위해 학습된 가우시안별 스칼라를 사용한다.

```python
def rasterise_2d(means, covs, colours, opacities, depths, image_size):
    """
    means:     (G, 2)
    covs:      (G, 2, 2)
    colours:   (G, 3)
    opacities: (G,)     [0, 1]
    depths:    (G,)     정렬을 위해 사용되는 가우시안별 스칼라
    image_size: (H, W)
    returns:   (H, W, 3) 렌더링된 이미지
    """
    H, W = image_size
    yy, xx = torch.meshgrid(
        torch.arange(H, dtype=torch.float32, device=means.device),
        torch.arange(W, dtype=torch.float32, device=means.device),
        indexing="ij",
    )
    points = torch.stack([xx, yy], dim=-1)

    densities = eval_2d_gaussian(means, covs, points)
    alphas = opacities[:, None, None] * densities
    alphas = alphas.clamp(0.0, 0.99)

    order = torch.argsort(depths)
    alphas = alphas[order]
    colours_sorted = colours[order]

    T = torch.ones(H, W, device=means.device)
    out = torch.zeros(H, W, 3, device=means.device)
    for i in range(means.size(0)):
        a = alphas[i]
        out += (T * a)[..., None] * colours_sorted[i][None, None, :]
        T = T * (1.0 - a)
    return out
```

빠르지 않다 — 실제 구현은 타일 기반 CUDA 커널을 사용한다 — 하지만 수학은 정확하고 완전히 미분 가능하다.

### 단계 3: 훈련 가능한 2D 스플랫 장면

```python
class Splats2D(nn.Module):
    def __init__(self, num_splats=128, image_size=64, seed=0):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        H, W = image_size, image_size
        self.means = nn.Parameter(torch.rand(num_splats, 2, generator=g) * torch.tensor([W, H]))
        self.log_scale = nn.Parameter(torch.ones(num_splats, 2) * math.log(2.0))
        self.rot = nn.Parameter(torch.zeros(num_splats))
        self.colour_logits = nn.Parameter(torch.randn(num_splats, 3, generator=g) * 0.5)
        self.opacity_logit = nn.Parameter(torch.zeros(num_splats))
        self.depth = nn.Parameter(torch.rand(num_splats, generator=g))

    def covs(self):
        s = torch.exp(self.log_scale)
        c, si = torch.cos(self.rot), torch.sin(self.rot)
        R = torch.stack([
            torch.stack([c, -si], dim=-1),
            torch.stack([si, c], dim=-1),
        ], dim=-2)
        S = torch.diag_embed(s ** 2)
        return R @ S @ R.transpose(-1, -2)

    def forward(self, image_size):
        covs = self.covs()
        colours = torch.sigmoid(self.colour_logits)
        opacities = torch.sigmoid(self.opacity_logit)
        return rasterise_2d(self.means, covs, colours, opacities, self.depth, image_size)
```

`log_scale`, `opacity_logit`, `colour_logits`는 모두 렌더링 시 올바른 활성화 함수를 통해 매핑되는 제약 없는 매개변수이다. 이는 모든 3DGS 구현의 표준 패턴이다.

### 단계 4: 2D 가우시안을 타겟 이미지에 피팅

```python
import math
import numpy as np

def make_target(size=64):
    yy, xx = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    img = np.zeros((size, size, 3), dtype=np.float32)
    mask = (xx - 20) ** 2 + (yy - 20) ** 2 < 10 ** 2
    img[mask] = [1.0, 0.2, 0.2]
    mask = (np.abs(xx - 45) < 8) & (np.abs(yy - 40) < 8)
    img[mask] = [0.2, 0.3, 1.0]
    return torch.from_numpy(img)


target = make_target(64)
model = Splats2D(num_splats=64, image_size=64)
opt = torch.optim.Adam(model.parameters(), lr=0.05)

for step in range(200):
    pred = model((64, 64))
    loss = F.mse_loss(pred, target)
    opt.zero_grad(); loss.backward(); opt.step()
    if step % 40 == 0:
        print(f"step {step:3d}  mse {loss.item():.4f}")
```

200단계에 걸쳐 64개의 가우시안이 두 가지 모양에 정착한다. 이것이 전체 아이디어이다 — 명시적 기하학 프리미티브에 대한 경사 하강법.

### 단계 5: 2D에서 3D로

3D 확장은 동일한 루프를 유지한다. 추가 사항:

1. 가우시안별 회전은 단일 각도 대신 쿼터니언이다.
2. 공분산은 `R S S^T R^T`이며, `R`은 쿼터니언으로, `S = diag(exp(log_scale))`로 구축된다.
3. 투영 `(mu, Sigma) -> (mu', Sigma')`은 카메라 외부 파라미터와 `mu`에서 원근 투영의 야코비안을 사용한다.
4. 색상은 구면 조화 확장이 되며; 시야 방향에서 평가한다.
5. 깊이 정렬은 학습된 스칼라 대신 실제 카메라 공간 z에서 이루어진다.

모든 프로덕션 구현(`gsplat`, `inria/gaussian-splatting`, `nerfstudio`)은 타일 기반 CUDA 커널로 GPU에서 정확히 이것을 수행한다.

### 단계 6: 구면 조화 평가

차수 3까지의 SH 기저는 채널당 16개 항을 가진다. 평가:

```python
def eval_sh_degree_3(sh_coeffs, dirs):
    """
    sh_coeffs: (..., 16, 3)   마지막 차원은 RGB 채널
    dirs:      (..., 3)       단위 벡터
    returns:   (..., 3)
    """
    C0 = 0.282094791773878
    C1 = 0.488602511902920
    C2 = [1.092548430592079, 1.092548430592079,
          0.315391565252520, 1.092548430592079,
          0.546274215296039]
    x, y, z = dirs[..., 0], dirs[..., 1], dirs[..., 2]
    x2, y2, z2 = x * x, y * y, z * z
    xy, yz, xz = x * y, y * z, x * z

    result = C0 * sh_coeffs[..., 0, :]
    result = result - C1 * y[..., None] * sh_coeffs[..., 1, :]
    result = result + C1 * z[..., None] * sh_coeffs[..., 2, :]
    result = result - C1 * x[..., None] * sh_coeffs[..., 3, :]

    result = result + C2[0] * xy[..., None] * sh_coeffs[..., 4, :]
    result = result + C2[1] * yz[..., None] * sh_coeffs[..., 5, :]
    result = result + C2[2] * (2.0 * z2 - x2 - y2)[..., None] * sh_coeffs[..., 6, :]
    result = result + C2[3] * xz[..., None] * sh_coeffs[..., 7, :]
    result = result + C2[4] * (x2 - y2)[..., None] * sh_coeffs[..., 8, :]

    # 차수 3 항목은 간결함을 위해 생략; 전체 16-계수 버전은 코드 파일에 있음
    return result
```

학습된 `sh_coeffs`는 해당 가우시안에 대한 "모든 방향의 색상"을 저장한다. 렌더링 시 현재 시야 방향에 대해 평가하고 3-벡터 RGB를 얻는다.

## 사용 It

실제 3DGS 작업을 위해서는 `gsplat`(Meta) 또는 `nerfstudio`를 사용한다:

```bash
pip install nerfstudio gsplat
ns-download-data example
ns-train splatfacto --data path/to/data
```

`splatfacto`는 nerfstudio의 3DGS 트레이너이다. 일반적인 장면에서 RTX 4090에서 10-30분이 소요된다.

2026년에 중요한 내보내기 옵션:

- `.ply` — 원시 가우시안 클라우드(휴대 가능, 가장 큰 파일).
- `.splat` — PlayCanvas / SuperSplat 양자화 형식.
- glTF `KHR_gaussian_splatting` — Khronos 표준, 뷰어 간 휴대 가능(2026년 2월 RC).
- OpenUSD `UsdVolParticleField3DGaussianSplat` — USD 네이티브, NVIDIA Omniverse 및 Vision Pro 파이프라인용.

4D / 동적 장면의 경우, `4DGS`와 `Deformable-3DGS`가 시간에 따라 변하는 평균과 불투명도로 동일한 기계를 확장한다.

## 배송 It

이 과목은 다음을 제공한다:

- `outputs/prompt-3dgs-capture-planner.md` — 주어진 장면 유형에 대한 캡처 세션(사진 수, 카메라 경로, 조명)을 계획하는 프롬프트.
- `outputs/skill-3dgs-export-router.md` — 하류 뷰어 또는 엔진에 따라 올바른 내보내기 형식(`.ply` / `.splat` / glTF / USD)을 선택하는 스킬.

## 연습 문제

1. **(쉬움)** 위의 2D 스플랫 트레이너를 다른 합성 이미지에서 실행한다. `num_splats`를 `[16, 64, 256]`에서 변경하고 각각에 대해 MSE vs 단계를 플롯한다. 수확 체감점을 식별한다.
2. **(중간)** 2D 래스터라이저를 확장하여 차수-2 고조파를 통해 스칼라 "뷰 각도"에 의존하는 가우시안별 RGB 색상을 지원한다. 두 개의 타겟 이미지 쌍에서 훈련하고 모델이 둘 다 재구성하는지 확인한다.
3. **(어려움)** `nerfstudio`를 클론하고 가지고 있는 장면(책상, 식물, 얼굴, 방)의 20장 사진 캡처로 `splatfacto`를 훈련한다. glTF `KHR_gaussian_splatting`으로 내보내고 뷰어(Three.js `GaussianSplats3D`, SuperSplat, Babylon.js V9)에서 연다. 훈련 시간, 가우시안 수, 렌더링 fps를 보고한다.

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| 3DGS | "가우시안 스플랫" | 수백만 개의 3D 가우시안으로 명시적 장면 표현, 가우시안별 위치, 회전, 스케일, 불투명도, SH 색상 |
| 공분산 | "가우시안의 형태" | `Sigma = R S S^T R^T`; 하나의 가우시안의 방향 및 이방성 스케일 |
| 알파 합성 | "뒤-앞 블렌딩" | NeRF의 체적 렌더링과 동일한 방정식, 이제 명시적 희소 집합에 대해 |
| 농축 | "복제 및 분할" | 재구성이 과소적합된 곳에 새로운 가우시안을 적응적으로 추가 |
| 가지치기 | "낮은 불투명도 삭제" | 훈련 중 0에 가까운 불투명도로 붕괴된 가우시안 제거 |
| 구면 조화 | "시점 의존 색상" | 구의 푸리에 기저; 색상을 시야 방향의 함수로 저장 |
| Splatfacto | "nerfstudio의 3DGS" | 2026년 3DGS 훈련의 가장 쉬운 경로 |
| `KHR_gaussian_splatting` | "glTF 표준" | 3DGS를 뷰어와 엔진 간에 휴대 가능하게 만드는 Khronos 2026 확장 |

## 추가 읽기

- [3D Gaussian Splatting for Real-Time Radiance Field Rendering (Kerbl et al., SIGGRAPH 2023)](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) — 원본 논문
- [gsplat (Meta/nerfstudio)](https://github.com/nerfstudio-project/gsplat) — 프로덕션 품질 CUDA 래스터라이저
- [nerfstudio Splatfacto](https://docs.nerf.studio/nerfology/methods/splat.html) — 참조 훈련 레시피
- [Khronos KHR_gaussian_splatting extension](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_gaussian_splatting/README.md) — 2026년 휴대용 형식
- [OpenUSD 26.03 release notes](https://openusd.org/release/) — `UsdVolParticleField3DGaussianSplat` 스키마
- [THE FUTURE 3D State of Gaussian Splatting 2026](https://www.thefuture3d.com/blog-0/2026/4/4/state-of-gaussian-splatting-2026) — 산업 개요
