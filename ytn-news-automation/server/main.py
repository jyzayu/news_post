import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .services.firestore_service import FirestoreService
from .models.news import NewsCreate, NewsUpdate, NewsOut


load_dotenv()

app = FastAPI(title="YTN News API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = FirestoreService()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/news", response_model=List[NewsOut])
def list_news() -> List[Dict[str, Any]]:
    return db.list_news(limit=200)


@app.post("/news", response_model=NewsOut)
def create_news(payload: NewsCreate) -> Dict[str, Any]:
    return db.create_news(payload.model_dump(exclude_none=True))


@app.get("/news/{doc_id}", response_model=NewsOut)
def get_news(doc_id: str) -> Dict[str, Any]:
    item = db.get_news_by_id(doc_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@app.put("/news/{doc_id}", response_model=NewsOut)
def update_news(doc_id: str, payload: NewsUpdate) -> Dict[str, Any]:
    item = db.update_news(doc_id, payload.model_dump(exclude_none=True))
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@app.delete("/news/{doc_id}")
def delete_news(doc_id: str) -> Dict[str, str]:
    db.delete_news(doc_id)
    return {"status": "deleted"}






