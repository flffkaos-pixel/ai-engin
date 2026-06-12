# 실시간/엣지 비전

> 모바일, 드론, IoT 기기에서 실행되는 비전. 속도가 전부입니다.

**유형:** 빌드  
**언어:** Python  
**시간:** ~60분

## 개념

- **MobileNet**: 깊이별 분리 합성곱 — 연산량 8~9배 감소
- **양자화**: FP32 → INT8 — 속도 2~4배, 메모리 4배 절약
- **ONNX/TensorRT**: 모델 최적화 → 엣지 배포

## 최적화 기법

| 기법 | 효과 |
|------|------|
| 깊이별 분리 Conv | 연산량 8~9x 감소 |
| 채널 가지치기 | 불필요 채널 제거 |
| INT8 양자화 | 추론 속도 2~4x |
| 지식 증류 | 큰 모델 → 작은 모델 지식 전달 |

## 빌드하기

```python
# ONNX 내보내기
torch.onnx.export(model, dummy_input, "model.onnx")
# INT8 양자화
model_int8 = torch.quantization.quantize_dynamic(model, {nn.Linear}, dtype=torch.qint8)
```

## 주요 용어

| 용어 | 의미 |
|------|------|
| 깊이별 분리 | 공간+채널 Conv 분리 — 경량화 |
| 양자화 | 가중치/활성화 정밀도 축소 |