from typing import List, Optional, Dict, Any
from . import db
from . import embeddings

def create_note(content: str) -> Dict[str, Any]:
    """
    Insert a note and its embedding into Postgres, return a dict.
    """
    emb = embeddings.embed_text(content)
    emb_str = embeddings.to_pgvector_literal(emb)
    conn = db.get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO notes (content, embedding)
                    VALUES (%s, %s::vector)
                    RETURNING id, content, created_at;
                    """,
                    (content, emb_str),
                )
                row = cur.fetchone()
                return {
                    "id": row[0],
                    "content": row[1],
                    "created_at": row[2].isoformat(),
                }
    finally:
        db.put_conn(conn)
def get_note(note_id: int) -> Optional[Dict[str, Any]]:
    conn = db.get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, content, created_at FROM notes WHERE id = %s;",
                    (note_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "id": row[0],
                    "content": row[1],
                    "created_at": row[2].isoformat(),
                }
    finally:
        db.put_conn(conn)
def list_notes(limit: int = 1) -> List[Dict[str, Any]]:
    conn = db.get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, content, created_at
                    FROM notes
                    ORDER BY id DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                return [
                        {
                            "id": r[0],
                            "conten": r[1],
                            "created_at": r[2].isoformat(),
                        }
                        for r in rows
                    ]
    finally:
        db.put_conn(conn)
def search_notes(query: str, limit: int = 1) -> List[Dict[str, Any]]:
    """
    Semantic search using pgvector <-> in SQL.
    Returns list of dicts with id, content, created_at, score.
    """
    query_emb = embeddings.embed_text(query)
    query_emb_str = embeddings.to_pgvector_literal(query_emb)
    conn = db.get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                    id,
                    content,
                    created_at,
                    embedding <-> %s::vector AS distance
                    FROM notes
                    ORDER BY embedding <-> %s::vector
                    LIMIT %s;
                    """,
                    (query_emb_str, query_emb_str, limit),
                )
                rows = cur.fetchall()
                results: List[Dict[str, Any]] = []
                for row in rows:
                    note_id, content, created_at, distance = row
                    d = float(distance) if distance is not None else 0.0
                    score = 1.0 / (1.0 + d) if d >= 0 else 0.0
                    results.append(
                        {
                            "id": note_id,
                            "content": content,
                            "created_at": created_at.isoformat(),
                            "score": score,
                        }
                    )
                return results
    finally:
        db.put_conn(conn)