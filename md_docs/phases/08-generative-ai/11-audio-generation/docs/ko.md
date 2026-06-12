# Audio 생성

> 오디오는 16-48 kHz의 1-D 신호이다. 5초 클립은 80-240k 샘플이다. 어떤 transformer도 해당 시퀀스를 직접 attend하지 않는다. 2026년 모든 production 오디오 모델에 대한解决方案은 동일하다: neural codec (Encodec, SoundStream, DAC)이 50-75 Hz에서 이산 토큰으로 오디오를 압축하고, transformer 또는 diffusion 모델이 토큰을 생성한다.

**유형:** 실습
**언어:** Python
**선수 과목:** Phase 6 · 02 (Audio Features), Phase 6 · 04 (ASR), Phase 8 · 06 (DDPM)
**소요 시간:** ~45분

## 문제

세 가지 오디오 생성 작업:

1. **텍스트-음성.** 주어진 텍스트에서 음성을 생성한다. 클린 음성은 협대역이며 강한 음소 구조를 갖는다 — 토큰 위의 transformer에 의해 잘 해결됨. VALL-E (Microsoft), NaturalSpeech 3, ElevenLabs, OpenAI TTS.
2. **음악 생성.** 프롬프트 (텍스트, 멜로디, 코드 진행, 장르)가 주어지면 음악을 생성한다. 훨씬 더 넓은 분포. MusicGen (Meta), Stable Audio 2.5, Suno v4, Udio, Riffusion.
3. **오디오 효과 / 사운드 디자인.** 프롬프트가 주어지면 환경 사운드 또는 Foley를 생성한다. AudioGen, AudioLDM 2, Stable Audio Open.

세 가지 모두 동일한 기질에서 실행된다: neural 오디오 codec + token-AR 또는 diffusion 생성기.

## 개념

![오디오 생성: codec 토큰 + transformer 또는 diffusion](../assets/audio-generation.svg)

### Neural 오디오 코덱

Encodec (Meta, 2022), SoundStream (Google, 2021), Descript Audio Codec (DAC, 2023). 컨벌루션 인코더가 파형을 단계별 벡터로 압축한다; 잔류 벡터 양자화 (RVQ)가 각 벡터를 K 코드북 인덱스의 级联으로 변환한다. Decoder가 그것을 반전한다. 8 RVQ 코드북에서 75 Hz로 2 kbps의 24 kHz 오디오 = 600 토큰/초.

```
waveform (16000 samples/sec)
    └─ encoder conv ─┐
                     ├─ RVQ layer 1 → indices at 75 Hz
                     ├─ RVQ layer 2 → indices at 75 Hz
                     ├─ ...
                     └─ RVQ layer 8
```

### 위의 두 가지 생성 패러다임

**Token-autoregressive.** RVQ 토큰을 시퀀스로 평면화하고 decoder-only transformer를 실행한다. MusicGen은 per-stream 오프셋과 함께 K 코드북 스트림을 병렬로Emit하기 위해 "지연된 병렬"을 사용한다. VALL-E는 텍스트 프롬프트 + 3초 음성 샘플에서 음성 토큰을 생성한다.

**잠재 diffusion.** codec 토큰을 연속 잠재로 패킹하거나 범주형 diffusion으로 모델링한다. Stable Audio 2.5는 연속 오디오 잠재에서 flow matching을 사용한다. AudioLDM 2는 텍스트- mel-오디오 diffusion을 사용한다.

2024-2026년 추세: flow matching이 음악에서 이기고 (더 빠른 추론, 더 깨끗한 샘플) token-AR은 여전히 음성에서 지배적，因为它는 자연적으로 causal이며 스트리밍에 적합하다.

## Production 환경

| 시스템 | 작업 | 백본 | 지연 시간 |
|--------|------|----------|---------|
| ElevenLabs V3 | TTS | Token-AR + neural vocoder | ~300ms 첫 번째 토큰 |
| OpenAI GPT-4o audio | 전이중 음성 | 종단간 멀티모달 AR | ~200ms |
| NaturalSpeech 3 | TTS | 잠재 flow matching | Non-streaming |
| Stable Audio 2.5 | 음악 / SFX | DiT + 오디오 잠재의 flow matching | 1분 클립에 ~10s |
| Suno v4 | 전체 노래 | 미공개; token-AR 의심 | 노래당 ~30s |
| Udio v1.5 | 전체 노래 | 미공개 | 노래당 ~30s |
| MusicGen 3.3B | 음악 | Encodec 32kHz에서 Token-AR | 실시간 |
| AudioCraft 2 | 음악 + SFX | Flow matching | 5s 클립에 ~5s |
| Riffusion v2 | 음악 | 스펙트로그램 diffusion | ~10s |

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|-----------------------|
| Neural codec | "오디오 압축" | 파형을 저차원 토큰 시퀀스로 압축. |
| RVQ | "잔류 벡터 양자화" | 다중 코드북으로 오디오 벡터를 이산 토큰으로 변환. |
| Token AR | "오디오의 autoregressive" | 이산 토큰의 순차적 생성. |
| Flow matching | "연속 생성" | 잠재 공간에서 diffusion의 대안. |
| TTS | "텍스트-음성" | 텍스트에서 음성合成. |

## 추가 자료

- [Defossez et al. (2022). High Fidelity Neural Audio Compression](https://arxiv.org/abs/2210.13438) — Encodec.
- [Copet et al. (2023). Simple and Controllable Music Generation](https://arxiv.org/abs/2311.03019) — MusicGen.