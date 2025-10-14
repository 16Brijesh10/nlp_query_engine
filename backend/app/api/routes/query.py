# # backend/app/api/routes/query.py (CLEANED)

# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel
# from typing import Dict, Any

# # We only need the dependency function for the POST endpoint
# from app.api.routes.schema import get_query_engine 
# from app.services.query_engine import QueryEngine # Type Hint only

# router = APIRouter()

# class QueryRequest(BaseModel):
#     query: str
#     limit: int = 50
#     offset: int = 0

# @router.post("/query")
# async def process_user_query(
#     req: QueryRequest,
#     # This line ensures the engine is initialized (via the /connect-database call) 
#     # before we attempt to use it.
#     qe: QueryEngine = Depends(get_query_engine) 
# ) -> Dict[str, Any]:
#     """
#     Processes a natural language query using the active QueryEngine.
#     """
#     try:
#         results = qe.process_query(req.query, req.limit, req.offset)
#         return {"status": "ok", "results": results}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

# # Remove any lines here that tried to initialize QueryEngine outside of the router function.

# backend/app/api/routes/query.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from time import time
from sqlalchemy import text
from app.api.routes.schema import get_query_engine
from app.services.query_engine import QueryEngine
from app.services.vector_store import VECTOR_STORE
import os
import google.generativeai as genai
import os
import requests

# optional Gemini import (Google Generative AI). Will only be used if key is present.
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    limit: int = 50
    offset: int = 0

# def synthesize_with_gemini(question: str, snippets: list) -> str:
#     """
#     ask Gemini to synthesize an answer from the top snippets.
#     Falls back to concatenated snippets if Gemini is not configured.
#     """
#     if not GEMINI_KEY:
#         return "\n\n".join([s["text"] for s in snippets[:3]])
#     # Build prompt
#     #system = "You are a helpful assistant summarizing document snippets to answer the user's question concisely."
#     prompt = f"Summarize the following document snippets to answer the question concisely:\n\nQuestion: {question}\n\n"
#     for i, s in enumerate(snippets[:5]):
#         prompt += f"\nSnippet {i+1}:\n{s['text']}\n"
#     prompt += "\nAnswer concisely:"
#     # Call Gemini chat
#     try:
#         # resp = genai.chat.create(model="gpt-4o-mini", messages=[{"role":"system","content":system}, {"role":"user","content":prompt}], temperature=0.0)
#         # return resp.choices[0].message.content.strip()
#         resp = genai.responses.create(
#             model="gpt-4o-mini",
#             temperature=0.0,
#             max_output_tokens=500,
#             input=prompt
#         )
#         # The response text is in resp.output_text
#         return resp.output_text

        
    # except Exception as e:
    #     print(f"[Gemini] synthesis failed: {e}")
    #     return "\n\n".join([s["text"] for s in snippets[:3]])
def synthesize_with_gemini(question: str, snippets: list) -> str:
    """Fallback: concatenate top 3 document snippets as summary."""
    if not snippets:
        return "No relevant documents found."
    return "\n\n".join([s["text"] for s in snippets[:3]])

router = APIRouter()

@router.post("/query")
async def process_user_query(req: QueryRequest, qe: QueryEngine = Depends(get_query_engine)) -> Dict[str, Any]:
    start = time()
    cache_key = f"{req.query}|{req.limit}|{req.offset}"
    # check cache
    cached = qe.cache.get(cache_key)
    if cached:
        cached["cache_status"] = "HIT"
        cached["execution_time_ms"] = round((time() - start) * 1000, 2)
        return {"status": "ok", "results": cached}

    results: Dict[str, Any] = {"query": req.query}
    qtype = qe.classify_query(req.query)
    results["query_type"] = qtype

    # SQL
    if qtype in ("sql", "hybrid"):
        sql, params = qe.generate_sql(req.query, req.limit, req.offset)
        if sql:
            try:
                sql_start = time()
                with qe.engine.connect() as conn:
                    # pass params as dict to execute
                    res = conn.execute(text(sql), params)
                    rows = [dict(r) for r in res.mappings()]
                results["sql_results"] = rows
                results["sql_time_ms"] = round((time() - sql_start) * 1000, 2)
            except Exception as e:
                results["sql_error"] = str(e)

    # Document (Chroma) retrieval
    if qtype in ("doc", "hybrid"):
        doc_start = time()
        docs = VECTOR_STORE.query(req.query, top_k=min(5, req.limit))
        results["doc_time_ms"] = round((time() - doc_start) * 1000, 2)
        results["doc_results"] = docs
        # optionally synthesize with Gemini
        if docs:
            synth = synthesize_with_gemini(req.query, docs)
            results["doc_answer"] = synth

    results["execution_time_ms"] = round((time() - start) * 1000, 2)
    # cache store
    qe.cache.set(cache_key, results)
    results["cache_status"] = "MISS"
    results["cache_stats"] = qe.cache.get_stats()

    return {"status": "ok", "results": results}
