# Audio Transformers — Whisper 아키텍처

> 오디오는 시간에 따른 주파수의 이미지이다. Whisper는 mel 스펙트로그램을 먹고 말을 되돌리는 ViT이다.

**유형:** 학습
**언어:** Python
**선수 과목:** Phase 7 · 05 (Full Transformer), Phase 7 · 08 (Encoder-Decoder), Phase 7 · 09 (ViT)
**소요 시간:** ~45분

## 문제

Whisper (OpenAI, Radford et al. 2022) 이전에는 자동 음성 인식 (ASR)의 최첨단이 wav2vec 2.0과 HuBERT였다 — self-supervised 특징 추출기 plus fine-tuned head. 높은 품질, 비싼 데이터 파이프라인, 도메인 취약. 다국어 음성 인식에는 언어 가족당 별도의 모델이 필요했다.

Whisper는 세 가지 내기를 했다:

1. **모든 것으로 교육.** 97개 언어로 인터넷에서 긁어온 680,000시간의 약하게 레이블된 오디오. 깨끗한 학계 코퍼스 없음. 음소 레이블 없음.
2. **멀티 태스크 단일 모델.** 전사, 번역, 음성 활동 감지, 언어 ID, 타임스탬핑을 태스크 토큰을 통해 jointly 교육된 하나의 decoder.
3. **표준 encoder-decoder transformer.** Encoder가 log-mel 스펙트로그램을 소비한다. Decoder가 텍스트 토큰을 autoregressive하게 생성한다. 보코더 없음, CTC 없음, HMM 없음.

결과: Whisper large-v3는 음성, 노이즈, 제로 클린 레이블 데이터가 있는 언어에서 강력하다. 2026년 모든 오픈소스 음성 어시스턴트와 대부분의 상업용 어시스턴트를 위한 기본 음성 프론트엔드이다.

## 개념

![Whisper 파이프라인: 오디오 → mel → encoder → decoder → 텍스트](../assets/whisper.svg)

### Step 1 — 리샘플 + 윈도우

16 kHz의 오디오. 30초로 클립/패드. Log-mel 스펙트로그램 계산: 80 mel 빈, 10 ms stride → ~3,000 프레임 × 80 특징. 이것이 Whisper가 보는 "입력 이미지"이다.

### Step 2 — convolutional stem

커널 3과 stride 2의 두 Conv1D 레이어가 3,000 프레임을 1,500으로 줄인다. 매개변수를 많이 추가하지 않고 시퀀스 길이를 절반으로 줄인다.

### Step 3 — encoder

1,500 타임스텝에 대한 24 레이어 (large용) transformer encoder. 정현파 위치 인코딩, self-attention, GELU FFN. 1,500 × 1,280 숨겨진 상태를 생성한다.

### Step 4 — decoder

24 레이어 transformer decoder. BPE 어휘에서 텍스트 토큰을 autoregressive하게 생성한다 — 몇 가지 오디오 특정 특수 토큰이 있는 GPT-2의 상위 집합.

### Step 5 — 태스크 토큰

decoder 프롬프트는 모델에 무엇을 할지 알려주는 컨트롤 토큰으로 시작한다:

```
<|startoftranscript|>  <|en|>  <|transcribe|>  <|0.00|>
```

또는

```
<|startoftranscript|>  <|fr|>  <|translate|>   <|0.00|>
```

모델은 이 규칙으로 교육되었다. 접두사로 작업을 제어한다. 2026년 equivalent of instruction-tuning이지만 음성에 적용된다.

### Step 6 — 출력

로그 확률 임계값이 있는 beam search (너비 5). `<|notimestamps|>` 토큰이 없을 때 0.02초마다 타임스탬프가 예측된다.

### Whisper 크기

| 모델 | 매개변수 | 레이어 | d_model | Heads | VRAM (fp16) |
|-------|--------|--------|---------|-------|-------------|
| Tiny | 39M | 4 | 384 | 6 | ~1 GB |
| Base | 74M | 6 | 512 | 8 | ~1 GB |
| Small | 244M | 12 | 768 | 12 | ~2 GB |
| Medium | 769M | 24 | 1024 | 16 | ~5 GB |
| Large | 1550M | 32 | 1280 | 20 | ~10 GB |
| Large-v3 | 1550M | 32 | 1280 | 20 | ~10 GB |
| Large-v3-turbo | 809M | 32 | 1280 | 20 | ~6 GB (4-layer decoder) |

