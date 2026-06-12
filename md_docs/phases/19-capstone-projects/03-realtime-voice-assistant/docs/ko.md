# 캡스톤 03 — 실시간 음성 어시스턴트 (ASR to LLM to TTS)

> 음성이 느낌이 좋은 음성 에이전트는 종단 간 지연 시간이 800ms 미만이고, 사용자가 말을 멈추었을 때를 인식하며, 버지인(barge-in)을 처리하고, 도구를 호출할 때 멈추지 않는다. Retell, Vapi, LiveKit Agents, Pipecat은 2026년에 모두 이 기준을 충족한다. 이들은 동일한 형태를 취한다: 스트리밍 ASR, 턴 감지기, 스트리밍 LLM, 스트리밍 TTS — 모든 것이 WebRTC로 연결되어 각 홉에서 공격적인 지연 시간 예산을 가진다. 이를 구축하고, WER과 MOS 및 오탯 빈도를 측정하며, 패킷 손실 하에서 테스트한다.

**유형:** 캡스톤
**언어:** Python (에이전트 + 파이프라인), TypeScript (웹 클라이언트)
**선수 과목:** Phase 6 (음성 및 오디오), Phase 7 (트랜스포머), Phase 11 (LLM 엔지니어링), Phase 13 (도구), Phase 14 (에이전트), Phase 17 (인프라)
**활용 phases:** P6 · P7 · P11 · P13 · P14 · P17
**소요 시간:** 30시간

## 문제

음성은 2025-2026년 가장 빠르게 움직이는 AI UX 카테고리이다. 기술적 천장선이 분기마다 낮아졌다. OpenAI Realtime API, Gemini 2.5 Live, Cartesia Sonic-2, ElevenLabs Flash v3, LiveKit Agents 1.0, Pipecat 0.0.70은 모두 800ms 미만의 첫 번째 오디오 출력을 손쉽게 달성한다. 기준은 지연 시간만이 아니다. 그것은 상호작용 느낌이다: 사용자를 끊지 않고, 끊기지 않고, 문장 중간Interrupt 후 복구하고, 대화 중 도구를 호출할 때 오디오를 멈추지 않고, 불안정한 모바일 네트워크를 견딘다.

세 개의 REST 호출을 연결로는 이를 얻을 수 없다. 아키텍처는 종단 간 파이프라인 스트리밍이다. 구축하면 실패 모드가 보인다: 전화 오디오에 튜닝된 VAD가 배경 TV에서 작동하고, 턴 감지기가punctuation을기다리다 끝내지 않고, TTS가 400ms 버퍼링 후 방출한다. 캡스톤은 이러한 문제를 하나씩 부하 하에서修正하고 지연 시간 및 품질 보고서를 게시하는 것이다.

## 개념

파이프라인에는 다섯 개의 스트리밍 단계가 있다: **오디오 입력** (브라우저 또는 PSTN의 WebRTC), **ASR** (Deepgram Nova-3 또는 faster-whisper의 스트리밍 부분 필사본), **턴 감지** (VAD + 부분 필사본의 완료 신호를 읽는 소형 턴 감지기 모델), **LLM** (턴이 완료된 것으로 판단되면 토큰을 스트리밍), **TTS** (첫 번째 LLM 토큰부터 약 200ms 이내에 오디오 스트리밍).

세 가지 교차 관심사. **버지인**: 사용자가 에이전트가 말하는 동안 말하기 시작하면 TTS가 취소되고 ASR이 즉시拾い上げる. **도구 사용**: 대화 중 함수 호출(날씨, 캘린더)은 오디오를 멈추지 않고 사이드 채널에서 실행해야 한다; 지연 시간이 300ms를 초과하면 에이전트가 확인 토큰("잠시만요...")을 미리发出한다. **백프레셔**: 패킷 손실 하에서 부분 필사본이 유지되고, VAD가 speech-gate 임계값을 높이며, 에이전트는 확인되지 않은 메시지에 대해 말하는 것을避けます.

측정 기준은 정량적이다. 15dB SNR에서 Hamming VAD 벤치마크에서 WER 8% 미만. 100개 측정 통화에서 첫 번째 오디오 출력 p50 800ms 미만. 오탯 비율 3% 미만. TTS에서 MOS 4.2 이상. 단일 g5.xlarge에서 50개 동시 통화. 이 수치가 결과물이다.

## 아키텍처

