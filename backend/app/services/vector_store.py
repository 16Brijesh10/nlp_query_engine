# # backend/app/services/vector_store.py

# from typing import List, Dict, Any, Optional
# import os
# import numpy as np
# from sentence_transformers import SentenceTransformer

# # chromadb
# import chromadb
# from chromadb.config import Settings
# from chromadb.utils import embedding_functions

# PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "backend/app/chroma_store")
# CHROMA_COLLECTION_NAME = "documents"

# class VectorStore:
#     def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
#         # local embedding model
#         self.model = SentenceTransformer(model_name)
#         # chroma client, persisted to disk
#         os.makedirs(PERSIST_DIR, exist_ok=True)
#         self.client = chromadb.PersistentClient(path=PERSIST_DIR)
#         try:
#             self.col = self.client.get_collection(CHROMA_COLLECTION_NAME)
#         except Exception:
#             self.col = self.client.create_collection(CHROMA_COLLECTION_NAME)

#     def embed_texts(self, texts: List[str]) -> List[List[float]]:
#         # returns list of float vectors
#         embs = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
#         return embs.tolist()

#     def add_documents(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]):
#         """
#         Add documents (texts) into Chroma with ids and metadatas.
#         """
#         if not texts:
#             return 0
#         emb = self.embed_texts(texts)
#         self.col.add(documents=texts, metadatas=metadatas, ids=ids, embeddings=emb)
#         return len(texts)

#     def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
#         """
#         Returns list of dicts: {id, document, metadata, distance}
#         """
#         q_emb = self.embed_texts([query_text])[0]
#         #results = self.col.query(query_embeddings=[q_emb], n_results=top_k, include=["documents", "metadatas", "distances", "ids"])
#         # when adding documents
#         results=self.col.add(documents=texts,metadatas=[{"source": m.get("source", ""), "id": i} for m, i in zip(metadatas, ids)],embeddings=emb)

#         docs = []
#         # results structure: dict of lists
#         for i in range(len(results["ids"][0])):
#             docs.append({
#                 "id": results["ids"][0][i],
#                 "text": results["documents"][0][i],
#                 "metadata": results["metadatas"][0][i],
#                 "distance": results["distances"][0][i]
#             })
#         return docs

# # singleton
# VECTOR_STORE = VectorStore()
# backend/app/services/vector_store.py

from typing import List, Dict, Any
import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "backend/app/chroma_store")
CHROMA_COLLECTION_NAME = "documents"

class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        os.makedirs(PERSIST_DIR, exist_ok=True)
        # NEW Chroma Persistent Client
        self.client = chromadb.PersistentClient(path=PERSIST_DIR)
        try:
            self.col = self.client.get_collection(CHROMA_COLLECTION_NAME)
        except Exception:
            self.col = self.client.create_collection(CHROMA_COLLECTION_NAME)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embs = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
        return embs.tolist()

    def add_documents(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]):
        if not texts:
            return 0
        emb = self.embed_texts(texts)
        # store id inside metadata to retrieve later
        enriched_meta = [{"source": m.get("source", ""), "id": i} for m, i in zip(metadatas, ids)]
        self.col.add(documents=texts, metadatas=enriched_meta, embeddings=emb, ids=ids)
        return len(texts)

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q_emb = self.embed_texts([query_text])[0]
        results = self.col.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]  # no "ids"
        )

        docs = []
        for i in range(len(results["documents"][0])):
            docs.append({
                "id": results["metadatas"][0][i].get("id"),
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        return docs

# singleton instance
VECTOR_STORE = VectorStore()
