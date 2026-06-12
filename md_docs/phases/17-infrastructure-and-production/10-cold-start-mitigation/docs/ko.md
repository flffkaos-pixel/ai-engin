# 서버리스 LLM의 콜드 스타트 완화

> 20 GB 모델 이미지가 cold에서 serving까지 가려면 7B에서 5-10분, 70B에서 20분 이상이 걸립니다. 진정한 서버리스 세계에서 그것은 워밍업이 아니라 가동 중지입니다. 완화는 5개 레이어에서 운영됩니다: pre-seeded 노드 이미지 (AWS의 Bottlerocket, 이중 볼륨 아키텍처), 모델 스트리밍 (NVIDIA Run:ai Model Streamer, vLLM에서 네이티브), GPU 메모리 스냅샷 (Modal 체크포인트, 최대 10x 빠른 재시작), 따뜻한 풀 (`min_workers=1`), 계층화된 로딩 (ServerlessLLM의 NVMe→DRAM→HBM 파이프라인, 10-200x 지연 시간 감소), 입력 토큰 (KB)을而非 KV 캐시 (GB)를 전송하는 라이브 마이그레이션. Modal은 2-4s 콜드 스타트를 최저로 게시합니다; Baseten 5-10s 기본값, pre-warming으로 1초 미만. 이 레슨은 5개 레이어를 측정, 예산, 쌓는 방법을 가르칩니다.

**유형:** 학습
**언어:** Python (stdlib, toy cold-start 경로 시뮬레이터)
**선수 과목:** Phase 17 · 02 (Inference Platform Economics), Phase 17 · 03 (GPU Autoscaling)
**소요 시간:** ~60분

## 학습 목표

--cold-start 완화의 5개 레이어를 열거하고 각 레이어에서 하나의 도구 또는 패턴의 이름을 붙입니다.
- 70B 모델에 대해 (노드 프로비저닝) + (가중치 다운로드) + (가중치를 HBM으로 로드) + (엔진 초기화)의 합으로 총 콜드 스타트 시간을 계산합니다.
- 라이브 마이그레이션이 KV 캐시 (GB)가 아닌 입력 토큰 (KB)을 전송하는 이유와 페널티 (재계산)가 무엇인지 설명합니다.
- 따뜻한 풀 트레이드오프 (유휴 GPU에 지불하거나 콜드 스타트 tail을受け入れる)와 `min_workers > 0`가 mandatory가 되는 SLA 임계값을 이름 짓습니다.

## 문제

서버리스 LLM 엔드포인트가 밤새 0으로 스케일합니다. 오전 8시에 트래픽이 급증합니다. 첫 번째 요청이 다음 동안 기다립니다:

1. Karpenter가 GPU 노드를 프로비저닝합니다: 45-60s.
2. 컨테이너가 가중치와 함께 30 GB 이미지를 pulling합니다: 120-300s.
3. 엔진이 가중치를 HBM에 로드합니다: 모델 크기 및 저장소 속도에 따라 45-120s.
4. vLLM 또는 TRT-LLM이 CUDA 그래프, KV 캐시 풀, 토크나이저를 초기화합니다: 10-30s.

전체: 하나의 토큰이 반환되기 전에 약 3-8분인 220-510s. SLA는 2s입니다. 따뜻한 풀 (`min_workers=1`)을 배송하면 문제가 사라지는 것처럼 보입니다 — 그러나 이제 24x7 하나의 유휴 GPU에 지불합니다. 서비스에 제품이 5개 있고 각각 하나의 따뜻한 복제본이 있으면, 단일 사용자가 호출했는지 여부에 관계없이 5 × 24 × 30 = 3,600 GPU-hours/월입니다.

콜드 스타트 완화는 항상 온의 지연 시간을近似하면서 서버리스 경제학을 유지하는 방법입니다.

## 개념

### 레이어 1 — pre-seeded 노드 이미지 (Bottlerocket)

AWS에서 Bottlerocket의 이중 볼륨 아키텍처는 OS와 데이터를 분리합니다. 컨테이너 이미지가 pre-pulled된 데이터 볼륨을 스냅샷합니다; `EC2NodeClass`에서 스냅샷 ID를 참조합니다. 새 노드가 로컬 NVMe에 이미 가중치가 있는 상태로 부팅합니다 — 2단계와 3단계의 일부는 사라집니다. Karpenter와 기본적으로 작동합니다. 대형 모델의 콜드 스타트당 일반적인 절감: 2-4분.

