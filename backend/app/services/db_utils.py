# backend/app/services/db_utils.py
from sqlalchemy import create_engine, text
from typing import List, Dict, Any

def get_engine(connection_string: str):
    return create_engine(connection_string, future=True)

def ensure_documents_table(engine):
    ddl = """
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        content TEXT,
        source_file TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))

def insert_documents(engine, chunks: List[Dict[str, Any]]):
    if not chunks:
        return 0
    insert_sql = text("INSERT INTO documents (content, source_file) VALUES (:content, :source)")
    with engine.begin() as conn:
        for c in chunks:
            conn.execute(insert_sql, {"content": c.get("text", ""), "source": c.get("source", "")})
    return len(chunks)

def ensure_employees_table(engine):
    ddl = """
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        name TEXT,
        role TEXT,
        department TEXT,
        raw_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name, role, department)
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))

def insert_employees(engine, rows: List[Dict[str, Any]]):
    if not rows:
        return 0
    # Use ON CONFLICT to avoid duplicates
    insert_sql = text("""
        INSERT INTO employees (name, role, department, raw_text)
        VALUES (:name, :role, :department, :raw_text)
        ON CONFLICT (name, role, department) DO NOTHING
    """)
    with engine.begin() as conn:
        for r in rows:
            conn.execute(insert_sql, {
                "name": r.get("name"),
                "role": r.get("role"),
                "department": r.get("department"),
                "raw_text": r.get("raw_text", "")
            })
    return len(rows)
