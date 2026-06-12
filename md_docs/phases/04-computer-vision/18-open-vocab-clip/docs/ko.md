# 개방 어휘 — CLIP

> 이미지와 텍스트를 공유 공간에 매핑. "고양이"라는 단어로 고양이 이미지 검색.

**유형:** 빌드 | **언어:** Python | **시간:** ~75분

## 개념
- CLIP: 이미지+텍스트 쌍으로 대조 학습
- 제로샷 분류: "a photo of {class}"로 모든 클래스 분류
- 멀티모달: 이미지 ↔ 텍스트 정렬

## 빌드
```python
model = CLIPModel.from_pretrained("openai/clip-vit-base")
inputs = tokenizer(["a cat", "a dog"], return_tensors="pt")
image_features = model.get_image_features(image)
text_features = model.get_text_features(**inputs)
similarity = image_features @ text_features.T
```