GCP의 동등: pre-baked 컨테이너 레이어가 있는 사용자 정의 VM 이미지. Azure: 동일한 패턴의 관리 디스크 스냅샷.

### 레이어 2 — 모델 스트리밍 (Run:ai Model Streamer)

첫 번째 요청에 응답하기 전에 전체 파일을 로드하는 대신, 레이어별로 GPU 메모리로 가중치를 스트리밍하고 첫 번째 transformer 블록이 상주하는 즉시 처리를 시작합니다. NVIDIA Run:ai Model Streamer는 vLLM 2026에서 네이티브로 shipping됩니다. S3, GCS, 로컬 NVMe에서 작동합니다. 가중치 로드 시간을 큰 모델에서 약 절반으로 줄입니다 — I/O와 컴퓨트 설정을 overlapping하여.

### 레이어 3 — GPU 메모리 스냅샷 (Modal)

Modal은 첫 번째 로드 후 GPU 상태 (가중치, CUDA 그래프, KV 캐시 영역)의 체크포인트를 찍습니다. 후속 재시작은 HBM으로 직접 deserialize합니다 — 재초기화보다 10x 빠릅니다. 이것은 "2초에 따뜻한 GPU를 부팅하는" 것에 가장 가까운 것입니다. Trade-off: 스냅샷은 GPU 토폴로지당이므로 Karpenter가 다른 SKU로 마이그레이션하면 다시 체크포인트를 찍습니다.

### 레이어 4 — 따뜻한 풀 (min_workers=1)

가장 간단한 완화: 하나의 복제본을 항상 준비 상태로 유지합니다. 비용은 시간당 GPU 요금 × 24x7입니다. 작은 모델에서 숫자는 가혹합니다 (30s 콜드 스타트를 피하기 위해 $0.85-$1.50/hr를 지불)되고 큰 모델에서는 친절합니다 (5분 콜드 스타트를 피하기 위해 $4/hr를 지불). 따뜻한 풀이 mandatory가 되는 SLA 임계값: 일반적으로 70B+ 모델에서 TTFT P99 < 60s.

### 레이어 5 — 계층화된 로딩 (ServerlessLLM)

ServerlessLLM은 저장소를 계층으로 취급합니다: NVMe (빠르지만 큼), DRAM (중간이지만 계층화됨), HBM (작지만 즉각적). 가중치는 DRAM에 미리 로드됩니다; 주문형 HBM으로 로드합니다. 논문은 순진한 disk-to-HBM 대비 cold 로드에서 10-200x 지연 시간 감소를 보고합니다. 프로덕션 채택은 초기이지만 vLLM과 통합이 존재합니다.

### 레이어 6 — 라이브 마이그레이션 (보너스 패턴)

노드가 사용할 수 없하게 되면 (spot 축출, 노드 드레인), 전통적인 패턴은 cold 시작另一个 복제본이고 요청 큐를 드레인합니다. 라이브 마이그레이션은 모델이 로드된 대상에게 입력 토큰 (킬로바이트)을 이동하고 대상에서 KV 캐시를 재계산합니다. 재계산은 GB의 KV 캐시를 네트워크로 전송하는 것보다 저렴합니다. 분리된 배포에 적용 가능합니다.

### 따뜻한 풀 수학

P99 TTFT SLA가 2s인 서비스의 경우, 질문은 "따뜻한 풀 예/아니오"가 아니라 "따뜻한 복제본이 몇 개, 어떤 경로가 그것들을 얻느냐"입니다.

- 고가치対話적 경로 (라이브 채팅, 음성 에이전트): `min_workers=1-2`.
- 백그라운드 배치 경로 (야간 분류): scale-to-zero容许, 5-10분 콜드 스타트olerable.
- 프리미엄 계층: 전담 용량으로 테넌트당 `min_workers`.

### 최적화 전에 측정

새 노드에서 70B 모델의 콜드 스타트 해부 (예시):

| 단계 | 시간 | 완화 |
|-------|------|--------|
| 노드 프로비저닝 | 50s | Bottlerocket + pre-seeded image, warm pool |
| 이미지 풀 | 180s | Pre-seeded 데이터 볼륨 (제거) |
| 가중치에서 HBM까지 | 75s | 모델 스트리머 (절반); GPU 스냅샷 (제거) |
| 엔진 초기화 | 20s | 지속적인 CUDA 그래프 캐시 |
| 첫 번째 포워드 | 3s | 최소 고유 지연 시간 |
| **전체 cold** | **328s** | |
| **완화 포함 전체** | **~15s** | 22x 감소 |

### 기억해야 할 숫자