```
browser / Twilio PSTN
        |
        v
   WebRTC / SIP edge
        |
        v
  LiveKit Agents 1.0  (or Pipecat 0.0.70)
        |
   +----+--------------+--------------+-----------------+
   |                   |              |                 |
   v                   v              v                 v
  ASR              VAD v5         turn-detector     side-channel
 (Deepgram         (Silero)          (LiveKit)        tools
  Nova-3 /         speech-gate    completion score    (weather,
  Whisper-v3)      per 20ms       on partials        calendar)
     |                   |              |
     +--------+----------+--------------+
              v
          LLM (streaming)
       GPT-4o-realtime / Gemini 2.5 Flash /
       cascaded Claude Haiku 4.5
              |
              v
          TTS streaming
       Cartesia Sonic-2 / ElevenLabs Flash v3
              |
              v
       audio back to caller
              |
              v
     OpenTelemetry voice traces -> Langfuse
```

## 기술 스택

- 전송: LiveKit Agents 1.0 (WebRTC) + Twilio PSTN 게이트웨이; Pipecat 0.0.70을 대체 프레임워크로 사용
- ASR: Deepgram Nova-3 (스트리밍, 300ms 미만의 첫 번째 부분) 또는 faster-whisper Whisper-v3-turbo 셀프 호스트
- VAD: Silero VAD v5 + LiveKit 턴 감지기 (부분 필사본을 읽는 소형 트랜스포머)
- LLM: 긴밀한 통합을 위한 OpenAI GPT-4o-realtime, Gemini 2.5 Flash Live, 또는 캐스케이드된 Claude Haiku 4.5 (스트리밍 완성, 별도 오디오 경로)
- TTS: Cartesia Sonic-2 (최저 첫 번째 바이트), ElevenLabs Flash v3, 또는 셀프 호스트를 위한 오픈소스 Orpheus
- 도구: 날씨/캘린더/예약을 위한 FastMCP 사이드 채널; 도구가 300ms 이상 걸리면 에이전트가 필러를 미리发出
- 관찰가능성: OpenTelemetry voice spans, 오디오 재생이 포함된 Langfuse voice traces
- 배포: 셀프 호스트 Whisper + Orpheus를 위한 단일 g5.xlarge (24GB VRAM); 최저 지연 시간을 위한 호스티드 APIs

## 실습

1. **WebRTC 세션.** LiveKit 방과 마이크 오디오를 스트리밍하는 웹 클라이언트를 설정한다. 서버에서 에이전트 워커를 방에 연결한다.

2. **ASR 스트리밍.** 20ms PCM 프레임을 Deepgram Nova-3 (또는 GPU의 faster-whisper)에 제공한다. 부분 및 최종 필사본을 구독한다. 부분당 지연 시간을 로그한다.

3. **VAD 및 턴 감지.** 프레임 스트림에서 Silero VAD v5를 실행한다. speech-end 이벤트에서 최신 부분 필사본에 대해 LiveKit 턴 감지기를起動한다. VAD가 500ms 동안 침묵이라고 말하고 턴 감지 점수가 완료 > 0.6일 때만 "턴 완료"로 커밋한다.

4. **LLM 스트림.** 턴 완료 시 실행 중인 대화 + 최종 필사본으로 LLM 호출을 시작한다. 토큰을 스트리밍한다. 첫 번째 토큰에서 TTS로 전달한다.

5. **TTS 스트림.** Cartesia Sonic-2가 오디오 청크를 스트리밍한다. 첫 번째 청크는 첫 번째 LLM 토큰부터 200ms 이내에 서버를 떠나야 한다. 청크를 LiveKit 방에发出; 클라이언트가 WebRTC 지터 버퍼를 통해 재생한다.

6. **버지인.** TTS가 재생되는 동안 VAD가 새로운 사용자 음성을 감지하면 TTS 스트림을 즉시 취소하고, 나머지 LLM 출력을 삭제하며, ASR을 다시 준비한다. `tts_canceled` span을 게시한다.

7. **도구 사이드 채널.** 날씨와 캘린더를 함수 호출 도구로 등록한다. 호출되면 동시에起動; 300ms 이내에 해결되지 않으면 LLM에 "잠시만요, 확인해보겠습니다"를 필러로发出; 도구가 반환되면再開한다.

8. **평가 하네스.** 100개 통화를 녹음한다. WER(보류된 필사본 대비), 오탯 비율(TTS가 사용자가 문장 중단에 있을 때 취소된 비율), 첫 번째 오디오 출력 p50, TTS MOS(인간 또는 NISQA), 지터-손실 테스트(3% 패킷 드롭)를 계산한다.

9. **부하 테스트.** 합성 발신자로 단일 g5.xlarge에서 50개 동시 통화를 실행한다. 지속적인 첫 번째 오디오 출력 p95를 측정한다.

## 활용

