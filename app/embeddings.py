from functools import lru_cache
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)

def get_model():
    # load pre-trained lightweight model to do txt to vec transformation
    return SentenceTransformer("all-MiniLM-L6-v2") # verify where gpt got this model from
def embed_text(text):
    model = get_model()
    vec = model.encode([text])[0] # 
    return vec.tolist()
def to_pgvector_literal(vec: List[float]) -> str:
    """Convert Python list[float] to pgvector literal: '[v1, v2, v3]'."""
    # why do we need to convert to str?
    result = []
    for x in vec:
        result.append(str(x))
    return "[" + ",".join(result) + "]"