Large-v3-turbo (2024)는 decoder를 32 레이어에서 4 레이어로 줄였다. <1 WER 포인트 회귀로 8× 더 빠른 디코딩. 그 디코딩 속도 향상 때문에 Whisper-turbo가 2026년 실시간 음성 에이전트의 기본이다.

### Whisper가 하지 않는 것

- diarization 없음 (누가 말하는지). 이를 위해 pyannote와 페어링.
- 네이티브 실시간 스트리밍 없음 — 30초 윈도우가 고정됨. Modern wrappers (`faster-whisper`, `WhisperX`)가 VAD + overlap으로 스트리밍을 추가한다.
- 외부 청킹 없이는 30초를 넘는 장기 컨텍스트 없음. 인간 음성이 전사를 위해 장기 컨텍스트가 필요한 경우는 드물기 때문에 실제로 잘 작동한다.

### 2026년 환경

| 작업 | 모델 | 메모 |
|------|-------|-------|
| 영어 ASR | Whisper-turbo, Moonshine | Moonshine은 에지에서 4× 빠름 |
| 다국어 ASR | Whisper-large-v3 | 97개 언어 |
| 스트리밍 ASR | faster-whisper + VAD | 150ms 지연 시간 목표 달성 가능 |
| TTS | Piper, XTTS-v2, Kokoro | Encoder-decoder 패턴이지만 Whisper 형태 |
| 오디오 + 언어 | AudioLM, SeamlessM4T | 하나의 transformer에서 텍스트 토큰 + 오디오 토큰 |

## 실습

`code/main.py`를 참조. Whisper를 교육하지 않는다 — log-mel 스펙트로그램 파이프라인 + 태스크 토큰 프롬프트 포매터를 구축한다. 그것들은 production에서 실제로 건드리는 부분이다.

### Step 1: 오디오 합성

440 Hz에서 1초 사인파를 16 kHz로 샘플링하여 생성한다. 16,000 샘플.

### Step 2: log-mel 스펙트로그램 (단순화)

완전한 mel 스펙트로그램에는 FFT가 필요하다. `librosa`가 필요 없이 파이프라인을 보여주는 단순화된 framing + per-frame energy 버전을 사용한다:

```python
def frame_signal(x, frame_size=400, hop=160):
    frames = []
    for start in range(0, len(x) - frame_size + 1, hop):
        frames.append(x[start:start + frame_size])
    return frames
```

프레임 = 25 ms, hop = 10 ms. Whisper의 윈도우와 일치. Per-frame energy는 교육을 위한 mel 빈을 대신한다.

### Step 3: 30초로 패드

Whisper는 항상 30초 청unks를 처리한다. 3,000 프레임으로 스펙트로그램을 패드 (또는 클립).

### Step 4: 프롬프트 토큰 구축

```python
def whisper_prompt(lang="en", task="transcribe", timestamps=True):
    tokens = ["<|startoftranscript|>", f"<|{lang}|>", f"<|{task}|>"]
    if not timestamps:
        tokens.append("<|notimestamps|>")
    return tokens
```

그것이 전체 작업 제어 표면이다. 4토큰 접두사.

## 활용

```python
import whisper
model = whisper.load_model("large-v3-turbo")
result = model.transcribe("meeting.wav", language="en", task="transcribe")
print(result["text"])
print(result["segments"][0]["start"], result["segments"][0]["end"])
```

더 빠르고 OpenAI 호환:

```python
from faster_whisper import WhisperModel
model = WhisperModel("large-v3-turbo", compute_type="int8_float16")
segments, info = model.transcribe("meeting.wav", vad_filter=True)
for s in segments:
    print(f"{s.start:.2f} - {s.end:.2f}: {s.text}")
```

**2026년 Whisper를 선택하는 경우:**

- 하나의 모델로 다국어 ASR.
- 노이즈가 있고 다양한 오디오의 강력한 전사.
- 연구 / 프로토타입 ASR — 가장 빠른 시작점.

