# Actor-Critic & A2C/A3C

> 정책+가치 동시 학습. Actor=행동, Critic=평가.

**유형:** 빌드 | **시간:** ~75min

## 개념
- Actor: 정책 π(a|s) — 행동 선택
- Critic: V(s) — 행동 평가
- A2C: Advantage=A(s,a)=Q(s,a)-V(s) — 동기식
- A3C: 비동기 병렬 학습