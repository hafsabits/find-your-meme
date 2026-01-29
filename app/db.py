import os
from psycopg2.pool import SimpleConnectionPool

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "notes_db")
DB_USER = os.getenv("DB_USED", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pass")

_pool : SimpleConnectionPool | None = None

def init_db_pool():
    """Initialize a global connection pool."""
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host = DB_HOST,
            port = DB_PORT,
            dbname = DB_NAME,
            user = DB_USER,
            password = DB_PASSWORD,
        )
def get_conn():
    """Get a connection from the pool."""
    if _pool is None:
        init_db_pool()
    return _pool.getconn()
def put_conn(conn):
    """Return a connection to the pool."""
    if _pool is not None and conn is not None:
        _pool.putconn(conn)

conn = get_conn()
def db_init_schema():
    """Create pgvector extension + notes table if they don't exist."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding vector(384) NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()            
                    );
                    """
                )
    finally:
        put_conn(conn)
