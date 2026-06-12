# 이미지 검색 — 메트릭 학습

> 유사한 이미지 찾기. 임베딩 공간에서 가장 가까운 이웃.

**유형:** 빌드 | **언어:** Python | **시간:** ~75분

## 개념
- Triplet Loss: anchor-positive 거리 < anchor-negative 거리
- ArcFace: 각도 기반 마진 → 얼굴 인식 표준
- 벡터 DB: FAISS/Milvus로 수백만 이미지 검색

## 빌드
```python
import faiss
index = faiss.IndexFlatL2(embedding_dim)
index.add(image_embeddings)
distances, indices = index.search(query_embedding, k=10)
```