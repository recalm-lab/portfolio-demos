"""社内文書RAGチャットボット（営業デモ）— FastAPI アプリ。

起動: uvicorn app.main:app --host 127.0.0.1 --port 8000
環境変数:
  LLM_PROVIDER=gemini|deepseek   （既定 gemini）
  EMBED_PROVIDER=gemini|local    （未指定時は LLM に連動: gemini→gemini / deepseek→local）
  GEMINI_API_KEY / DEEPSEEK_API_KEY
  DOCS_DIR （既定: プロジェクト直下の docs/）
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.providers import build_providers
from app.rag import RagIndex, answer_question, load_documents

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(os.environ.get("DOCS_DIR", BASE_DIR / "docs"))
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="社内文書RAGチャットボット（自社デモ）")

_state: dict = {}


@app.on_event("startup")
def _startup() -> None:
    llm, embedder = build_providers()
    chunks = load_documents(DOCS_DIR)
    index = RagIndex(chunks, embedder)
    _state.update(llm=llm, index=index)
    print(f"[rag-demo] chunks={len(chunks)} llm={llm.name} embedder={embedder.name}")


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def index_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    idx: RagIndex = _state["index"]
    return {
        "status": "ok",
        "chunks": len(idx.chunks),
        "llm": _state["llm"].name,
        "embedder": idx.embedder.name,
    }


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    return answer_question(_state["index"], _state["llm"], req.question)