**다른 것을 선택하는 경우:**

- 에지에서의 초저지연 스트리밍 — Moonshine이 품질이 일치할 때 Whisper를 이긴다.
- <200 ms가 필요한 실시간 대화형 AI — 전용 스트리밍 ASR.
- 화자 diarization — Whisper는 이것을 하지 않는다; pyannote를 추가한다.

## 결과물

`outputs/skill-asr-configurator.md`를 참조. 이 skill는 새 음성 애플리케이션에 대한 ASR 모델, 디코딩 매개변수 및 사전 처리 파이프라인을 선택한다.

## 연습 문제

1. **쉬움.** `code/main.py`를 실행한다. 10 ms hop에서 16 kHz의 1초 신호에 대한 프레임 수가 ~100 프레임인지 확인한다. 30초: ~3,000 프레임.
2. **보통.** `numpy.fft`를 사용하여 완전한 log-mel 스펙트로그램을 구축한다. 수치 오차 내에서 80 mel 빈이 `librosa.feature.melspectrogram(n_mels=80)`와 일치하는지 확인한다.
3. **어려움.** 스트리밍 추론을 구현: 2초 overlap으로 10초 윈도우로 오디오를 청킹하고, 각 청크에서 Whisper를 실행하고, 전사를 병합한다. 5분 podcast 샘플에서 단일 통과 대비 WER를 측정한다.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-----------------|-----------------------|
| Mel spectrogram | "오디오 이미지" | 2D 표현: 한 축의 주파수 빈, 다른 축의 시간 프레임; 셀당 로그 스케일 에너지. |
| Log-mel | "Whisper가 보는 것" | 로그를 통과한 Mel 스펙트로그램; 인간의 음량 인식을 근사. |
| Frame | "하나의 시간 슬라이스" | 샘플의 25 ms 윈도우; 10 ms stride로 overlapping. |
| Task token | "음성에 대한 프롬프트 접두사" | decoder 프롬프트의 `<|transcribe|>` / `<|translate|>` 같은 특수 토큰. |
| Voice activity detection (VAD) | "음성을 찾는다" | ASR 전에 무음을 제거하는 게이트; 비용을 대폭 절감. |
| CTC | "Connectionist Temporal Classification" | 정렬 자유 교육용 클래식 ASR 손실; Whisper는 사용하지 않음. |
| Whisper-turbo | "작은 decoder, 전체 encoder" | large-v3 encoder + 4-layer decoder; 8× 더 빠른 디코딩. |
| Faster-whisper | "production 래퍼" | CTranslate2 재구현; int8 양자화; OpenAI 참조보다 4× 빠름. |

## 추가 자료

- [Radford et al. (2022). Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — Whisper 논문.
- [OpenAI Whisper repo](https://github.com/openai/whisper) — 참조 코드 + 모델 가중치. Conv1D stem + encoder + decoder를 위에서 아래로 ~400줄에서 보려면 `whisper/model.py`를 읽는다.
- [OpenAI Whisper — `whisper/decoding.py`](https://github.com/openai/whisper/blob/main/whisper/decoding.py) — 5-6단계에서 설명된 beam-search + task-token 로직이 여기 있다; 500줄, 완전히 읽을 수 있다.
- [Baevski et al. (2020). wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations](https://arxiv.org/abs/2006.11477) — 전구자; 일부 설정에서 여전히 SOTA 특징.
- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) — production 래퍼, 참조보다 4× 빠름.
- [Jia et al. (2024). Moonshine: Speech Recognition for Live Transcription and Voice Commands](https://arxiv.org/abs/2410.15608) — 2024 에지 친화적 ASR, Whisper 형태이지만 더 작음.
- [HuggingFace blog — "Fine-Tune Whisper For Multilingual ASR with 🤗 Transformers"](https://huggingface.co/blog/fine-tune-whisper) — mel 스펙트로그램 전처리기 및 토큰 타임스탬프 처리를 포함한 표준 fine-tuning 레시피.
- [HuggingFace `modeling_whisper.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/whisper/modeling_whisper.py) — 수업의 아키텍처 다이어그램을 반영한 전체 구현 (encoder, decoder, cross-attention, 생성).