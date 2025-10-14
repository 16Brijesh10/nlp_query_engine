# backend/app/services/document_processor.py

import os
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from pypdf import PdfReader
import re
from datetime import datetime

class DocumentProcessor:
    def __init__(self):
        # lazy model load
        self._model = None
        self.index: faiss.Index | None = None
        self.chunks_metadata: List[Dict[str, Any]] = []

    @property
    def model(self):
        """Load SentenceTransformer on first access."""
        if self._model is None:
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._model

    def dynamic_chunking(self, content: str, filename: str) -> List[Dict[str, str]]:
        """
        Split text into paragraph-like chunks.
        Returns list of {"text","source","chunk_id"} dicts.
        """
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chunks: List[Dict[str, str]] = []
        for i, p in enumerate(paragraphs):
            chunks.append({
                "text": p,
                "source": filename,
                "chunk_id": f"{filename}_{i}"
            })
        return chunks

    def _read_file(self, file_path: str) -> str:
        """
        Read file content. For PDFs, extract text per page and skip None pages.
        Returns empty string on failure.
        """
        file_path_lower = file_path.lower()

        if file_path_lower.endswith('.pdf'):
            try:
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
            except Exception as e:
                # keep the error visible in logs
                print(f"[DocumentProcessor] PDF read error for {file_path}: {e}")
                return ""

        # fallback for plain text files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

    def process_documents(self, file_paths: List[str]) -> tuple[list,list]:
        """
        Processes multiple documents, generates embeddings, and indexes them into FAISS.
        Returns a list of chunk IDs that were added.
        """
        all_chunks_text: List[str] = []
        new_chunks_metadata: List[Dict[str, Any]] = []

        # 1) chunk and collect text
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            content = self._read_file(file_path)
            chunks = self.dynamic_chunking(content, filename)

            if not content or not content.strip():
                print(f"[DocumentProcessor] No text extracted from {filename}")
                continue

            chunks = self.dynamic_chunking(content, filename)

            # fallback: if dynamic_chunking returned nothing, add full content as one chunk
            if not chunks:
                chunks = [{"text": content, "source": filename, "chunk_id": f"{filename}_0"}]

            for chunk in chunks:
                # ensure chunk has text
                txt = chunk.get("text", "").strip()
                if not txt:
                    continue
                all_chunks_text.append(txt)
                new_chunks_metadata.append(chunk)

        if not all_chunks_text:
            print("[DocumentProcessor] No chunks to index after processing all files.")
            return [],[]

        # 2) generate embeddings (ensure we get a numpy array)
        try:
            embeddings = self.model.encode(all_chunks_text, convert_to_tensor=False, batch_size=32).astype(np.float32)
        except Exception as e:
            print(f"[DocumentProcessor] Embedding generation failed: {e}")
            return []

        # convert to numpy float32 and ensure 2D shape
        embeddings = np.array(embeddings, dtype=np.float32)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # 3) initialize FAISS index if needed
        if self.index is None:
            embedding_dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(embedding_dim)
            print(f"[DocumentProcessor] Initialized FAISS index with dim {embedding_dim}")

        # 4) add to index
        try:
            self.index.add(embeddings)
        except Exception as e:
            print(f"[DocumentProcessor] FAISS add failed: {e}")
            return []

        # 5) update metadata (order must match index vectors)
        self.chunks_metadata.extend(new_chunks_metadata)

        print(f"[DocumentProcessor] Indexed {len(new_chunks_metadata)} chunks. Total chunks: {len(self.chunks_metadata)}")

        return [c['chunk_id'] for c in new_chunks_metadata],self.extract_structured_rows()
    def extract_structured_rows(self, chunks: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
        """
        Extracts structured employee info from given document chunks.
        If chunks is None, uses self.chunks_metadata.
        """
        if chunks is None:
            chunks = self.chunks_metadata

        rows = []
        for chunk in chunks:
            text = chunk["text"]
            lines = text.split("\n")
            for line in lines:
                match = re.search(
                    r"Name\s*[:\-]?\s*(?P<name>[^\n,]+).*?Role\s*[:\-]?\s*(?P<role>[^\n,]+).*?(Dept|Department)\s*[:\-]?\s*(?P<department>[^\n,]+)",
                    line, re.IGNORECASE
                )
                if match:
                    rows.append({
                        "name": match.group("name").strip(),
                        "role": match.group("role").strip(),
                        "department": match.group("department").strip(),
                        "raw_text": line.strip()
                    })
        return rows


    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search FAISS for the query and return matched chunk metadata.
        This function is robust to small index sizes and returns [] if nothing is found.
        """
        if self.index is None:
            print("[DocumentProcessor] FAISS index not initialized (search).")
            return []

        total_vectors = int(self.index.ntotal) if hasattr(self.index, "ntotal") else len(self.chunks_metadata)
        if total_vectors == 0 or not self.chunks_metadata:
            print("[DocumentProcessor] No vectors indexed (search).")
            return []

        # encode query vector
        try:
            qvec = self.model.encode([query], convert_to_tensor=False)
        except Exception as e:
            print(f"[DocumentProcessor] Query embedding failed: {e}")
            return []

        qvec = np.array(qvec, dtype=np.float32)
        if qvec.ndim == 1:
            qvec = qvec.reshape(1, -1)

        # ensure k is <= number of indexed vectors and > 0
        k = min(top_k, total_vectors)
        if k <= 0:
            return []

        # perform search
        try:
            D, I = self.index.search(qvec, k)
        except Exception as e:
            print(f"[DocumentProcessor] FAISS search failed: {e}")
            return []

        # debug
        print(f"[DocumentProcessor] FAISS returned indices: {I} distances: {D}")

        results: List[Dict[str, Any]] = []
        for idx in I[0]:
            # FAISS may return -1 for empty slots; ensure valid index before read
            if idx is None:
                continue
            if isinstance(idx, (int, np.integer)) and 0 <= int(idx) < len(self.chunks_metadata):
                results.append(self.chunks_metadata[int(idx)])

        return results
