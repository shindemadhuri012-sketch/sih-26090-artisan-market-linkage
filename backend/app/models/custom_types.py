"""
SIH 26090: Custom SQLAlchemy Types & Vector Abstraction
Provides dialect-aware vector embedding type with native pgvector support on PostgreSQL
and fallback JSON/String serialization on SQLite for deterministic unit testing.
"""

import json
from typing import List, Optional
from sqlalchemy import TypeDecorator, Text
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT

try:
    from pgvector.sqlalchemy import Vector as PgVector
    PGVECTOR_INSTALLED = True
except ImportError:
    PGVECTOR_INSTALLED = False
    PgVector = None


class EmbeddingVector(TypeDecorator):
    """
    Dialect-aware vector embedding column type.
    - PostgreSQL: Renders native `vector(dim)` via pgvector.
    - SQLite / Other: Fallback serialization as JSON text string to allow
      schema generation and offline testing without PostgreSQL.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PGVECTOR_INSTALLED and PgVector is not None:
            return dialect.type_descriptor(PgVector(self.dim))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Optional[List[float]], dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and PGVECTOR_INSTALLED:
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return None
        return list(value)
