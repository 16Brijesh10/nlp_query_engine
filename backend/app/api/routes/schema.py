# backend/app/api/routes/schema.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services.schema_discovery import SchemaDiscovery
from app.services.query_engine import QueryEngine
from app.services.db_utils import get_engine, ensure_employees_table  # New import

router = APIRouter()

class ConnectRequest(BaseModel):
    connection_string: str

_LAST_SCHEMA_CACHE: Dict[str, Any] = {}
_LAST_CONNECTION_STRING: str = ""
_QUERY_ENGINE_INSTANCE: Optional[QueryEngine] = None

def get_query_engine_instance(reset: bool = False) -> QueryEngine:
    """
    Returns the active QueryEngine.
    If reset=True, re-initializes it using the last connection string and schema.
    """
    global _QUERY_ENGINE_INSTANCE, _LAST_CONNECTION_STRING, _LAST_SCHEMA_CACHE

    if reset or _QUERY_ENGINE_INSTANCE is None:
        if not _LAST_CONNECTION_STRING:
            raise HTTPException(status_code=404, detail="No database connected yet.")
        # Re-analyze schema
        sd = SchemaDiscovery(_LAST_CONNECTION_STRING)
        _LAST_SCHEMA_CACHE = sd.analyze_database()
        # Re-initialize engine
        _QUERY_ENGINE_INSTANCE = QueryEngine(_LAST_CONNECTION_STRING, _LAST_SCHEMA_CACHE)
    return _QUERY_ENGINE_INSTANCE


def get_query_engine() -> QueryEngine:
    if _QUERY_ENGINE_INSTANCE is None:
        raise HTTPException(
            status_code=404,
            detail="Query engine not initialized. Please connect to a database first.",
        )
    return _QUERY_ENGINE_INSTANCE

@router.post("/connect-database")
async def connect_database(req: ConnectRequest):
    global _LAST_SCHEMA_CACHE, _LAST_CONNECTION_STRING, _QUERY_ENGINE_INSTANCE

    try:
        # Step 0: Ensure employees table exists
        engine = get_engine(req.connection_string)
        ensure_employees_table(engine)

        # Step 1: Analyze Schema
        sd = SchemaDiscovery(req.connection_string)
        schema = sd.analyze_database()

        # Step 2: Cache results
        _LAST_SCHEMA_CACHE = schema
        _LAST_CONNECTION_STRING = req.connection_string

        # Step 3: Initialize QueryEngine
        _QUERY_ENGINE_INSTANCE = QueryEngine(req.connection_string, schema)

        return {
            "status": "ok",
            "message": "Database connected, schema discovered, and query engine initialized.",
            "schema": schema,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect or analyze database: {type(e).__name__}: {str(e)}",
        )

@router.get("/get-schema")
async def get_schema():
    if not _LAST_SCHEMA_CACHE:
        raise HTTPException(status_code=404, detail="No schema found. Connect to a database first.")
    return {"schema": _LAST_SCHEMA_CACHE}
