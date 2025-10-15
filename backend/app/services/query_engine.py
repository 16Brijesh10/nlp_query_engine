# backend/app/services/query_engine.py

from app.services.schema_discovery import SchemaDiscovery
from app.services.document_processor import DocumentProcessor
from app.services.cache import QueryCache # NEW IMPORT
from sentence_transformers import SentenceTransformer
from rapidfuzz import process as rf_process
from sqlalchemy import text, create_engine
import re
from typing import Dict, Any, List, Optional

class QueryEngine:
    def __init__(self, connection_string: str, schema: Dict[str, Any]): 
        # Schema is passed in, but we re-analyze to ensure consistency (optional, but robust)
        self.schema = SchemaDiscovery(connection_string).analyze_database()
        self.engine = create_engine(connection_string)
        
        # DP and Cache are initialized here, but DP is immediately OVERRIDDEN by schema.py 
        # to use the global, persistent DocumentProcessor instance.
        self.dp = DocumentProcessor()
        self.cache = QueryCache()
        
    def classify_query(self, q: str) -> str:
        """
        Classifies query as 'sql', 'doc', or 'hybrid'.
        """
        ql = q.lower()
        
        # 1. Document keywords (high confidence for DOC)
        doc_keywords = ["who", "what", "when", "where", "summary", "describe", "details"]
        if any(kw in ql for kw in doc_keywords):
            return "doc"
        
        # 2. SQL keywords (high confidence for SQL)
        sql_keywords = ["count", "sum", "average", "list", "how many", "top", "highest", "lowest"]
        if any(kw in ql for kw in sql_keywords):
            return "sql"
        
        # 3. Default fallback
        return "hybrid"

    def map_to_columns(self, q: str, topn=3):
        # Creates list of column names for fuzzy matching (T.col format)
        col_names = []
        for tname, tinfo in self.schema["tables"].items():
            for c in tinfo.get("columns", []):
                col_names.append(f"{tname}.{c['name']}")
        
        # returns list of tuples (col, score, idx)
        return rf_process.extract(q, col_names, limit=topn)

    def generate_sql(self, q: str, limit: int, offset: int) -> tuple[Optional[str], dict]:
        emp_table = None
        for k, v in self.schema.get("inferences", {}).items():
            if v == "employees":
                emp_table = k
                break
        if not self.schema.get("tables"):
            return None, {}
        table = emp_table or list(self.schema["tables"].keys())[0]

        # Try to extract a keyword (name, role, etc.) from the query
        keyword_match = re.search(r"how many\s+(\w+)", q, re.I)
        if keyword_match:
            keyword = keyword_match.group(1)
            sql = f"SELECT COUNT(*) as count FROM {table} WHERE name ILIKE :kw"
            params = {"kw": f"%{keyword}%"}
        else:
            sql = f"SELECT COUNT(*) as count FROM {table}"
            params = {}

        return sql, params



    def process_query(self, user_query: str, limit: int, offset: int):
        # 1. CACHE CHECK
        cache_key = f"{user_query}|{limit}|{offset}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            cached_result["cache_status"] = "HIT"
            cached_result["cache_stats"] = self.cache.get_stats()
            return cached_result
        
        # 2. EXECUTE
        qtype = self.classify_query(user_query)
        results = {"query": user_query, "query_type": qtype}
        
        # SQL Execution
        if qtype in ("sql", "hybrid"):
            sql, params = self.generate_sql(user_query, limit, offset) 
            
            if sql is not None:
                try:
                    with self.engine.connect() as conn:
                        res = conn.execute(text(sql), params)
                        # Use .mappings() for reliable dict conversion
                        rows = [dict(r) for r in res.mappings()] 
                        
                    results["sql_results"] = rows
                except Exception as e:
                    # Log SQL error but continue if possible
                    print(f"SQL Execution Error: {e}")
                    results["sql_error"] = str(e)
                
        # Document Search (safe)
        if qtype in ("doc", "hybrid"):
            # ensure dp is available and has chunks
            if not getattr(self, "dp", None) or self.dp.index is None or len(self.dp.chunks_metadata) == 0:
                results["doc_results"] = []
                results["doc_warning"] = "No documents ingested yet."
            else:
                topk = min(5, len(self.dp.chunks_metadata))
                docs = self.dp.search(user_query, top_k=topk)
                results["doc_results"] = docs
            
        # 3. CACHE SAVE
        if "sql_results" in results or "doc_results" in results:
             self.cache.set(cache_key, results)
             results["cache_status"] = "MISS"
        else:
             results["cache_status"] = "N/A" # Query failed or produced no results
        
        results["cache_stats"] = self.cache.get_stats()
        return results
