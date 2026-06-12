# 캡스톤 12 — 비디오 이해 파이프라인 (장면, QA, 검색)

> Twelve Labs가 Marengo + Pegasus를 제품화했다. VideoDB가 비디오용 CRUD API를 shipped했다. AI2의 Molmo 2가 오픈 VLM 체크포인트를 게시했다. Gemini long-context가 수 시간의 비디오를 기본으로 처리한다. TimeLens-100K가 규모에서 시간적 grounding을 정의했다. 2026년 파이프라인이 확립되었다: 장면 분할, 장면당 캡션 + 임베딩, 대본 정렬, 다중 벡터 인덱스, (start, end) 타임스탬프와 프레임 미리보기로 답변하는 쿼리. 캡스톤은 100시간을 수집하고, 공개 벤치마크에 도달하고, 계수 및 행동 질문에서 환각을 측정하는 것이다.

**유형:** 캡스톤
**언어:** Python (파이프라인), TypeScript (UI)
**선수 과목:** Phase 4 (CV), Phase 6 (음성), Phase 7 (트랜스포머), Phase 11 (LLM 엔지니어링), Phase 12 (멀티모달), Phase 17 (인프라)
**활용 phases:** P4 · P6 · P7 · P11 · P12 · P17
**소요 시간:** 30시간

## 문제

장형 비디오 QA는 2026년 규모에서 대역폭이 가장 많이 필요한 멀티모달 문제이다. Gemini 2.5 Pro는 기본적으로 2시간 비디오를 읽을 수 있지만, 100시간의 비디오를 쿼리 가능한 코퍼스에 수집하려면 장면 수준 인덱스가 여전히 필요하다. 운영 형태는 장면 분할(TransNetV2 또는 PySceneDetect), VLM(Gemini 2.5, Qwen3-VL-Max, Molmo 2)으로 장면당 캡셔닝, 단어 타임스탬프가 있는 대본 정렬(Whisper-v3-turbo), 캡션, 프레임 임베딩, 대본을 나란히 저장하는 다중 벡터 인덱스를 결합한다. 쿼리 파이프라인은 (start, end) 타임스탬프와 프레임 미리보기로 답변한다.

벤치마크는 공개되어 있다(ActivityNet-QA, NeXT-GQA) plus 자체 100개 질문 커스텀 세트. 계수 및 행동 유형 질문에 대한 환각은 알려진 단단한 실패 클래스로, 캡스톤이 명시적으로 측정한다.

## 개념

수집 시 세 파이프라인이 병렬로 실행된다. **장면 분할**은 비디오를 장면으로 자른다. **VLM 캡셔닝**은 키프레임당 캡션과 프레임 임베딩을 생성한다. **ASR 정렬**은 단어 수준 타임스탬프로 생성한다. 세 스트림은 (scene_id, 시간 범위)로 조인된다. 각 장면은 다중 벡터 인덱스(Qdrant)에서 세 가지 벡터 유형을 가진다: 캡션 임베딩, 키프레임 임베딩, 대본 임베딩.

쿼리 시간에 자연어 질문이 세 벡터 모두에 대해 실행된다; 결과는 RRF로 병합된다; 시간적 grounding 어댑터(TimeLens 스타일)가 상위 장면 내의 (start, end) 창을 세밀화한다. VLM 합성기(Gemini 2.5 Pro 또는 Qwen3-VL-Max)는 쿼리 + 상위 장면 + 자른 프레임을 가져가고 인용된 타임스탬프와 프레임 미리보기로 답변한다.

환각 측정이 중요하다. 계수("몇 명이 방에 들어오는가?") 및 행동 유형("쉐프가 저어 전에 부었는가?") 질문은 알려진 바와 같이 신뢰할 수 없다. 설명적 질문과 별도로 정확도를 보고한다.

## 아키텍처

```
video file / URL
      |
      v
PySceneDetect / TransNetV2  (scene segmentation)
      |
      +--- per-scene keyframe --- VLM caption + frame embedding
      |                            (Gemini 2.5 Pro / Qwen3-VL-Max / Molmo 2)
      |
      +--- audio channel --- Whisper-v3-turbo ASR + word timestamps
      |
      v
multi-vector Qdrant: {caption_emb, keyframe_emb, transcript_emb}
      |
query:
  dense queries against all three -> RRF merge -> top-k scenes
      |
      v
TimeLens / VideoITG temporal grounding (refine start/end within scene)
      |
      v
VLM synth: query + top scenes + frame previews
      |
      v
answer + (start, end) timestamps + frame thumbs + citations
```

## 기술 스택

- 장면 분할: TransNetV2 (2024-26년 최첨단) 또는 PySceneDetect
- ASR: 단어 타임스탬프가 있는 faster-whisper를 통한 Whisper-v3-turbo
- VLM 캡셔너 + 응답자: Gemini 2.5 Pro 또는 Qwen3-VL-Max 또는 Molmo 2
- 시간적 grounding: TimeLens-100K-훈련 어댑터 또는 VideoITG
- 인덱스: 다중 벡터 지원이 있는 Qdrant (캡션 / 프레임 / 대본)
- UI: HTML5 비디오 플레이어 및 장면 썸네일이 있는 Next.js 15
- Eval: ActivityNet-QA, NeXT-GQA, 커스텀 100개 질문 수동 레이블 세트
- 환각 벤치마크: 수동 레이블이 있는 계수 및 행동 유형 하위 집합

## 실습

1. **수집 워커.** YouTube URL 또는 로컬 MP4를 accept한다. 필요하면 720p로 다운스케일한다. `{video_id, file_path}`를 유지한다.

