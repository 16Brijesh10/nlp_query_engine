# backend/app/services/schema_discovery.py
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.reflection import Inspector
from typing import Dict, Any
import re

class SchemaDiscovery:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = create_engine(connection_string, pool_pre_ping=True)

    def analyze_database(self) -> Dict[str, Any]:
        inspector: Inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        schema = {"tables": {}}
        for table in tables:
            cols = inspector.get_columns(table)
            pk = inspector.get_primary_keys(table) if hasattr(inspector, "get_primary_keys") else []
            fks = inspector.get_foreign_keys(table)
            # Sample data (limit 5) safely
            sample = []
            try:
                with self.engine.connect() as conn:
                    res = conn.execute(text(f"SELECT * FROM {table} LIMIT 5"))
                    sample = [dict(row) for row in res]
            except Exception:
                sample = []
            schema["tables"][table] = {
            "columns": [{ "name": c["name"], "type": str(c["type"])} for c in cols],
            "primary_key": pk,
            "foreign_keys": fks,
            "sample": sample,
            }
        # optional: infer roles like employees/departments by name heuristics
        schema["inferences"] = self._infer_table_roles(schema)
        return schema

    def _infer_table_roles(self, schema):
        roles = {}
        for tname, tinfo in schema["tables"].items():
            low = tname.lower()
            if re.search(r"emp|staff|person|personnel", low):
                roles[tname] = "employees"
            elif re.search(r"dept|division|department", low):
                roles[tname] = "departments"
            elif re.search(r"doc|document|resume", low):
                roles[tname] = "documents"
            elif re.search(r"proj|project|assignment|task", low):
                roles[tname] = "projects"
        return roles
