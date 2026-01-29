from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import db
from . import notes_repo
# what does the dot in the imports below mean?
    # from .db import init_db_pool, init_db_schema
    # from . import notes_repo

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    db.init_db_pool()
    db.db_init_schema()
    yield
    # anything before the yield, will be executed before the application starts.

app = FastAPI(lifespan=lifespan)


# ---------- Pydantic schemas (API layer) ----------
class NoteCreate(BaseModel): # what is base model?
    content: str
class NoteOut(BaseModel):
    id: int
    content: str
    created_at: str
class SearchResult(BaseModel):
    id: int
    content: str
    created_at: str
    score: float

# ---------- Templates setup ----------

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- JSON API endpoints ----------

@app.post("/notes", response_model=NoteOut)
def create_note_endpoint(note_in: NoteCreate):
    note = notes_repo.create_note(note_in.content)
    return note


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note_endpoint(note_id: int):
    note = notes_repo.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.get("/notes", response_model=List[NoteOut])
def list_notes_endpoint(limit: int = 1):
    return notes_repo.list_notes(limit=limit)


@app.get("/search", response_model=List[SearchResult])
def search_notes_endpoint(q: str, limit: int = 1):
    return notes_repo.search_notes(q, limit=limit)