- Modal 콜드 스타트: 2-4s (GPU 스냅샷 포함).
- Baseten 기본 콜드 스타트: 5-10s; pre-warming으로 1초 미만.
- 순진한 70B 콜드 스타트: 3-8분.
- Run:ai Model Streamer: ~2x 가중치 로드 스피드업.
- ServerlessLLM 계층화된 로딩: 10-200x 지연 시간 감소 (논문 숫자).

## 활용

`code/main.py`는 각 완화와 함께 그리고 없이 콜드 스타트 경로를 모델링합니다. 총 콜드 스타트 시간, 따뜻한 풀 비용, 따뜻한 풀이 자체를 지불하는 균형 요청률을 보고합니다.

## 결과물

이 레슨은 `outputs/skill-cold-start-planner.md`를 산출합니다. SLA, 모델 크기, 트래픽 형태가 주어지면 어떤 완화를 쌓을지 선택합니다.

## 연습문제

1. `code/main.py`를 실행하세요. SLO에서 추가 요청 드롭을 통해 콜드 스타트 세금을 지불하는 것보다 따뜻한 복제본이 더 저렴한 균형 요청률을 계산하세요.
2. P99 TTFT SLA가 3s인 13B 모델을 배포합니다. 달성하기 위한 최소 완화 스택 (가장 적은 레이어)을 선택하세요.
3. Bottlerocket pre-seeding은 이미지 풀을 제거하지만 가중치는 여전히 스냅샷에서 HBM으로 로드됩니다. 스냅샷 지원 NVMe가 7 GB/s에서 읽으면 70B 모델의 wall-clock을 계산하세요.
4. 서버리스 제공자가 GPU 스냅샷 (Modal)을 제공하며 팀이 "스냅샷이 PII를 유출한다"고 거부합니다. 양쪽 주장 — 현실적인 위험은 무엇이며 완화는 무엇입니까 (임시 스냅샷, 암호화, 네임스페이스 격리)?
5. 계층화된 따뜻한 풀 정책을 디자인하세요: 유료 사용자, 평가판 사용자, 배치 작업에 대해 몇 개의 따뜻한 복제본입니까? 수학을 보여주세요.

## 핵심 용어

| 용어 | 人们怎么说 | 실제 의미 |
|------|----------------|------------------------|
| Cold start | "큰 일시정지" | 새 복제본에서 요청에서 첫 번째 토큰까지의 시간 |
| Warm pool | "항상 온 최소" | 최소 하나의 복제본을 준비 상태로 유지하기 위한 `min_workers >= 1` |
| Pre-seeded image | "굽기한 AMI" | 컨테이너 가중치가 미리 상주하는 노드 이미지 |
| Bottlerocket | "AWS 노드 OS" | 이중 볼륨 스냅샷 지원이 있는 AWS 컨테이너 최적화 OS |
| Model streamer | "스트리밍 로드" | 가중치 I/O를 컴퓨트 설정과 overlapping |
| GPU snapshot | "HBM로 체크포인트" | 로드 후 GPU 상태 직렬화; 재시작 시 deserialize |
| 계층화된 로딩 | "NVMe + DRAM + HBM" | 저장소 티어의 계층; 주문형 로드 |
| Live migration | "토큰 이동" | 입력 전송 (KB), 대상에서 KV 재계산 |
| `min_workers` | "따뜻한 복제본" | 서버리스 최소 keep-alive 수 |
| Scale-to-zero | "완전한 서버리스" | 유휴시 비용 없음; 전체 콜드 스타트 세금.accept |

## 추가 자료

- [Modal — Cold start performance](https://modal.com/docs/guide/cold-start) — Modal의 게시된 벤치마크 및 체크포인트 아키텍처.
- [AWS Bottlerocket](https://github.com/bottlerocket-os/bottlerocket) — pre-seeded 데이터 볼륨 스냅샷 패턴.
- [NVIDIA Run:ai Model Streamer](https://github.com/run-ai/runai-model-streamer) — 가중치 로드를 컴퓨트 설정과 overlapping.
- [Baseten — Cold-start mitigation](https://www.baseten.co/blog/cold-start-mitigation/) — pre-warming 플레이북.
- [ServerlessLLM 논문 (USENIX OSDI'24)](https://www.usenix.org/conference/osdi24/presentation/fu) — 계층화된 로딩 디자인.
- [NVIDIA — Kubernetes에서 분리된 LLM 추론](https://developer.nvidia.com/blog/deploying-disaggregated-llm-inference-workloads-on-kubernetes/) — 분리된 배포를 위한 라이브 마이그레이션.