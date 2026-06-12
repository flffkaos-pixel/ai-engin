# Q-Learning & SARSA

> 행동 가치 학습. On-policy vs Off-policy.

**유형:** 빌드 | **시간:** ~75min

## 개념
- Q(s,a): 상태 s에서 행동 a의 가치
- Q-Learning: max Q로 업데이트 (off-policy)
- SARSA: 실제 다음 행동으로 업데이트 (on-policy)
- TD: 즉시 보상+추정값 → MC보다 빠른 학습