```
caller: "what is the weather in tokyo tomorrow"
[asr  ] partial @280ms: "what is the"
[asr  ] partial @540ms: "what is the weather"
[turn ] completion score 0.82 at @820ms; commit
[llm  ] first token @960ms
[tool ] weather.tokyo tomorrow -> 68/52 partly cloudy @1140ms
[tts  ] first audio-out @1040ms: "Tokyo tomorrow will be partly cloudy..."
turn latency: 1040ms user-stop -> audio-out
```

## 결과물

`outputs/skill-voice-agent.md`가 결과물이다. 도메인(고객 지원, 예약, 키오스크)이 주어지면 측정 기준에 맞게 튜닝된 ASR/VAD/LLM/TTS 파이프라인으로 LiveKit 에이전트를 설정한다. 채점 기준:

| 가중치 | 기준 | 측정 방법 |
|:-:|---|---|
| 25 | 종단 간 지연 시간 | 100개 녹음 통화에서 첫 번째 오디오 출력 p50 800ms 미만 |
| 20 | 턴 테이킹 품질 | Hamming VAD 벤치마크에서 오탯 비율 3% 미만 |
| 20 | 도구 사용 정확성 | 오디오를 멈추지 않고 올바른 데이터를 반환하는 대화 중 도구 호출 |
| 20 | 패킷 손실 하 신뢰성 | 3% 패킷 드롭 주입 시 WER 및 턴 테이킹 안정성 |
| 15 | 평가 하네스 완전성 | 공개 config로 재현 가능한 측정 |
| **100** | | |

## 연습 문제

1. Deepgram Nova-3을 g5.xlarge의 faster-whisper v3 turbo로 교체한다. 지연 시간과 WER 격차를 측정한다. CPU 대 GPU 결정이 중요한 곳을 식별한다.

2. 중단 조정 정책을 추가한다: 사용자가 도구 호출 중에 버지인하면 에이전트가 어떻게 해야 하는가? 세 가지 정책을 비교한다(하드 취소, 도구 완료 후 중지, 다음 턴 대기).

3. 적대적 턴 감지기 테스트를 실행한다: 사용자에게 문장 중간에 긴 일시중지를 준다. 오탯을 최소화하면서 900ms를 넘지 않도록 VAD 침묵 임계값과 턴 감지 점수 임계값을 조정한다.

4. Twilio를 통해 PSTN에서 동일한 에이전트를 배포한다. PSTN 첫 번째 오디오 출력을 WebRTC와 비교한다. 지터 버퍼 및 코덱 차이를 설명한다.

5. 비영어 언어(일본어, 스페인어)에 대한 음성 활동 감지를 추가한다. Silero VAD v5의 가양 트리거 비율 대 언어 특정 파인 튜닝을 측정한다.

## 핵심 용어

| 용어 |人们在说什么 |实际意思 |
|------|-----------------|------------------------|
| 턴 감지 | "End of utterance" | VAD 침묵과 부분 필사본을given으로 사용자가 말하기를 마쳤다고 판단하는 분류기 |
| 버지인 | "Interruption handling" | TTS 재생 중 VAD가 새로운 사용자 음성을 감지하면 취소 |
| 첫 번째 오디오 출력 | "Latency" | 사용자가 말하기를 멈추고 첫 번째 오디오 패킷이 서버를 떠나는 시간 |
| VAD | "Speech gate" | 오디오 프레임을 음성 대 침묵으로 분류하는 모델; Silero VAD v5가 2026년 기본값 |
| 지터 버퍼 | "Audio smoothing" | 네트워크 분산을흡수하기 위해 패킷을 잠시 유지하는 클라이언트 측 버퍼 |
| 필러 | "Acknowledgment token" | 도구가 느릴 때 침묵을 피하기 위해 에이전트가发出하는 짧은 문구 |
| MOS | "Mean opinion score" | 지각적 음성 품질 등급; NISQA가 자동화된 프록시 |

## 추가 자료

- [LiveKit Agents 1.0](https://github.com/livekit/agents) — 기준 WebRTC 에이전트 프레임워크
- [Pipecat](https://github.com/pipecat-ai/pipecat) — 대체 Python 우선 스트리밍 에이전트 프레임워크
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime) — 통합 음성 모델에 대한 참조
- [Deepgram Nova-3 documentation](https://developers.deepgram.com/docs) — 스트리밍 ASR 참조
- [Silero VAD v5](https://github.com/snakers4/silero-vad) — VAD 참조 모델
- [Cartesia Sonic-2](https://docs.cartesia.ai) — 저지연 TTS 참조
- [Retell AI architecture](https://docs.retellai.com) — 운영 음성 에이전트 아키텍처
- [Vapi.ai production stack](https://docs.vapi.ai) — 대체 운영 참조