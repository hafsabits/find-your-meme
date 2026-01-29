from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer
# every time uvicorn crashes and restarts, you have to add into memory again. EVERY TIME
# TODO
    # Swap in-memory NOTES for Postgres + psycopg2.
    # Replace Python-side similarity with pgvector and <->.
    # Add a tiny HTML UI on top.

app = FastAPI()
@lru_cache(maxsize=1)

def get_model():
    # load pre-trained lightweight model to do txt to vec transformation
    return SentenceTransformer("all-MiniLM-L6-v2") # verify where gpt got this model from
def embed_text(text):
    model = get_model()
    vec = model.encode([text])[0] # 
    return vec.tolist()
def cosin_similarity(a, b):
    # 1e-12 is very small value to prevent dividing by zero
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)

class Note(BaseModel):
    id: int
    content: str
class NoteCreate(BaseModel):
    content: str
class SearchResult(Note):
    score: float # similarity score for two sentences

NOTES = []
_next_id = 1

def add_note(content):
    global _next_id
    embedding = embed_text(content)
    note = {"id": _next_id,
            "content": content,
            "embedding": embedding
            }
    NOTES.append(note)
    _next_id += 1
    return Note(id=note["id"], content=note["content"])

def get_note_by_id(note_id):
    for n in NOTES:
        if n["id"] == note_id:
            return Note(id=n["id"], content=n["content"])
    return None
def search_notes(query, limit: int = 10) -> List[SearchResult]:
    if not NOTES:
        return []
    # start by embedding search query
    q_emb = np.array(embed_text(query), dtype=float)
    results = []
    # then search the entire db to find vec most similar
    for n in NOTES:
        n_emb = np.array(n["embedding"], dtype=float)
        score = cosin_similarity(q_emb, n_emb)
        results.append(
            SearchResult(
                id=n["id"],
                content=n["content"],
                score=score,
            )
        )
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/notes", response_model=Note)
def create_note_endpoint(note_in: NoteCreate):
    return add_note(note_in.content)
@app.get("/notes/{note_id}", response_model=Note)
def get_note_endpoint(note_id):
    note = get_note_by_id(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note
@app.get("/search", response_model=List[SearchResult])
def search_notes_endpoint(q, limit: int = 10):
    return search_notes(q, limit=limit)