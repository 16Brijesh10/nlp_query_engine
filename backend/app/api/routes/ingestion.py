
# backend/app/api/routes/ingestion.py

import tempfile
import os
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel

from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VECTOR_STORE
from app.services.db_utils import get_engine, ensure_documents_table, insert_documents, ensure_employees_table, insert_employees
from app.api.routes import schema as schema_route
from app.api.routes.schema import get_query_engine_instance

router = APIRouter()

try:
    GLOBAL_DP = DocumentProcessor()
except Exception as e:
    print(f"CRITICAL: Failed to initialize DocumentProcessor: {e}")
    GLOBAL_DP = None

def get_document_processor() -> DocumentProcessor:
    if GLOBAL_DP is None:
        raise HTTPException(status_code=500, detail="Document processor not initialized.")
    return GLOBAL_DP

class DatabaseConnectRequest(BaseModel):
    connection_string: str

@router.post("/database")
async def connect_database(request: DatabaseConnectRequest):
    # legacy: keep for compatibility
    return {"status": "ok", "connection_string": request.connection_string}

@router.post("/upload-documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    dp: DocumentProcessor = Depends(get_document_processor)
):
    saved_paths: List[str] = []
    try:
        for f in files:
            suffix = os.path.splitext(f.filename)[1]
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            content = await f.read()
            tmp_file.write(content)
            tmp_file.close()
            saved_paths.append(tmp_file.name)

        # process -> chunk ids and structured rows
        chunk_ids, extracted_rows = dp.process_documents(saved_paths)

        # Add chunks to Chroma (persistent)
        # Build texts, metadatas, ids from dp.chunks_metadata for newly added chunks
        # dp.process_documents appended new_chunks_metadata to dp.chunks_metadata in order; we'll map by chunk_ids
        id_to_chunk = {c["chunk_id"]: c for c in dp.chunks_metadata}
        new_texts = []
        new_metas = []
        new_ids = []
        for cid in chunk_ids:
            c = id_to_chunk.get(cid)
            if c:
                new_ids.append(cid)
                new_texts.append(c["text"])
                new_metas.append({"source": c.get("source", "")})

        added = 0
        if new_texts:
            added = VECTOR_STORE.add_documents(new_ids, new_texts, new_metas)

        # Persist raw chunks into documents table if DB connected (DATABASE_URL or last connection)
        DATABASE_URL = os.getenv("DATABASE_URL") or getattr(schema_route, "_LAST_CONNECTION_STRING", None)
        inserted_docs = 0
        inserted_emp = 0
        if DATABASE_URL:
            engine = get_engine(DATABASE_URL)
            ensure_documents_table(engine)
            inserted_docs = insert_documents(engine, dp.chunks_metadata or [])

            # ensure employees table exists then insert extracted rows
            if extracted_rows:
                ensure_employees_table(engine)
                inserted_emp = insert_employees(engine, extracted_rows)
                # after inserting structured rows, refresh schema cache so UI sees new rows/tables
                try:
                    get_query_engine_instance(reset=True)
                    sd = schema_route.SchemaDiscovery(DATABASE_URL)
                    schema_route._LAST_SCHEMA_CACHE = sd.analyze_database()
                    # reset QueryEngine instance so it picks up new schema (if present)
                    # from app.api.routes.schema import _QUERY_ENGINE_INSTANCE
                    # if _QUERY_ENGINE_INSTANCE:
                    #     # Re-initialize QueryEngine with refreshed schema (simple approach)
                    #     _QUERY_ENGINE_INSTANCE = None
                except Exception as e:
                    print(f"[Ingestion] Schema refresh failed: {e}")

        return {
            "status": "ok",
            "filenames": [f.filename for f in files],
            "processed_chunks": len(chunk_ids),
            "chroma_added": added,
            "inserted_documents": inserted_docs,
            "inserted_structured_rows": inserted_emp
        }

    except Exception as e:
        print(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")

    finally:
        for path in saved_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as cleanup_err:
                print(f"[Ingestion] Cleanup warning: {cleanup_err}")


