# 음성 에이전트: Pipecat과 LiveKit

> 음성 에이전트는 2026년의 일급 프로덕션 카테고리다. Pipecat은 Python 프레임 기반 파이프라인(VAD → STT → LLM → TTS → transport)을 제공한다. LiveKit Agents는 AI 모델을 WebRTC를 통해 사용자에게 연결한다. 프리미엄 스택의 프로덕션 지연 시간 목표는 450-600ms 종단 간이다.

**Type:** Learn
**Languages:** Python (stdlib)
**Prerequisites:** Phase 14 · 01 (Agent Loop), Phase 14 · 12 (Workflow Patterns)
**Time:** ~60분

## 학습 목표

- Pipecat의 프레임 기반 파이프라인을 설명한다: DOWNSTREAM (source→sink) 및 UPSTREAM (제어).
- 표준 음성 파이프라인 단계와 Pipecat이 지원하는 전송을 명명한다.
- LiveKit Agents의 두 가지 음성 에이전트 클래스(MultimodalAgent, VoicePipelineAgent)와 각각이 적합한 경우를 설명한다.
- 2026년 프로덕션 지연 시간 기대치와 아키텍처 선택을 어떻게 주도하는지 요약한다.

## 문제

음성 에이전트는 TTS가 추가된 텍스트 루프가 아니다. 지연 시간 예산이 가혹하고(~600ms), 부분 오디오가 기본이며, 턴 감지는 모델이고, 전송 범위는 전화 SIP에서 WebRTC까지 다양하다. 프레임 기반 파이프라인(Pipecat)을 구축하거나 플랫폼(LiveKit)에 의존해야 한다.

## 개념

### Pipecat (pipecat-ai/pipecat)

- Python 프레임 기반 파이프라인 프레임워크.
- `Frame` → `FrameProcessor` 체인.
- 두 가지 흐름 방향:
  - **DOWNSTREAM** — source → sink (오디오 입력, TTS 출력).
  - **UPSTREAM** — 피드백 및 제어 (취소, 메트릭, barge-in).
- `PipelineTask`는 이벤트(`on_pipeline_started`, `on_pipeline_finished`, `on_idle_timeout`)와 관찰자(메트릭/트레이싱/RTVI)로 생명주기 관리.

일반적인 파이프라인:

```
VAD (Silero) → STT → LLM (context alternates user/assistant) → TTS → transport
```

전송: Daily, LiveKit, SmallWebRTCTransport, FastAPI WebSocket, WhatsApp.

Pipecat Flows는 구조화된 대화(상태 머신)를 추가. Pipecat Cloud는 관리형 런타임.

### LiveKit Agents (livekit/agents)

- AI 모델을 WebRTC를 통해 사용자에게 연결.
- 주요 개념: `Agent`, `AgentSession`, `entrypoint`, `AgentServer`.
- 두 가지 음성 에이전트 클래스:
  - **MultimodalAgent** — OpenAI Realtime 또는 동등을 통한 직접 오디오.
  - **VoicePipelineAgent** — STT → LLM → TTS 캐스케이드; 텍스트 수준 제어 제공.
- 변환기 모델을 통한 의미 턴 감지.
- 네이티브 MCP 통합.
- SIP를 통한 전화.
- LiveKit Inference를 통해 API 키 없이 50개 이상의 모델; 플러그인을 통해 200개 이상.

### 상용 플랫폼

Vapi (~450-600ms 최적화된 프리미엄 스택) 및 Retell (~600ms 종단 간 180개 테스트 통화)이 이 위에 구축. WebRTC 팀 없이 관리형 음성 스택을 원할 때 플랫폼 선택.

### 이 패턴이 잘못되는 경우