2. **장면 분할.** TransNetV2 또는 PySceneDetect를 실행하여 `[{scene_id, start_ms, end_ms, keyframe_path}]`를 생성한다. 대상 100시간: ~6k-8k 장면.

3. **ASR 패스.** 오디오에서 Whisper-v3-turbo를 실행한다; 단어 수준 타임스탬프를 내보낸다; 장면당 대본 슬라이스로 분할한다.

4. **VLM 캡셔닝.** 장면당 Gemini 2.5 Pro(또는 Qwen3-VL-Max)에 키프레임과 짧은 캡션 템플릿으로 호출한다. 캡션 + 프레임 임베딩을 생성한다.

5. **다중 벡터 인덱스.** 세 개의 명명된 벡터가 있는 Qdrant 컬렉션. 페이로드: `{video_id, scene_id, start_ms, end_ms, keyframe_url}`.

6. **쿼리.** 자연어 질문이 세 개의 dense 쿼리를 실행한다; 상반 순위 융합으로 병합한다; top-k=5 장면.

7. **시간적 grounding.** 상위 장면에서 TimeLens 스타일 어댑터를 실행하여 장면 내 (start, end) 창을 세밀화한다.

8. **VLM 합성.** 쿼리 + 상위 3개 장면 클립(이미지 또는 짧은 클립으로) + 대본으로 Gemini 2.5 Pro를 호출한다. `(video_id, start_ms, end_ms)` 인용을要求한다.

9. **Eval.** ActivityNet-QA 및 NeXT-GQA를 실행한다. 100개 질문 커스텀 세트를 구축한다. 전체 정확도 + 클래스별 분석(계수, 행동, 설명)을 보고한다.

## 활용

```
$ video-qa ask --url=https://youtube.com/watch?v=X "how many cars pass the intersection in the first minute?"
[scene]    23 scenes detected
[asr]      transcript complete, 4m12s
[index]    69 vectors written (23 scenes x 3)
[query]    top scene: scene 3 [01:32-01:54], confidence 0.84
[ground]   refined window: [00:12-00:58]
[synth]    gemini 2.5 pro, 1.4s
answer:    5 cars pass the intersection between 00:12 and 00:58.
citations: [scene 3: 00:12-00:58]
          [frame preview at 00:14, 00:27, 00:44, 00:51, 00:57]
```

## 결과물

`outputs/skill-video-qa.md`가 결과물이다. YouTube URL 또는 업로드된 비디오가 주어지면 파이프라인이 장면을 인덱싱하고 타임스탬프가 지정된 인용과 함께 질문에 답변한다.

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 시간적 grounding IoU | 보류된 grounding 세트에서 교집합 over-union |
| 20 | QA 정확도 | NeXT-GQA 및 커스텀 100개 질문 |
| 20 | 수집 처리량 | 사용된 금액 대비 시간 단위 비디오 |
| 20 | UI 및 인용 UX | 타임스탬프 링크, 썸네일 스트립, 프레임으로 점프 |
| 15 | 환각률 | 계수 및 행동 유형 정확도 별도로 |
| **100** | | |

## 연습 문제

1. 캡셔닝 패스에서 Gemini 2.5 Pro를 Qwen3-VL-Max로 교체한다. 인간이 평가한 50개 장면 샘플에서 캡션 품질 delta를 보고한다.

2. 장면당 프레임 임베딩을 하나의 풀링된 벡터 대신 다중 벡터로 줄인다. 검색 regression을 측정한다.

3. "엄격한 계수" 모드 구축: 합성기가 각 계수된 인스턴스를 타임스탬프와 함께 추출하고 사용자가 클릭하여 확인한다. 사용자 확인이 환각을 감소시키는지 측정한다.

4. 수집 비용 벤치마크: 세 가지 VLM 선택에 따른 시간당 금액. 최적의甜蜜점을 선택한다.

5. 화자 diarized 대본 추가: 오디오에서 pyannote 화자 diarization을 실행하고 화자별 대본을 임베딩한다. "Alice가 X에 대해 무엇이라고 말했는가?" 쿼리를演示한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 장면 분할 | "Shot detection" | 샷 경계에서 비디오를 장면으로 자르기 |
| 다중 벡터 인덱스 | "Caption + frame + transcript" | 표현당 명명된 벡터가 있는 Qdrant 컬렉션 |
| 시간적 grounding | "When exactly did it happen" | 쿼리 답변에 대한 (start, end) 창 세밀화 |
| 프레임 임베딩 | "Visual representation" | 키프레임의 벡터 임베딩; 장면 시각적 유사성에 사용 |
| RRF 융합 | "Reciprocal rank fusion" | 여러 순위 목록 간의 병합 전략; 클래식 하이브리드 검색 기법 |
| 계수 환각 | "Miscount" | "X가 몇 개인가" 질문에서 VLMs의 알려진 실패 모드 |
| ActivityNet-QA | "Video-QA benchmark" | 장형 비디오 QA 정확도 벤치마크 |

## 추가 자료

- [AI2 Molmo 2](https://allenai.org/blog/molmo2) — 오픈 VLM 체크포인트
- [TimeLens (CVPR 2026)](https://github.com/TencentARC/TimeLens) — 규모에서 시간적 grounding
- [Gemini Video long-context](https://deepmind.google/technologies/gemini) — 호스티드 기준
- [VideoDB](https://videodb.io) — 비디오용 CRUD API 기준
- [Twelve Labs Marengo + Pegasus](https://www.twelvelabs.io) — 상업적 기준
- [TransNetV2](https://github.com/soCzech/TransNetV2) — 장면 분할 모델
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) — 클래식 오픈 대안
- [ActivityNet-QA](https://arxiv.org/abs/1906.02467) — 기준 평가 벤치마크