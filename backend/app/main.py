# backend/app/main.py
from fastapi import FastAPI
from app.api.routes import ingestion, query, schema

app = FastAPI(title="NLP Query Engine")

app.include_router(ingestion.router, prefix="/api", tags=["ingest"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(schema.router, prefix="/api", tags=["schema"])