- **Barge-in 처리 없음.** 사용자가 중단; 에이전트가 계속 말함. Pipecat에서는 UPSTREAM 취소 프레임, LiveKit에서는 이에 상응하는 것 필요.
- **STT 신뢰도 무시.** 낮은 신뢰도 트랜스크립트가 복음처럼 LLM에 제공. 신뢰도에 게이트를 두거나 확인 요청.
- **TTS 문장 중간 차단.** 파이프라인이 발화 중간에 취소될 때 TTS가 알거나 오디오를 잘라야 함.
- **지연 시간 예산 무시.** 모든 구성 요소가 50-200ms 추가. 출시 전 체인 합계 계산.

### 2026년 일반적인 지연 시간

- VAD: 20-60ms
- STT partial: 100-250ms
- LLM first token: 150-400ms
- TTS first audio: 100-200ms
- Transport RTT: 30-80ms

종단 간 450-600ms가 프리미엄. 800-1200ms가 일반적. 1500ms 이상은 고장난 느낌.

## 직접 구현하기

`code/main.py`는 프레임 기반 장난감 파이프라인:

- `Frame` 유형 (audio, transcript, text, tts_audio, control).
- `process(frame)`가 있는 `Processor` 인터페이스.
- 스크립트 기반 프로세서로서의 5단계 파이프라인 (VAD → STT → LLM → TTS → transport).
- Barge-in을 보여주는 UPSTREAM 취소 프레임.

실행:

```
python3 code/main.py
```

트레이스는 정상 흐름과 TTS를 문장 중간에 중단하는 barge-in 취소를 보여준다.

## 활용하기

- **Pipecat** for full control — custom processors, Python-first, pluggable providers.
- **LiveKit Agents** for WebRTC-first deployments and telephony.
- **Vapi / Retell** for hosted voice agents without a WebRTC team.
- **OpenAI Realtime / Gemini Live** for direct audio-in/audio-out (MultimodalAgent).

## 배포하기

`outputs/skill-voice-pipeline.md` scaffolds a Pipecat-shaped voice pipeline with VAD + STT + LLM + TTS + transport plus barge-in handling.

## 연습 문제

1. 장난감 파이프라인에 메트릭 관찰자 추가: 단계당 초당 프레임 수 계산. 지연 시간이 어디서 누적되는가?
2. 신뢰도 게이트 STT 구현: 임계값 아래에서 "다시 말씀해 주시겠어요?" 요청.
3. 의미 턴 감지 추가: 간단한 규칙 — 트랜스크립트가 "?"로 끝나면 턴 종료.
4. Pipecat의 전송 문서 읽기. stdlib 전송을 SmallWebRTCTransport 구성(스텁)으로 교체.
5. 동일한 쿼리에서 OpenAI Realtime과 STT+LLM+TTS 캐스케이드 측정. 텍스트 수준 제어가 어떤 지연 시간 비용을 수반하는가?

## 주요 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|-------------------|-----------|
| Frame | "이벤트" | 파이프라인의 타입화된 데이터 단위 (audio, transcript, text, control) |
| Processor | "파이프라인 단계" | process(frame)이 있는 핸들러 |
| DOWNSTREAM | "순방향 흐름" | 소스에서 싱크로: 오디오 입력, 음성 출력 |
| UPSTREAM | "피드백 흐름" | 제어: 취소, 메트릭, barge-in |
| VAD | "음성 활동 감지" | 사용자가 말하는 중인지 감지 |
| Semantic turn detection | "스마트 턴 종료" | 사용자가 말을 마쳤다는 모델 기반 결정 |
| MultimodalAgent | "직접 오디오 에이전트" | 오디오 입력, 오디오 출력; 중간에 텍스트 없음 |
| VoicePipelineAgent | "캐스케이드 에이전트" | STT + LLM + TTS; 텍스트 수준 제어 |

## 추가 자료

- [Pipecat docs](https://docs.pipecat.ai/getting-started/introduction) — frame-based pipeline, processors, transports
- [LiveKit Agents docs](https://docs.livekit.io/agents/) — WebRTC + voice primitives
- [Vapi](https://vapi.ai/) — managed voice platform
- [Retell AI](https://www.retellai.com/) — managed voice, latency-benchmarked
